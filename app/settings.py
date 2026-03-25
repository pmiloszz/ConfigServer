from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")
    database_url: str = "sqlite:///./flags.db"
    environment: str = "dev"
    debug: bool = True
    use_alembic: bool = False
    api_key: str = ""


settings = Settings()
