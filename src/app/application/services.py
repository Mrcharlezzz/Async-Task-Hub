import inject
from datetime import datetime, timezone
from src.app.domain.models import (
    Task,
    TaskMetadata,
    TaskPayload,
    TaskProgress,
    TaskResult,
    TaskState,
    TaskStatus,
    TaskType,
)
from src.app.domain.repositories import TaskManagerRepository


class ProgressService:
    """Provides access to progress data for background tasks."""

    def __init__(self):
        self._task_manager: TaskManagerRepository = inject.instance(TaskManagerRepository)

    async def get_progress(self, task_name: str) -> TaskStatus:
        """Return the current status for the task identified by ``task_name``."""
        status = await self._task_manager.get_status(task_name)
        return status


class ResultService:
    """Provides access to result data for background tasks."""

    def __init__(self):
        self._task_manager: TaskManagerRepository = inject.instance(TaskManagerRepository)

    async def get_result(self, task_id: str) -> TaskResult:
        """Return the current result payload for the task identified by ``task_id``."""
        result = await self._task_manager.get_result(task_id)
        return result

class TaskService:
    """Handles submission of asynchronous tasks to the Celery broker."""

    def __init__(self):
        self._task_manager: TaskManagerRepository = inject.instance(TaskManagerRepository)

    async def push_task(self, task_type: TaskType, payload: TaskPayload) -> str:
        """Enqueue a task with the provided payload and return its task id."""
        task = await self.create_task(task_type, payload)
        return task.id

    async def create_task(self, task_type: TaskType, payload: TaskPayload) -> Task:
        """
        Create a typed task and enqueue it via the task manager.
        """
        task = Task(
            task_type=task_type,
            payload=payload,
            status=TaskStatus(state=TaskState.QUEUED, progress=TaskProgress()),
            metadata=TaskMetadata(created_at=datetime.now(timezone.utc)),
        )
        task.id = await self._task_manager.enqueue(task)
        return task
