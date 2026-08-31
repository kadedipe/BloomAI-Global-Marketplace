from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Role, User
from .security import password_hash


@dataclass(frozen=True)
class AdminBootstrapResult:
    user: User
    created: bool
    credentials_updated: bool


async def bootstrap_admin(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    name: str,
    update_existing: bool = False,
) -> AdminBootstrapResult:
    normalized_email = email.strip().lower()
    normalized_name = name.strip()

    if not normalized_email:
        raise ValueError("Admin email is required")
    if len(password) < 10 or len(password) > 128:
        raise ValueError("Admin password must be between 10 and 128 characters")
    if len(normalized_name) < 2 or len(normalized_name) > 120:
        raise ValueError("Admin name must be between 2 and 120 characters")

    existing = (
        await db.execute(select(User).where(User.email == normalized_email))
    ).scalar_one_or_none()

    if existing:
        if existing.role != Role.admin:
            raise ValueError(
                "An account with this email already exists and is not an administrator; "
                "refusing to elevate it automatically"
            )
        if not update_existing:
            return AdminBootstrapResult(
                user=existing,
                created=False,
                credentials_updated=False,
            )

        existing.name = normalized_name
        existing.password_hash = password_hash.hash(password)
        await db.commit()
        await db.refresh(existing)
        return AdminBootstrapResult(
            user=existing,
            created=False,
            credentials_updated=True,
        )

    user = User(
        email=normalized_email,
        name=normalized_name,
        role=Role.admin,
        password_hash=password_hash.hash(password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return AdminBootstrapResult(user=user, created=True, credentials_updated=False)
