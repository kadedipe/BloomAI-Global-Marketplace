import os
from unittest.mock import AsyncMock, patch

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import app


def test_health():
    with TestClient(app, headers={"origin": "http://localhost:5173"}) as client:
        assert client.get("/health/live").json()["status"] == "ok"


def test_registration_login_cookie_and_logout():
    with TestClient(app, headers={"origin": "http://localhost:5173"}) as client:
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
        assert response.status_code == 200
        assert response.json()["access_token"]
        assert "bloomai_session" in response.cookies
        assert client.get("/api/v1/auth/me").json()["email"] == payload["email"]
        assert client.post("/api/v1/auth/logout").status_code == 204
        assert client.get("/api/v1/auth/me").status_code == 401


def test_vendor_can_create_product_with_session_cookie():
    with TestClient(app, headers={"origin": "http://localhost:5173"}) as client:
        payload = {
            "email": "catalog@example.com",
            "password": "strong-password",
            "name": "Catalog Vendor",
            "role": "vendor",
        }
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        assert client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        ).status_code == 200
        with patch("app.main.publish_event", new=AsyncMock()) as publisher:
            response = client.post(
                "/api/v1/products",
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
    with TestClient(app, headers={"origin": "http://localhost:5173"}) as client:
        payload = {
            "email": "customer@example.com",
            "password": "strong-password",
            "name": "Plant Buyer",
            "role": "customer",
        }
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        assert client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        ).status_code == 200
        response = client.post(
            "/api/v1/products",
            json={"name": "Rose", "price": "10.00", "currency": "USD"},
        )
        assert response.status_code == 403


def test_production_rejects_weak_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="weak")


def test_vendor_cannot_modify_another_vendors_product():
    with TestClient(app, headers={"origin": "http://localhost:5173"}) as client:
        first = {"email": "owner@example.com", "password": "strong-password", "name": "Owner", "role": "vendor"}
        second = {"email": "other@example.com", "password": "strong-password", "name": "Other", "role": "vendor"}
        client.post("/api/v1/auth/register", json=first)
        client.post("/api/v1/auth/login", json={"email": first["email"], "password": first["password"]})
        with patch("app.main.publish_event", new=AsyncMock()):
            product = client.post("/api/v1/products", json={"name": "Owned Rose", "price": "50.00", "currency": "NGN"}).json()
        client.post("/api/v1/auth/logout")
        client.post("/api/v1/auth/register", json=second)
        client.post("/api/v1/auth/login", json={"email": second["email"], "password": second["password"]})
        assert client.patch(f"/api/v1/products/{product['id']}", json={"name": "Stolen Rose"}).status_code == 403
        assert client.delete(f"/api/v1/products/{product['id']}").status_code == 403


def test_cookie_mutation_rejects_untrusted_origin():
    with TestClient(app) as client:
        payload = {"email": "csrf@example.com", "password": "strong-password", "name": "CSRF Vendor", "role": "vendor"}
        client.post("/api/v1/auth/register", json=payload)
        client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
        response = client.post("/api/v1/products", json={"name": "Blocked", "price": "10.00", "currency": "NGN"})
        assert response.status_code == 403
