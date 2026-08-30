import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
from fastapi.testclient import TestClient
from app.main import app


def test_health():
    with TestClient(app) as client:
        assert client.get("/health/live").json()["status"] == "ok"


def test_registration_and_login():
    with TestClient(app) as client:
        payload = {
            "email": "vendor@example.com",
            "password": "strong-password",
            "name": "Bloom Vendor",
            "role": "vendor",
        }
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        response = client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        )
        assert response.status_code == 200 and response.json()["access_token"]
