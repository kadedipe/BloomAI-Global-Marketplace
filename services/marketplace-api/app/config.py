from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_JWT_SECRET = "development-only-secret-change-me"


class Settings(BaseSettings):
    app_name: str = "BloomAI Marketplace API"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./bloomai.sqlite3"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] | str = ["http://localhost:5173"]
    jwt_secret: str = DEVELOPMENT_JWT_SECRET
    jwt_expiry_minutes: int = 60
    auth_cookie_name: str = "bloomai_session"
    enable_api_docs: bool = False
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    product_image_max_bytes: int = 5_000_000
    paystack_secret_key: str = ""
    paystack_callback_url: str = ""
    paystack_currencies: str = "NGN"
    resend_api_key: str = ""
    resend_from_email: str = ""
    web_base_url: str = "http://localhost:5173"
    public_api_base_url: str = ""
    order_reservation_minutes: int = 30
    shipping_flat_amount: float = 0.0
    shipping_free_threshold: float = 0.0
    sales_tax_percent: float = 0.0
    aftership_api_key: str = ""
    aftership_webhook_secret: str = ""
    aftership_api_version: str = "2026-07"
    rate_limit_enabled: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value):
        return (
            [v.strip().rstrip("/") for v in value.split(",")]
            if isinstance(value, str)
            else value
        )

    @field_validator("database_url", mode="before")
    @classmethod
    def async_database_url(cls, value: str):
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.environment == "production" and (
            len(self.jwt_secret) < 32 or self.jwt_secret == DEVELOPMENT_JWT_SECRET
        ):
            raise ValueError(
                "JWT_SECRET must be at least 32 characters and must not use the "
                "development default in production"
            )
        if self.order_reservation_minutes < 5:
            raise ValueError("ORDER_RESERVATION_MINUTES must be at least 5")
        if self.shipping_flat_amount < 0 or self.shipping_free_threshold < 0:
            raise ValueError("Shipping configuration cannot be negative")
        if not 0 <= self.sales_tax_percent <= 100:
            raise ValueError("SALES_TAX_PERCENT must be between 0 and 100")
        return self

    @property
    def cloudinary_enabled(self) -> bool:
        return all((self.cloudinary_cloud_name, self.cloudinary_api_key, self.cloudinary_api_secret))

    @property
    def paystack_enabled(self) -> bool:
        return bool(self.paystack_secret_key and self.paystack_callback_url)

    @property
    def transactional_email_enabled(self) -> bool:
        return bool(self.resend_api_key and self.resend_from_email)

    @property
    def aftership_enabled(self) -> bool:
        return bool(self.aftership_api_key)


@lru_cache
def get_settings():
    return Settings()
