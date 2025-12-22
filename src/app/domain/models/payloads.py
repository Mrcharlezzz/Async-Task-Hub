from pydantic import BaseModel, Field


class TaskPayload(BaseModel):
    """Marker/base class for task payloads."""

    pass


class DocumentAnalysisPayload(TaskPayload):
    document_ids: list[str] = Field(
        description="IDs of documents to analyze."
    )
    run_ocr: bool = Field(
        default=True, description="Whether to run OCR before analysis."
    )
    language: str = Field(
        default="eng", description="OCR language code."
    )


class ComputePiPayload(TaskPayload):
    digits: int = Field(description="Number of digits to compute.")
