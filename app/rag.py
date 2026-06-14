"""RAG pipeline: retrieve Stack Overflow Q&A passages and generate a grounded answer.

The embedding model, FAISS index, and Groq client are loaded once (load_pipeline)
and reused across requests.
"""
import logging
import time
from typing import Optional

from groq import Groq
from langchain_community.vectorstores import FAISS

from app import config
from app.embeddings import make_embeddings

logger = logging.getLogger(__name__)

# Loaded once at startup by load_pipeline().
_embeddings = None
_vectorstore = None
_groq = None

SYSTEM_PROMPT = (
    "You are a helpful Python programming assistant for data science learners. "
    "Answer the question using ONLY the Stack Overflow context provided. "
    "Include short code examples when they help. If the context does not contain "
    "enough information to answer, say so plainly instead of guessing. "
    "Be concise and accurate."
)


def load_pipeline() -> None:
    """Load the embedding model, FAISS index, and Groq client (once)."""
    global _embeddings, _vectorstore, _groq

    logger.info("loading embedding model: %s", config.EMBED_MODEL)
    _embeddings = make_embeddings()

    logger.info("loading FAISS index from: %s", config.INDEX_DIR)
    _vectorstore = FAISS.load_local(
        config.INDEX_DIR,
        _embeddings,
        allow_dangerous_deserialization=True,  # we built this artifact ourselves
    )

    _groq = Groq(api_key=config.GROQ_API_KEY)
    logger.info("pipeline ready (%d vectors)", _vectorstore.index.ntotal)


def reload_index() -> None:
    """Reload the FAISS index from disk (e.g., after a rebuild)."""
    global _vectorstore
    logger.info("reloading FAISS index from: %s", config.INDEX_DIR)
    _vectorstore = FAISS.load_local(
        config.INDEX_DIR, _embeddings, allow_dangerous_deserialization=True
    )
    logger.info("index reloaded (%d vectors)", _vectorstore.index.ntotal)


def is_ready() -> bool:
    return _vectorstore is not None and _groq is not None


def retrieve(question: str, k: int):
    """Return a list of (Document, distance) for the question (lower distance = closer)."""
    return _vectorstore.similarity_search_with_score(question, k=k)


def build_prompt(question: str, docs) -> str:
    """Assemble the grounded user prompt from retrieved Q&A passages."""
    blocks = []
    for i, (doc, _score) in enumerate(docs, 1):
        url = doc.metadata.get("url", "")
        blocks.append(f"[Source {i}] {url}\n{doc.page_content}")
    context = "\n\n---\n\n".join(blocks) if blocks else "(no relevant context found)"
    return (
        f"Context from Stack Overflow:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer (grounded in the context above):"
    )


def answer(question: str, k: Optional[int] = None) -> dict:
    """Retrieve context and generate a grounded answer with source citations."""
    if k is None:
        k = config.TOP_K
    t0 = time.perf_counter()

    docs = retrieve(question, k)
    t_retrieve = time.perf_counter()

    prompt = build_prompt(question, docs)
    completion = _groq.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=config.GROQ_MAX_TOKENS,
    )
    t_llm = time.perf_counter()

    text = completion.choices[0].message.content
    usage = completion.usage
    top_dist = float(docs[0][1]) if docs else None
    sources = [
        {
            "url": doc.metadata.get("url", ""),
            "title": doc.metadata.get("title", ""),
            "score": doc.metadata.get("so_score"),
        }
        for doc, _ in docs
    ]

    logger.info(
        "ask q_len=%d k=%d top_dist=%s t_retrieve_ms=%d t_llm_ms=%d t_total_ms=%d "
        "tokens_in=%s tokens_out=%s",
        len(question), k,
        f"{top_dist:.3f}" if top_dist is not None else "na",
        int((t_retrieve - t0) * 1000),
        int((t_llm - t_retrieve) * 1000),
        int((t_llm - t0) * 1000),
        getattr(usage, "prompt_tokens", "na"),
        getattr(usage, "completion_tokens", "na"),
    )

    return {"answer": text, "sources": sources}
