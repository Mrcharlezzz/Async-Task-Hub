from celery.result import AsyncResult
from pydantic import ValidationError

from src.api.domain.models import StatusDTO


def to_status_dto(result : AsyncResult) -> StatusDTO:
    info = result.info or {}
    try:
        if result.failed():
            return StatusDTO(
                task_id=result.id,
                state="FAILURE",
                progress=None,
                message=info.get("message"),
                result=None,
            )

        return StatusDTO(
            task_id=result.id,
            state=result.state,
            progress=info.get("progress"),
            message=info.get("message"),
            result=result.result if result.successful() else None,
        )

    except ValidationError as e:
        # fallback: mark as failure with error message
        return StatusDTO(
            task_id=result.id,
            state="FAILURE",
            progress=None,
            message=f"Mapping error: {e.errors()}",
            result=None,
        )
