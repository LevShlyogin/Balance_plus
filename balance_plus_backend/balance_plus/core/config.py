from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    GITLAB_URL: str
    GITLAB_APP_ID: str
    GITLAB_APP_SECRET: str
    GITLAB_REDIRECT_URI: str
    GITLAB_TEMPLATE_PROJECT_ID: int

    class Config:
        env_file = ".env"

settings = Settings() 