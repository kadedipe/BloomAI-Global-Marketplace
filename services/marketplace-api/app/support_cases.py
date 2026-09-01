from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import (
    Role,
    SupportCase,
    SupportCaseMessage,
    SupportCasePriority,
    SupportCaseStatus,
    User,
)
from .notifications import create_notification, notify_role
from .security import current_user

router = APIRouter(tags=["support-cases"])


class SupportCaseMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    author_user_id: int | None
    author_role: str
    body: str
    created_at: datetime


class SupportCaseResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    order_id: int | None
    category: str
    subject: str
    status: SupportCaseStatus
    priority: SupportCasePriority
    assigned_admin_id: int | None
    last_message_at: datetime
    created_at: datetime
    updated_at: datetime
    messages: list[SupportCaseMessageResponse] = []


class SupportCaseListResponse(BaseModel):
    items: list[SupportCaseResponse]


class SupportCaseReplyRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)


class AdminSupportCaseUpdate(BaseModel):
    status: SupportCaseStatus | None = None
    priority: SupportCasePriority | None = None
    assign_to_me: bool = False


def require_participant(user: User) -> None:
    if user.role not in {Role.customer, Role.vendor}:
        raise HTTPException(status_code=403, detail="Customer or vendor account required")


def require_admin(user: User) -> None:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Administrator access required")


async def case_response(db: AsyncSession, case: SupportCase) -> SupportCaseResponse:
    owner = await db.get(User, case.user_id)
    messages = (
        (
            await db.execute(
                select(SupportCaseMessage)
                .where(SupportCaseMessage.case_id == case.id)
                .order_by(SupportCaseMessage.created_at.asc(), SupportCaseMessage.id.asc())
            )
        )
        .scalars()
        .all()
    )
    return SupportCaseResponse(
        id=case.id,
        user_id=case.user_id,
        user_name=owner.name if owner else "Participant",
        user_email=owner.email if owner else "",
        order_id=case.order_id,
        category=case.category,
        subject=case.subject,
        status=case.status,
        priority=case.priority,
        assigned_admin_id=case.assigned_admin_id,
        last_message_at=case.last_message_at,
        created_at=case.created_at,
        updated_at=case.updated_at,
        messages=list(messages),
    )


async def open_support_case(
    db: AsyncSession,
    *,
    user: User,
    category: str,
    message: str,
    order_id: int | None,
    priority: SupportCasePriority = SupportCasePriority.normal,
) -> tuple[SupportCase, int]:
    subject = f"{category.replace('_', ' ').title()} support request"
    case = SupportCase(
        user_id=user.id,
        order_id=order_id,
        category=category,
        subject=subject,
        status=SupportCaseStatus.open,
        priority=priority,
    )
    db.add(case)
    await db.flush()
    db.add(
        SupportCaseMessage(
            case_id=case.id,
            author_user_id=user.id,
            author_role=user.role.value,
            body=message.strip(),
        )
    )
    case.last_message_at = datetime.now(timezone.utc)

    notification_type = (
        "system.critical.support" if priority == SupportCasePriority.critical else "system.support"
    )
    admins_notified = await notify_role(
        db,
        Role.admin,
        type=notification_type,
        title=f"Support case #{case.id}: {subject}",
        message=(
            f"{user.name} ({user.email}) opened support case #{case.id}."
            + (f" Order #{order_id}." if order_id else "")
            + f" {message.strip()}"
        ),
        link=f"/admin.html#support-case-{case.id}",
    )
    await create_notification(
        db,
        user_id=user.id,
        type="system.support",
        title=f"Support case #{case.id} opened",
        message="Your support request was recorded. You can continue the conversation from BloomAI Support.",
        link="/#market",
        force=True,
    )
    return case, admins_notified


async def participant_case(db: AsyncSession, user: User, case_id: int) -> SupportCase:
    case = await db.get(SupportCase, case_id)
    if not case or case.user_id != user.id:
        raise HTTPException(status_code=404, detail="Support case not found")
    return case


