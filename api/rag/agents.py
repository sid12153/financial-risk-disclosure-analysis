from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from api.rag.hf_client import HFInferenceClient
from api.rag.faiss_store import search


@dataclass
class Plan:
    intent: str  # "risk_analysis" | "out_of_scope"
    rewritten_query: str
    top_k: int
    doc_id: Optional[str]


@dataclass
class VerifyResult:
    ok: bool
    reason: str
    must_refuse: bool


def _safe_json_extract(text: str) -> Dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return {}


def planner_agent(
    client: HFInferenceClient,
    model: str,
    question: str,
    doc_id: Optional[str],
    top_k_default: int,
) -> Tuple[Plan, float]:
    prompt = f"""
You are a planner for a strict SEC filing RAG system.

Rules:
- If question asks for trivia, personal preferences, stock price predictions/targets, future forecasts, or anything not in filings => intent="out_of_scope".
- Otherwise intent="risk_analysis".
- Rewrite the query for retrieval (short, keyword-rich).
- Set top_k between 3 and 8.

Return ONLY JSON:
{{
  "intent": "risk_analysis|out_of_scope",
  "rewritten_query": "...",
  "top_k": 5,
  "doc_id": "{doc_id or ""}"
}}
User question: {question}
""".strip()

    res = client.generate(model=model, prompt=prompt, max_new_tokens=220, temperature=0.0)
    obj = _safe_json_extract(res.text)

    intent = obj.get("intent", "risk_analysis")
    rewritten = obj.get("rewritten_query", question)
    tk = int(obj.get("top_k", top_k_default))
    tk = max(3, min(8, tk))
    planned_doc = obj.get("doc_id") or doc_id

    return Plan(intent=intent, rewritten_query=rewritten, top_k=tk, doc_id=planned_doc), res.latency_ms


def verifier_agent(
    client: HFInferenceClient,
    model: str,
    question: str,
    evidence_chunks: List[Dict],
    min_score: float,
) -> Tuple[VerifyResult, float]:
    snippets = []
    for e in evidence_chunks[:5]:
        snippets.append(f"[{e['chunk_id']}] score={e['score']:.3f}\n{e['text'][:700]}")
    evidence_blob = "\n\n".join(snippets)

    prompt = f"""
You are a verifier for a strict SEC filing RAG system.

Decide if the evidence is sufficient to answer the question from filings ONLY.

Refuse if:
- question is out-of-scope (trivia, stock target, future price, personal preferences)
- top score < {min_score}
- evidence does not mention the topic directly

Return ONLY JSON:
{{
  "ok": true/false,
  "must_refuse": true/false,
  "reason": "..."
}}

Question: {question}

Evidence:
{evidence_blob}
""".strip()

    res = client.generate(model=model, prompt=prompt, max_new_tokens=220, temperature=0.0)
    obj = _safe_json_extract(res.text)

    ok = bool(obj.get("ok", False))
    must_refuse = bool(obj.get("must_refuse", not ok))
    reason = obj.get("reason", "Verifier refused due to insufficient evidence or out-of-scope question.")

    return VerifyResult(ok=ok, must_refuse=must_refuse, reason=reason), res.latency_ms


def summarizer_agent(
    client: HFInferenceClient,
    model: str,
    question: str,
    evidence_chunks: List[Dict],
) -> Tuple[str, float]:
    snippets = []
    for e in evidence_chunks[:5]:
        snippets.append(f"[{e['chunk_id']}]\n{e['text'][:1200]}")
    evidence_blob = "\n\n".join(snippets)

    prompt = f"""
You are a financial filings assistant.

Answer the question using ONLY the evidence below.
Write 3–6 bullet points in clear, normal English.
Every bullet MUST end with a citation like (chunk_id).
Do NOT invent details.
If evidence is insufficient, say exactly: "I can’t answer from the indexed filings."

Question: {question}

Evidence:
{evidence_blob}
""".strip()

    res = client.generate(model=model, prompt=prompt, max_new_tokens=360, temperature=0.2)
    return res.text.strip(), res.latency_ms


def run_multi_agent(
    question: str,
    doc_id: Optional[str],
    top_k: int,
    min_score: float,
    planner_model: str,
    verifier_model: str,
    summary_model: str,
) -> Dict:
    client = HFInferenceClient()

    plan, planner_ms = planner_agent(client, planner_model, question, doc_id, top_k_default=top_k)
    if plan.intent == "out_of_scope":
        return {
            "refused": True,
            "refusal_reason": "Planner classified question as out-of-scope for filings.",
            "plan": plan,
            "latency": {"planner_ms": planner_ms, "retrieval_ms": 0.0, "verifier_ms": 0.0, "summary_ms": 0.0},
            "hits": [],
            "answer": "",
            "top_score": 0.0,
        }

    # Retrieval (FAISS) — unchanged
    t0 = time.perf_counter()
    hits = search(query=plan.rewritten_query, top_k=plan.top_k, doc_id=plan.doc_id)
    t1 = time.perf_counter()
    retrieval_ms = (t1 - t0) * 1000.0

    if not hits:
        return {
            "refused": True,
            "refusal_reason": "No relevant evidence retrieved.",
            "plan": plan,
            "latency": {"planner_ms": planner_ms, "retrieval_ms": retrieval_ms, "verifier_ms": 0.0, "summary_ms": 0.0},
            "hits": [],
            "answer": "",
            "top_score": 0.0,
        }

    top_score = float(hits[0].score)
    if top_score < min_score:
        return {
            "refused": True,
            "refusal_reason": f"Top retrieval score ({top_score:.3f}) is below confidence threshold ({min_score:.2f}).",
            "plan": plan,
            "latency": {"planner_ms": planner_ms, "retrieval_ms": retrieval_ms, "verifier_ms": 0.0, "summary_ms": 0.0},
            "hits": hits,
            "answer": "",
            "top_score": top_score,
        }

    verify, verifier_ms = verifier_agent(
        client,
        verifier_model,
        question,
        evidence_chunks=[{"chunk_id": h.chunk_id, "score": float(h.score), "text": h.text} for h in hits],
        min_score=min_score,
    )

    if verify.must_refuse:
        return {
            "refused": True,
            "refusal_reason": verify.reason,
            "plan": plan,
            "latency": {"planner_ms": planner_ms, "retrieval_ms": retrieval_ms, "verifier_ms": verifier_ms, "summary_ms": 0.0},
            "hits": hits,
            "answer": "",
            "top_score": top_score,
        }

    answer, summary_ms = summarizer_agent(
        client,
        summary_model,
        question,
        evidence_chunks=[{"chunk_id": h.chunk_id, "score": float(h.score), "text": h.text} for h in hits],
    )

    # If summarizer refuses, propagate it as refusal (keeps system strict)
    if answer.strip() == "I can’t answer from the indexed filings.":
        return {
            "refused": True,
            "refusal_reason": "Summarizer refused due to insufficient grounded evidence.",
            "plan": plan,
            "latency": {"planner_ms": planner_ms, "retrieval_ms": retrieval_ms, "verifier_ms": verifier_ms, "summary_ms": summary_ms},
            "hits": hits,
            "answer": "",
            "top_score": top_score,
        }

    return {
        "refused": False,
        "refusal_reason": None,
        "plan": plan,
        "latency": {"planner_ms": planner_ms, "retrieval_ms": retrieval_ms, "verifier_ms": verifier_ms, "summary_ms": summary_ms},
        "hits": hits,
        "answer": answer,
        "top_score": top_score,
    }
