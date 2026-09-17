from app.config import Settings


PUBLIC_WEB_ORIGIN = "https://bloomaiglobalmarketplace.com"
WWW_WEB_ORIGIN = "https://www.bloomaiglobalmarketplace.com"
LEGACY_WEB_ORIGIN = "https://bloomai-web-production.up.railway.app"
PRODUCTION_JWT_SECRET = "production-test-secret-at-least-32-characters"


def test_web_base_origin_is_added_to_cors_origins():
    settings = Settings(
        web_base_url=f"{PUBLIC_WEB_ORIGIN}/#market",
        cors_origins=LEGACY_WEB_ORIGIN,
    )

    assert LEGACY_WEB_ORIGIN in settings.cors_origins
    assert PUBLIC_WEB_ORIGIN in settings.cors_origins


def test_web_base_origin_is_not_duplicated():
    settings = Settings(
        web_base_url=f"{PUBLIC_WEB_ORIGIN}/",
        cors_origins=f"{PUBLIC_WEB_ORIGIN}/",
    )

    assert settings.cors_origins == [PUBLIC_WEB_ORIGIN]


def test_production_origins_accept_canonical_www_and_legacy_hosts():
    settings = Settings(
        environment="production",
        jwt_secret=PRODUCTION_JWT_SECRET,
        web_base_url=PUBLIC_WEB_ORIGIN,
        cors_origins=f"{PUBLIC_WEB_ORIGIN},{WWW_WEB_ORIGIN},{LEGACY_WEB_ORIGIN}",
    )

    assert settings.cors_origins == [
        PUBLIC_WEB_ORIGIN,
        WWW_WEB_ORIGIN,
        LEGACY_WEB_ORIGIN,
    ]


def test_production_self_heals_stale_cors_configuration():
    settings = Settings(
        environment="production",
        jwt_secret=PRODUCTION_JWT_SECRET,
        web_base_url=LEGACY_WEB_ORIGIN,
        cors_origins=LEGACY_WEB_ORIGIN,
    )

    assert PUBLIC_WEB_ORIGIN in settings.cors_origins
    assert WWW_WEB_ORIGIN in settings.cors_origins
    assert LEGACY_WEB_ORIGIN in settings.cors_origins
