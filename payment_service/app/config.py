import logging

from pydantic_settings import BaseSettings
from pydantic import Field, model_validator

logger = logging.getLogger("payment_service.config")


class Settings(BaseSettings):
    app_name: str = Field(default="payment_service")

    DATABASE_URL: str
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    log_level: str = Field(default="INFO")

    # Internal service authentication (no default — must be set explicitly)
    internal_secret_token: str

    # JWT configuration (shared with user_service for token verification)
    jwt_secret_key: str = Field(default="")
    jwt_algorithm: str = Field(default="HS256")

    # Paddle Billing configuration
    paddle_api_key: str = Field(default="")
    paddle_webhook_secret: str = Field(default="")
    paddle_environment: str = Field(default="sandbox")  # "sandbox" or "production"
    paddle_success_url: str = Field(default="")
    paddle_cancel_url: str = Field(default="")

    # Service URLs
    service_base_url: str = Field(default="http://localhost:8000")
    subscription_service_url: str = Field(default="http://localhost:8080")

    # Idempotency
    idempotency_ttl_seconds: int = Field(default=86400)  # 24 hours

    # Reconciliation job (payment->subscription mismatch detection)
    reconciliation_interval_seconds: int = Field(default=300)  # 5 minutes
    reconciliation_lookback_hours: int = Field(default=24)

    # Feature flags
    payments_enabled: bool = Field(default=False)  # Disabled by default until provider setup complete

    @model_validator(mode="after")
    def _validate_secrets_when_enabled(self) -> "Settings":
        """Validate that critical secrets are configured when payments are enabled."""
        if not self.payments_enabled:
            return self

        if not self.jwt_secret_key:
            raise ValueError(
                "jwt_secret_key must be set when payments_enabled=True"
            )
        if not self.paddle_webhook_secret:
            raise ValueError(
                "paddle_webhook_secret must be set when payments_enabled=True"
            )
        if not self.paddle_api_key:
            raise ValueError(
                "paddle_api_key must be set when payments_enabled=True"
            )
        return self

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore[call-arg]
