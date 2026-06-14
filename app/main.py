"""FastAPI service for the Python Q&A Assistant."""
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, Field

from app import config, rag
from app.indexer import build_index as build_index_fn
from app.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logging.getLogger(__name__).info("startup: loading RAG pipeline")
    rag.load_pipeline()
    logging.getLogger(__name__).info("startup complete")
    yield
    logging.getLogger(__name__).info("shutdown")


app = FastAPI(title="Python Q&A Assistant", version="1.0", lifespan=lifespan)
logger = logging.getLogger(__name__)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="A Python programming question")
    top_k: Optional[int] = Field(None, ge=1, le=20)


class Source(BaseModel):
    url: str
    title: str = ""
    score: Optional[int] = None


class AskResponse(BaseModel):
    answer: str
    sources: List[Source]


class ReindexRequest(BaseModel):
    data_dir: Optional[str] = None
    max_docs: Optional[int] = Field(None, ge=1)
    min_question_score: Optional[int] = None
    min_answer_score: Optional[int] = None


# In-process status for the (single) background rebuild.
_reindex_status = {"state": "idle", "detail": "", "vectors": None}


@app.get("/health")
def health():
    return {"status": "ok", "ready": rag.is_ready()}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    logger.info("received question: %r", req.question[:200])
    return rag.answer(req.question, k=req.top_k)


def _do_reindex(data_dir, min_q, min_a, max_docs):
    _reindex_status.update(state="running", detail="building index", vectors=None)
    try:
        n = build_index_fn(data_dir, config.INDEX_DIR, min_q, min_a, max_docs)
        rag.reload_index()  # swap the freshly built index into the live service
        _reindex_status.update(state="done", detail=f"built {n} vectors", vectors=n)
        logger.info("reindex complete: %d vectors", n)
    except Exception as exc:
        logger.exception("reindex failed")
        _reindex_status.update(state="failed", detail=str(exc), vectors=None)


@app.post("/reindex")
def reindex(req: ReindexRequest, background_tasks: BackgroundTasks):
    """Rebuild the FAISS index from the dataset (runs in the background)."""
    if _reindex_status["state"] == "running":
        return {"state": "running", "detail": "a rebuild is already in progress"}
    data_dir = req.data_dir or config.DATA_DIR
    min_q = req.min_question_score if req.min_question_score is not None else config.MIN_QUESTION_SCORE
    min_a = req.min_answer_score if req.min_answer_score is not None else config.MIN_ANSWER_SCORE
    max_docs = req.max_docs or config.MAX_DOCS
    _reindex_status.update(state="running", detail="queued", vectors=None)
    background_tasks.add_task(_do_reindex, data_dir, min_q, min_a, max_docs)
    logger.info("reindex started: data_dir=%s max_docs=%d", data_dir, max_docs)
    return {"state": "started", "detail": f"rebuilding from {data_dir} (max_docs={max_docs})"}


@app.get("/reindex/status")
def reindex_status():
    return _reindex_status
