from pydantic_settings import BaseSettings
from typing import List
import logging

class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5433/account_service"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Currency API
    currency_api_url: str = "https://api.exchangerate-api.com/v4/latest"
    currency_cache_ttl: int = 3600  # 1 hour in seconds
    
    # API Settings
    api_title: str = "Account Service"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    
    # External Services
    expense_service_url: str = "http://localhost:8003"
    income_service_url: str = "http://localhost:8004"
    user_service_url: str = "http://localhost:8001"
    currency_service_url: str = "http://localhost:8010"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    internal_secret_token: str = "your-internal-secret-token-here"
    
    # Validation limits
    max_balance: float = 999999999.99
    max_name_length: int = 100
    max_description_length: int = 500
    max_currency_length: int = 3
    
    # HTTP Settings
    http_timeout: float = 5.0
    http_retry_attempts: int = 3
    log_level: str = "INFO"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(',')]

settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
