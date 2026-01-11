
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class ApiSettings(BaseSettings):
    """Configuration for API limits and metadata."""
    MAX_DIGITS: int = 2000
    APP_NAME: str = "posttager-pi"
    APP_VERSION: str = "0.1.0"

    model_config = ConfigDict(env_file=".env", extra="ignore")
