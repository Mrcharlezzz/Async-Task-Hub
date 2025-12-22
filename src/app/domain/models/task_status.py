from pydantic import BaseModel, Field

from src.app.domain.models.task_progress import TaskProgress
from src.app.domain.models.task_state import TaskState


class TaskStatus(BaseModel):
    state: TaskState = Field(description="Current lifecycle state of the task.")
    progress: TaskProgress = Field(description="Progress information for the task.")
    message: str | None = Field(
        default=None, description="Optional status or error message."
    )
