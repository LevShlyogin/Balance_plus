from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Celery
    CELERY_BROKER_URL: str = "amqp://guest:guest@rabbitmq:5672//"
    CELERY_RESULT_BACKEND: str = "rpc://"
    
    # Git
    GIT_REPO_BASE_PATH: str = "/tmp/condenser_repos"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Service
    SERVICE_NAME: str = "condenser_calculation_service"
    SERVICE_VERSION: str = "1.2.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()