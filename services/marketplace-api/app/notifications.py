from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .database import get_db
from .email_delivery import send_transactional_email
from .media import delete_profile_image, upload_profile_image
from .models import (
    FulfillmentStatus,
    Notification,
    NotificationPreference,
    Order,
    OrderStatus,
    Product,
    RefundStatus,
    Role,
    User,
)
from .payments import request as paystack_request
from .schemas import UserResponse
from .security import current_user

api_router = APIRouter(prefix="/api/v1")
notification_router = APIRouter(prefix="/notifications", tags=["notifications"])
orders_router = APIRouter(prefix="/orders", tags=["orders"])
settings = get_settings()

CATEGORY_FIELDS = {
    "account": "account_in_app",
    "orders": "orders_in_app",
    "payments": "payments_in_app",
    "vendor_activity": "vendor_activity_in_app",
    "system": "system_in_app",
}


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    title: str
    message: str
    link: str | None
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int


class NotificationPreferenceResponse(BaseModel):
    account_in_app: bool
    orders_in_app: bool
    payments_in_app: bool
    vendor_activity_in_app: bool
    system_in_app: bool
    email_enabled: bool
    email_delivery_available: bool
    critical_admin_alerts_mandatory: bool


class NotificationPreferenceUpdate(BaseModel):
    account_in_app: bool = True
    orders_in_app: bool = True
    payments_in_app: bool = True
    vendor_activity_in_app: bool = True
    system_in_app: bool = True
    email_enabled: bool = False


class TestNotificationRequest(BaseModel):
    target_role: Role


class TestNotificationResponse(BaseModel):
    target_role: Role
    delivered: int


class OrderCheckoutRequest(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=20)
    recipient_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=5, max_length=40)
    address_line1: str = Field(min_length=4, max_length=240)
    city: str = Field(min_length=2, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=32)
    country: str = Field(min_length=2, max_length=120)
    buyer_note: str | None = Field(default=None, max_length=1000)


class OrderCheckoutResponse(BaseModel):
    order_id: int
    reference: str
    authorization_url: str
    access_code: str


class OrderSummaryResponse(BaseModel):
    id: int
    reference: str
    product_id: int
    product_name: str
    product_image_url: str | None
    buyer_id: int
    buyer_name: str
    vendor_id: int
    vendor_name: str
    quantity: int
    unit_price: Decimal
    total: Decimal
    currency: str
    status: OrderStatus
    fulfillment_status: FulfillmentStatus
    carrier: str | None
    tracking_number: str | None
    shipped_at: datetime | None
    delivered_at: datetime | None
    refund_status: RefundStatus
    refund_reason: str | None
    refund_requested_at: datetime | None
    refund_processed_at: datetime | None
    recipient_name: str | None
    phone: str | None
    address_line1: str | None
    city: str | None
    region: str | None
    postal_code: str | None
    country: str | None
    buyer_note: str | None
    created_at: datetime
    paid_at: datetime | None


def notification_category(type: str) -> str:
    if type.startswith("account."):
        return "account"
    if type.startswith("order."):
        return "orders"
    if type.startswith("payment."):
        return "payments"
    if type.startswith("product.") or type.startswith("vendor."):
        return "vendor_activity"
    return "system"


def critical_for_admin(type: str) -> bool:
    return type.startswith("system.critical")


async def get_or_create_preferences(db: AsyncSession, user_id: int) -> NotificationPreference:
    preference = (
        await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == user_id))
    ).scalar_one_or_none()
    if preference is None:
        preference = NotificationPreference(user_id=user_id)
        db.add(preference)
        await db.flush()
    return preference


async def delivery_preferences(
    db: AsyncSession, user: User, type: str, *, force: bool = False
) -> tuple[bool, bool]:
    preference = await get_or_create_preferences(db, user.id)
    mandatory = user.role == Role.admin and critical_for_admin(type)
    category_field = CATEGORY_FIELDS[notification_category(type)]
    in_app = force or mandatory or bool(getattr(preference, category_field))
    email = mandatory or (preference.email_enabled and bool(getattr(preference, category_field)))
    return in_app, email


