from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from cryptography.fernet import Fernet
import logging


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    DATABASE_URL: str

    # API Settings
    API_TITLE: str = "Bank Sync Service"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"

    # External Services
    WORKSPACE_SERVICE_URL: str = "http://workspace_service:8000"
    EXPENSE_SERVICE_URL: str = "http://expense_service:8000"
    INCOME_SERVICE_URL: str = "http://income_service:8000"
    ACCOUNT_SERVICE_URL: str = "http://account_service:8000"
    CATEGORY_SERVICE_URL: str = "http://category_service:8000"
    SUBSCRIPTION_SERVICE_URL: str = "http://subscription_service:8080"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    INTERNAL_SECRET_TOKEN: str

    # Encryption key for bank tokens (Fernet, 32-byte base64)
    BANK_TOKEN_ENCRYPTION_KEY: str

    # Monobank
    MONOBANK_API_BASE_URL: str = "https://api.monobank.ua"
    MONOBANK_RATE_LIMIT_SECONDS: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        _placeholders = {
            "your-secret-key-here",
            "my-secret-token",
            "changeme-in-production",
            "your-internal-secret-token-here",
        }
        if not self.INTERNAL_SECRET_TOKEN or self.INTERNAL_SECRET_TOKEN in _placeholders:
            raise ValueError("INTERNAL_SECRET_TOKEN must be set to a strong, unique value")
        if not self.SECRET_KEY or self.SECRET_KEY in _placeholders:
            raise ValueError("SECRET_KEY must be set to a strong, unique value")
        try:
            Fernet(self.BANK_TOKEN_ENCRYPTION_KEY.encode())
        except Exception:
            raise ValueError(
                "BANK_TOKEN_ENCRYPTION_KEY must be a valid Fernet key (44-char URL-safe base64)"
            )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
