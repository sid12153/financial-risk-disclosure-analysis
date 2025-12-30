from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from api.rag.faiss_store import list_sources, search
import csv
from datetime import datetime

import os
import time
from api.rag.hf_client import HFInferenceClient
from api.rag.agents import run_multi_agent

PLANNER_MODEL = os.getenv("HF_PLANNER_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
VERIFIER_MODEL = os.getenv("HF_VERIFIER_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
SUMMARY_MODEL = os.getenv("HF_SUMMARY_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
MIN_RETRIEVAL_SCORE = 0.53

LOG_PATH = Path("monitoring/query_log.csv")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
if not LOG_PATH.exists():
    LOG_PATH.write_text(
        "ts,question,doc_id,top_k,top_score,refused,total_ms,planner_ms,retrieval_ms,verifier_ms,summary_ms\n",
        encoding="utf-8"
    )

RAW_DIR = Path("data/raw")
app = FastAPI(title="Finance RAG (Strict, Evidence-Based)")


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
    t0 = time.perf_counter()

    out = run_multi_agent(
        question=req.question,
        doc_id=req.doc_id,
        top_k=req.top_k,
        min_score=MIN_RETRIEVAL_SCORE,
        planner_model=PLANNER_MODEL,
        verifier_model=VERIFIER_MODEL,
        summary_model=SUMMARY_MODEL,
    )
    hits = out.get("hits", [])
    lat = out.get("latency", {})
    plan = out.get("plan", None)

    print(
        f"[ASK] refused={out.get('refused')} top_score={out.get('top_score', 0.0):.3f} "
        f"hits={len(hits)} doc_id={getattr(plan, 'doc_id', None) or (hits[0].doc_id if hits else req.doc_id)}"
    )

    if plan:
        print(f"[PLAN] intent={plan.intent} top_k={plan.top_k} rewritten='{plan.rewritten_query[:120]}'")

    print(
        f"[LAT] planner_ms={lat.get('planner_ms', 0):.1f} "
        f"retrieval_ms={lat.get('retrieval_ms', 0):.1f} "
        f"verifier_ms={lat.get('verifier_ms', 0):.1f} "
        f"summary_ms={lat.get('summary_ms', 0):.1f}"
    )

    if hits:
        preview = hits[0].text.replace("\n", " ")[:140]
        print(f"[TOP] {hits[0].chunk_id} score={float(hits[0].score):.3f} text='{preview}...'")


    t1 = time.perf_counter()
    total_ms = (t1 - t0) * 1000.0

    hits = out.get("hits", [])
    top_score = float(out.get("top_score", 0.0))
    plan = out.get("plan", None)

    used_doc_id = req.doc_id
    if not used_doc_id and plan and getattr(plan, "doc_id", None):
        used_doc_id = plan.doc_id
    if not used_doc_id and hits:
        used_doc_id = hits[0].doc_id

    lat = out.get("latency", {})
    planner_ms = float(lat.get("planner_ms", 0.0))
    retrieval_ms = float(lat.get("retrieval_ms", 0.0))
    verifier_ms = float(lat.get("verifier_ms", 0.0))
    summary_ms = float(lat.get("summary_ms", 0.0))

    # CSV-safe logging (prevents comma issues)
    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            datetime.utcnow().isoformat(),
            req.question,
            used_doc_id or "",
            int(req.top_k),
            f"{top_score:.3f}",
            str(bool(out.get("refused", True))).upper(),
            f"{total_ms:.1f}",
            f"{planner_ms:.1f}",
            f"{retrieval_ms:.1f}",
            f"{verifier_ms:.1f}",
            f"{summary_ms:.1f}",
        ])

    if out.get("refused"):
        return AskResponse(
            answer="I can’t answer that reliably from the indexed filings.",
            refused=True,
            refusal_reason=out.get("refusal_reason", "Refused."),
            citations=[],
            evidence=[],
        )

    citations = [Citation(chunk_id=h.chunk_id, doc_id=h.doc_id, score=float(h.score)) for h in hits]
    evidence = [{"chunk_id": h.chunk_id, "doc_id": h.doc_id, "score": float(h.score), "text": h.text} for h in hits]

    return AskResponse(
        answer=out.get("answer", ""),
        refused=False,
        refusal_reason=None,
        citations=citations,
        evidence=evidence,
    )


