import os
from unittest.mock import AsyncMock, patch

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings
from pydantic import ValidationError
import pytest


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


def test_vendor_can_create_product():
    with TestClient(app) as client:
        payload = {
            "email": "catalog@example.com",
            "password": "strong-password",
            "name": "Catalog Vendor",
            "role": "vendor",
        }
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        token = client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        ).json()["access_token"]
        with patch("app.main.publish_event", new=AsyncMock()) as publisher:
            response = client.post(
                "/api/v1/products",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": "Peace Lily",
                    "description": "Indoor plant",
                    "price": "24.99",
                    "currency": "USD",
                },
            )
        assert response.status_code == 201
        assert response.json()["name"] == "Peace Lily"
        publisher.assert_awaited_once()


def test_customer_cannot_create_product():
    with TestClient(app) as client:
        payload = {
            "email": "customer@example.com",
            "password": "strong-password",
            "name": "Plant Buyer",
            "role": "customer",
        }
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        token = client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        ).json()["access_token"]
        response = client.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Rose", "price": "10.00", "currency": "USD"},
        )
        assert response.status_code == 403


def test_production_rejects_weak_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="weak")
