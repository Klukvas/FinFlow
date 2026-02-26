from pydantic_settings import BaseSettings
from pydantic import model_validator
import logging

class Settings(BaseSettings):
    CATEGORY_SERVICE_URL: str
    ACCOUNT_SERVICE_URL: str
    CURRENCY_SERVICE_URL: str = "http://currency_service:8000"
    USER_SERVICE_URL: str = "http://user_service:8000"
    WORKSPACE_SERVICE_URL: str = "http://workspace_service:8000"
    INTERNAL_SECRET_TOKEN: str
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    LOG_LEVEL: str = "INFO"
    MAX_AMOUNT: float = 999999.99
    MAX_DESCRIPTION_LENGTH: int = 500
    DEFAULT_CURRENCY: str = "USD"
    HTTP_TIMEOUT: float = 5.0
    HTTP_RETRY_ATTEMPTS: int = 3
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://65.21.159.67,https://65.21.159.67"
    SUBSCRIPTION_SERVICE_URL: str = "http://subscription_service:8080"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        _placeholders = {
            "your-secret-key-here",
            "my-secret-token",
            "changeme-in-production",
            "your-internal-secret-token-here",
        }
        if not self.INTERNAL_SECRET_TOKEN or self.INTERNAL_SECRET_TOKEN in _placeholders:
            raise ValueError(
                "INTERNAL_SECRET_TOKEN must be set to a strong, unique value"
            )
        if not self.SECRET_KEY or self.SECRET_KEY in _placeholders:
            raise ValueError(
                "SECRET_KEY must be set to a strong, unique value"
            )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)