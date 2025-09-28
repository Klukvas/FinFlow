import os
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
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
