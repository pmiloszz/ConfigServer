# app/settings.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")
    database_url: str = "sqlite:///./flags.db"
    environment: str = "dev"
    debug: bool = True

settings = Settings()