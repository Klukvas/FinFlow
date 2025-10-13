from pydantic_settings import BaseSettings
from typing import List
import os
import logging

class Settings(BaseSettings):
    # Database - No default, must be provided via environment variable
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    
    # External services
    USER_SERVICE_URL: str = "http://user_service:8000"
    CATEGORY_SERVICE_URL: str = "http://category_service:8000"
    ACCOUNT_SERVICE_URL: str = "http://account_service:8000"
    INTERNAL_SECRET: str = "my-secret-token"
    INTERNAL_SECRET_TOKEN: str = "internal-secret-key"  # Fallback for compatibility
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://65.21.159.67,https://65.21.159.67"
    
    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Income specific settings
    MAX_AMOUNT: float = 999999.99
    MAX_DESCRIPTION_LENGTH: int = 500
    
    # HTTP settings
    HTTP_TIMEOUT: float = 5.0
    HTTP_RETRY_ATTEMPTS: int = 3
    
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
