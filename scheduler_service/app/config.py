from pydantic_settings import BaseSettings
from pydantic import Field, model_validator


class Settings(BaseSettings):
    """Scheduler Service Configuration"""
    
    app_name: str = Field(default="scheduler_service")
    
    # Database
    DATABASE_URL: str
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # Logging
    log_level: str = Field(default="INFO")
    
    # Internal service authentication
    internal_secret_token: str = Field(default="")
    
    # Service URLs
    subscription_service_url: str = Field(default="http://localhost:8080")
    payment_service_url: str = Field(default="http://localhost:8000")
    
    # Scheduler settings
    scheduler_timezone: str = Field(default="UTC")
    renewal_check_cron: str = Field(default="0 */1 * * *")  # Every hour
    renewal_window_days: int = Field(default=1)  # Check subscriptions expiring in 1 day
    max_retry_attempts: int = Field(default=3)
    retry_delay_seconds: int = Field(default=300)  # 5 minutes
    
    # Job execution settings
    job_max_instances: int = Field(default=1)  # Prevent concurrent execution
    job_coalesce: bool = Field(default=True)  # Merge missed runs
    job_misfire_grace_time: int = Field(default=300)  # 5 minutes
    
    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        _placeholders = {
            "your-secret-key-here",
            "my-secret-token",
            "changeme-in-production",
            "your-internal-secret-token-here",
        }
        if not self.internal_secret_token or self.internal_secret_token in _placeholders:
            raise ValueError(
                "internal_secret_token must be set to a strong, unique value"
            )
        return self

    class Config:
        env_file = ".env"


settings = Settings()  # type: ignore[call-arg]
