from __future__ import annotations

import pytest

from src.app.domain.models import ComputePiPayload, TaskType
from src.app.domain.models.task_progress import TaskProgress
from src.app.domain.models.task_state import TaskState
from src.app.domain.models.task_status import TaskStatus


@pytest.mark.asyncio
async def test_task_service_enqueue_uses_repository(stubbed_services):
    services_module, task_stub, _storage_stub = stubbed_services
    service = services_module.TaskService()

    payload = ComputePiPayload(digits=12)
    task_id = await service.push_task(TaskType.COMPUTE_PI, payload)

    assert task_id == "compute_pi-1"
    assert len(task_stub.enqueued_tasks) == 1
    enqueued = task_stub.enqueued_tasks[0]
    assert enqueued.task_type == TaskType.COMPUTE_PI
    assert enqueued.payload == payload


@pytest.mark.asyncio
async def test_task_service_returns_status_from_repository(stubbed_services):
    services_module, task_stub, storage_stub = stubbed_services
    status = TaskStatus(
        state=TaskState.COMPLETED,
        progress=TaskProgress(percentage=1.0),
        message=None,
    )
    storage_stub.status_by_id["job-42"] = status

    service = services_module.TaskService()
    returned = await service.get_status("job-42")

    assert returned is status
