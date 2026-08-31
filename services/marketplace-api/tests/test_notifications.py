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
