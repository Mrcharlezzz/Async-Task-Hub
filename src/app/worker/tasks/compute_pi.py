import time
from datetime import datetime, timezone

from mpmath import mp

from src.app.infrastructure.celery.app import celery_app
from src.app.worker.reporter import TaskReporter
from src.setup.worker_config import get_worker_settings

_settings = get_worker_settings()


def get_pi(digits: int) -> str:
    mp.dps = digits
    return str(mp.pi)


@celery_app.task(name="compute_pi", bind=True)
def compute_pi(self, payload: dict) -> dict:
    """
    Pi computation task.
    Simulates heavy pi calculation.
    """
    reporter = TaskReporter(self)
    payload_data = payload["payload"]
    digits: int = payload_data["digits"]
    pi: str = get_pi(digits)
    started_at = datetime.now(timezone.utc)

    for k in range(digits):
        time.sleep(_settings.SLEEP_PER_DIGIT_SEC)
        progress = (k + 1) / digits
        reporter.report_progress(progress, started_at)

    return reporter.report_completed(pi, started_at)
