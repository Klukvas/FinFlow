from pydantic_settings import BaseSettings
from typing import Optional
import logging


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"

    # Internal services
    USER_SERVICE_URL: str = "http://user_service:8000"
    SUBSCRIPTION_SERVICE_URL: str = "http://subscription_service:8080"
    INTERNAL_SECRET_TOKEN: Optional[str] = None

    # Invite settings
    INVITE_EXPIRE_DAYS: int = 3  # Invites expire after 3 days

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }

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

