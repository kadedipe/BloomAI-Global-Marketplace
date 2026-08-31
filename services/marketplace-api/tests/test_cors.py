import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient

from app.main import app


def test_notification_preferences_put_is_allowed_by_cors():
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/notifications/preferences",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "PUT",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert "PUT" in response.headers["access-control-allow-methods"]
