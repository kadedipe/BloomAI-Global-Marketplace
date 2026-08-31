import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient

from app.main import app
from app.segmentation import OrganizationSize, ParticipantCategory


def test_customer_cannot_access_admin_analytics():
    with TestClient(app, headers={"origin": "http://localhost:5173"}) as client:
        payload = {
            "email": "analytics-customer@example.com",
            "password": "strong-password",
            "name": "Analytics Customer",
            "role": "customer",
        }
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        assert client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        ).status_code == 200
        assert client.get("/api/v1/admin/analytics/overview").status_code == 403
        assert client.get("/api/v1/admin/participants").status_code == 403


def test_required_marketplace_segments_are_available():
    assert OrganizationSize.small.value == "small"
    assert OrganizationSize.mid_size.value == "mid_size"
    assert OrganizationSize.large.value == "large"
    assert ParticipantCategory.botanical_garden.value == "botanical_garden"
    assert ParticipantCategory.government_agency.value == "government_agency"
    assert ParticipantCategory.university.value == "university"
    assert ParticipantCategory.research_institution.value == "research_institution"
