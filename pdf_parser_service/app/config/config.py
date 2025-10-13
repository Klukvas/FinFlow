from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Service Configuration
    service_name: str = "pdf-parser-service"
    version: str = "1.0.0"
    debug: bool = False

    SECRET_KEY: str
    ALGORITHM: str
    
    # CORS Configuration
    cors_origins: str
    
    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = ["application/pdf"]
    upload_directory: str = "uploads"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

settings = Settings()
