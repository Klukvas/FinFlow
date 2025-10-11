import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/recurring_db"

    # Service URLs
    EXPENSE_SERVICE_URL: str = "http://expense-service:8000"
    INCOME_SERVICE_URL: str = "http://income-service:8000"
    CATEGORY_SERVICE_URL: str = "http://category-service:8000"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    
    PROJECT_NAME: str = "Recurring Payments Service"
    
    # Security
    INTERNAL_SECRET: str
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://localhost:8080,http://65.21.159.67,https://65.21.159.67"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        case_sensitive = False
        env_file = ".env"


settings = Settings()
