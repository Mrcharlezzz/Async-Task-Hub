from dataclasses import dataclass


@dataclass(frozen=True)
class TaskRoute:
    task_type: str
    celery_task: str
    queue: str | None = None


class TaskRegistry:
    """Registry mapping task types to Celery routing info."""

    def __init__(self) -> None:
        self._registry: dict[str, TaskRoute] = {
            "compute_pi": TaskRoute(
                task_type="compute_pi",
                celery_task="compute_pi",
                queue=None,
            ),
            "document_analysis": TaskRoute(
                task_type="document_analysis",
                celery_task="document_analysis",
                queue="doc-tasks",
            ),
        }

    def route_for_task_type(self, task_type: str) -> TaskRoute:
        try:
            return self._registry[task_type]
        except KeyError as exc:
            raise ValueError(f"No task route registered for task type {task_type!r}") from exc