@router.get("/support/cases", response_model=SupportCaseListResponse)
async def list_my_support_cases(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    require_participant(user)
    cases = (
        (
            await db.execute(
                select(SupportCase)
                .where(SupportCase.user_id == user.id)
                .order_by(SupportCase.last_message_at.desc(), SupportCase.id.desc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return SupportCaseListResponse(items=[await case_response(db, item) for item in cases])


@router.get("/support/cases/{case_id}", response_model=SupportCaseResponse)
async def get_my_support_case(
    case_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    require_participant(user)
    case = await participant_case(db, user, case_id)
    return await case_response(db, case)


@router.post("/support/cases/{case_id}/reply", response_model=SupportCaseResponse)
async def reply_to_my_support_case(
    case_id: int,
    payload: SupportCaseReplyRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    require_participant(user)
    case = await participant_case(db, user, case_id)
    if case.status in {SupportCaseStatus.resolved, SupportCaseStatus.closed}:
        raise HTTPException(
            status_code=409,
            detail="Resolved or closed support cases must be reopened by an administrator before receiving replies",
        )
    db.add(
        SupportCaseMessage(
            case_id=case.id,
            author_user_id=user.id,
            author_role=user.role.value,
            body=payload.message.strip(),
        )
    )
    case.last_message_at = datetime.now(timezone.utc)
    if case.status == SupportCaseStatus.waiting_on_user:
        case.status = SupportCaseStatus.open
    await notify_role(
        db,
        Role.admin,
        type="system.support",
        title=f"New reply on support case #{case.id}",
        message=f"{user.name} replied to support case #{case.id}: {payload.message.strip()}",
        link=f"/admin.html#support-case-{case.id}",
    )
    await db.commit()
    await db.refresh(case)
    return await case_response(db, case)


@router.get("/admin/support/cases", response_model=SupportCaseListResponse)
async def list_admin_support_cases(
    case_status: SupportCaseStatus | None = Query(default=None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    query = select(SupportCase)
    if case_status is not None:
        query = query.where(SupportCase.status == case_status)
    cases = (
        (
            await db.execute(
                query.order_by(SupportCase.last_message_at.desc(), SupportCase.id.desc()).limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return SupportCaseListResponse(items=[await case_response(db, item) for item in cases])


@router.get("/admin/support/cases/{case_id}", response_model=SupportCaseResponse)
async def get_admin_support_case(
    case_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    case = await db.get(SupportCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Support case not found")
    return await case_response(db, case)


@router.patch("/admin/support/cases/{case_id}", response_model=SupportCaseResponse)
async def update_admin_support_case(
    case_id: int,
    payload: AdminSupportCaseUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    case = await db.get(SupportCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Support case not found")

    status_changed = payload.status is not None and payload.status != case.status
    if payload.status is not None:
        case.status = payload.status
    if payload.priority is not None:
        case.priority = payload.priority
    if payload.assign_to_me:
        case.assigned_admin_id = user.id

    if status_changed:
        await create_notification(
            db,
            user_id=case.user_id,
            type="system.support",
            title=f"Support case #{case.id} updated",
            message=f"Your support case status is now {case.status.value.replace('_', ' ')}.",
            link="/#market",
            force=True,
        )
    await db.commit()
    await db.refresh(case)
    return await case_response(db, case)


@router.post(
    "/admin/support/cases/{case_id}/reply",
    response_model=SupportCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def admin_reply_support_case(
    case_id: int,
    payload: SupportCaseReplyRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    case = await db.get(SupportCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Support case not found")
    if case.status == SupportCaseStatus.closed:
        raise HTTPException(status_code=409, detail="Closed support cases cannot receive replies")

    db.add(
        SupportCaseMessage(
            case_id=case.id,
            author_user_id=user.id,
            author_role=Role.admin.value,
            body=payload.message.strip(),
        )
    )
    case.assigned_admin_id = case.assigned_admin_id or user.id
    case.status = SupportCaseStatus.waiting_on_user
    case.last_message_at = datetime.now(timezone.utc)
    await create_notification(
        db,
        user_id=case.user_id,
        type="system.support",
        title=f"BloomAI replied to support case #{case.id}",
        message=payload.message.strip(),
        link="/#market",
        force=True,
    )
    await db.commit()
    await db.refresh(case)
    return await case_response(db, case)
