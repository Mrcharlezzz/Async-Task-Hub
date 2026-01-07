from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.naive.compute_pi.storage import ComputePiStore
from src.naive.document_analysis.storage import DocumentAnalysisStore

router = APIRouter(prefix="/naive", tags=["naive"])


class NaivePiRequest(BaseModel):
    digits: int = Field(..., ge=1, le=2000)
    task_id: str | None = None


class NaiveDocRequest(BaseModel):
    document_path: str = Field(..., description="Local path to the document.")
    keywords: list[str] = Field(..., description="Keywords to search for.")
    task_id: str | None = None


def _compute_store() -> ComputePiStore:
    store = ComputePiStore("/data/naive.sqlite")
    store.init_db()
    return store


def _doc_store() -> DocumentAnalysisStore:
    store = DocumentAnalysisStore("/data/naive.sqlite")
    store.init_db()
    return store


@router.post("/calculate_pi")
def naive_calculate_pi(body: NaivePiRequest):
    store = _compute_store()
    task_id = body.task_id or uuid4().hex
    if store.get_task(task_id) is None:
        store.create_task(task_id, body.digits)
    return {"task_id": task_id}


@router.get("/check_progress")
def naive_check_progress(task_id: str = Query(..., description="Naive task id")):
    store = _compute_store()
    task = store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    percent = 0.0
    if task.progress_total:
        percent = task.progress_current / task.progress_total
    return {
        "state": task.status,
        "progress": {
            "current": task.progress_current,
            "total": task.progress_total,
            "percentage": percent,
        },
        "metrics": task.metrics,
    }


@router.get("/task_result")
def naive_task_result(task_id: str = Query(..., description="Naive task id")):
    store = _compute_store()
    task = store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.task_id,
        "partial_result": task.result,
        "done": task.done,
    }


@router.post("/document-analysis")
def naive_document_analysis(body: NaiveDocRequest):
    store = _doc_store()
    task_id = body.task_id or uuid4().hex
    if store.get_doc_task(task_id) is None:
        store.create_doc_task(task_id, body.document_path, body.keywords)
    return {"task_id": task_id}


@router.get("/document-analysis/status")
def naive_document_status(task_id: str = Query(..., description="Naive task id")):
    store = _doc_store()
    task = store.get_doc_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    percent = 0.0
    if task.progress_total:
        percent = task.progress_current / task.progress_total
    return {
        "state": task.status,
        "progress": {
            "current": task.progress_current,
            "total": task.progress_total,
            "percentage": percent,
        },
        "metrics": task.metrics,
    }


@router.get("/document-analysis/snippets")
def naive_document_snippets(task_id: str = Query(...), after: int | None = None):
    store = _doc_store()
    task = store.get_doc_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    last_id = after if after is not None else task.last_snippet_id
    snippets = store.get_doc_snippets_since(task_id, last_id)
    if snippets:
        store.mark_doc_snippets_delivered(task_id, snippets[-1]["id"])
    return {"snippets": snippets, "last_id": snippets[-1]["id"] if snippets else last_id}
