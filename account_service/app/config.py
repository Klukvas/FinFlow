from pydantic_settings import BaseSettings
from typing import List
import logging

class Settings(BaseSettings):
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "case_sensitive": False
    }
    
    # Database - No default, must be provided via environment variable
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Currency API
    CURRENCY_API_URL: str = "https://api.exchangerate-api.com/v4/latest"
    CURRENCY_CACHE_TTL: int = 3600  # 1 hour in seconds
    
    # API Settings
    API_TITLE: str = "Account Service"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://65.21.159.67,https://65.21.159.67"
    
    # External Services
    EXPENSE_SERVICE_URL: str = "http://expense_service:8000"
    INCOME_SERVICE_URL: str = "http://income_service:8000"
    USER_SERVICE_URL: str = "http://user_service:8000"
    CURRENCY_SERVICE_URL: str = "http://currency_service:8000"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    INTERNAL_SECRET_TOKEN: str
    
    # Validation limits
    MAX_BALANCE: float = 999999999.99
    MAX_NAME_LENGTH: int = 100
    MAX_DESCRIPTION_LENGTH: int = 500
    MAX_CURRENCY_LENGTH: int = 3
    
    # HTTP Settings
    HTTP_TIMEOUT: float = 5.0
    HTTP_RETRY_ATTEMPTS: int = 3
    LOG_LEVEL: str = "INFO"
    
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
