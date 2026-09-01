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
    return response.json()


def login(client: TestClient, email: str):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 200


def logout(client: TestClient):
    assert client.post("/api/v1/auth/logout").status_code == 204


def checkout_payload(product_id: int, quantity: int = 1):
    return {
        "product_id": product_id,
        "quantity": quantity,
        "recipient_name": "Commerce Buyer",
        "phone": "+256700000010",
        "address_line1": "10 Garden Road",
        "city": "Kampala",
        "region": "Central",
        "postal_code": "",
        "country": "Uganda",
        "buyer_note": "Protect the plant during transit",
    }


def test_inventory_reservation_and_cancel_restore(monkeypatch):
    async def fake_paystack(method, path, **kwargs):
        assert method == "POST"
        assert path == "/transaction/initialize"
        return {
            "authorization_url": "https://checkout.example.test/pay",
            "access_code": "stock_test",
        }

    monkeypatch.setattr("app.notifications.paystack_request", fake_paystack)

    with TestClient(app, headers=ORIGIN) as client:
        register(client, "stock-vendor@example.com", "vendor", "Stock Vendor")
        login(client, "stock-vendor@example.com")
        product = client.post(
            "/api/v1/products",
            json={
                "name": "Limited Orchid",
                "description": "Two units only",
                "price": 1000,
                "currency": "NGN",
                "inventory_quantity": 2,
                "is_active": True,
            },
        ).json()
        logout(client)

        register(client, "stock-buyer-one@example.com", "customer", "Stock Buyer One")
        login(client, "stock-buyer-one@example.com")
        first = client.post(
            "/api/v1/orders/checkout", json=checkout_payload(product["id"], 2)
        )
        assert first.status_code == 201
        order_id = first.json()["order_id"]
        logout(client)

        register(client, "stock-buyer-two@example.com", "customer", "Stock Buyer Two")
        login(client, "stock-buyer-two@example.com")
        blocked = client.post(
            "/api/v1/orders/checkout", json=checkout_payload(product["id"], 1)
        )
        assert blocked.status_code == 409
        logout(client)

        login(client, "stock-buyer-one@example.com")
        cancelled = client.patch(f"/api/v1/orders/{order_id}/cancel")
        assert cancelled.status_code == 200
        logout(client)

        login(client, "stock-buyer-two@example.com")
        available = client.post(
            "/api/v1/orders/checkout", json=checkout_payload(product["id"], 1)
        )
        assert available.status_code == 201


def test_paid_order_fulfillment_receipt_and_refund_request(monkeypatch):
    async def fake_checkout(method, path, **kwargs):
        assert method == "POST"
        return {
            "authorization_url": "https://checkout.example.test/pay",
            "access_code": "fulfillment_test",
        }

    async def fake_verify(method, path, **kwargs):
        assert method == "GET"
        return {
            "status": "success",
            "amount": 150000,
            "currency": "NGN",
            "id": 555001,
        }

    monkeypatch.setattr("app.notifications.paystack_request", fake_checkout)
    monkeypatch.setattr("app.main.paystack_request", fake_verify)

    with TestClient(app, headers=ORIGIN) as client:
        register(client, "fulfill-vendor@example.com", "vendor", "Fulfill Vendor")
        login(client, "fulfill-vendor@example.com")
        product = client.post(
            "/api/v1/products",
            json={
                "name": "Receipt Rose",
                "description": "Fulfillment test",
                "price": 1500,
                "currency": "NGN",
                "inventory_quantity": 5,
            },
        ).json()
        logout(client)

        register(client, "fulfill-buyer@example.com", "customer", "Fulfill Buyer")
        login(client, "fulfill-buyer@example.com")
        checkout = client.post(
            "/api/v1/orders/checkout", json=checkout_payload(product["id"])
        )
        assert checkout.status_code == 201
        order_id = checkout.json()["order_id"]
        reference = checkout.json()["reference"]

        verified = client.get(f"/api/v1/payments/{reference}/verify")
        assert verified.status_code == 200
        assert verified.json()["status"] == "paid"

        receipt = client.get(f"/api/v1/orders/{order_id}/receipt")
        assert receipt.status_code == 200
        assert receipt.json()["receipt_number"] == f"BLM-{order_id:08d}"
        assert receipt.json()["total"] == "1500.00"
        logout(client)

        login(client, "fulfill-vendor@example.com")
        processing = client.patch(
            f"/api/v1/orders/{order_id}/fulfillment",
            json={"status": "processing"},
        )
        assert processing.status_code == 200
        shipped = client.patch(
            f"/api/v1/orders/{order_id}/fulfillment",
            json={
                "status": "shipped",
                "carrier": "Bloom Express",
                "tracking_number": "BLM-TRACK-001",
            },
        )
        assert shipped.status_code == 200
        assert shipped.json()["tracking_number"] == "BLM-TRACK-001"
        delivered = client.patch(
            f"/api/v1/orders/{order_id}/fulfillment",
            json={"status": "delivered"},
        )
        assert delivered.status_code == 200
        logout(client)

        login(client, "fulfill-buyer@example.com")
        refund = client.post(
            f"/api/v1/orders/{order_id}/refund-request",
            json={"reason": "The delivered plant was damaged in transit."},
        )
        assert refund.status_code == 200
        assert refund.json()["refund_status"] == "requested"
        logout(client)

        login(client, "fulfill-vendor@example.com")
        review = client.patch(
            f"/api/v1/orders/{order_id}/refund-review",
            json={"decision": "approved"},
        )
        assert review.status_code == 200
        assert review.json()["refund_status"] == "approved"
