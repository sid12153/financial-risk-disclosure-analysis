from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from api.rag.hf_client import HFInferenceClient
from api.rag.faiss_store import search

import os
from opentelemetry import trace
from phoenix.otel import register

_PHX_ON = os.getenv("PHOENIX_ENABLED", "false").lower() == "true"
if _PHX_ON:
    # For local phoenix in docker, you can set this in .env:
    # PHOENIX_COLLECTOR_ENDPOINT=http://phoenix:6006
    register()  # reads env defaults
tracer = trace.get_tracer(__name__)

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
  "rewritten_query": "",
  "top_k": 5,
  "doc_id": "{doc_id or ""}"
}}
User question: {question}
""".strip()

    res = client.generate(model=model, prompt=prompt, max_new_tokens=220, temperature=0.0)
    obj = _safe_json_extract(res.text)

    intent = obj.get("intent", "risk_analysis")
    rewritten = obj.get("rewritten_query", question)
    if intent == "out_of_scope":
        rewritten = ""
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

def _set(span, k: str, v):
    try:
        if v is None:
            return
        span.set_attribute(k, v)
    except Exception:
        pass

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

    # Root trace: 1 trace per /ask
    with tracer.start_as_current_span("ask") as root:
        _set(root, "question", question[:400])
        _set(root, "doc_id.requested", doc_id or "")
        _set(root, "top_k.requested", int(top_k))
        _set(root, "min_score", float(min_score))
        _set(root, "model.planner", planner_model)
        _set(root, "model.verifier", verifier_model)
        _set(root, "model.summarizer", summary_model)

        # ---- Planner span ----
        with tracer.start_as_current_span("planner") as sp:
            plan, planner_ms = planner_agent(client, planner_model, question, doc_id, top_k_default=top_k)
            _set(sp, "planner.intent", plan.intent)
            _set(sp, "planner.top_k", int(plan.top_k))
            _set(sp, "planner.doc_id", plan.doc_id or "")
            _set(sp, "planner.rewritten_query", plan.rewritten_query[:400])
            _set(sp, "planner.latency_ms", float(planner_ms))

        if plan.intent == "out_of_scope":
            _set(root, "refused", True)
            _set(root, "refusal_stage", "planner")
            _set(root, "refusal_reason", "Planner classified question as out-of-scope for filings.")
            _set(root, "rewritten_query", "")
            return {
                "refused": True,
                "refusal_reason": "Planner classified question as out-of-scope for filings.",
                "plan": plan,
                "latency": {"planner_ms": planner_ms, "retrieval_ms": 0.0, "verifier_ms": 0.0, "summary_ms": 0.0},
                "hits": [],
                "answer": "",
                "top_score": 0.0,
            }

        # ---- Retrieval span ----
        with tracer.start_as_current_span("retrieval") as sp:
            t0 = time.perf_counter()
            hits = search(query=plan.rewritten_query, top_k=plan.top_k, doc_id=plan.doc_id)
            t1 = time.perf_counter()
            retrieval_ms = (t1 - t0) * 1000.0

            _set(sp, "retrieval.doc_id", plan.doc_id or "")
            _set(sp, "retrieval.top_k", int(plan.top_k))
            _set(sp, "retrieval.latency_ms", float(retrieval_ms))
            _set(sp, "retrieval.hits", int(len(hits)))

            if hits:
                _set(sp, "retrieval.top_score", float(hits[0].score))
                # log only ids (NOT full text)
                _set(sp, "retrieval.top_chunk_id", hits[0].chunk_id)
                _set(sp, "retrieval.chunk_ids", ",".join([h.chunk_id for h in hits[:10]]))

        if not hits:
            _set(root, "refused", True)
            _set(root, "refusal_stage", "retrieval")
            _set(root, "refusal_reason", "No relevant evidence retrieved.")
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
        _set(root, "top_score", top_score)

        if top_score < min_score:
            _set(root, "refused", True)
            _set(root, "refusal_stage", "threshold")
            _set(root, "refusal_reason", f"Top retrieval score below threshold ({top_score:.3f} < {min_score:.2f}).")
            return {
                "refused": True,
                "refusal_reason": f"Top retrieval score ({top_score:.3f}) is below confidence threshold ({min_score:.2f}).",
                "plan": plan,
                "latency": {"planner_ms": planner_ms, "retrieval_ms": retrieval_ms, "verifier_ms": 0.0, "summary_ms": 0.0},
                "hits": hits,
                "answer": "",
                "top_score": top_score,
            }

        # ---- Verifier span ----
        with tracer.start_as_current_span("verifier") as sp:
            verify, verifier_ms = verifier_agent(
                client,
                verifier_model,
                question,
                evidence_chunks=[{"chunk_id": h.chunk_id, "score": float(h.score), "text": h.text} for h in hits],
                min_score=min_score,
            )
            _set(sp, "verifier.ok", bool(verify.ok))
            _set(sp, "verifier.must_refuse", bool(verify.must_refuse))
            _set(sp, "verifier.reason", verify.reason[:500])
            _set(sp, "verifier.latency_ms", float(verifier_ms))

        if verify.must_refuse:
            _set(root, "refused", True)
            _set(root, "refusal_stage", "verifier")
            _set(root, "refusal_reason", verify.reason[:500])
            return {
                "refused": True,
                "refusal_reason": verify.reason,
                "plan": plan,
                "latency": {"planner_ms": planner_ms, "retrieval_ms": retrieval_ms, "verifier_ms": verifier_ms, "summary_ms": 0.0},
                "hits": hits,
                "answer": "",
                "top_score": top_score,
            }

        # ---- Summarizer span ----
        with tracer.start_as_current_span("summarizer") as sp:
            answer, summary_ms = summarizer_agent(
                client,
                summary_model,
                question,
                evidence_chunks=[{"chunk_id": h.chunk_id, "score": float(h.score), "text": h.text} for h in hits],
            )
            _set(sp, "summarizer.latency_ms", float(summary_ms))
            _set(sp, "summarizer.answer_chars", int(len(answer or "")))

        if (answer or "").strip() == "I can’t answer from the indexed filings.":
            _set(root, "refused", True)
            _set(root, "refusal_stage", "summarizer")
            _set(root, "refusal_reason", "Summarizer refused due to insufficient grounded evidence.")
            return {
                "refused": True,
                "refusal_reason": "Summarizer refused due to insufficient grounded evidence.",
                "plan": plan,
                "latency": {"planner_ms": planner_ms, "retrieval_ms": retrieval_ms, "verifier_ms": verifier_ms, "summary_ms": summary_ms},
                "hits": hits,
                "answer": "",
                "top_score": top_score,
            }

        _set(root, "refused", False)
        _set(root, "latency.planner_ms", float(planner_ms))
        _set(root, "latency.retrieval_ms", float(retrieval_ms))
        _set(root, "latency.verifier_ms", float(verifier_ms))
        _set(root, "latency.summary_ms", float(summary_ms))

        return {
            "refused": False,
            "refusal_reason": None,
            "plan": plan,
            "latency": {"planner_ms": planner_ms, "retrieval_ms": retrieval_ms, "verifier_ms": verifier_ms, "summary_ms": summary_ms},
            "hits": hits,
            "answer": answer,
            "top_score": top_score,
        }

