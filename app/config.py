"""Configuration loaded from environment variables (.env)."""
import os

from dotenv import load_dotenv

load_dotenv()

# LLM (Groq)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "1024"))

# Embeddings (local)
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "32"))
EMBED_CACHE_DIR = os.getenv("EMBED_CACHE_DIR") or None  # None -> default HF cache

# Vector index
INDEX_DIR = os.getenv("INDEX_DIR", "data/index")
# Source dataset (CSVs) used to (re)build the index
DATA_DIR = os.getenv("DATA_DIR", "data/dataset")
# Optional expected embedding dimension; if set, the build verifies the index
# matches it (FAISS otherwise infers the dimension automatically).
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE")) if os.getenv("VECTOR_SIZE") else None

# Retrieval
TOP_K = int(os.getenv("TOP_K", "4"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Build-time corpus filters (used by scripts/build_index.py)
MIN_QUESTION_SCORE = int(os.getenv("MIN_QUESTION_SCORE", "5"))
MIN_ANSWER_SCORE = int(os.getenv("MIN_ANSWER_SCORE", "1"))
MAX_DOCS = int(os.getenv("MAX_DOCS", "50000"))
