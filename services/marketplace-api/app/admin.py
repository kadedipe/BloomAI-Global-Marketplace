from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Order, OrderStatus, Product, Role, User
from .security import current_user
from .segmentation import OrganizationSize, ParticipantCategory, ParticipantProfile

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


async def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != Role.admin:
        raise HTTPException(403, "Admin access required")
    return user


class SegmentUpdate(BaseModel):
    organization_name: str | None = Field(default=None, max_length=180)
    organization_size: OrganizationSize
    category: ParticipantCategory
    country: str | None = Field(default=None, max_length=100)
    address_line1: str | None = Field(default=None, max_length=180)
    city: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=32)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    geocoding_source: str | None = Field(default=None, max_length=80)
    industry: str | None = Field(default=None, max_length=120)


async def profile_map(db: AsyncSession) -> dict[int, ParticipantProfile]:
    profiles = (await db.execute(select(ParticipantProfile))).scalars().all()
    return {profile.user_id: profile for profile in profiles}


def profile_payload(user: User, profile: ParticipantProfile | None) -> dict:
    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "organization_name": profile.organization_name if profile else None,
        "organization_size": (
            profile.organization_size.value if profile else OrganizationSize.unclassified.value
        ),
        "category": (
            profile.category.value if profile else ParticipantCategory.unclassified.value
        ),
        "country": profile.country if profile else None,
        "address_line1": profile.address_line1 if profile else None,
        "city": profile.city if profile else None,
        "region": profile.region if profile else None,
        "postal_code": profile.postal_code if profile else None,
        "latitude": profile.latitude if profile else None,
        "longitude": profile.longitude if profile else None,
        "geocoding_source": profile.geocoding_source if profile else None,
        "geocoded_at": profile.geocoded_at if profile else None,
        "industry": profile.industry if profile else None,
        "joined_at": user.created_at,
    }


@router.get("/analytics/overview")
async def analytics_overview(
    _: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    user_rows = (
        await db.execute(select(User.role, func.count(User.id)).group_by(User.role))
    ).all()
    role_counts = {role.value: count for role, count in user_rows}

    total_products = await db.scalar(select(func.count(Product.id))) or 0
    total_orders = await db.scalar(select(func.count(Order.id))) or 0
    paid_orders = (
        await db.scalar(select(func.count(Order.id)).where(Order.status == OrderStatus.paid))
        or 0
    )
    paid_revenue = (
        await db.scalar(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                Order.status == OrderStatus.paid
            )
        )
        or Decimal("0")
    )
    new_users_30d = (
        await db.scalar(select(func.count(User.id)).where(User.created_at >= thirty_days_ago))
        or 0
    )
    orders_30d = (
        await db.scalar(select(func.count(Order.id)).where(Order.created_at >= thirty_days_ago))
        or 0
    )
    revenue_30d = (
        await db.scalar(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                and_(Order.status == OrderStatus.paid, Order.paid_at >= thirty_days_ago)
            )
        )
        or Decimal("0")
    )

    return {
        "generated_at": now,
        "users": {
            "total": sum(role_counts.values()),
            "customers": role_counts.get(Role.customer.value, 0),
            "vendors": role_counts.get(Role.vendor.value, 0),
            "admins": role_counts.get(Role.admin.value, 0),
            "new_last_30_days": new_users_30d,
        },
        "commerce": {
            "products": total_products,
            "orders": total_orders,
            "paid_orders": paid_orders,
            "gross_revenue": float(paid_revenue),
            "orders_last_30_days": orders_30d,
            "revenue_last_30_days": float(revenue_30d),
        },
    }


