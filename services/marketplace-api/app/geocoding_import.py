from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Role, User
from .segmentation import ParticipantProfile


class VerifiedGeocodeRow(BaseModel):
    """One verified participant location supplied by a trusted source."""

    user_id: int | None = Field(default=None, ge=1)
    email: str | None = Field(default=None, max_length=320)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    source: str = Field(min_length=2, max_length=80)
    verified: bool
    address_line1: str | None = Field(default=None, max_length=180)
    city: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=32)
    country: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_identity_and_verification(self) -> "VerifiedGeocodeRow":
        if self.user_id is None and not self.email:
            raise ValueError("user_id or email is required")
        if not self.verified:
            raise ValueError("coordinates must be explicitly verified before import")
        self.email = self.email.lower().strip() if self.email else None
        self.source = self.source.strip()
        if not self.source:
            raise ValueError("source is required")
        return self


class ImportResult(BaseModel):
    total_rows: int
    valid_rows: int
    applied_rows: int
    skipped_rows: int
    dry_run: bool
    errors: list[dict[str, Any]]


async def resolve_participant(db: AsyncSession, row: VerifiedGeocodeRow) -> User | None:
    if row.user_id is not None:
        user = await db.get(User, row.user_id)
        if user and row.email and user.email.lower() != row.email:
            return None
        return user
    return (
        await db.execute(select(User).where(User.email == row.email))
    ).scalar_one_or_none()


async def import_verified_geocodes(
    db: AsyncSession,
    rows: list[VerifiedGeocodeRow],
    *,
    dry_run: bool = True,
) -> ImportResult:
    """Validate and optionally apply trusted coordinates without geocoding or inference."""

    errors: list[dict[str, Any]] = []
    pending: list[tuple[User, VerifiedGeocodeRow]] = []
    seen_users: set[int] = set()

    for index, row in enumerate(rows, start=1):
        user = await resolve_participant(db, row)
        if not user or user.role == Role.admin:
            errors.append(
                {
                    "row": index,
                    "identifier": row.email or row.user_id,
                    "error": "Marketplace participant not found",
                }
            )
            continue
        if user.id in seen_users:
            errors.append(
                {
                    "row": index,
                    "identifier": row.email or row.user_id,
                    "error": "Duplicate participant in import batch",
                }
            )
            continue
        seen_users.add(user.id)
        pending.append((user, row))

    if not dry_run:
        now = datetime.now(timezone.utc)
        for user, row in pending:
            profile = (
                await db.execute(
                    select(ParticipantProfile).where(ParticipantProfile.user_id == user.id)
                )
            ).scalar_one_or_none()
            if profile is None:
                profile = ParticipantProfile(user_id=user.id)
                db.add(profile)

            profile.latitude = row.latitude
            profile.longitude = row.longitude
            profile.geocoding_source = row.source
            profile.geocoded_at = now

            # Address fields are only replaced when the trusted import supplies them.
            for field in (
                "address_line1",
                "city",
                "region",
                "postal_code",
                "country",
            ):
                value = getattr(row, field)
                if value is not None:
                    setattr(profile, field, value.strip() or None)

        await db.commit()

    return ImportResult(
        total_rows=len(rows),
        valid_rows=len(pending),
        applied_rows=0 if dry_run else len(pending),
        skipped_rows=len(errors),
        dry_run=dry_run,
        errors=errors,
    )
