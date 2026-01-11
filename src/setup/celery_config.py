from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class CelerySettings(BaseSettings):
    """Configuration for Celery broker/result backend."""
    REDIS_URL: str = "redis://redis:6379/0" 
    RESULT_TTL_SECONDS: int = 3600

    model_config = ConfigDict(env_file=".env", extra="ignore")

def get_celery_settings() -> CelerySettings:
    """Return a fresh Celery settings instance."""
    return CelerySettings()
