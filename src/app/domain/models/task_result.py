from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.app.domain.models.task_metadata import TaskMetadata


class TaskResultMetadata(BaseModel):
    """Execution metadata for a task result."""

    worker: str | None = Field(
        default=None, description="Worker hostname or identifier."
    )
    queue: str | None = Field(
        default=None, description="Queue name used for execution."
    )
    trace_id: str | None = Field(
        default=None, description="Trace identifier for request correlation."
    )


class TaskResult(BaseModel):
    task_id: str = Field(description="Identifier of the task.")
    task_metadata: TaskMetadata | None = Field(
        default=None, description="Lifecycle metadata for the task."
    )
    data: Any | None = Field(default=None, description="Result payload.")
    metadata: TaskResultMetadata | None = Field(
        default=None, description="Execution metadata for the result."
    )
    expires_at: datetime | None = Field(
        default=None, description="When the result expires."
    )
    ttl_seconds: int | None = Field(
        default=None, description="Time-to-live in seconds."
    )
