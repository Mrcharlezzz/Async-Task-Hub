from __future__ import annotations

from src.api.domain.models import StatusDTO


def test_task_service_enqueue_uses_repository(stubbed_services):
    services_module, stub = stubbed_services
    service = services_module.TaskService()

    payload = {"digits": 12}
    task_id = service.push_task("compute_pi", payload)

    assert task_id == "compute_pi-1"
    assert stub.enqueued == [("compute_pi", payload)]


def test_progress_service_returns_status_from_repository(stubbed_services):
    services_module, stub = stubbed_services
    status = StatusDTO(
        task_id="job-42",
        state="SUCCESS",
        progress=1.0,
        message=None,
        result="3.14",
    )
    stub.status_by_id["job-42"] = status

    service = services_module.ProgressService()
    returned = service.get_progress("job-42")

    assert returned is status
