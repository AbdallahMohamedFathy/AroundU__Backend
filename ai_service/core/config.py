from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AroundU AI Service"
    ENVIRONMENT: str = "development"
    BACKEND_URL: str = "http://api:8000/api"
    PORT: int = 8001
    LOG_LEVEL: str = "info"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
