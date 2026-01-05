from __future__ import annotations

from typing import Protocol

from src.app.domain.events.task_event import TaskEvent


class TaskStatusBroadcaster(Protocol):
    async def broadcast_status(self, event: TaskEvent) -> None:
        """Broadcast a task status event to connected clients."""
