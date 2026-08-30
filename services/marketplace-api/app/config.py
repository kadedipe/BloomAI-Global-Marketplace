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
        return self


@lru_cache
def get_settings():
    return Settings()
