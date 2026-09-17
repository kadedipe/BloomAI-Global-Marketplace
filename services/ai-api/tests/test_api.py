import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app, get_cors_origins, runtime


PUBLIC_WEB_ORIGIN = "https://bloomaiglobalmarketplace.com"
WWW_WEB_ORIGIN = "https://www.bloomaiglobalmarketplace.com"
LEGACY_WEB_ORIGIN = "https://bloomai-web-production.up.railway.app"


def test_liveness():
    assert TestClient(app).get("/health/live").json() == {"status": "ok", "service": "ai-api"}


def test_rejects_non_image():
    response = TestClient(app).post("/api/v1/classify", files={"image": ("x.txt", b"no", "text/plain")})
    assert response.status_code == 415


def test_classification_response(monkeypatch):
    monkeypatch.setattr(type(runtime), "ready", property(lambda self: True))
    monkeypatch.setattr(runtime, "predict", lambda image, top_k: [{
        "class_index": 0, "category_id": "1", "name": "pink primrose", "confidence": 0.95,
    }])
    image = Image.new("RGB", (32, 32), "red")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    response = TestClient(app).post("/api/v1/classify", files={"image": ("flower.png", buffer.getvalue(), "image/png")})
    assert response.status_code == 200
    assert response.json()["predictions"][0]["name"] == "pink primrose"


def test_production_cors_self_heals_stale_configuration(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ORIGINS", LEGACY_WEB_ORIGIN)

    origins = get_cors_origins()

    assert PUBLIC_WEB_ORIGIN in origins
    assert WWW_WEB_ORIGIN in origins
    assert LEGACY_WEB_ORIGIN in origins
