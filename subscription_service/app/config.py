from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = Field(default="subscription_service")

    DATABASE_URL: str

    redis_url: str = Field(default="redis://localhost:6379/0")

    log_level: str = Field(default="INFO")

    # Entitlements cache TTL seconds (min,max)
    ents_ttl_min: int = Field(default=60)
    ents_ttl_max: int = Field(default=300)

    # Grace period (days) for non-canceled subscriptions after expires_at.
    # Users keep access during this window so failed renewals don't
    # immediately revoke access.  Canceled subscriptions get NO grace.
    grace_period_days: int = Field(default=3)

    # Internal service authentication
    internal_secret_token: str = Field(default="")
    
    # JWT configuration (shared with user_service for token verification)
    jwt_secret_key: str = Field(default="")
    jwt_algorithm: str = Field(default="HS256")

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore[call-arg]


