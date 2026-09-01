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


def test_customer_checkout_order_history_vendor_sales_and_cancel(monkeypatch):
    async def fake_paystack(method, path, **kwargs):
        assert method == "POST"
        assert path == "/transaction/initialize"
        assert kwargs["json"]["amount"] == 240000
        return {
            "authorization_url": "https://checkout.example.test/pay",
            "access_code": "access_test",
        }

    monkeypatch.setattr("app.notifications.paystack_request", fake_paystack)

    with TestClient(app, headers=ORIGIN) as client:
        vendor = register(client, "order-vendor@example.com", "vendor", "Order Vendor")
        login(client, "order-vendor@example.com")
        product_response = client.post(
            "/api/v1/products",
            json={
                "name": "Test Orchid",
                "description": "Order flow test product",
                "price": 1200,
                "currency": "NGN",
            },
        )
        assert product_response.status_code == 201
        product = product_response.json()
        logout(client)

        customer = register(client, "order-customer@example.com", "customer", "Order Customer")
        login(client, "order-customer@example.com")
        checkout = client.post(
            "/api/v1/orders/checkout",
            json={
                "product_id": product["id"],
                "quantity": 2,
                "recipient_name": "Order Customer",
                "phone": "+256700000000",
                "address_line1": "1 Garden Road",
                "city": "Kampala",
                "region": "Central",
                "postal_code": "",
                "country": "Uganda",
                "buyer_note": "Handle with care",
            },
        )
        assert checkout.status_code == 201
        assert checkout.json()["authorization_url"] == "https://checkout.example.test/pay"

        mine = client.get("/api/v1/orders")
        assert mine.status_code == 200
        assert len(mine.json()) == 1
        order = mine.json()[0]
        assert order["buyer_id"] == customer["id"]
        assert order["vendor_id"] == vendor["id"]
        assert order["product_name"] == "Test Orchid"
        assert order["quantity"] == 2
        assert order["city"] == "Kampala"
        assert order["country"] == "Uganda"
        assert order["status"] == "pending"

        cancelled = client.patch(f"/api/v1/orders/{order['id']}/cancel")
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"
        logout(client)

        login(client, "order-vendor@example.com")
        sales = client.get("/api/v1/orders/sales")
        assert sales.status_code == 200
        assert len(sales.json()) == 1
        assert sales.json()[0]["buyer_name"] == "Order Customer"
        assert sales.json()[0]["status"] == "cancelled"


def test_vendor_cannot_buy_own_product(monkeypatch):
    async def fake_paystack(*args, **kwargs):
        raise AssertionError("Paystack should not be called for an owned product")

    monkeypatch.setattr("app.notifications.paystack_request", fake_paystack)

    with TestClient(app, headers=ORIGIN) as client:
        register(client, "self-vendor@example.com", "vendor", "Self Vendor")
        login(client, "self-vendor@example.com")
        product = client.post(
            "/api/v1/products",
            json={"name": "Own Plant", "description": "", "price": 500, "currency": "NGN"},
        ).json()
        response = client.post(
            "/api/v1/orders/checkout",
            json={
                "product_id": product["id"],
                "quantity": 1,
                "recipient_name": "Self Vendor",
                "phone": "+256700000001",
                "address_line1": "2 Garden Road",
                "city": "Kampala",
                "country": "Uganda",
            },
        )
        assert response.status_code == 409
