from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Configuration for database connectivity."""
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
