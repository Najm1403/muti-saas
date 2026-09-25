# core/config.py

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always resolve .env relative to this file, regardless of working directory.
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    All fields map directly to keys in .env.
    """

    APP_NAME: str = "Storixx"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # ── CORS ──────────────────────────────────────────────────
    # Comma-separated list of allowed origins, or "*" for development.
    # Example: "https://app.example.com,https://admin.example.com"
    CORS_ORIGINS: str = "*"

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800

    # ── JWT / Auth ────────────────────────────────────────────
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_RESET_EXPIRE_MINUTES: int = 15

    # ── SMTP / Email (Brevo) ──────────────────────────────────
    SMTP_HOST: str = "smtp-relay.brevo.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "b22c7e001@smtp-brevo.com"
    SMTP_PASSWORD: str = ""          # Set this in .env — Brevo API key
    SMTP_FROM_EMAIL: str = "b22c7e001@smtp-brevo.com"
    SMTP_FROM_NAME: str = "FastFood SaaS"

    @model_validator(mode="after")
    def production_configuration(self):
        if self.ENVIRONMENT.lower() == "production":
            if self.DEBUG or self.DB_ECHO:
                raise ValueError("Production debug/SQL logging must be disabled.")
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
            if not origins or any(not origin.startswith("https://") for origin in origins):
                raise ValueError("Production CORS_ORIGINS must contain explicit HTTPS origins.")
            if len(self.SECRET_KEY) < 32:
                raise ValueError("Production SECRET_KEY must contain at least 32 characters.")
        return self

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
