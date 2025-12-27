from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class EvidenceChunk:
    chunk_id: str
    doc_id: str
    text: str
    score: int


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
    if chunk_size <= 0:
        return []

    chunks: List[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)

    return chunks


def tokenize_simple(s: str) -> List[str]:
    # simple, deterministic tokenizer
    out: List[str] = []
    cur = []

    for ch in s.lower():
        if ch.isalnum():
            cur.append(ch)
        else:
            if cur:
                out.append("".join(cur))
                cur = []
    if cur:
        out.append("".join(cur))

    return out


def retrieve_top_k(doc_id: str, doc_text: str, query: str, top_k: int = 5) -> List[EvidenceChunk]:
    query_tokens = set(tokenize_simple(query))
    if not query_tokens:
        return []

    chunks = chunk_text(doc_text)
    scored: List[EvidenceChunk] = []

    for i, ch in enumerate(chunks):
        ch_tokens = set(tokenize_simple(ch))
        score = 0
        for t in query_tokens:
            if t in ch_tokens:
                score += 1

        if score > 0:
            scored.append(
                EvidenceChunk(
                    chunk_id=f"{doc_id}::chunk_{i}",
                    doc_id=doc_id,
                    text=ch,
                    score=score,
                )
            )

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]