async def create_notification(
    db: AsyncSession,
    *,
    user_id: int,
    type: str,
    title: str,
    message: str,
    link: str | None = None,
    force: bool = False,
) -> Notification | None:
    user = await db.get(User, user_id)
    if not user:
        return None
    in_app, email = await delivery_preferences(db, user, type, force=force)
    notification = None
    if in_app:
        notification = Notification(
            user_id=user_id, type=type, title=title, message=message, link=link
        )
        db.add(notification)
    if email and settings.transactional_email_enabled:
        await send_transactional_email(to=user.email, subject=title, message=message, link=link)
    return notification


async def notify_users(
    db: AsyncSession,
    user_ids: set[int] | list[int] | tuple[int, ...],
    *,
    type: str,
    title: str,
    message: str,
    link: str | None = None,
    force: bool = False,
) -> int:
    delivered = 0
    for user_id in set(user_ids):
        created = await create_notification(
            db,
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            link=link,
            force=force,
        )
        delivered += int(created is not None)
    return delivered


async def notify_role(
    db: AsyncSession,
    role: Role,
    *,
    type: str,
    title: str,
    message: str,
    link: str | None = None,
    exclude_user_ids: set[int] | None = None,
) -> int:
    excluded = exclude_user_ids or set()
    user_ids = (await db.execute(select(User.id).where(User.role == role))).scalars().all()
    return await notify_users(
        db,
        {user_id for user_id in user_ids if user_id not in excluded},
        type=type,
        title=title,
        message=message,
        link=link,
    )


def preference_response(
    preference: NotificationPreference, user: User
) -> NotificationPreferenceResponse:
    return NotificationPreferenceResponse(
        **{field: getattr(preference, field) for field in CATEGORY_FIELDS.values()},
        email_enabled=preference.email_enabled,
        email_delivery_available=settings.transactional_email_enabled,
        critical_admin_alerts_mandatory=user.role == Role.admin,
    )


def ensure_available(product: Product, quantity: int) -> None:
    if not product.is_active:
        raise HTTPException(status_code=409, detail="This listing is currently unavailable")
    if product.inventory_quantity is not None and product.inventory_quantity < quantity:
        raise HTTPException(
            status_code=409,
            detail=f"Only {product.inventory_quantity} unit(s) are currently available",
        )


def reserve_inventory(product: Product, order: Order) -> None:
    if order.inventory_reserved:
        return
    ensure_available(product, order.quantity)
    if product.inventory_quantity is not None:
        product.inventory_quantity -= order.quantity
        order.inventory_reserved = True


def release_inventory(product: Product | None, order: Order) -> None:
    if not product or not order.inventory_reserved:
        return
    if product.inventory_quantity is not None:
        product.inventory_quantity += order.quantity
    order.inventory_reserved = False


async def order_summary(db: AsyncSession, order: Order) -> OrderSummaryResponse:
    product = await db.get(Product, order.product_id)
    buyer = await db.get(User, order.buyer_id)
    vendor = await db.get(User, product.vendor_id) if product else None
    return OrderSummaryResponse(
        id=order.id,
        reference=order.reference,
        product_id=order.product_id,
        product_name=product.name if product else f"Product #{order.product_id}",
        product_image_url=product.image_url if product else None,
        buyer_id=order.buyer_id,
        buyer_name=buyer.name if buyer else "Customer",
        vendor_id=product.vendor_id if product else 0,
        vendor_name=vendor.name if vendor else "Vendor",
        quantity=order.quantity,
        unit_price=order.unit_price,
        total=order.total,
        currency=order.currency,
        status=order.status,
        fulfillment_status=order.fulfillment_status,
        carrier=order.carrier,
        tracking_number=order.tracking_number,
        shipped_at=order.shipped_at,
        delivered_at=order.delivered_at,
        refund_status=order.refund_status,
        refund_reason=order.refund_reason,
        refund_requested_at=order.refund_requested_at,
        refund_processed_at=order.refund_processed_at,
        recipient_name=order.recipient_name,
        phone=order.phone,
        address_line1=order.address_line1,
        city=order.city,
        region=order.region,
        postal_code=order.postal_code,
        country=order.country,
        buyer_note=order.buyer_note,
        created_at=order.created_at,
        paid_at=order.paid_at,
    )


@notification_router.get("", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    items = (
        (
            await db.execute(
                query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit)
            )
        )
        .scalars()
        .all()
    )
    unread_count = (
        await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user.id, Notification.read_at.is_(None)
            )
        )
    ).scalar_one()
    return NotificationListResponse(items=list(items), unread_count=unread_count)


