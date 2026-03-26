import json
import logging
from dataclasses import dataclass
from decimal import Decimal

from pydantic_settings import BaseSettings
from pydantic import Field, PrivateAttr, model_validator

logger = logging.getLogger("payment_service.config")


@dataclass(frozen=True)
class PaddlePriceEntry:
    plan_code: str
    paddle_price_id: str
    amount: Decimal
    currency: str = "USD"
    billing_period: str = "monthly"


def _parse_price_map(raw_json: str) -> tuple[dict[str, PaddlePriceEntry], dict[str, PaddlePriceEntry]]:
    """Parse PADDLE_PRICE_MAP JSON into forward (by plan_code) and reverse (by price_id) dicts."""
    raw = json.loads(raw_json)
    by_plan: dict[str, PaddlePriceEntry] = {}
    by_price_id: dict[str, PaddlePriceEntry] = {}
    for plan_code, cfg in raw.items():
        entry = PaddlePriceEntry(
            plan_code=plan_code,
            paddle_price_id=cfg["price_id"],
            amount=Decimal(str(cfg.get("amount", "0"))),
            currency=cfg.get("currency", "USD"),
            billing_period=cfg.get("billing_period", "monthly"),
        )
        by_plan[plan_code] = entry
        by_price_id[entry.paddle_price_id] = entry
    return by_plan, by_price_id


class Settings(BaseSettings):
    app_name: str = Field(default="payment_service")

    DATABASE_URL: str
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    log_level: str = Field(default="INFO")
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:3002,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:3002,http://127.0.0.1:5173")

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

    # Paddle price map: JSON string mapping plan_code -> {price_id, amount, currency, billing_period}
    # Example: '{"professional":{"price_id":"pri_xxx","amount":"9.99"},"enterprise":{"price_id":"pri_yyy","amount":"29.99"}}'
    paddle_price_map_json: str = Field(default="{}", alias="PADDLE_PRICE_MAP")

    # Parsed price maps (populated by model_validator, excluded from serialization)
    _price_map_by_plan: dict[str, PaddlePriceEntry] = PrivateAttr(default_factory=dict)
    _price_map_by_price_id: dict[str, PaddlePriceEntry] = PrivateAttr(default_factory=dict)

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
    def _validate_and_parse(self) -> "Settings":
        """Validate secrets and parse PADDLE_PRICE_MAP at startup (fail-fast)."""
        _placeholders = {
            "your-secret-key-here",
            "my-secret-token",
            "changeme-in-production",
            "your-internal-secret-token-here",
            "test-secret-token",
        }
        if not self.internal_secret_token or self.internal_secret_token in _placeholders:
            raise ValueError(
                "internal_secret_token must be set to a strong, unique value"
            )

        # Validate JSON structure even when payments are disabled (fail-fast)
        try:
            by_plan, by_price_id = _parse_price_map(self.paddle_price_map_json)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ValueError(f"PADDLE_PRICE_MAP is invalid: {e}") from e

        # Assign parsed maps regardless of payments_enabled — other code
        # (e.g. pricing endpoint) relies on the maps being populated.
        self._price_map_by_plan = by_plan
        self._price_map_by_price_id = by_price_id

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

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    def get_price_by_plan(self, plan_code: str) -> PaddlePriceEntry | None:
        return self._price_map_by_plan.get(plan_code)

    def get_price_by_paddle_id(self, paddle_price_id: str) -> PaddlePriceEntry | None:
        return self._price_map_by_price_id.get(paddle_price_id)

    class Config:
        env_file = ".env"
        populate_by_name = True


settings = Settings()  # type: ignore[call-arg]
