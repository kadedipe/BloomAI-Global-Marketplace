import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient

from app.main import app

ORIGIN = {"origin": "http://localhost:5173"}
PASSWORD = "strong-password"


def register(client: TestClient, email: str, role: str, name: str):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "name": name, "role": role},
    )
    assert response.status_code == 201


def login(client: TestClient, email: str):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 200


def logout(client: TestClient):
    assert client.post("/api/v1/auth/logout").status_code == 204


def checkout_payload(product_id: int):
    return {
        "product_id": product_id,
        "quantity": 1,
        "recipient_name": "Manual Buyer",
        "phone": "+256700000011",
        "address_line1": "11 Garden Road",
        "city": "Kampala",
        "region": "Central",
        "postal_code": "",
        "country": "Uganda",
        "buyer_note": "Local delivery test",
    }


def test_paid_order_can_use_local_delivery_without_tracking(monkeypatch):
    async def fake_checkout(method, path, **kwargs):
        assert method == "POST"
        assert path == "/transaction/initialize"
        return {
            "authorization_url": "https://checkout.example.test/manual",
            "access_code": "manual_delivery_test",
        }

    async def fake_verify(method, path, **kwargs):
        assert method == "GET"
        return {
            "status": "success",
            "amount": 200000,
            "currency": "NGN",
            "id": 555002,
        }

    monkeypatch.setattr("app.notifications.paystack_request", fake_checkout)
    monkeypatch.setattr("app.main.paystack_request", fake_verify)

    with TestClient(app, headers=ORIGIN) as client:
        register(client, "manual-vendor@example.com", "vendor", "Manual Vendor")
        login(client, "manual-vendor@example.com")
        product = client.post(
            "/api/v1/products",
            json={
                "name": "Local Delivery Lily",
                "description": "No-tracking fulfillment test",
                "price": 2000,
                "currency": "NGN",
                "inventory_quantity": 3,
            },
        ).json()
        logout(client)

        register(client, "manual-buyer@example.com", "customer", "Manual Buyer")
        login(client, "manual-buyer@example.com")
        checkout = client.post(
            "/api/v1/orders/checkout",
            json=checkout_payload(product["id"]),
        )
        assert checkout.status_code == 201
        order_id = checkout.json()["order_id"]
        reference = checkout.json()["reference"]
        verified = client.get(f"/api/v1/payments/{reference}/verify")
        assert verified.status_code == 200
        assert verified.json()["status"] == "paid"
        logout(client)

        login(client, "manual-vendor@example.com")
        processing = client.patch(
            f"/api/v1/orders/{order_id}/fulfillment",
            json={"status": "processing"},
        )
        assert processing.status_code == 200

        shipped = client.patch(
            f"/api/v1/orders/{order_id}/fulfillment",
            json={"status": "shipped", "delivery_method": "local_delivery"},
        )
        assert shipped.status_code == 200
        body = shipped.json()
        assert body["fulfillment_status"] == "shipped"
        assert body["carrier"] == "Local delivery"
        assert body["tracking_number"] is None
        assert body["tracking_status"] == "manual"
        assert body["tracking_provider_id"] is None
        assert body["delivery_method"] == "local_delivery"
        assert body["shipped_at"] is not None

        delivered = client.patch(
            f"/api/v1/orders/{order_id}/fulfillment",
            json={"status": "delivered"},
        )
        assert delivered.status_code == 200
        assert delivered.json()["fulfillment_status"] == "delivered"
        assert delivered.json()["delivered_at"] is not None


def test_no_tracking_method_is_required_when_tracking_is_absent():
    from app.manual_fulfillment import _manual_method

    assert _manual_method("local-delivery") == "local_delivery"
    assert _manual_method("Vendor Delivery") == "vendor_delivery"
