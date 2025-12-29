import pytest

from src.app.application.handlers import handle_result_event, handle_status_event
from src.app.domain.events.task_event import TaskEvent
from src.app.domain.models.task_progress import TaskProgress
from src.app.domain.models.task_state import TaskState
from src.app.domain.models.task_status import TaskStatus
from src.app.domain.repositories import StorageRepository


class StubStorage(StorageRepository):
    def __init__(self) -> None:
        self.status_calls: list[tuple[str, TaskStatus]] = []
        self.result_calls: list[tuple[str, object]] = []

    async def create_task(self, user_id: str, task):  # pragma: no cover - not used
        raise NotImplementedError

    async def get_task(self, user_id: str, task_id: str):  # pragma: no cover - not used
        raise NotImplementedError

    async def get_status(self, user_id: str, task_id: str):  # pragma: no cover - not used
        raise NotImplementedError

    async def get_result(self, user_id: str, task_id: str):  # pragma: no cover - not used
        raise NotImplementedError

    async def list_tasks(self, user_id: str, **kwargs):  # pragma: no cover - not used
        raise NotImplementedError

    async def update_task_status(self, task_id: str, status: TaskStatus, metadata=None) -> None:
        self.status_calls.append((task_id, status))

    async def set_task_result(self, task_id: str, result, finished_at=None) -> None:
        self.result_calls.append((task_id, result))


@pytest.mark.asyncio
async def test_handle_status_event_updates_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    storage = StubStorage()

    import inject

    monkeypatch.setattr(inject, "instance", lambda interface: storage)

    status = TaskStatus(
        state=TaskState.RUNNING,
        progress=TaskProgress(current=1, total=4, percentage=0.25),
        message="working",
    )
    event = TaskEvent.status("task-1", status)

    await handle_status_event(event)

    assert storage.status_calls == [("task-1", status)]


@pytest.mark.asyncio
async def test_handle_result_event_updates_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    storage = StubStorage()

    import inject

    monkeypatch.setattr(inject, "instance", lambda interface: storage)

    payload = {"task_id": "task-2", "data": {"value": 42}}
    event = TaskEvent.result("task-2", payload)

    await handle_result_event(event)

    assert len(storage.result_calls) == 1
    task_id, result = storage.result_calls[0]
    assert task_id == "task-2"
    assert result.task_id == "task-2"
    assert result.data == {"value": 42}
