# api/rag/faiss_store.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np

from api.rag.embeddings import embed_texts

INDEX_PATH = Path("data/processed/embeddings.faiss")
META_PATH = Path("data/processed/embeddings_meta.jsonl")
CHUNKS_PATH = Path("data/processed/chunks.jsonl")

@dataclass
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    score: float
    text: str


_index: faiss.Index | None = None
_meta: List[Dict[str, Any]] | None = None
_text_by_idx: List[str] | None = None


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_store() -> Tuple[faiss.Index, List[Dict[str, Any]], List[str]]:
    global _index, _meta, _text_by_idx

    if _index is not None and _meta is not None and _text_by_idx is not None:
        return _index, _meta, _text_by_idx

    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Missing {INDEX_PATH}. Run: python -m scripts.build_faiss_index")
    if not META_PATH.exists():
        raise FileNotFoundError(f"Missing {META_PATH}. Run: python -m scripts.build_faiss_index")
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"Missing {CHUNKS_PATH}. Run: python -m scripts.build_chunks")

    _index = faiss.read_index(str(INDEX_PATH))
    _meta = _read_jsonl(META_PATH)

    # Load only texts in the same order as FAISS ids
    chunks = _read_jsonl(CHUNKS_PATH)
    _text_by_idx = [c["text"] for c in chunks]

    if len(_meta) != len(_text_by_idx):
        raise ValueError(f"Meta rows ({len(_meta)}) != chunks rows ({len(_text_by_idx)}). Rebuild artifacts.")

    return _index, _meta, _text_by_idx


def list_sources() -> List[Dict[str, Any]]:
    _, meta, _ = load_store()
    seen = {}
    for m in meta:
        doc_id = m.get("doc_id")
        if not doc_id:
            continue
        if doc_id not in seen:
            seen[doc_id] = {
                "doc_id": doc_id,
                "filename": m.get("filename"),
                "company": m.get("company"),
                "filing_year": m.get("filing_year"),
                "filing_type": m.get("filing_type"),
            }
    return [seen[k] for k in sorted(seen.keys())]


def search(
    query: str,
    top_k: int = 5,
    doc_id: Optional[str] = None,
) -> List[RetrievedChunk]:
    index, meta, text_by_idx = load_store()

    q_emb = embed_texts([query])  # normalized vectors
    D, I = index.search(np.asarray(q_emb, dtype=np.float32), k=max(top_k * 6, top_k))

    results: List[RetrievedChunk] = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx < 0:
            continue
        m = meta[idx]
        if doc_id is not None and m.get("doc_id") != doc_id:
            continue

        results.append(
            RetrievedChunk(
                chunk_id=m.get("chunk_id") or f"{m.get('doc_id')}::chunk_{idx}",
                doc_id=m.get("doc_id") or "unknown",
                score=float(score),
                text=text_by_idx[idx],
            )
        )
        if len(results) >= top_k:
            break

    return results

