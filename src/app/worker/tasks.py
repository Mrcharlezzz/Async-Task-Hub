import time
from datetime import datetime, timezone
from typing import Any

from mpmath import mp

from src.app.infrastructure.celery.app import celery_app
from src.setup.worker_config import get_worker_settings

_settings = get_worker_settings()

celery_app.autodiscover_tasks(
    packages=["src.app.worker"],
    related_name="tasks",
    force=True,
)


def get_pi(digits: int) -> str:
    mp.dps = digits
    return str(mp.pi)


def _base_meta(self, payload: dict, started_at: datetime | None = None) -> dict:
    payload_data = payload.get("payload", {})
    return {
        "started_at": started_at.isoformat() if started_at else None,
        "worker": getattr(self.request, "hostname", None),
        "queue": (self.request.delivery_info or {}).get("routing_key"),
        "trace_id": payload_data.get("trace_id"),
    }


@celery_app.task(name="compute_pi", bind=True)
def compute_pi(self, payload: dict) -> dict:
    """
    Pi computation task.
    Simulates heavy pi calculation.
    """
    payload_data = payload["payload"]
    digits: int = payload_data["digits"]
    pi: str = get_pi(digits)
    started_at = datetime.now(timezone.utc)

    for k in range(digits):
        time.sleep(_settings.SLEEP_PER_DIGIT_SEC)
        progress = (k + 1) / digits
        self.update_state(
            state="PROGRESS",
            meta={
                "progress": progress,
                "message": None,
                "result": None,
                **_base_meta(self, payload, started_at),
            },
        )

    result = {
        "progress": 1.0,
        "message": None,
        "result": pi,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        **_base_meta(self, payload, started_at),
    }
    return result


def _simulate_steps(
    self,
    payload: dict[str, Any],
    steps: int,
    started_at: datetime,
    sleep: float = 0.1,
) -> None:
    for idx in range(steps):
        time.sleep(sleep)
        self.update_state(
            state="PROGRESS",
            meta={
                "progress": (idx + 1) / steps,
                "message": None,
                "result": None,
                **_base_meta(self, payload, started_at),
            },
        )


@celery_app.task(name="document_analysis", bind=True)
def document_analysis(self, payload: dict) -> dict:
    """
    Dummy document analysis task.
    """
    started_at = datetime.now(timezone.utc)
    _simulate_steps(self, payload, steps=5, started_at=started_at)
    return {
        "progress": 1.0,
        "message": None,
        "result": {
            "task_id": self.request.id,
            "task_type": payload.get("task_type"),
            "payload": payload.get("payload"),
            "analysis": "documents analyzed",
        },
        "finished_at": datetime.now(timezone.utc).isoformat(),
        **_base_meta(self, payload, started_at),
    }
