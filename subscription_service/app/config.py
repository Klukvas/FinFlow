from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = Field(default="subscription_service")

    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_user: str = Field(default="postgres")
    db_password: str = Field(default="postgres")
    db_name: str = Field(default="subscription_db")

    redis_url: str = Field(default="redis://localhost:6379/0")

    log_level: str = Field(default="INFO")

    # Entitlements cache TTL seconds (min,max)
    ents_ttl_min: int = Field(default=60)
    ents_ttl_max: int = Field(default=300)

    # Internal service authentication
    internal_secret_token: str = Field(default="my-secret-token")

    class Config:
        env_prefix = "SUBS_"
        env_file = ".env"


settings = Settings()  # type: ignore[call-arg]


