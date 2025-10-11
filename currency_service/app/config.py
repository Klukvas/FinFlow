from pydantic_settings import BaseSettings
from typing import List
import logging

class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}
    
    # API Settings
    api_title: str = "Currency Service"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://65.21.159.67,https://65.21.159.67"
    
    # Redis
    redis_url: str = "redis://localhost:6377"
    
    # Currency API
    currency_api_url: str = "https://api.exchangerate-api.com/v4/latest"
    currency_cache_ttl: int = 3600  # 1 hour in seconds
    fallback_cache_ttl: int = 86400  # 24 hours for fallback rates
    
    # HTTP Settings
    http_timeout: float = 10.0
    http_retry_attempts: int = 3
    log_level: str = "INFO"
    
    # Security
    internal_secret_token: str = "your-internal-secret-token-here"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
