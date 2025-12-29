from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from api.rag.faiss_store import list_sources, search

import csv
from datetime import datetime

DOC_CACHE = {}

RAW_DIR = Path("data/raw")
app = FastAPI(title="Finance RAG (Strict, Evidence-Based)")

MIN_RETRIEVAL_SCORE = 0.60
LOG_PATH = Path("monitoring/query_log.csv")

class AskRequest(BaseModel):
    question: str
    doc_id: Optional[str] = None
    top_k: int = 5
    max_pages: Optional[int] = None  # useful for quick dev runs


class Citation(BaseModel):
    chunk_id: str
    doc_id: str
    score: float


class AskResponse(BaseModel):
    answer: str
    refused: bool
    refusal_reason: Optional[str] = None
    citations: List[Citation]
    evidence: List[Dict[str, Any]]  # includes chunk text for transparency

def clean_excerpt(s: str) -> str:
    return " ".join(s.replace("\u00a0", " ").split())

def sentence_safe_snippet(text: str, max_len: int = 320) -> str:
    t = clean_excerpt(text)

    # If chunk begins mid-word, skip forward to first space
    if t and t[0].islower():
        first_space = t.find(" ")
        if 0 < first_space < 50:
            t = t[first_space + 1 :]

    # Try to start at the first likely sentence start.
    # Heuristic: find first ". " then start after it, if the beginning looks broken.
    if len(t) > 0 and t[0].islower():
        dot = t.find(". ")
        if 0 <= dot < 200:
            t = t[dot + 2 :]

    # Trim to max length nicely
    if len(t) > max_len:
        t = t[:max_len].rsplit(" ", 1)[0] + "..."
    return t

def log_query(question, doc_id, top_score, refused, num_hits):
    LOG_PATH.parent.mkdir(exist_ok=True)

    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().isoformat(),
            question,
            doc_id,
            f"{top_score:.3f}",
            refused,
            num_hits,
        ])

def dedupe_hits(hits, max_per_doc=3):
    seen = {}
    deduped = []

    for h in hits:
        if h.doc_id not in seen:
            seen[h.doc_id] = 0
        if seen[h.doc_id] < max_per_doc:
            deduped.append(h)
            seen[h.doc_id] += 1

    return deduped

def keyword_coverage_gate(question: str, evidence_texts: List[str], min_hits: int = 2) -> bool:
    """
    Returns True if evidence contains enough question keywords.
    This is a simple guardrail to avoid answering out-of-scope queries
    that still get high embedding similarity.
    """
    q = question.lower()

    # Ignore very short tokens and generic words
    stop = {
        "what", "is", "the", "a", "an", "of", "to", "for", "in", "on", "and", "or",
        "are", "was", "were", "be", "been", "with", "from", "next", "year", "company"
    }

    tokens = []
    cur = []
    for ch in q:
        if ch.isalnum():
            cur.append(ch)
        else:
            if cur:
                tok = "".join(cur)
                if len(tok) >= 4 and tok not in stop:
                    tokens.append(tok)
                cur = []
    if cur:
        tok = "".join(cur)
        if len(tok) >= 4 and tok not in stop:
            tokens.append(tok)

    tokens = list(dict.fromkeys(tokens))  # dedupe, keep order
    if not tokens:
        return True  # nothing meaningful to gate on

    hay = " ".join([t.lower() for t in evidence_texts])

    hit_count = 0
    for t in tokens:
        if t in hay:
            hit_count += 1

    return hit_count >= min_hits

@app.get("/")
def root():
    return {"message": "Finance RAG API is running. See /docs"}

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/sources")
def sources() -> Dict[str, Any]:
    return {
        "available_docs": list_sources()
    }

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    def clean_excerpt(s: str) -> str:
        # Collapse whitespace and remove weird PDF line breaks/non-breaking spaces
        return " ".join(s.replace("\u00a0", " ").split())

    # doc_id is optional. If provided, we filter results to that filing only.
    try:
        hits = search(query=req.question, top_k=req.top_k, doc_id=req.doc_id)
    except FileNotFoundError as e:
        return AskResponse(
            answer="",
            refused=True,
            refusal_reason=str(e),
            citations=[],
            evidence=[],
        )

    if not hits:
        return AskResponse(
            answer="I can’t answer that from the indexed filings I currently have.",
            refused=True,
            refusal_reason="No relevant evidence retrieved. Try rephrasing or choose a different filing.",
            citations=[],
            evidence=[],
        )
    
    top_score = float(hits[0].score)

    if top_score < MIN_RETRIEVAL_SCORE:
        log_query(req.question, req.doc_id, top_score, True, len(hits))
        return AskResponse(
            answer="I can’t answer that reliably from the indexed filings.",
            refused=True,
            refusal_reason=f"Top retrieval score ({top_score:.3f}) is below confidence threshold ({MIN_RETRIEVAL_SCORE:.2f}).",
            citations=[],
            evidence=[],
        )

    hits = dedupe_hits(hits, max_per_doc=3)

    # Guardrail: keyword coverage gate (avoid semantic false positives)
    evidence_texts = [h.text for h in hits[: min(len(hits), 5)]]
    if not keyword_coverage_gate(req.question, evidence_texts, min_hits=2):
        log_query(req.question, req.doc_id, top_score, True, len(hits))
        return AskResponse(
            answer="I can’t answer that reliably from the indexed filings.",
            refused=True,
            refusal_reason="Retrieved text does not contain enough direct coverage of the question terms (scope guardrail).",
            citations=[],
            evidence=[],
        )

    # Evidence-first response (no generation beyond citations)
    answer_lines = [
        "Evidence found in the indexed filings for your question.",
        "",
        "Top retrieved excerpts:",
    ]

    for h in hits[:3]:
        snippet = sentence_safe_snippet(h.text, max_len=320)
        answer_lines.append(f"- {snippet} ({h.chunk_id})")

    citations = [Citation(chunk_id=h.chunk_id, doc_id=h.doc_id, score=float(h.score)) for h in hits]
    
    if not citations:
        return AskResponse(
            answer="",
            refused=True,
            refusal_reason="No citations could be generated for this query.",
            citations=[],
            evidence=[],
        )

    evidence: List[Dict[str, Any]] = []
    for h in hits:
        evidence.append(
            {
                "chunk_id": h.chunk_id,
                "doc_id": h.doc_id,
                "score": float(h.score),
                "text": h.text,  # keep raw text for transparency
                "text_clean": clean_excerpt(h.text),  # nicer display option for UI
            }
        )

    return AskResponse(
        answer="\n".join(answer_lines),
        refused=False,
        refusal_reason=None,
        citations=citations,
        evidence=evidence,
    )
