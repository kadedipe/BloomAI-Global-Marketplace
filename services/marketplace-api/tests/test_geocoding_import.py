import os

import pytest
from pydantic import ValidationError

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.geocoding_import import VerifiedGeocodeRow


def test_verified_geocode_requires_explicit_verification():
    with pytest.raises(ValidationError, match="explicitly verified"):
        VerifiedGeocodeRow(
            email="customer@example.com",
            latitude=0.3476,
            longitude=32.5825,
            source="trusted-import",
            verified=False,
        )


def test_verified_geocode_requires_participant_identifier():
    with pytest.raises(ValidationError, match="user_id or email is required"):
        VerifiedGeocodeRow(
            latitude=0.3476,
            longitude=32.5825,
            source="trusted-import",
            verified=True,
        )


def test_verified_geocode_rejects_invalid_coordinates():
    with pytest.raises(ValidationError):
        VerifiedGeocodeRow(
            email="customer@example.com",
            latitude=91,
            longitude=181,
            source="trusted-import",
            verified=True,
        )


def test_verified_geocode_normalizes_email_and_source():
    row = VerifiedGeocodeRow(
        email=" Customer@Example.COM ",
        latitude=0.3476,
        longitude=32.5825,
        source=" verified-geocoder ",
        verified=True,
        country="Uganda",
    )

    assert row.email == "customer@example.com"
    assert row.source == "verified-geocoder"
    assert row.country == "Uganda"
