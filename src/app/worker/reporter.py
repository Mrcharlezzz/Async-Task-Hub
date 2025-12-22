from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import inject

from src.app.domain.models.task_metadata import TaskMetadata
from src.app.domain.models.task_progress import TaskProgress
from src.app.domain.models.task_result import TaskResult
from src.app.domain.models.task_state import TaskState
from src.app.domain.models.task_status import TaskStatus
from src.app.domain.repositories import StorageRepository
from src.setup.app_config import configure_di


class TaskReporter:
    """Mirror task state updates to both Celery and the storage backend."""

    def __init__(self, celery_task: Any) -> None:
        configure_di()
        self._task = celery_task
        self._storage: StorageRepository = inject.instance(StorageRepository)

    def report_progress(self, progress: float, started_at: datetime) -> None:
        meta = {
            "progress": progress,
            "message": None,
            "result": None,
            "started_at": started_at.isoformat(),
        }
        self._task.update_state(state="PROGRESS", meta=meta)

        status = TaskStatus(
            state=TaskState.RUNNING,
            progress=TaskProgress(percentage=progress),
            message=None,
        )
        metadata = TaskMetadata(
            started_at=started_at,
            updated_at=datetime.now(timezone.utc),
        )
        self._run_async(self._storage.update_task_status(self._task.request.id, status, metadata))

    def report_completed(self, result: Any, started_at: datetime) -> dict:
        finished_at = datetime.now(timezone.utc)
        status = TaskStatus(
            state=TaskState.COMPLETED,
            progress=TaskProgress(percentage=1.0),
            message=None,
        )
        metadata = TaskMetadata(
            started_at=started_at,
            finished_at=finished_at,
            updated_at=finished_at,
        )
        self._run_async(self._storage.update_task_status(self._task.request.id, status, metadata))
        self._run_async(
            self._storage.set_task_result(
                self._task.request.id,
                TaskResult(
                    task_id=self._task.request.id,
                    task_metadata=metadata,
                    data=result,
                ),
                finished_at=finished_at,
            )
        )

        return {
            "progress": 1.0,
            "message": None,
            "result": result,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
        }

    @staticmethod
    def _run_async(coro: Any) -> None:
        asyncio.run(coro)
