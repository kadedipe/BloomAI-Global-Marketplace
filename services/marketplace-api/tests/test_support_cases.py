import asyncio
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_bootstrap import bootstrap_admin
from app.database import SessionLocal
from app.main import app
from app.models import Order, OrderStatus, Product, User

ORIGIN = {"origin": "http://localhost:5173"}


def register_and_login(client: TestClient, email: str, role: str = "customer") -> None:
    payload = {
        "email": email,
        "password": "strong-password",
        "name": "Support User",
        "role": role,
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": payload["password"]},
    ).status_code == 200


async def create_admin(email: str, password: str = "strong-admin-password") -> None:
    async with SessionLocal() as db:
        await bootstrap_admin(db, email=email, password=password, name="Support Admin")


async def seed_support_orders(email: str) -> tuple[int, int]:
    async with SessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one()
        product = Product(
            vendor_id=user.id,
            name="Support Test Flower",
            description="Support context test",
            price=Decimal("25.00"),
            currency="NGN",
        )
        db.add(product)
        await db.flush()
        older = Order(
            reference=f"SUPPORT-OLD-{user.id}",
            buyer_id=user.id,
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("20.00"),
            total=Decimal("20.00"),
            currency="NGN",
            status=OrderStatus.cancelled,
            created_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        latest = Order(
            reference=f"SUPPORT-LATEST-{user.id}",
            buyer_id=user.id,
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("25.00"),
            total=Decimal("25.00"),
            currency="NGN",
            status=OrderStatus.paid,
            created_at=datetime.now(timezone.utc),
        )
        db.add_all([older, latest])
        await db.commit()
        return older.id, latest.id


def test_escalation_creates_persistent_support_case():
    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, "support-case-customer@example.com")
        response = client.post(
            "/api/v1/support/escalate",
            json={
                "message": "I think a payment may be unauthorized",
                "category": "payment",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["escalated"] is True
        assert body["case_id"] >= 1

        cases = client.get("/api/v1/support/cases").json()["items"]
        created = next(item for item in cases if item["id"] == body["case_id"])
        assert created["priority"] == "critical"
        assert created["status"] == "open"
        assert created["messages"][0]["body"] == "I think a payment may be unauthorized"


def test_critical_assistant_uses_latest_order_and_escalation_keeps_association():
    email = "support-latest-order@example.com"
    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, email)
        older_id, latest_id = asyncio.run(seed_support_orders(email))

        assistant = client.post(
            "/api/v1/support/assistant",
            json={"message": "I think a payment on my account may be unauthorized."},
        )
        assert assistant.status_code == 200
        body = assistant.json()
        assert body["order_id"] == latest_id
        assert f"Order #{latest_id}" in body["reply"]
        assert f"Order #{older_id}" not in body["reply"]

        escalated = client.post(
            "/api/v1/support/escalate",
            json={
                "message": "I think a payment on my account may be unauthorized.",
                "category": body["category"],
                "order_id": body["order_id"],
            },
        )
        assert escalated.status_code == 201
        case_id = escalated.json()["case_id"]
        case = client.get(f"/api/v1/support/cases/{case_id}").json()
        assert case["order_id"] == latest_id


def test_participant_can_reply_to_own_case():
    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, "support-case-reply@example.com", role="vendor")
        case_id = client.post(
            "/api/v1/support/escalate",
            json={"message": "I need help with a listing", "category": "vendor_product"},
        ).json()["case_id"]
        response = client.post(
            f"/api/v1/support/cases/{case_id}/reply",
            json={"message": "Here is more information about the listing."},
        )
        assert response.status_code == 200
        assert response.json()["messages"][-1]["author_role"] == "vendor"


def test_resolved_case_requires_admin_reopen_before_participant_reply():
    admin_email = "support-reopen-admin@example.com"
    owner_email = "support-reopen-owner@example.com"
    asyncio.run(create_admin(admin_email))
    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, owner_email)
        case_id = client.post(
            "/api/v1/support/escalate",
            json={"message": "I need help with my order", "category": "order"},
        ).json()["case_id"]
        client.post("/api/v1/auth/logout")
        assert client.post(
            "/api/v1/auth/login",
            json={"email": admin_email, "password": "strong-admin-password"},
        ).status_code == 200
        assert client.patch(
            f"/api/v1/admin/support/cases/{case_id}",
            json={"status": "resolved"},
        ).status_code == 200

        client.post("/api/v1/auth/logout")
        assert client.post(
            "/api/v1/auth/login",
            json={"email": owner_email, "password": "strong-password"},
        ).status_code == 200
        blocked = client.post(
            f"/api/v1/support/cases/{case_id}/reply",
            json={"message": "I have another detail."},
        )
        assert blocked.status_code == 409
        assert "reopened by an administrator" in blocked.json()["detail"]

        client.post("/api/v1/auth/logout")
        assert client.post(
            "/api/v1/auth/login",
            json={"email": admin_email, "password": "strong-admin-password"},
        ).status_code == 200
        reopened = client.patch(
            f"/api/v1/admin/support/cases/{case_id}",
            json={"status": "open"},
        )
        assert reopened.status_code == 200

        client.post("/api/v1/auth/logout")
        assert client.post(
            "/api/v1/auth/login",
            json={"email": owner_email, "password": "strong-password"},
        ).status_code == 200
        reply = client.post(
            f"/api/v1/support/cases/{case_id}/reply",
            json={"message": "I have another detail."},
        )
        assert reply.status_code == 200


def test_admin_can_assign_reply_and_resolve_case():
    admin_email = "support-case-admin@example.com"
    asyncio.run(create_admin(admin_email))
    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, "support-case-owner@example.com")
        case_id = client.post(
            "/api/v1/support/escalate",
            json={"message": "My refund is missing", "category": "refund"},
        ).json()["case_id"]
        client.post("/api/v1/auth/logout")
        assert client.post(
            "/api/v1/auth/login",
            json={"email": admin_email, "password": "strong-admin-password"},
        ).status_code == 200

        listed = client.get("/api/v1/admin/support/cases?status=open")
        assert listed.status_code == 200
        assert any(item["id"] == case_id for item in listed.json()["items"])

        assigned = client.patch(
            f"/api/v1/admin/support/cases/{case_id}",
            json={"assign_to_me": True, "status": "in_progress"},
        )
        assert assigned.status_code == 200
        assert assigned.json()["assigned_admin_id"] is not None
        assert assigned.json()["status"] == "in_progress"

        reply = client.post(
            f"/api/v1/admin/support/cases/{case_id}/reply",
            json={"message": "We received your support request and will follow up here."},
        )
        assert reply.status_code == 201
        assert reply.json()["status"] == "waiting_on_user"
        assert reply.json()["messages"][-1]["author_role"] == "admin"

        resolved = client.patch(
            f"/api/v1/admin/support/cases/{case_id}",
            json={"status": "resolved"},
        )
        assert resolved.status_code == 200
        assert resolved.json()["status"] == "resolved"


def test_admin_support_routes_reject_participants():
    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, "support-case-no-admin@example.com")
        response = client.get("/api/v1/admin/support/cases")
        assert response.status_code == 403
