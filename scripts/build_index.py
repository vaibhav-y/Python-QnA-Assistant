"""CLI to build the FAISS index from the Stack Overflow CSVs.

Usage:
    python scripts/build_index.py --data-dir data/dataset --index-dir data/index
    python scripts/build_index.py --data-dir data/sample --min-question-score 0 --min-answer-score 0
"""
import argparse
import logging
import sys
from pathlib import Path

# Allow running directly as a script (put project root on the import path).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.indexer import build_index
from app.logging_config import setup_logging

logger = logging.getLogger("build_index")


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Build the FAISS index.")
    parser.add_argument("--data-dir", default=config.DATA_DIR)
    parser.add_argument("--index-dir", default=config.INDEX_DIR)
    parser.add_argument("--max-docs", type=int, default=config.MAX_DOCS)
    parser.add_argument("--min-question-score", type=int, default=config.MIN_QUESTION_SCORE)
    parser.add_argument("--min-answer-score", type=int, default=config.MIN_ANSWER_SCORE)
    args = parser.parse_args()

    try:
        n = build_index(
            args.data_dir, args.index_dir,
            args.min_question_score, args.min_answer_score, args.max_docs,
            show_progress=True,
        )
    except ValueError as exc:
        logger.error(str(exc))
        sys.exit(1)
    logger.info("done: %d vectors in %s", n, args.index_dir)


if __name__ == "__main__":
    main()
