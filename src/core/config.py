import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pydantic import Field, validator

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "AroundU API"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "production"

    # Security
    # In production, this MUST be set via environment variable
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes as per requirements
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7    # 7 days as per requirements

    # Database
    DATABASE_URL: str
    
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_QUERY_TIMEOUT_MS: int = 5000
    
    # Redis
    REDIS_URL: str = ""
    ENABLE_REDIS: bool = False

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    # AI Service
    AI_SERVICE_URL: str = ""
    AI_TIMEOUT_SECONDS: float = 3.0
    AI_MAX_RETRIES: int = 3

    # Ai sentiment service
    AI_SENTIMENT_URL: str = "https://mazenmaher26-aroundu-sentiment.hf.space/predict"
    AI_SENTIMENT_TIMEOUT_SECONDS: float = 3.0
    AI_SENTIMENT_MAX_RETRIES: int = 3
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # Rate Limiting
    RATE_LIMIT_ANON: int = 30
    RATE_LIMIT_AUTH: int = 120

   
    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    UPLOAD_FOLDER: str = "./uploads"
    ALLOWED_EXTENSIONS: list[str] = ["jpg", "jpeg", "png", "webp"]

    # CORS
    CORS_ORIGINS: str = "*" # Default for dev
    CORS_ALLOW_CREDENTIALS: bool = True

    # Firebase
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = Field(default=None, alias="FIREBASE_SERVICE_ACCOUNT_PATH")
    FIREBASE_SERVICE_ACCOUNT_JSON: Optional[str] = Field(default=None, alias="FIREBASE_SERVICE_ACCOUNT_JSON")

    def get_cors_origins(self) -> list:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # Settings Config
    model_config = SettingsConfigDict(
        env_file=".env",  
        case_sensitive=True,
        extra="ignore"
    )



settings = Settings()
