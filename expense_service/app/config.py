from pydantic_settings import BaseSettings
from typing import Optional
import logging

class Settings(BaseSettings):
    CATEGORY_SERVICE_URL: str
    ACCOUNT_SERVICE_URL: str
    INTERNAL_SECRET_TOKEN: str
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    LOG_LEVEL: str = "INFO"
    MAX_AMOUNT: float = 999999.99
    MAX_DESCRIPTION_LENGTH: int = 500
    HTTP_TIMEOUT: float = 5.0
    HTTP_RETRY_ATTEMPTS: int = 3
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://65.21.159.67,https://65.21.159.67"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
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