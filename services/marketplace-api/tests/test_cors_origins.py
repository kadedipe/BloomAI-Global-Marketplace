from app.config import Settings


def test_web_base_origin_is_added_to_cors_origins():
    settings = Settings(
        web_base_url="https://bloomai-web-production.up.railway.app/#market",
        cors_origins="https://example.com",
    )

    assert "https://example.com" in settings.cors_origins
    assert "https://bloomai-web-production.up.railway.app" in settings.cors_origins


def test_web_base_origin_is_not_duplicated():
    settings = Settings(
        web_base_url="https://bloomai-web-production.up.railway.app/",
        cors_origins="https://bloomai-web-production.up.railway.app/",
    )

    assert settings.cors_origins == ["https://bloomai-web-production.up.railway.app"]