@notification_router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    preference = await get_or_create_preferences(db, user.id)
    await db.commit()
    await db.refresh(preference)
    return preference_response(preference, user)


@notification_router.patch("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    preference = await get_or_create_preferences(db, user.id)
    changes = payload.model_dump()
    if changes["email_enabled"] and not settings.transactional_email_enabled:
        raise HTTPException(
            status_code=409, detail="Transactional email delivery is not configured"
        )
    for field, value in changes.items():
        setattr(preference, field, value)
    preference.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(preference)
    return preference_response(preference, user)


@notification_router.post("/profile-photo", response_model=UserResponse)
async def upload_user_profile_photo(
    image: UploadFile = File(...),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in {Role.customer, Role.vendor}:
        raise HTTPException(
            status_code=403,
            detail="Profile photos are available to customer and vendor accounts",
        )
    previous_public_id = user.avatar_public_id
    uploaded = await upload_profile_image(image, user.id)
    user.avatar_url = uploaded["image_url"]
    user.avatar_public_id = uploaded["image_public_id"]
    await db.commit()
    await db.refresh(user)
    if previous_public_id and previous_public_id != user.avatar_public_id:
        await delete_profile_image(previous_public_id)
    return user


@notification_router.delete("/profile-photo", response_model=UserResponse)
async def remove_user_profile_photo(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    if user.role not in {Role.customer, Role.vendor}:
        raise HTTPException(
            status_code=403,
            detail="Profile photos are available to customer and vendor accounts",
        )
    previous_public_id = user.avatar_public_id
    user.avatar_url = None
    user.avatar_public_id = None
    await db.commit()
    await db.refresh(user)
    await delete_profile_image(previous_public_id)
    return user


@notification_router.post("/test", response_model=TestNotificationResponse, status_code=201)
async def send_test_notification(
    payload: TestNotificationRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Administrator access required")
    user_ids = (
        await db.execute(select(User.id).where(User.role == payload.target_role))
    ).scalars().all()
    unique_user_ids = set(user_ids)
    if not unique_user_ids:
        raise HTTPException(
            status_code=404,
            detail=f"No {payload.target_role.value} accounts are available for notification testing",
        )
    destination = "/admin.html" if payload.target_role == Role.admin else "/#market"
    delivered = await notify_users(
        db,
        unique_user_ids,
        type="system.test",
        title="BloomAI notification test",
        message=(
            "This is an administrator-initiated test notification. "
            "No order, payment, or marketplace analytics record was created."
        ),
        link=destination,
        force=True,
    )
    await db.commit()
    return TestNotificationResponse(target_role=payload.target_role, delivered=delivered)


@notification_router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    notification = await db.get(Notification, notification_id)
    if not notification or notification.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(notification)
    return notification


@notification_router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(timezone.utc))
    )
    await db.commit()


@orders_router.post("/checkout", response_model=OrderCheckoutResponse, status_code=201)
async def checkout_order(
    payload: OrderCheckoutRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in {Role.customer, Role.vendor}:
        raise HTTPException(status_code=403, detail="Customer or vendor account required")
    product = await db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.vendor_id == user.id:
        raise HTTPException(status_code=409, detail="Vendors cannot purchase their own product")
    ensure_available(product, payload.quantity)
    supported = {
        item.strip().upper() for item in settings.paystack_currencies.split(",")
    }
    if product.currency not in supported:
        raise HTTPException(
            status_code=422,
            detail=f"Paystack checkout is not enabled for {product.currency}",
        )

    total = product.price * payload.quantity
    reference = f"bloom-{uuid.uuid4().hex}"
    values = payload.model_dump(exclude={"product_id", "quantity"})
    for key, value in values.items():
        if isinstance(value, str):
            values[key] = value.strip() or None
    order = Order(
        reference=reference,
        buyer_id=user.id,
        product_id=product.id,
        quantity=payload.quantity,
        unit_price=product.price,
        total=total,
        currency=product.currency,
        status=OrderStatus.pending,
        **values,
    )
    reserve_inventory(product, order)
    db.add(order)
    await db.flush()
    try:
        data = await paystack_request(
            "POST",
            "/transaction/initialize",
            json={
                "email": user.email,
                "amount": int(total * Decimal("100")),
                "currency": product.currency,
                "reference": reference,
                "callback_url": settings.paystack_callback_url,
                "metadata": {
                    "order_id": order.id,
                    "product_id": product.id,
                    "buyer_id": user.id,
                },
            },
        )
    except HTTPException:
        await db.rollback()
        raise

    await db.commit()
    await create_notification(
        db,
        user_id=user.id,
        type="order.created",
        title="Order started",
        message=f"Your order for {product.name} is awaiting payment confirmation.",
        link="/#orders",
    )
    await create_notification(
        db,
        user_id=product.vendor_id,
        type="order.created",
        title="New order received",
        message=f"A customer started an order for {product.name} ({product.currency} {total}).",
        link="/#orders",
    )
    await notify_role(
        db,
        Role.admin,
        type="order.created",
        title="New marketplace order",
        message=f"Order #{order.id} was created for {product.name} ({product.currency} {total}).",
        link="/admin.html#activity",
        exclude_user_ids={user.id, product.vendor_id},
    )
    await db.commit()
    return OrderCheckoutResponse(order_id=order.id, reference=reference, **data)


@orders_router.get("", response_model=list[OrderSummaryResponse])
async def my_orders(
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    orders = (
        (
            await db.execute(
                select(Order)
                .where(Order.buyer_id == user.id)
                .order_by(Order.created_at.desc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return [await order_summary(db, order) for order in orders]


@orders_router.get("/sales", response_model=list[OrderSummaryResponse])
async def sales_orders(
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in {Role.vendor, Role.admin}:
        raise HTTPException(status_code=403, detail="Vendor access required")
    query = select(Order).join(Product, Product.id == Order.product_id)
    if user.role == Role.vendor:
        query = query.where(Product.vendor_id == user.id)
    orders = (
        (await db.execute(query.order_by(Order.created_at.desc()).limit(limit)))
        .scalars()
        .all()
    )
    return [await order_summary(db, order) for order in orders]


@orders_router.patch("/{order_id}/cancel", response_model=OrderSummaryResponse)
async def cancel_order(
    order_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await db.get(Order, order_id)
    if not order or order.buyer_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=409, detail="Only pending orders can be cancelled")
    product = await db.get(Product, order.product_id)
    release_inventory(product, order)
    order.status = OrderStatus.cancelled
    order.fulfillment_status = FulfillmentStatus.cancelled
    await create_notification(
        db,
        user_id=user.id,
        type="order.cancelled",
        title="Order cancelled",
        message=f"Order #{order.id} has been cancelled.",
        link="/#orders",
    )
    if product:
        await create_notification(
            db,
            user_id=product.vendor_id,
            type="order.cancelled",
            title="Customer cancelled order",
            message=f"Order #{order.id} for {product.name} was cancelled before payment.",
            link="/#orders",
        )
    await db.commit()
    await db.refresh(order)
    return await order_summary(db, order)


@orders_router.post("/{order_id}/pay", response_model=OrderCheckoutResponse)
async def retry_order_payment(
    order_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await db.get(Order, order_id)
    if not order or order.buyer_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in {OrderStatus.pending, OrderStatus.failed}:
        raise HTTPException(status_code=409, detail="This order cannot be sent for payment")
    product = await db.get(Product, order.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not order.inventory_reserved:
        reserve_inventory(product, order)
    reference = f"bloom-{uuid.uuid4().hex}"
    try:
        data = await paystack_request(
            "POST",
            "/transaction/initialize",
            json={
                "email": user.email,
                "amount": int(order.total * Decimal("100")),
                "currency": order.currency,
                "reference": reference,
                "callback_url": settings.paystack_callback_url,
                "metadata": {
                    "order_id": order.id,
                    "product_id": product.id,
                    "buyer_id": user.id,
                },
            },
        )
    except HTTPException:
        await db.rollback()
        raise
    order.reference = reference
    order.status = OrderStatus.pending
    order.fulfillment_status = FulfillmentStatus.unfulfilled
    await db.commit()
    return OrderCheckoutResponse(order_id=order.id, reference=reference, **data)


api_router.include_router(notification_router)
api_router.include_router(orders_router)
router = api_router
