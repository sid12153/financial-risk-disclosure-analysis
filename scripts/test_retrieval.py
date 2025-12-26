# scripts/test_retrieval.py
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

import faiss
import numpy as np

from api.rag.embeddings import embed_texts

# INDEX_PATH = Path("data/processed/embeddings.faiss")
INDEX_PATH = Path("C:/Users/Siddharth/Desktop/Portfolio_Projects/Finance-AI-RAG/data/processed/embeddings.faiss")
# META_PATH = Path("data/processed/embeddings_meta.jsonl")
META_PATH = Path("C:/Users/Siddharth/Desktop/Portfolio_Projects/Finance-AI-RAG/data/processed/embeddings_meta.jsonl")
# CHUNKS_PATH = Path("data/processed/chunks.jsonl")
CHUNKS_PATH = Path("C:/Users/Siddharth/Desktop/Portfolio_Projects/Finance-AI-RAG/data/processed/chunks.jsonl")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    index = faiss.read_index(str(INDEX_PATH))
    meta = read_jsonl(META_PATH)
    chunks = read_jsonl(CHUNKS_PATH)

    q = "What regulatory or compliance risks are highlighted related to capital requirements and resolution planning?"
    q_emb = embed_texts([q])
    D, I = index.search(np.asarray(q_emb, dtype=np.float32), k=5)

    print("Query:", q)
    print("\nTop matches:")
    for rank, idx in enumerate(I[0], start=1):
        m = meta[idx]
        text = chunks[idx]["text"][:300].replace("\n", " ")
        print(f"\n{rank}. {m['chunk_id']} | {m['company']} {m['filing_year']} {m['filing_type']} | score={D[0][rank-1]:.3f}")
        print(text, "...")


if __name__ == "__main__":
    main()
