import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient

from app.main import app
from app.models import Role, User
from app.production_validation import settings
from app.security import current_user

ORIGIN = {"origin": "http://localhost:5173"}


def admin_user():
    return User(
        id=999999,
        email="commerce-admin@example.com",
        name="Commerce Admin",
        role=Role.admin,
        password_hash="not-used",
    )


def test_readiness_is_admin_only():
    with TestClient(app, headers=ORIGIN) as client:
        payload = {
            "email": "readiness-customer@example.com",
            "password": "strong-password",
            "name": "Readiness Customer",
            "role": "customer",
        }
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        assert client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        ).status_code == 200
        assert client.get("/api/v1/admin/commerce/readiness").status_code == 403


def test_readiness_reports_provider_state_without_secret_values(monkeypatch):
    app.dependency_overrides[current_user] = admin_user
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "database_url", "postgresql+asyncpg://user:secret@db/prod")
    monkeypatch.setattr(settings, "public_api_base_url", "https://api.example.test")
    monkeypatch.setattr(settings, "web_base_url", "https://www.example.test")
    monkeypatch.setattr(settings, "paystack_secret_key", "sk_test_redacted")
    monkeypatch.setattr(settings, "paystack_callback_url", "https://www.example.test/payment/callback")
    monkeypatch.setattr(settings, "aftership_api_key", "as-test-redacted")
    monkeypatch.setattr(settings, "aftership_webhook_secret", "webhook-redacted")
    try:
        with TestClient(app, headers=ORIGIN) as client:
            response = client.get("/api/v1/admin/commerce/readiness")
            assert response.status_code == 200
            data = response.json()
            assert data["ready"] is True
            assert data["provider_state"]["paystack"]["mode"] == "test"
            assert data["provider_state"]["paystack"]["webhook_url"] == (
                "https://api.example.test/api/v1/payments/webhook"
            )
            assert data["provider_state"]["aftership"]["webhook_url"] == (
                "https://api.example.test/api/v1/shipping/aftership/webhook"
            )
            body = response.text
            assert "sk_test_redacted" not in body
            assert "as-test-redacted" not in body
            assert "webhook-redacted" not in body
            assert "secret@db" not in body
    finally:
        app.dependency_overrides.pop(current_user, None)
