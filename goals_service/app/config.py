from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List
import os
import logging


class Settings(BaseSettings):
    PROJECT_NAME: str = "Goals Service"
    VERSION: str = "1.0.0"
    
    # Database - No default, must be provided via environment variable
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://65.21.159.67,https://65.21.159.67"
    
    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        _placeholders = {
            "your-secret-key-here",
            "my-secret-token",
            "changeme-in-production",
            "your-internal-secret-token-here",
        }
        if not self.INTERNAL_SECRET_TOKEN or self.INTERNAL_SECRET_TOKEN in _placeholders:
            raise ValueError(
                "INTERNAL_SECRET_TOKEN must be set to a strong, unique value"
            )
        if not self.SECRET_KEY or self.SECRET_KEY in _placeholders:
            raise ValueError(
                "SECRET_KEY must be set to a strong, unique value"
            )
        return self

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # External Services
    USER_SERVICE_URL: str = "http://user_service:8000"
    EXPENSE_SERVICE_URL: str = "http://expense_service:8000"
    INCOME_SERVICE_URL: str = "http://income_service:8000"
    CURRENCY_SERVICE_URL: str = "http://currency_service:8000"
    SUBSCRIPTION_SERVICE_URL: str = "http://subscription_service:8080"
    WORKSPACE_SERVICE_URL: str = "http://workspace_service:8000"
    
    # Internal communication
    INTERNAL_SECRET_TOKEN: str
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
