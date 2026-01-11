from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    """Configuration for worker behavior in compute_pi tasks."""
    SLEEP_PER_DIGIT_SEC: float = 0.1
    ROUNDING_POLICY: str = "TRUNCATE"

    model_config = ConfigDict(env_file=".env", extra="ignore")

def get_worker_settings() -> WorkerSettings:
    """Return a fresh worker settings instance."""
    return WorkerSettings()
