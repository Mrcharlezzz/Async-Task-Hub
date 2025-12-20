from __future__ import annotations

import asyncio

from celery.result import AsyncResult

from src.api.domain.repositories import TaskManagerRepository
from src.api.infrastructure.celery.app import celery_app
from src.api.infrastructure.celery.mappers import CeleryMapper
from src.api.infrastructure.celery.task_registry import TaskRegistry
from src.api.domain.models.task import Task
from src.api.domain.models.task_status import TaskStatus


class CeleryTaskManager(TaskManagerRepository):
    """
    Orchestrates task queue operations such as enqueuing tasks and retrieving their status.
    """

    def __init__(self, celery_app_instance=celery_app):
        self._celery_app = celery_app_instance
        self._registry = TaskRegistry()

    async def enqueue(self, task_name: str, payload: dict, queue: str | None = None) -> str:
        """
        Enqueue a task in the broker and return the task id.
        """
        async_result = await asyncio.to_thread(
            self._celery_app.send_task, task_name, args=[payload], queue=queue
        )
        return async_result.id

    async def enqueue_task(self, task: Task) -> str:
        """
        Enqueue a task and return the task id.
        """
        route = self._registry.route_for_task_type(task.task_type)
        message = {
            "task_type": task.task_type,
            "payload": task.payload.model_dump(),
        }
        async_result = await asyncio.to_thread(
            self._celery_app.send_task, route.celery_task, args=[message], queue=route.queue
        )
        return async_result.id

    async def get_status(self, task_id: str) -> TaskStatus:
        """
        Retrieve the current status for a task.
        """
        result = await asyncio.to_thread(AsyncResult, task_id, app=self._celery_app)
        return await asyncio.to_thread(CeleryMapper.map_status, result)
