FROM python:3.11-slim

# uv for fast installs (copy the static binary from the official image)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /code

# Build deps for native wheels (faiss, lxml).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY app ./app
# The prebuilt FAISS index must exist locally before building the image
# (run scripts/build_index.py first). Adjust the path if INDEX_DIR differs.
COPY data/index ./data/index

ENV INDEX_DIR=data/index
# Most platforms inject $PORT (HF Spaces uses 7860); default to 8000 locally.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
