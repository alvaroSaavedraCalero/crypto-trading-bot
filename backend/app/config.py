import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./trading_bot.db"
    )
    
    # App
    APP_NAME: str = "Crypto Trading Bot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API
    API_PREFIX: str = "/api/v1"
    
    # Security (optional - you can add JWT later)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    class Config:
        case_sensitive = True


settings = Settings()
