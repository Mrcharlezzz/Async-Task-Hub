import time
from datetime import datetime, timezone

from src.app.infrastructure.celery.app import celery_app
from src.app.worker.reporter import TaskReporter


def _simulate_steps(reporter: TaskReporter, steps: int, started_at: datetime, sleep: float) -> None:
    for idx in range(steps):
        time.sleep(sleep)
        reporter.report_progress((idx + 1) / steps, started_at)


@celery_app.task(name="document_analysis", bind=True)
def document_analysis(self, payload: dict) -> dict:
    """
    Dummy document analysis task.
    """
    reporter = TaskReporter(self)
    started_at = datetime.now(timezone.utc)
    _simulate_steps(reporter, steps=5, started_at=started_at, sleep=0.1)
    result = {
        "task_id": self.request.id,
        "task_type": payload.get("task_type"),
        "payload": payload.get("payload"),
        "analysis": "documents analyzed",
    }
    return reporter.report_completed(result, started_at)
