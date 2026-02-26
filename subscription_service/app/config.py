from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = Field(default="subscription_service")

    DATABASE_URL: str

    redis_url: str = Field(default="redis://localhost:6379/0")

    log_level: str = Field(default="INFO")
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:3002,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:3002,http://127.0.0.1:5173")

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

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore[call-arg]


