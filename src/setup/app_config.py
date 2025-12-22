import inject

from src.app.domain.repositories import StorageRepository, TaskManagerRepository
from src.app.infrastructure.celery.repositories import CeleryTaskManager
from src.app.infrastructure.postgres.orm import PostgresOrm
from src.app.infrastructure.postgres.repositories import PostgresStorageRepository
from src.setup.db_config import get_database_settings


def _config(binder: inject.Binder) -> None:
    """Bind domain interfaces to concrete implementations."""
    db_settings = get_database_settings()
    orm = PostgresOrm(db_settings.DATABASE_URL)
    binder.bind(TaskManagerRepository, CeleryTaskManager())
    binder.bind(StorageRepository, PostgresStorageRepository(orm))


def configure_di() -> None:
    """Dependency injection configuration."""
    if not inject.is_configured():
        inject.configure(_config)
