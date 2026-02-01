import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AroundU API"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "supersecretkey" # TODO: Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week

    # Database
    DATABASE_URL: str = "sqlite:///./aroundu.db"

    class Config:
        env_file = ".env"

settings = Settings()