@router.get("/analytics/segments")
async def analytics_segments(
    _: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    users = (await db.execute(select(User).where(User.role != Role.admin))).scalars().all()
    profiles = await profile_map(db)

    result = {}
    for role in (Role.customer, Role.vendor):
        role_users = [user for user in users if user.role == role]
        size_counts = Counter()
        category_counts = Counter()
        country_counts = Counter()
        for user in role_users:
            profile = profiles.get(user.id)
            size_counts[
                profile.organization_size.value
                if profile
                else OrganizationSize.unclassified.value
            ] += 1
            category_counts[
                profile.category.value
                if profile
                else ParticipantCategory.unclassified.value
            ] += 1
            if profile and profile.country:
                country_counts[profile.country] += 1

        result[role.value] = {
            "total": len(role_users),
            "by_size": dict(size_counts),
            "by_category": dict(category_counts),
            "by_country": dict(country_counts.most_common(12)),
        }

    return result


@router.get("/participants")
async def participants(
    role: Role | None = Query(default=None),
    organization_size: OrganizationSize | None = Query(default=None),
    category: ParticipantCategory | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).where(User.role != Role.admin).order_by(User.created_at.desc())
    if role:
        if role == Role.admin:
            return []
        query = query.where(User.role == role)

    users = (await db.execute(query)).scalars().all()
    profiles = await profile_map(db)

    filtered = []
    for user in users:
        profile = profiles.get(user.id)
        current_size = (
            profile.organization_size if profile else OrganizationSize.unclassified
        )
        current_category = (
            profile.category if profile else ParticipantCategory.unclassified
        )
        if organization_size and current_size != organization_size:
            continue
        if category and current_category != category:
            continue
        filtered.append((user, profile))

    page = filtered[offset : offset + limit]
    payload = []
    for user, profile in page:
        base = profile_payload(user, profile)
        if user.role == Role.customer:
            order_count = (
                await db.scalar(select(func.count(Order.id)).where(Order.buyer_id == user.id))
                or 0
            )
            spend = (
                await db.scalar(
                    select(func.coalesce(func.sum(Order.total), 0)).where(
                        and_(Order.buyer_id == user.id, Order.status == OrderStatus.paid)
                    )
                )
                or Decimal("0")
            )
            base["activity"] = {
                "orders": order_count,
                "paid_spend": float(spend),
            }
        else:
            product_count = (
                await db.scalar(
                    select(func.count(Product.id)).where(Product.vendor_id == user.id)
                )
                or 0
            )
            vendor_order_count = (
                await db.scalar(
                    select(func.count(Order.id))
                    .join(Product, Order.product_id == Product.id)
                    .where(Product.vendor_id == user.id)
                )
                or 0
            )
            vendor_revenue = (
                await db.scalar(
                    select(func.coalesce(func.sum(Order.total), 0))
                    .join(Product, Order.product_id == Product.id)
                    .where(
                        and_(
                            Product.vendor_id == user.id,
                            Order.status == OrderStatus.paid,
                        )
                    )
                )
                or Decimal("0")
            )
            base["activity"] = {
                "products": product_count,
                "orders_received": vendor_order_count,
                "gross_sales": float(vendor_revenue),
            }
        payload.append(base)

    return {"total": len(filtered), "items": payload}


@router.patch("/participants/{user_id}/segment")
async def update_segment(
    user_id: int,
    payload: SegmentUpdate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if (payload.latitude is None) != (payload.longitude is None):
        raise HTTPException(422, "Latitude and longitude must be provided together")

    user = await db.get(User, user_id)
    if not user or user.role == Role.admin:
        raise HTTPException(404, "Marketplace participant not found")

    profile = (
        await db.execute(
            select(ParticipantProfile).where(ParticipantProfile.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not profile:
        profile = ParticipantProfile(user_id=user_id)
        db.add(profile)

    coordinates_changed = (
        profile.latitude != payload.latitude or profile.longitude != payload.longitude
    )
    profile.organization_name = payload.organization_name
    profile.organization_size = payload.organization_size
    profile.category = payload.category
    profile.country = payload.country
    profile.address_line1 = payload.address_line1
    profile.city = payload.city
    profile.region = payload.region
    profile.postal_code = payload.postal_code
    profile.latitude = payload.latitude
    profile.longitude = payload.longitude
    profile.geocoding_source = payload.geocoding_source if payload.latitude is not None else None
    if coordinates_changed:
        profile.geocoded_at = datetime.now(timezone.utc) if payload.latitude is not None else None
    profile.industry = payload.industry
    await db.commit()
    await db.refresh(profile)
    return profile_payload(user, profile)


@router.get("/activity")
async def activity_feed(
    limit: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    users = (
        await db.execute(select(User).order_by(User.created_at.desc()).limit(limit))
    ).scalars().all()
    products = (
        await db.execute(select(Product).order_by(Product.created_at.desc()).limit(limit))
    ).scalars().all()
    orders = (
        await db.execute(select(Order).order_by(Order.created_at.desc()).limit(limit))
    ).scalars().all()

    user_lookup = {user.id: user for user in users}
    product_lookup = {product.id: product for product in products}
    events = []

    for user in users:
        events.append(
            {
                "type": "account.created",
                "occurred_at": user.created_at,
                "actor_id": user.id,
                "actor_name": user.name,
                "role": user.role.value,
                "summary": f"{user.name} joined as {user.role.value}",
            }
        )
    for product in products:
        vendor = user_lookup.get(product.vendor_id) or await db.get(User, product.vendor_id)
        events.append(
            {
                "type": "product.created",
                "occurred_at": product.created_at,
                "actor_id": product.vendor_id,
                "actor_name": vendor.name if vendor else f"Vendor {product.vendor_id}",
                "role": "vendor",
                "summary": f"Published {product.name}",
            }
        )
    for order in orders:
        buyer = user_lookup.get(order.buyer_id) or await db.get(User, order.buyer_id)
        product = product_lookup.get(order.product_id) or await db.get(Product, order.product_id)
        events.append(
            {
                "type": "order.paid" if order.status == OrderStatus.paid else "order.created",
                "occurred_at": order.paid_at or order.created_at,
                "actor_id": order.buyer_id,
                "actor_name": buyer.name if buyer else f"Customer {order.buyer_id}",
                "role": "customer",
                "summary": f"{order.status.value.title()} order for {product.name if product else 'product'}",
                "amount": float(order.total),
                "currency": order.currency,
            }
        )

    events.sort(key=lambda item: item["occurred_at"], reverse=True)
    return events[:limit]
