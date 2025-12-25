from __future__ import annotations

import importlib
from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.app.domain.exceptions import TaskNotFoundError
from datetime import datetime

from src.app.domain.models.task import Task
from src.app.domain.models.task_metadata import TaskMetadata
from src.app.domain.models.task_result import TaskResult
from src.app.domain.models.task_state import TaskState
from src.app.domain.models.task_status import TaskStatus
from src.app.domain.models.task_type import TaskType
from src.app.domain.models.task_view import TaskView
from src.app.domain.repositories import StorageRepository, TaskManagerRepository


class StubTaskManager(TaskManagerRepository):
    """Simple in-memory TaskManager replacement for tests."""

    def __init__(self) -> None:
        self.enqueued_tasks: list[Task] = []
        self.status_by_id: dict[str, TaskStatus] = {}
        self.results_by_id: dict[str, TaskResult] = {}

    async def enqueue(self, task: Task) -> str:
        if task.id is None:
            task.id = f"{task.task_type.value}-{len(self.enqueued_tasks) + 1}"
        task_id = task.id
        self.enqueued_tasks.append(task)
        return task_id

    async def get_status(self, task_id: str) -> TaskStatus:
        if task_id not in self.status_by_id:
            raise TaskNotFoundError(task_id)
        return self.status_by_id[task_id]

    async def get_result(self, task_id: str) -> TaskResult:
        if task_id not in self.results_by_id:
            raise TaskNotFoundError(task_id)
        return self.results_by_id[task_id]


class StubStorageRepository(StorageRepository):
    def __init__(self) -> None:
        self.status_by_id: dict[str, TaskStatus] = {}
        self.results_by_id: dict[str, TaskResult] = {}
        self._counter = 0

    async def create_task(self, user_id: str, task: Task) -> str:
        if task.id is None:
            self._counter += 1
            task.id = f"{task.task_type.value}-{self._counter}"
        return task.id

    async def get_task(self, user_id: str, task_id: str) -> Task | None:
        return None

    async def list_tasks(
        self,
        user_id: str,
        *,
        task_type: TaskType | None = None,
        state: TaskState | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TaskView]:
        return []

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        metadata: TaskMetadata | None = None,
    ) -> None:
        return None

    async def set_task_result(
        self,
        task_id: str,
        result: TaskResult,
        finished_at: datetime | None = None,
    ) -> None:
        return None

    async def get_status(self, user_id: str, task_id: str) -> TaskStatus:
        if task_id not in self.status_by_id:
            raise TaskNotFoundError(task_id)
        return self.status_by_id[task_id]

    async def get_result(self, user_id: str, task_id: str) -> TaskResult:
        if task_id not in self.results_by_id:
            raise TaskNotFoundError(task_id)
        return self.results_by_id[task_id]


@pytest.fixture
def env_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide required environment variables for ApiSettings."""
    monkeypatch.setenv("MAX_DIGITS", "5")
    monkeypatch.setenv("APP_NAME", "Test API")
    monkeypatch.setenv("APP_VERSION", "0.1.0")


def _patch_inject_instance(
    monkeypatch: pytest.MonkeyPatch,
    task_stub: StubTaskManager,
    storage_stub: StubStorageRepository,
) -> Callable[[object], object]:
    """Patch `inject.instance` to always return the stub repository."""
    import inject

    def fake_instance(interface: object) -> object:
        if interface is TaskManagerRepository:
            return task_stub
        if interface is StorageRepository:
            return storage_stub
        raise RuntimeError(f"Unexpected dependency request: {interface}")

    monkeypatch.setattr(inject, "instance", fake_instance)
    return fake_instance


@pytest.fixture
def stubbed_services(env_settings: None, monkeypatch: pytest.MonkeyPatch):
    """Reload service module with stubbed repository injection."""
    task_stub = StubTaskManager()
    storage_stub = StubStorageRepository()
    _patch_inject_instance(monkeypatch, task_stub, storage_stub)

    services_module = importlib.reload(importlib.import_module("src.app.application.services"))
    return services_module, task_stub, storage_stub


@pytest.fixture
def api_client(env_settings: None, monkeypatch: pytest.MonkeyPatch):
    """FastAPI test client with services wired to the stub task manager."""
    task_stub = StubTaskManager()
    storage_stub = StubStorageRepository()
    _patch_inject_instance(monkeypatch, task_stub, storage_stub)

    # Reload modules so module-level singletons pick up the patched injector.
    services_module = importlib.reload(importlib.import_module("src.app.application.services"))  # noqa: F841
    routes_module = importlib.reload(importlib.import_module("src.app.presentation.routes"))

    app = FastAPI()
    app.include_router(routes_module.router)
    client = TestClient(app)
    return client, task_stub, storage_stub
