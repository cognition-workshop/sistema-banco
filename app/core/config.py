from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./db.sqlite3"
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    MINIMUM_DEPOSIT_AMOUNT: int = 10
    MINIMUM_WITHDRAWAL_AMOUNT: int = 10
    ACCOUNT_NUMBER_START_FROM: int = 1000000000
    
    CELERY_BROKER_URL: str = "redis://localhost:6379"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"


settings = Settings()
