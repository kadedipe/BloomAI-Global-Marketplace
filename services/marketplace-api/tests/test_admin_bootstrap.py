import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.admin_bootstrap import bootstrap_admin
from app.database import Base
from app.models import Role, User


@pytest.mark.asyncio
async def test_bootstrap_creates_admin_and_is_idempotent():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with sessions() as db:
        first = await bootstrap_admin(
            db,
            email="Admin@Example.com",
            password="strong-admin-password",
            name="BloomAI Administrator",
        )
        assert first.created is True
        assert first.user.email == "admin@example.com"
        assert first.user.role == Role.admin

        second = await bootstrap_admin(
            db,
            email="admin@example.com",
            password="different-password",
            name="Different Name",
        )
        assert second.created is False
        assert second.credentials_updated is False
        assert second.user.name == "BloomAI Administrator"

    await engine.dispose()


@pytest.mark.asyncio
async def test_bootstrap_refuses_to_promote_existing_marketplace_user():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with sessions() as db:
        db.add(
            User(
                email="vendor@example.com",
                name="Existing Vendor",
                role=Role.vendor,
                password_hash="not-used-in-this-test",
            )
        )
        await db.commit()

        with pytest.raises(ValueError, match="refusing to elevate"):
            await bootstrap_admin(
                db,
                email="vendor@example.com",
                password="strong-admin-password",
                name="BloomAI Administrator",
            )

        user = (
            await db.execute(select(User).where(User.email == "vendor@example.com"))
        ).scalar_one()
        assert user.role == Role.vendor

    await engine.dispose()
