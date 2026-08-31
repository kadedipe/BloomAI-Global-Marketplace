import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient

from app.main import app


ORIGIN = {"origin": "http://localhost:5173"}


def register_and_login(client: TestClient, email: str, role: str) -> None:
    password = "strong-password"
    assert client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Photo User", "role": role},
    ).status_code == 201
    assert client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    ).status_code == 200


def test_customer_can_upload_and_remove_optional_profile_photo(monkeypatch):
    async def fake_upload(image, user_id):
        assert image.content_type == "image/png"
        return {
            "image_url": f"https://images.example.test/users/{user_id}.png",
            "image_public_id": f"bloomai/users/{user_id}/profile/avatar",
        }

    deleted = []

    async def fake_delete(public_id):
        deleted.append(public_id)

    monkeypatch.setattr("app.notifications.upload_profile_image", fake_upload)
    monkeypatch.setattr("app.notifications.delete_profile_image", fake_delete)

    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, "profile-customer@example.com", "customer")
        response = client.post(
            "/api/v1/notifications/profile-photo",
            files={"image": ("avatar.png", b"fake-image", "image/png")},
        )
        assert response.status_code == 200
        assert response.json()["avatar_url"].startswith("https://images.example.test/users/")
        assert client.get("/api/v1/auth/me").json()["avatar_url"] == response.json()["avatar_url"]

        removed = client.delete("/api/v1/notifications/profile-photo")
        assert removed.status_code == 200
        assert removed.json()["avatar_url"] is None
        assert deleted == ["bloomai/users/1/profile/avatar"]


def test_vendor_profile_photo_is_optional(monkeypatch):
    async def fake_upload(image, user_id):
        return {
            "image_url": f"https://images.example.test/vendors/{user_id}.webp",
            "image_public_id": f"bloomai/users/{user_id}/profile/vendor-avatar",
        }

    monkeypatch.setattr("app.notifications.upload_profile_image", fake_upload)

    with TestClient(app, headers=ORIGIN) as client:
        register_and_login(client, "profile-vendor@example.com", "vendor")
        before = client.get("/api/v1/auth/me")
        assert before.status_code == 200
        assert before.json()["avatar_url"] is None

        uploaded = client.post(
            "/api/v1/notifications/profile-photo",
            files={"image": ("vendor.webp", b"fake-image", "image/webp")},
        )
        assert uploaded.status_code == 200
        assert uploaded.json()["avatar_url"].endswith(".webp")
