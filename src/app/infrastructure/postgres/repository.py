from __future__ import annotations

from datetime import datetime

from src.app.domain.models.task import Task
from src.app.domain.models.task_metadata import TaskMetadata
from src.app.domain.models.task_result import TaskResult
from src.app.domain.models.task_state import TaskState
from src.app.domain.models.task_status import TaskStatus
from src.app.domain.models.task_type import TaskType
from src.app.domain.repositories import StorageRepository, TaskSummary
from src.app.infrastructure.postgres.orm import PostgresOrm


class PostgresStorageRepository(StorageRepository):
    """
    Postgres-backed storage implementation.
    This is a scaffold; wire in your DB client/queries as needed.
    """

    def __init__(self, orm: PostgresOrm) -> None:
        self._orm = orm

    async def create_task(self, user_id: str, task: Task) -> str:
        raise NotImplementedError

    async def get_task(self, user_id: str, task_id: str) -> Task | None:
        raise NotImplementedError

    async def list_tasks(
        self,
        user_id: str,
        *,
        task_type: TaskType | None = None,
        state: TaskState | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TaskSummary]:
        raise NotImplementedError

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        metadata: TaskMetadata | None = None,
    ) -> None:
        raise NotImplementedError

    async def set_task_result(
        self,
        task_id: str,
        result: TaskResult,
        finished_at: datetime | None = None,
    ) -> None:
        raise NotImplementedError
