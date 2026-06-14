"""Build the FAISS index from the Stack Overflow Python CSVs.

Shared by the CLI (scripts/build_index.py) and the API's /reindex endpoint.
Steps: load CSVs -> filter by score -> top answer per question -> clean HTML
-> build Q&A documents -> embed (one vector per URL) -> save FAISS.
"""
import gc
import logging
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app import config
from app.embeddings import make_embeddings

logger = logging.getLogger(__name__)


def clean_html(text) -> str:
    """Strip HTML tags but keep the text (including code) readable."""
    if not isinstance(text, str):
        return ""
    return BeautifulSoup(text, "lxml").get_text(separator="\n").strip()


def load_csvs(data_dir: Path):
    logger.info("loading CSVs from %s", data_dir)
    # Read only the columns we use, to keep memory low.
    questions = pd.read_csv(
        data_dir / "Questions.csv", encoding="latin-1",
        usecols=["Id", "Score", "Title", "Body"],
    )
    answers = pd.read_csv(
        data_dir / "Answers.csv", encoding="latin-1",
        usecols=["ParentId", "Score", "Body"],
    )
    try:
        tags = pd.read_csv(
            data_dir / "Tags.csv", encoding="latin-1", usecols=["Id", "Tag"]
        )
    except FileNotFoundError:
        tags = None
    logger.info("loaded %d questions, %d answers", len(questions), len(answers))
    return questions, answers, tags


def build_documents(questions, answers, tags, min_q, min_a, max_docs):
    # Scores occasionally parse as strings in this dataset
    # (non-numeric -> NaN, which then fails the >= filter and is dropped).
    questions = questions.copy()
    answers = answers.copy()
    questions["Score"] = pd.to_numeric(questions["Score"], errors="coerce")
    answers["Score"] = pd.to_numeric(answers["Score"], errors="coerce")

    questions = questions[questions["Score"] >= min_q]
    logger.info("%d questions after Score >= %d", len(questions), min_q)

    # Top-scored answer per question.
    answers = answers[answers["Score"] >= min_a]
    best = (
        answers.sort_values("Score", ascending=False)
        .drop_duplicates("ParentId", keep="first")
        .set_index("ParentId")
    )

    tag_map = {}
    if tags is not None:
        tag_map = tags.groupby("Id")["Tag"].apply(list).to_dict()

    # Highest-scored questions first, so the cap keeps the best content.
    questions = questions.sort_values("Score", ascending=False)

    docs = []
    for _, q in questions.iterrows():
        qid = q["Id"]
        if qid not in best.index:
            continue
        title = str(q["Title"])
        content = (
            f"Question: {title}\n\n{clean_html(q['Body'])}\n\n"
            f"Answer:\n{clean_html(best.loc[qid, 'Body'])}"
        )
        docs.append(
            Document(
                page_content=content,
                metadata={
                    "url": f"https://stackoverflow.com/questions/{qid}",
                    "title": title,
                    "so_score": int(q["Score"]),
                    "tags": tag_map.get(qid, []),
                },
            )
        )
        if len(docs) >= max_docs:
            break

    logger.info("built %d Q&A documents", len(docs))
    return docs


def build_index(data_dir, index_dir, min_q, min_a, max_docs, show_progress=False) -> int:
    """Build and persist the FAISS index. Returns the number of vectors written."""
    questions, answers, tags = load_csvs(Path(data_dir))
    docs = build_documents(questions, answers, tags, min_q, min_a, max_docs)
    if not docs:
        raise ValueError("no documents built; check the filters or input data")

    # Free the large source DataFrames before embedding to keep peak memory down.
    del questions, answers, tags
    gc.collect()

    logger.info("loading embedding model: %s", config.EMBED_MODEL)
    embeddings = make_embeddings(show_progress=show_progress)
    logger.info("embedding %d documents (one vector per URL) and building FAISS index", len(docs))
    vectorstore = FAISS.from_documents(docs, embeddings)

    dim = vectorstore.index.d
    logger.info("vector dimension: %d", dim)
    if config.VECTOR_SIZE and dim != config.VECTOR_SIZE:
        raise ValueError(
            f"VECTOR_SIZE mismatch: configured {config.VECTOR_SIZE} but index has {dim}"
        )

    Path(index_dir).mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(index_dir)
    logger.info("saved index to %s (%d vectors)", index_dir, vectorstore.index.ntotal)
    return vectorstore.index.ntotal
