from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .database import get_db
from .email_delivery import send_transactional_email
from .models import Notification, NotificationPreference, Role, User
from .security import current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])
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


async def delivery_preferences(db: AsyncSession, user: User, type: str, *, force: bool = False) -> tuple[bool, bool]:
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
        notification = Notification(user_id=user_id, type=type, title=title, message=message, link=link)
        db.add(notification)
    if email and settings.transactional_email_enabled:
        await send_transactional_email(
            to=user.email,
            subject=title,
            message=message,
            link=link,
        )
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
            db, user_id=user_id, type=type, title=title, message=message, link=link, force=force
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


def preference_response(preference: NotificationPreference, user: User) -> NotificationPreferenceResponse:
    return NotificationPreferenceResponse(
        **{field: getattr(preference, field) for field in CATEGORY_FIELDS.values()},
        email_enabled=preference.email_enabled,
        email_delivery_available=settings.transactional_email_enabled,
        critical_admin_alerts_mandatory=user.role == Role.admin,
    )


@router.get("", response_model=NotificationListResponse)
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
        (await db.execute(query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit)))
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


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    preference = await get_or_create_preferences(db, user.id)
    await db.commit()
    await db.refresh(preference)
    return preference_response(preference, user)


@router.patch("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    preference = await get_or_create_preferences(db, user.id)
    changes = payload.model_dump()
    if changes["email_enabled"] and not settings.transactional_email_enabled:
        raise HTTPException(status_code=409, detail="Transactional email delivery is not configured")
    for field, value in changes.items():
        setattr(preference, field, value)
    preference.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(preference)
    return preference_response(preference, user)


@router.post("/test", response_model=TestNotificationResponse, status_code=201)
async def send_test_notification(
    payload: TestNotificationRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Administrator access required")
    user_ids = (await db.execute(select(User.id).where(User.role == payload.target_role))).scalars().all()
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


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
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


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(timezone.utc))
    )
    await db.commit()
