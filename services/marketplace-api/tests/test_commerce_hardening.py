import base64
import hashlib
import hmac
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient

from app import hardening
from app.config import get_settings
from app.main import app
from app.shipping import valid_aftership_signature

ORIGIN = {"origin": "http://localhost:5173"}
PASSWORD = "strong-password"


def register(client, email, role, name):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "name": name, "role": role},
    )
    assert response.status_code == 201


def login(client, email):
    assert client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    ).status_code == 200


def logout(client):
    assert client.post("/api/v1/auth/logout").status_code == 204


def checkout_payload(product_id):
    return {
        "product_id": product_id,
        "quantity": 1,
        "recipient_name": "Hardening Buyer",
        "phone": "+256700000010",
        "address_line1": "10 Garden Road",
        "city": "Kampala",
        "region": "Central",
        "postal_code": "",
        "country": "Uganda",
        "buyer_note": "Leave at reception",
    }


def test_structured_checkout_quote_inventory_expiry_and_legacy_retirement(monkeypatch):
    async def fake_paystack(method, path, **kwargs):
        assert method == "POST"
        assert path == "/transaction/initialize"
        return {
            "authorization_url": "https://checkout.example.test/pay",
            "access_code": "hardening_test",
        }

    monkeypatch.setattr("app.notifications.paystack_request", fake_paystack)
    monkeypatch.setattr(hardening.settings, "shipping_flat_amount", 100.0)
    monkeypatch.setattr(hardening.settings, "shipping_free_threshold", 0.0)
    monkeypatch.setattr(hardening.settings, "sales_tax_percent", 10.0)
    monkeypatch.setattr(hardening.settings, "order_reservation_minutes", 0)

    with TestClient(app, headers=ORIGIN) as client:
        register(client, "hardening-vendor@example.com", "vendor", "Hardening Vendor")
        login(client, "hardening-vendor@example.com")
        product = client.post(
            "/api/v1/products",
            json={
                "name": "Hardening Rose",
                "description": "Concurrency test listing",
                "price": 1000,
                "currency": "NGN",
                "inventory_quantity": 1,
            },
        ).json()
        logout(client)

        register(client, "hardening-buyer@example.com", "customer", "Hardening Buyer")
        login(client, "hardening-buyer@example.com")

        quote = client.post(
            "/api/v1/orders/quote",
            json={"product_id": product["id"], "quantity": 1, "country": "Uganda"},
        )
        assert quote.status_code == 200
        assert quote.json()["subtotal"] == "1000.00"
        assert quote.json()["shipping_amount"] == "100.00"
        assert quote.json()["tax_amount"] == "100.00"
        assert quote.json()["total"] == "1200.00"

        checkout = client.post("/api/v1/orders/checkout", json=checkout_payload(product["id"]))
        assert checkout.status_code == 201
        assert checkout.json()["total"] == "1200.00"
        assert checkout.json()["reservation_expires_at"]

        # A new quote triggers idempotent expiry cleanup; inventory becomes available again.
        quote_after_expiry = client.post(
            "/api/v1/orders/quote",
            json={"product_id": product["id"], "quantity": 1, "country": "Uganda"},
        )
        assert quote_after_expiry.status_code == 200
        orders = client.get("/api/v1/orders").json()
        assert orders[0]["status"] == "cancelled"

        legacy = client.post(
            "/api/v1/payments/initialize",
            json={"product_id": product["id"], "quantity": 1},
        )
        assert legacy.status_code == 410
        assert "orders/checkout" in legacy.json()["detail"]


def test_checkout_returns_provider_url_when_notifications_fail(monkeypatch):
    async def fake_paystack(method, path, **kwargs):
        assert method == "POST"
        assert path == "/transaction/initialize"
        return {
            "authorization_url": "https://checkout.example.test/recoverable",
            "access_code": "recoverable_test",
        }

    async def fail_notification(*args, **kwargs):
        raise RuntimeError("notification provider unavailable")

    monkeypatch.setattr("app.notifications.paystack_request", fake_paystack)
    monkeypatch.setattr(hardening, "create_notification", fail_notification)

    with TestClient(app, headers=ORIGIN) as client:
        register(client, "response-vendor@example.com", "vendor", "Response Vendor")
        login(client, "response-vendor@example.com")
        product = client.post(
            "/api/v1/products",
            json={
                "name": "Response Rose",
                "description": "Checkout response safety",
                "price": 2500,
                "currency": "NGN",
                "inventory_quantity": 2,
            },
        ).json()
        logout(client)

        register(client, "response-buyer@example.com", "customer", "Response Buyer")
        login(client, "response-buyer@example.com")

        checkout = client.post(
            "/api/v1/orders/checkout", json=checkout_payload(product["id"])
        )
        assert checkout.status_code == 201
        body = checkout.json()
        assert body["authorization_url"] == "https://checkout.example.test/recoverable"
        assert body["order_id"]

        orders = client.get("/api/v1/orders")
        assert orders.status_code == 200
        persisted = next(item for item in orders.json() if item["id"] == body["order_id"])
        assert persisted["status"] == "pending"


def test_aftership_webhook_signature(monkeypatch):
    monkeypatch.setenv("AFTERSHIP_WEBHOOK_SECRET", "tracking-secret")
    get_settings.cache_clear()
    payload = b'{"event":"tracking_update"}'
    signature = base64.b64encode(
        hmac.new(b"tracking-secret", payload, hashlib.sha256).digest()
    ).decode()
    assert valid_aftership_signature(payload, signature)
    assert not valid_aftership_signature(payload + b"x", signature)
    get_settings.cache_clear()
