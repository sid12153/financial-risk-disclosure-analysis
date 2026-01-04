# Monitoring, Metrics, and Observability

This folder contains lightweight monitoring artifacts for the Finance Risk Disclosure Analysis system.

The goal is not “model accuracy” (we don’t have labeled QA pairs yet) — the goal is **measurable reliability**:
- refusal behavior when evidence is weak or out-of-scope
- traceability via citations
- latency by step and end-to-end
- evidence strength distribution over real analyst-style questions

---

## What’s Logged

### 1) Query Log (`query_log.csv`)

Every `/ask` request appends a row with a stable schema:

| column | description |
|---|---|
| `ts` | UTC timestamp |
| `question` | raw user question |
| `doc_id` | filing selected (or inferred) |
| `top_k` | retrieval depth |
| `top_score` | similarity score for the best chunk |
| `refused` | `TRUE` if the system refused |
| `total_ms` | end-to-end latency |
| `planner_ms` | planner latency |
| `retrieval_ms` | FAISS retrieval latency |
| `verifier_ms` | verifier latency |
| `summary_ms` | summarizer latency |

This creates an auditable record of how the system behaved over time.

> Note: logs are intentionally CSV (simple, portable).  
> Future: ship to a structured sink (S3/CloudWatch).

---

## Metrics Report (Offline Summary)

### Script: `scripts/metrics_report.py`

This script reads `monitoring/query_log.csv` and prints:

- **Requests (N)**
- **Refusal rate (%)**
- **Latency percentiles** (P50 / P95 / P99)
- **Top-score distribution histogram** (evidence strength buckets)
- **Breakdown by doc_id** (refusal + avg top score per filing)

This is intentionally “boring metrics” — the kind reviewers trust.

**Run locally**
```bash
python scripts/metrics_report.py
```

## Phoenix Tracing (OpenTelemetry)

Phoenix is used to provide end-to-end observability for every `/ask` request.
Each query is recorded as a trace with structured spans and metadata, allowing
inspection of decisions, evidence quality, and latency.

This makes the system auditable and suitable for compliance-facing workflows.

---

### What is traced

Each request produces **one root trace** with child spans for:

- **Planner**
  - intent classification (in-scope / out-of-scope)
  - rewritten retrieval query
  - chosen `top_k`

- **Retrieval**
  - FAISS search execution
  - top retrieval score
  - retrieved chunk IDs

- **Verifier**
  - accept or refuse decision
  - refusal reason (if applicable)

- **Summarizer**
  - grounded answer generation
  - citation enforcement

- **Latency**
  - per-step latency
  - end-to-end request latency

All spans include structured attributes such as:
`doc_id`, `top_k`, `top_score`, `refused`, and refusal stage.

---

### How Phoenix runs

Phoenix runs as a Docker service defined in `docker-compose.yml`.

**Exposed endpoints**
- Phoenix UI: `http://localhost:6006` (local)
- Phoenix UI: `http://<server-ip>:6006` (deployed)

The FastAPI service exports OpenTelemetry traces directly to Phoenix.

---

### Why this matters

- It **refuses** rather than hallucinating
- Every answer is **traceable to evidence**
- Decision logic is **inspectable per request**
- Latency is measured and monitored

Even without labeled ground-truth data, reliability is demonstrated via:
- refusal rate (scope enforcement)
- traceability count (citation discipline)
- evidence score distributions
- latency percentiles (production feasibility)
