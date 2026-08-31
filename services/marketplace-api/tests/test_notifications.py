import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient

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
