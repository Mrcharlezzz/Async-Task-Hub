
import inject
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

from src.app.domain.repositories import TaskManagerRepository
from src.app.infrastructure.celery.celery_task_manager import CeleryTaskManager


class ApiSettings(BaseSettings):
    MAX_DIGITS: int = 2000
    APP_NAME: str = "posttager-pi"
    APP_VERSION: str = "0.1.0"

    model_config = ConfigDict(env_file=".env", extra="ignore")
        

def get_api_settings() -> ApiSettings:
    return ApiSettings() # type: ignore[call-arg]

def _config(binder: inject.Binder) -> None:
    """
    Bind domain interfaces to concrete implementations.
    """
    binder.bind(TaskManagerRepository, CeleryTaskManager())


def configure_di() -> None:
    """Dependency injection configuration."""
    if not inject.is_configured():
        inject.configure(_config)
