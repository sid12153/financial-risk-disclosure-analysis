# api/rag/embeddings.py
from __future__ import annotations

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None


def get_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model


def embed_texts(texts: List[str], model_name: str = DEFAULT_MODEL_NAME, batch_size: int = 32) -> np.ndarray:
    model = get_model(model_name)
    emb = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,  # cosine similarity via inner product
    )
    return np.asarray(emb, dtype=np.float32)
