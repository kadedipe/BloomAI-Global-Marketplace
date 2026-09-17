from app.config import Settings


PUBLIC_WEB_ORIGIN = "https://bloomaiglobalmarketplace.com"
LEGACY_WEB_ORIGIN = "https://bloomai-web-production.up.railway.app"


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
        web_base_url=PUBLIC_WEB_ORIGIN,
        cors_origins=(
            f"{PUBLIC_WEB_ORIGIN},"
            "https://www.bloomaiglobalmarketplace.com,"
            f"{LEGACY_WEB_ORIGIN}"
        ),
    )

    assert settings.cors_origins == [
        PUBLIC_WEB_ORIGIN,
        "https://www.bloomaiglobalmarketplace.com",
        LEGACY_WEB_ORIGIN,
    ]
