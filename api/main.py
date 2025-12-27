from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from api.rag.faiss_store import list_sources, search


DOC_CACHE = {}

RAW_DIR = Path("data/raw")
app = FastAPI(title="Finance RAG (Strict, Evidence-Based)")


class AskRequest(BaseModel):
    question: str
    doc_id: Optional[str] = None
    top_k: int = 5
    max_pages: Optional[int] = None 


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

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    def clean_excerpt(s: str) -> str:
        # Collapse whitespace and remove weird PDF line breaks/non-breaking spaces
        return " ".join(s.replace("\u00a0", " ").split())

    # doc_id is optional. If provided, results filter to that filing only.
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

