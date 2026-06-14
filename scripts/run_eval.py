"""Run a set of diverse Python questions through the RAG pipeline and write the
responses to test_results.md (the evaluation deliverable).

    python scripts/run_eval.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config, rag
from app.logging_config import setup_logging

QUERIES = [
    "How do I reverse a list in Python?",
    "How do I read a CSV file with pandas?",
    "What is the difference between a list and a tuple?",
    "Why do I get 'IndexError: list index out of range'?",
    "How do I read a JSON file in Python?",
    "What is the Pythonic way to merge two dictionaries?",
    "What does the GIL (global interpreter lock) do in Python?",
    "How do I sort a list of dictionaries by a key's value?",
    "How do I center a div in CSS?",          # out-of-scope (not Python)
    "Why is my code slow?",                    # vague / under-specified
]

OUT = Path(__file__).resolve().parent.parent / "test_results.md"


def main():
    setup_logging()
    rag.load_pipeline()

    header = [
        "# Test Results",
        "",
        "Diverse Python queries run through the RAG pipeline against the real "
        "Stack Overflow index. Includes two deliberate edge cases (an out-of-scope "
        "question and a vague one) to probe grounding behaviour.",
        "",
        f"- **LLM:** `{config.GROQ_MODEL}` (Groq)",
        f"- **Embeddings:** `{config.EMBED_MODEL}`",
        f"- **Index:** {rag._vectorstore.index.ntotal} vectors (one per Stack Overflow URL)",
        f"- **top_k:** {config.TOP_K}",
        "- **Reproduce:** `python scripts/run_eval.py`",
        "",
        "---",
        "",
    ]

    blocks = []
    for i, q in enumerate(QUERIES, 1):
        t0 = time.perf_counter()
        res = rag.answer(q)
        dt = time.perf_counter() - t0
        block = [f"## {i}. {q}", "", "**Answer:**", "", res["answer"], ""]
        if res["sources"]:
            block.append("**Sources:**")
            for s in res["sources"]:
                block.append(f"- [{s.get('title') or s['url']}]({s['url']})")
            block.append("")
        block.append(f"_Latency: {dt:.2f}s_")
        blocks.append("\n".join(block))
        print(f"[{i}/{len(QUERIES)}] {dt:5.2f}s  {q[:45]}")

    footer = ["", "---", "", "## Observations & Quality", "", "_PENDING_REVIEW_", ""]
    OUT.write_text("\n".join(header) + "\n\n".join(blocks) + "\n" + "\n".join(footer))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
