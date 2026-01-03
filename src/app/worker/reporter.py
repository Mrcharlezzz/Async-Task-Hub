from __future__ import annotations

from typing import Any

import inject

from src.app.domain.events.task_event import TaskEvent
from src.app.domain.models.task_status import TaskStatus
from src.app.domain.repositories import TaskEventPublisherRepository


class TaskReporter:
    """Publish task events to the stream."""

    def __init__(
        self,
        task_id: str,
        publisher: TaskEventPublisherRepository | None = None,
    ) -> None:
        self._task_id = task_id
        self._publisher = publisher or inject.instance(TaskEventPublisherRepository)

    def report_status(self, status: TaskStatus) -> None:
        event = TaskEvent.status(self._task_id, status)
        self._publish(event)

    def report_result(self, result_snapshot: dict[str, Any]) -> None:
        event = TaskEvent.result(self._task_id, result_snapshot)
        self._publish(event)

    def report_result_chunk(self, chunk_id: str, data: Any, is_last: bool = False) -> None:
        event = TaskEvent.result_chunk(self._task_id, chunk_id, data, is_last=is_last)
        self._publish(event)

    def _publish(self, event: TaskEvent) -> None:
        self._publisher.publish(event)
