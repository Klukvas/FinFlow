from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = Field(default="payment_service")

    DATABASE_URL: str
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    log_level: str = Field(default="INFO")

    # Internal service authentication
    internal_secret_token: str = Field(default="my-secret-token")
    
    # JWT configuration (shared with user_service for token verification)
    jwt_secret_key: str = Field(default="")
    jwt_algorithm: str = Field(default="HS256")

    # WayForPay configuration
    wayforpay_merchant_account: str = Field(default="")
    wayforpay_merchant_secret_key: str = Field(default="")
    wayforpay_merchant_domain: str = Field(default="")
    wayforpay_return_url: str = Field(default="")
    wayforpay_callback_url: str = Field(default="")
    wayforpay_api_url: str = Field(default="https://api.wayforpay.com/api")
    wayforpay_enable_recurring: bool = Field(default=True)  # Recurring tokens enabled - WayForPay confirmed support
    wayforpay_rectoken_format: str = Field(default="string")  # Format: "string" ("1"), "integer" (1), or "boolean" (true)
    
    # Service URLs
    service_base_url: str = Field(default="http://localhost:8000")
    subscription_service_url: str = Field(default="http://localhost:8080")
    
    # Idempotency
    idempotency_ttl_seconds: int = Field(default=86400)  # 24 hours
    
    # Feature flags
    payments_enabled: bool = Field(default=False)  # Disabled by default until Wayforpay approval

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore[call-arg]
