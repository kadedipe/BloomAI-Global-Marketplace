import asyncio
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_bootstrap import bootstrap_admin
from app.database import SessionLocal
from app.main import app
from app.models import User
from app.notifications import create_notification


ORIGIN = {"origin": "http://localhost:5173"}


def register_and_login(client: TestClient, email: str, role: str = "customer") -> None:
    payload = {
        "email": email,
        "password": "strong-password",
        "name": "Notification User",
        "role": role,
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": payload["password"]},
    ).status_code == 200


async def create_admin(email: str, password: str = "strong-admin-password") -> None:
    async with SessionLocal() as db:
        await bootstrap_admin(
            db,
            email=email,
            password=password,
            name="Notification Admin",
        )


async def create_direct_notification(email: str, type: str) -> bool:
    async with SessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one()
        created = await create_notification(
            db,
            user_id=user.id,
            type=type,
            title="Preference test",
            message="Preference filtering test",
        )
        await db.commit()
        return created is not None


def test_new_account_receives_welcome_notification():
    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, "notifications-welcome@example.com")
        response = client.get("/api/v1/notifications")
        assert response.status_code == 200
        body = response.json()
        assert body["unread_count"] == 1
        assert body["items"][0]["type"] == "account.welcome"
        assert body["items"][0]["read_at"] is None


def test_notification_can_be_marked_read_and_all_read():
    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, "notifications-read@example.com", role="vendor")
        items = client.get("/api/v1/notifications").json()["items"]
        notification_id = items[0]["id"]

        response = client.patch(f"/api/v1/notifications/{notification_id}/read")
        assert response.status_code == 200
        assert response.json()["read_at"] is not None
        assert client.get("/api/v1/notifications").json()["unread_count"] == 0

        assert client.post("/api/v1/notifications/read-all").status_code == 204


def test_notifications_require_authentication():
    with TestClient(app, headers=ORIGIN) as client:
        assert client.get("/api/v1/notifications").status_code == 401
        assert client.get("/api/v1/notifications/preferences").status_code == 401


def test_user_can_update_preferences_and_suppress_order_notifications():
    email = "notifications-preferences@example.com"
    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, email)
        preferences = client.get("/api/v1/notifications/preferences")
        assert preferences.status_code == 200
        assert preferences.json()["orders_in_app"] is True
        assert preferences.json()["email_delivery_available"] is False

        payload = {
            "account_in_app": True,
            "orders_in_app": False,
            "payments_in_app": True,
            "vendor_activity_in_app": True,
            "system_in_app": True,
        }
        response = client.put("/api/v1/notifications/preferences", json=payload)
        assert response.status_code == 200
        assert response.json()["orders_in_app"] is False
        assert asyncio.run(create_direct_notification(email, "order.created")) is False
        assert asyncio.run(create_direct_notification(email, "payment.paid")) is True


def test_customer_cannot_send_test_notifications():
    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, "notifications-non-admin@example.com")
        response = client.post(
            "/api/v1/notifications/test",
            json={"target_role": "customer"},
        )
        assert response.status_code == 403


def test_admin_can_send_test_notification_to_customer_role():
    admin_email = "notifications-admin@example.com"
    admin_password = "strong-admin-password"
    customer_email = "notifications-target@example.com"

    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, customer_email)
        client.post("/api/v1/auth/logout")
        asyncio.run(create_admin(admin_email, admin_password))
        assert client.post(
            "/api/v1/auth/login",
            json={"email": admin_email, "password": admin_password},
        ).status_code == 200

        response = client.post(
            "/api/v1/notifications/test",
            json={"target_role": "customer"},
        )
        assert response.status_code == 201
        assert response.json()["target_role"] == "customer"
        assert response.json()["delivered"] >= 1

        client.post("/api/v1/auth/logout")
        assert client.post(
            "/api/v1/auth/login",
            json={"email": customer_email, "password": "strong-password"},
        ).status_code == 200
        items = client.get("/api/v1/notifications").json()["items"]
        assert any(item["type"] == "system.test" for item in items)


def test_admin_critical_alerts_bypass_system_preference():
    email = "notifications-critical-admin@example.com"
    password = "strong-admin-password"
    asyncio.run(create_admin(email, password))
    with TestClient(app, headers=ORIGIN) as client:
        assert client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        ).status_code == 200
        payload = {
            "account_in_app": False,
            "orders_in_app": False,
            "payments_in_app": False,
            "vendor_activity_in_app": False,
            "system_in_app": False,
        }
        response = client.put("/api/v1/notifications/preferences", json=payload)
        assert response.status_code == 200
        assert response.json()["critical_admin_alerts_mandatory"] is True
        assert asyncio.run(create_direct_notification(email, "system.critical.database")) is True
