from fastapi.testclient import TestClient
from app.main import app

def test_liveness():
    assert TestClient(app).get("/health/live").json() == {"status":"ok", "service":"ai-api"}

def test_rejects_non_image():
    response = TestClient(app).post("/api/v1/classify", files={"image":("x.txt", b"no", "text/plain")})
    assert response.status_code == 415

