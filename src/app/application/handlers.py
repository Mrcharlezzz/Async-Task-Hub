import logging

import inject

from src.app.application.broadcaster import TaskStatusBroadcaster
from src.app.domain.events.task_event import TaskEvent
from src.app.domain.models.task_result import TaskResult
from src.app.domain.models.task_state import TaskState
from src.app.domain.models.task_status import TaskStatus
from src.app.domain.repositories import StorageRepository

logger = logging.getLogger(__name__)


class TaskEventHandler:
    def __init__(
        self,
        storage: StorageRepository | None = None,
        broadcaster: TaskStatusBroadcaster | None = None,
        status_delta: float = 0.02,
    ) -> None:
        self._storage = storage or inject.instance(StorageRepository)
        self._broadcaster = broadcaster or inject.instance(TaskStatusBroadcaster)
        self._status_delta = status_delta
        self._status_cache: dict[str, float] = {}

    async def handle_status_event(self, event: TaskEvent) -> None:
        status_payload = event.payload.get("status")
        if not isinstance(status_payload, dict):
            raise ValueError("Status payload is missing or invalid")
        status = TaskStatus.model_validate(status_payload)
        pct = status.progress.percentage or 0.0
        last_pct = self._status_cache.get(event.task_id)
        is_terminal = status.state in {
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELLED,
        }
        if last_pct is None or abs(pct - last_pct) >= self._status_delta or is_terminal:
            await self._storage.update_task_status(event.task_id, status)
            self._status_cache[event.task_id] = pct
            if is_terminal:
                self._status_cache.pop(event.task_id, None)
        await self._broadcaster.broadcast_status(event)

    async def handle_result_event(self, event: TaskEvent) -> None:
        result_payload = event.payload.get("result")
        if isinstance(result_payload, dict):
            result_data = dict(result_payload)
            result_data.setdefault("task_id", event.task_id)
            result = TaskResult.model_validate(result_data)
        else:
            result = TaskResult(task_id=event.task_id, data=result_payload)
        await self._storage.set_task_result(event.task_id, result)

    async def handle_result_chunk_event(self, event: TaskEvent) -> None:
        payload = event.payload
        if not isinstance(payload, dict):
            raise ValueError("Result chunk payload is missing or invalid")
        if "chunk_id" not in payload or "data" not in payload:
            raise ValueError("Result chunk payload must include chunk_id and data")
        await self._broadcaster.broadcast_result_chunk(event)
