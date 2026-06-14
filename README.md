# Python Programming Q&A Assistant

A retrieval-augmented (RAG) assistant that answers Python questions, grounded in real
Stack Overflow Q&A pairs and returned **with source citations**. The RAG pipeline (local
`bge-small` embeddings + FAISS + Groq-hosted Llama 3.3 70B) is exposed two ways: a
**FastAPI** REST service and a self-contained **Streamlit** chat UI.

**Live URL:** https://python-qna-assistant.streamlit.app

## Architecture

```
              OFFLINE (build the index once)
  SO CSVs -> clean HTML -> filter by Score -> top answer per question
          -> embed (bge-small) -> FAISS artifact (index.faiss + index.pkl)

              ONLINE — two entry points to the same pipeline (app/rag.py)
  Streamlit UI (streamlit_app.py)        FastAPI service (app/main.py)
    imports the pipeline in-process        POST /ask     -> {answer, sources}
    chat + "rebuild index" button          GET  /health
                                           POST /reindex -> rebuild + hot-reload

  both: embed query -> FAISS top-k -> Groq Llama-3.3-70b -> grounded answer + citations
```

The heavy embedding work happens once, offline. The Streamlit app loads the model + index
**in-process** (no HTTP); the FastAPI service exposes the same pipeline as a REST API.

## Tech stack

| Layer | Choice |
|-------|--------|
| LLM (generation) | Groq `llama-3.3-70b-versatile` (free tier) |
| Embeddings | `BAAI/bge-small-en-v1.5` (local, sentence-transformers) |
| Vector store | FAISS (flat, via LangChain) — one vector per Q&A URL |
| REST API | FastAPI + Uvicorn |
| UI | Streamlit (loads the pipeline in-process) |

## Project structure

```
app/
  main.py            FastAPI app: /ask, /health, /reindex
  rag.py             retrieve -> build prompt -> generate
  indexer.py         build the FAISS index (shared by CLI, API, and UI)
  embeddings.py      embedding-model factory (shared by build + query)
  config.py          settings from environment
  logging_config.py  file-based logging setup
scripts/
  build_index.py     CLI: CSVs -> FAISS artifact
streamlit_app.py     self-contained Streamlit chat UI
tests/
  test_api.py        pytest + TestClient (RAG + builder mocked)
data/
  sample/            tiny CSVs for a smoke-test build
  dataset/           full Kaggle CSVs — you download these (gitignored)
  index/             built FAISS artifact — generated (gitignored)
Dockerfile
pyproject.toml
requirements.txt
.env.example
```

## Setup

> Requires [uv](https://docs.astral.sh/uv/). Install it with `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`.

```bash
# 1. Create a virtualenv and install deps (uv)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# edit .env and set GROQ_API_KEY (free key: https://console.groq.com)
```

### Get the dataset

Download the [Stack Overflow Python Questions](https://www.kaggle.com/datasets/stackoverflow/pythonquestions)
dataset and place `Questions.csv`, `Answers.csv`, `Tags.csv` in `data/dataset/`:

```bash
kaggle datasets download -d stackoverflow/pythonquestions -p data/dataset --unzip
```

### Build the index

```bash
# Full dataset (filters to high-score Q&A; see .env for thresholds)
python scripts/build_index.py --data-dir data/dataset --index-dir data/index

# Or smoke-test on the bundled sample (no download needed)
python scripts/build_index.py --data-dir data/sample --index-dir data/index \
  --min-question-score 0 --min-answer-score 0
```

You can also rebuild from the UI ("Rebuild from dataset") or via `POST /reindex`.

## Configuration

All settings come from environment variables (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | _(required)_ | Groq API key for generation |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq chat model |
| `GROQ_MAX_TOKENS` | `1024` | Max tokens generated per answer |
| `EMBED_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model (local) |
| `EMBED_BATCH_SIZE` | `32` | Batch size when embedding at build time |
| `EMBED_CACHE_DIR` | _(HF default)_ | Where to cache the embedding model |
| `INDEX_DIR` | `data/index` | FAISS artifact location |
| `DATA_DIR` | `data/dataset` | Source CSVs for (re)building the index |
| `VECTOR_SIZE` | _(unset)_ | If set, the build verifies the index dimension |
| `TOP_K` | `4` | Passages retrieved per question |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MIN_QUESTION_SCORE` | `5` | Build: keep questions scoring ≥ this |
| `MIN_ANSWER_SCORE` | `1` | Build: keep answers scoring ≥ this |
| `MAX_DOCS` | `50000` | Build: cap on indexed Q&A pairs |

## Run

### Streamlit UI (standalone)

```bash
streamlit run streamlit_app.py
```

Loads the model + index in-process, so it runs on its own — no separate backend. Opens a
chat UI at `http://localhost:8501`. Needs `GROQ_API_KEY` in `.env` to answer; the sidebar
"Rebuild" control needs the dataset in `data/dataset/`.

### FastAPI service (REST API)

```bash
uvicorn app.main:app --reload
```

Exposes the same pipeline as REST — `/ask`, `/health`, `/reindex` — with interactive docs
at `http://localhost:8000/docs`.

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I read a CSV file with pandas?"}'

# rebuild the index from the dataset (background task) + check status
curl -X POST http://localhost:8000/reindex -H "Content-Type: application/json" -d '{"max_docs": 20000}'
curl http://localhost:8000/reindex/status
```

## Testing

```bash
pytest
```

Tests stub the RAG layer and the index builder, so they run without a model, index, or key.

## Logging

All application logs go to `app.log` in the project root (level via `LOG_LEVEL`). Each
`/ask` logs a latency + token-usage breakdown.

## Deployment

The UI and the API are independent and deploy separately (both free-tier):

- **Streamlit UI** → **Streamlit Community Cloud**. It's self-contained, so it hosts the
  whole pipeline. Set `GROQ_API_KEY` in the app's Secrets, and make the FAISS index
  available (commit `data/index/` via Git LFS, or build it at startup). Mind the ~1GB RAM
  limit — keep the index modest.
- **FastAPI API** → **Hugging Face Spaces (Docker)**, as the REST deliverable. Reads
  `$PORT` and `$INDEX_DIR`; ship the prebuilt index with the image.

**Live app:** https://python-qna-assistant.streamlit.app

## Limitations

- The dataset skews ~2008–2016, so some answers reference Python 2 or older library APIs.
  Build-time score filtering helps, but answers may occasionally be dated.
- Answers are only as good as the retrieved Stack Overflow content; the model is instructed
  to say when the context is insufficient rather than guess.
- Rebuilding loads the dataset + embeds in-process (memory-heavy). On Streamlit Community
  Cloud the raw CSVs aren't bundled, so use a prebuilt index there and rebuild locally; for
  the API, `/reindex` with multiple workers only reloads the worker that handled it.
