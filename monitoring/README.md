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

> Note: logs are intentionally CSV (simple, portable, recruiter-friendly).  
> Future: ship to a structured sink (S3/CloudWatch/ELK).

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
