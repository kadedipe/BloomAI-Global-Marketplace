import asyncio
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient

from app.admin_bootstrap import bootstrap_admin
from app.database import SessionLocal
from app.main import app

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
