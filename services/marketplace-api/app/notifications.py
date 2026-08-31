from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Notification, Role, User
from .security import current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


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


class TestNotificationRequest(BaseModel):
    target_role: Role


class TestNotificationResponse(BaseModel):
    target_role: Role
    delivered: int


async def create_notification(
    db: AsyncSession,
    *,
    user_id: int,
    type: str,
    title: str,
    message: str,
    link: str | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        link=link,
    )
    db.add(notification)
    return notification


async def notify_users(
    db: AsyncSession,
    user_ids: set[int] | list[int] | tuple[int, ...],
    *,
    type: str,
    title: str,
    message: str,
    link: str | None = None,
) -> None:
    for user_id in set(user_ids):
        await create_notification(
            db,
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            link=link,
        )


async def notify_role(
    db: AsyncSession,
    role: Role,
    *,
    type: str,
    title: str,
    message: str,
    link: str | None = None,
    exclude_user_ids: set[int] | None = None,
) -> None:
    excluded = exclude_user_ids or set()
    user_ids = (
        await db.execute(select(User.id).where(User.role == role))
    ).scalars().all()
    await notify_users(
        db,
        {user_id for user_id in user_ids if user_id not in excluded},
        type=type,
        title=title,
        message=message,
        link=link,
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
                Notification.user_id == user.id,
                Notification.read_at.is_(None),
            )
        )
    ).scalar_one()
    return NotificationListResponse(items=list(items), unread_count=unread_count)


@router.post("/test", response_model=TestNotificationResponse, status_code=201)
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
    await notify_users(
        db,
        unique_user_ids,
        type="system.test",
        title="BloomAI notification test",
        message=(
            "This is an administrator-initiated test notification. "
            "No order, payment, or marketplace analytics record was created."
        ),
        link=destination,
    )
    await db.commit()
    return TestNotificationResponse(
        target_role=payload.target_role,
        delivered=len(unique_user_ids),
    )


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
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(timezone.utc))
    )
    await db.commit()
