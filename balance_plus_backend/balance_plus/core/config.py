from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    gitlab_client_id: str
    gitlab_client_secret: str
    secret_key: str
    redis_url: str

    class Config:
        env_file = ".env"

settings = Settings() 