from typing import Any

from pydantic import BaseModel, Field


class StatusDTO(BaseModel):
    """
    Represents the status of a Celery task.
    """

    task_id: str = Field(..., description="Unique identifier of the task")
    state: str = Field(
        ..., description="Celery task state: PENDING, STARTED, PROGRESS, SUCCESS, FAILURE"
    )
    progress: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Normalized progress value between 0 and 1 if available",
    )
    message: str | None = Field(None, description="Optional progress or error message")
    result: Any | None = Field(None, description="Task result data if state=SUCCESS")
