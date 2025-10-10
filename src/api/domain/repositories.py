from __future__ import annotations

from typing import Protocol

from src.api.domain.models import StatusDTO


class TaskManagerRepository(Protocol):
    """Repository contract for enqueueing tasks and retrieving their status."""

    def enqueue(self, task_name: str, payload: dict) -> str:
        """Schedule a task with the given payload and return its identifier."""

    def get_status(self, task_id: str) -> StatusDTO:
        """Fetch the current status representation for the task identified by ``task_id``."""
