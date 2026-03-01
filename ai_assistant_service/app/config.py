from pydantic_settings import BaseSettings
from pydantic import model_validator
import logging


class Settings(BaseSettings):
    # Anthropic API
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"
    ANTHROPIC_MAX_TOKENS: int = 2048

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # JWT / Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    INTERNAL_SECRET_TOKEN: str

    # Service URLs
    EXPENSE_SERVICE_URL: str = "http://expense_service:8000"
    INCOME_SERVICE_URL: str = "http://income_service:8000"
    DEBT_SERVICE_URL: str = "http://debt_service:8000"
    GOALS_SERVICE_URL: str = "http://goals_service:8000"
    ACCOUNT_SERVICE_URL: str = "http://account_service:8000"
    CATEGORY_SERVICE_URL: str = "http://category_service:8000"
    RECURRING_SERVICE_URL: str = "http://recurring_service:8000"
    SUBSCRIPTION_SERVICE_URL: str = "http://subscription_service:8080"

    # Limits
    HTTP_TIMEOUT: float = 5.0
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    DOCS_ENABLED: bool = False

    # Cache TTL (seconds)
    CACHE_TTL: int = 604800  # 7 days

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        _placeholders = {
            "your-secret-key-here",
            "my-secret-token",
            "my-dev-internal-token",
            "super-secret-key",
            "changeme-in-production",
            "your-internal-secret-token-here",
        }
        if not self.INTERNAL_SECRET_TOKEN or self.INTERNAL_SECRET_TOKEN in _placeholders:
            raise ValueError("INTERNAL_SECRET_TOKEN must be set to a strong, unique value")
        if not self.SECRET_KEY or self.SECRET_KEY in _placeholders:
            raise ValueError("SECRET_KEY must be set to a strong, unique value")
        if not self.ANTHROPIC_API_KEY or self.ANTHROPIC_API_KEY.startswith("sk-placeholder"):
            raise ValueError(
                "ANTHROPIC_API_KEY must be set to a valid Anthropic API key"
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
