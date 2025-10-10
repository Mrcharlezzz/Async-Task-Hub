from __future__ import annotations

from celery.result import AsyncResult

from src.api.domain.models import StatusDTO
from src.api.domain.repositories import TaskManagerRepository
from src.api.infrastructure.celery.app import celery_app
from src.api.infrastructure.mappers import to_status_dto


class CeleryTaskManager(TaskManagerRepository):
    """
    Orchestrates task queue operations such as enqueuing tasks and retrieving their status.
    """

    def __init__(self, celery_app_instance=celery_app):
        self._celery_app = celery_app_instance

    def enqueue(self, task_name: str, payload: dict) -> str:
        """
        Enqueue a task in the broker and return the task id.
        """
        async_result = self._celery_app.send_task(task_name, args=[payload])
        return async_result.id

    def get_status(self, task_id: str) -> StatusDTO:
        """
        Retrieve the current status for a task.
        """
        result = AsyncResult(task_id, app=self._celery_app)
        return to_status_dto(result)
