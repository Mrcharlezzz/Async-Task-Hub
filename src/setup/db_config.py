from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Configuration for database connectivity."""
    DATABASE_URL: str

    model_config = ConfigDict(env_file=".env", extra="ignore")
