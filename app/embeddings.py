"""Embedding model factory.

Used by both the offline index build and the online query path, so the exact
same embedding configuration is applied on both sides.
"""
from langchain_huggingface import HuggingFaceEmbeddings

from app import config


def make_embeddings(show_progress: bool = False) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=config.EMBED_MODEL,
        cache_folder=config.EMBED_CACHE_DIR,
        show_progress=show_progress,
        encode_kwargs={
            "normalize_embeddings": True,  # cosine-ready
            "batch_size": config.EMBED_BATCH_SIZE,
        },
    )
