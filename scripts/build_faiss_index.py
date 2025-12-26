# scripts/build_faiss_index.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import faiss
from tqdm import tqdm

from api.rag.embeddings import embed_texts, DEFAULT_MODEL_NAME

# CHUNKS_PATH = Path("data/processed/chunks.jsonl")
CHUNKS_PATH = Path("C:/Users/Siddharth/Desktop/Portfolio_Projects/Finance-AI-RAG/data/processed/chunks.jsonl")
# INDEX_PATH = Path("data/processed/embeddings.faiss")
INDEX_PATH = Path("C:/Users/Siddharth/Desktop/Portfolio_Projects/Finance-AI-RAG/data/processed/embeddings.faiss")
# META_PATH = Path("data/processed/embeddings_meta.jsonl")
META_PATH = Path("C:/Users/Siddharth/Desktop/Portfolio_Projects/Finance-AI-RAG/data/processed/embeddings_meta.jsonl")
BATCH_SIZE = 32


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main():
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"Missing {CHUNKS_PATH}. Run chunking first.")

    rows = read_jsonl(CHUNKS_PATH)
    if not rows:
        raise ValueError("chunks.jsonl is empty")

    texts = [r["text"] for r in rows]

    # Embed in batches
    all_embs: List[np.ndarray] = []
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Embedding"):
        batch = texts[i : i + BATCH_SIZE]
        embs = embed_texts(batch, model_name=DEFAULT_MODEL_NAME, batch_size=BATCH_SIZE)
        all_embs.append(embs)

    X = np.vstack(all_embs).astype(np.float32)
    dim = X.shape[1]

    # Cosine similarity with normalized vectors => use inner product index
    index = faiss.IndexFlatIP(dim)
    index.add(X)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))

    # Write aligned metadata (FAISS id == line number)
    with META_PATH.open("w", encoding="utf-8") as f:
        for r in rows:
            meta = {
                "chunk_id": r.get("chunk_id"),
                "doc_id": r.get("doc_id"),
                "filename": r.get("filename"),
                "company": r.get("company"),
                "filing_year": r.get("filing_year"),
                "filing_type": r.get("filing_type"),
                "n_chars": r.get("n_chars"),
            }
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")

    print(f"Chunks: {len(rows)}")
    print(f"Embedding dim: {dim}")
    print(f"Wrote FAISS index: {INDEX_PATH}")
    print(f"Wrote metadata:   {META_PATH}")
    print("Model:", DEFAULT_MODEL_NAME)


if __name__ == "__main__":
    main()
