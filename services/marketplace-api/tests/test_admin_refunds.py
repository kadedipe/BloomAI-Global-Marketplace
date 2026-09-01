import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient

from app.main import app
from app.models import Role, User
from app.security import current_user

ORIGIN = {"origin": "http://localhost:5173"}


def admin_user():
    return User(
        id=999998,
        email="refund-admin@example.com",
        name="Refund Admin",
        role=Role.admin,
        password_hash="not-used",
    )


def test_refund_queue_is_admin_only():
    with TestClient(app, headers=ORIGIN) as client:
        payload = {
            "email": "refund-customer@example.com",
            "password": "strong-password",
            "name": "Refund Customer",
            "role": "customer",
        }
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        assert client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        ).status_code == 200
        assert client.get("/api/v1/admin/commerce/refunds").status_code == 403


def test_admin_can_load_refund_queue():
    app.dependency_overrides[current_user] = admin_user
    try:
        with TestClient(app, headers=ORIGIN) as client:
            response = client.get("/api/v1/admin/commerce/refunds")
            assert response.status_code == 200
            assert "items" in response.json()
            assert isinstance(response.json()["items"], list)
    finally:
        app.dependency_overrides.pop(current_user, None)
