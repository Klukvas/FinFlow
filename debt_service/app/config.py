from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5433/debt_service"
    
    # API Settings
    api_title: str = "Debt Service"
    api_version: str = "1.0.0"
    debug: bool = False
    
    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    
    # External Services
    category_service_url: str = "http://localhost:8001"
    category_service_token: str = "internal-token"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    internal_secret_token: str = "your-internal-secret-token-here"
    
    # Validation limits
    max_amount: float = 999999.99
    max_name_length: int = 255
    max_description_length: int = 500
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

settings = Settings()
