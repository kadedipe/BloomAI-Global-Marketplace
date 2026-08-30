import pytest
from pydantic import ValidationError

from app.config import DEVELOPMENT_JWT_SECRET, Settings


def test_production_rejects_development_jwt_secret():
    with pytest.raises(ValidationError, match="must not use the development default"):
        Settings(environment="production", jwt_secret=DEVELOPMENT_JWT_SECRET)


def test_production_accepts_strong_custom_jwt_secret():
    settings = Settings(environment="production", jwt_secret="a" * 48)
    assert settings.jwt_secret == "a" * 48


def test_api_docs_are_explicitly_disabled_by_default():
    assert Settings().enable_api_docs is False


def test_api_docs_can_be_explicitly_enabled():
    assert Settings(enable_api_docs=True).enable_api_docs is True
