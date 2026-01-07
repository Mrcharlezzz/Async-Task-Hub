from pydantic import BaseModel, Field


class TaskPayload(BaseModel):
    """Marker/base class for task payloads."""

    pass


class DocumentAnalysisPayload(TaskPayload):
    document_path: str = Field(description="Local path to the document to analyze.")
    keywords: list[str] = Field(
        description="Keywords to search for (case-insensitive substring match)."
    )


class ComputePiPayload(TaskPayload):
    digits: int = Field(description="Number of digits to compute.")
