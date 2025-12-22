from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    DATABASE_URL: str

    model_config = ConfigDict(env_file=".env", extra="ignore")


def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()  # type: ignore[call-arg]
