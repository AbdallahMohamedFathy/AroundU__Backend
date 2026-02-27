import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict


import secrets
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "AroundU API"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")

    # Security
    # In production, this MUST be set via environment variable
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes as per requirements
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7    # 7 days as per requirements

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_QUERY_TIMEOUT_MS: int = 5000

    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@aroundu.com"
    EMAILS_FROM_NAME: str = "AroundU"

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_ANON: int = 30
    RATE_LIMIT_AUTH: int = 120

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    ENABLE_REDIS: bool = False

    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    UPLOAD_FOLDER: str = "./uploads"
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,gif,webp"

    # CORS
    CORS_ORIGINS: str = "*" # Default for dev
    CORS_ALLOW_CREDENTIALS: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # AI Service
    AI_SERVICE_URL: str = "http://ai_service:8001"
    AI_TIMEOUT_SECONDS: float = 3.0
    AI_MAX_RETRIES: int = 3

    def get_cors_origins(self) -> list:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
