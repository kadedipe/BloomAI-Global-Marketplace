import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient

from app.main import app

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
        "recipient_name": "Reference Buyer",
        "phone": "+256700000011",
        "address_line1": "11 Garden Road",
        "city": "Kampala",
        "region": "Central",
        "postal_code": "",
        "country": "Uganda",
        "buyer_note": "Reference regression",
    }


def test_checkout_and_pay_now_accept_paystack_reference_field(monkeypatch):
    async def fake_paystack(method, path, **kwargs):
        assert method == "POST"
        assert path == "/transaction/initialize"
        supplied_reference = kwargs["json"]["reference"]
        return {
            "authorization_url": "https://checkout.example.test/pay",
            "access_code": "reference_test",
            "reference": supplied_reference,
        }

    monkeypatch.setattr("app.hardening.paystack_request", fake_paystack)
    monkeypatch.setattr("app.checkout_safe.hardening.paystack_request", fake_paystack)

    with TestClient(app, headers=ORIGIN) as client:
        register(client, "reference-vendor@example.com", "vendor", "Reference Vendor")
        login(client, "reference-vendor@example.com")
        product = client.post(
            "/api/v1/products",
            json={
                "name": "Reference Rose",
                "description": "Reference field regression listing",
                "price": 1000,
                "currency": "NGN",
                "inventory_quantity": 3,
            },
        ).json()
        logout(client)

        register(client, "reference-buyer@example.com", "customer", "Reference Buyer")
        login(client, "reference-buyer@example.com")

        checkout = client.post(
            "/api/v1/orders/checkout", json=checkout_payload(product["id"])
        )
        assert checkout.status_code == 201
        checkout_body = checkout.json()
        assert checkout_body["reference"].startswith("bloom-")
        assert checkout_body["authorization_url"] == "https://checkout.example.test/pay"

        order_id = checkout_body["order_id"]
        retry = client.post(f"/api/v1/orders/{order_id}/pay")
        assert retry.status_code == 200
        retry_body = retry.json()
        assert retry_body["reference"].startswith("bloom-")
        assert retry_body["authorization_url"] == "https://checkout.example.test/pay"
        assert retry_body["reference"] != checkout_body["reference"]
