from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Goals Service"
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/goals_db"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # External Services
    USER_SERVICE_URL: str = "http://user_service:8000"
    EXPENSE_SERVICE_URL: str = "http://expense_service:8000"
    INCOME_SERVICE_URL: str = "http://income_service:8003"
    
    # Internal communication
    INTERNAL_SECRET: str = "internal-secret-key"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
