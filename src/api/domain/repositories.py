from __future__ import annotations

from typing import Protocol

from src.api.domain.models.task_status import TaskStatus
from src.api.domain.models.task import Task


class TaskManagerRepository(Protocol):
    """Repository contract for enqueueing tasks and retrieving their status."""

    async def enqueue(self, task: Task) -> str:
        """Schedule a task and return its identifier."""

    async def get_status(self, task_id: str) -> TaskStatus:
        """Fetch the current status representation for the task identified by ``task_id``."""
