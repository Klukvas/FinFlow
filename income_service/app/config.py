from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/income_db"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    
    # External services
    user_service_url: str = "http://user_service:8000"
    category_service_url: str = "http://category_service:8000"
    account_service_url: str = "http://account_service:8000"
    internal_secret: str = "my-secret-token"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Logging
    log_level: str = "INFO"
    
    # Income specific settings
    max_amount: float = 999999.99
    max_description_length: int = 500
    
    # HTTP settings
    http_timeout: float = 5.0
    http_retry_attempts: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
