from pydantic_settings import BaseSettings
from pydantic import model_validator
import logging

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    INTERNAL_SECRET_TOKEN: str
    LOG_LEVEL: str = "INFO"
    MAX_CATEGORY_DEPTH: int = 2
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://65.21.159.67,https://65.21.159.67"
    
    # Internal services
    SUBSCRIPTION_SERVICE_URL: str = "http://subscription_service:8080"
    WORKSPACE_SERVICE_URL: str = "http://workspace_service:8000"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }

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