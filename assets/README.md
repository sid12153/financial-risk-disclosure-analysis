
# Assets and Evidence

This directory contains screenshots and visual artifacts used to **demonstrate system behavior, reliability, and deployment**, rather than UI polish.

Each asset corresponds to a concrete capability of the Financial Disclosure Intelligence system.

---

assets/

├── screenshots/

│   ├── home_UI.jpg

│   ├── answer_1.jpg

│   ├── answer_2.jpg

│   ├── answer_3.jpg

│   ├── refusal.jpg

│   ├── phoenix_kpi.jpg

│   ├── phoenix_trace.jpg

│   ├── metrics_report.jpg

│   ├── docker_compose.jpg

│   ├── docker_logs.jpg

│   └── aws_inbound_rules.jpg

├── assets.md

└── screenshots/

|   └── ss.md


---

## UI and Answering Behavior

### `home_UI.jpg`
**What it shows**
- Streamlit frontend with selected filing metadata
- Clear statement of evidence-first and refusal policy

**Why it matters**
- Confirms the system is designed for analyst workflows
- Shows document-scoped querying (company, year, filing type)

---

### `answer_1.jpg`, `answer_2.jpg`, `answer_3.jpg`
**What they show**
- Successful answers grounded in retrieved SEC filing excerpts
- Chunk-level citations attached to each bullet
- Evidence excerpts visible to the user

**Why it matters**
- Demonstrates traceability from answer → source text
- Shows that answers are not generated without evidence
- Confirms citation discipline is enforced end-to-end

---

### `refusal.jpg`
**What it shows**
- System refusing an out-of-scope or unsupported question

**Why it matters**
- Proves the system does not hallucinate
- Demonstrates guardrail enforcement at runtime
- Validates “refusal over guessing” policy

---

## Observability and Tracing (Phoenix)

### `phoenix_kpi.jpg`
**What it shows**
- Phoenix dashboard with:
  - total traces
  - latency percentiles (P50, P99)
  - request volume

**Why it matters**
- Demonstrates production-style observability
- Shows system latency characteristics
- Confirms tracing is active in deployment

---

### `phoenix_trace.jpg`
**What it shows**
- A full request trace with child spans:
  - planner
  - retrieval
  - verifier
  - summarizer
- Span metadata (doc_id, top_score, refusal flags)

**Why it matters**
- Shows decision transparency per request
- Enables post-hoc debugging and auditability
- Mirrors enterprise LLM monitoring practices

---

## Metrics and Evaluation

### `metrics_report.jpg`
**What it shows**
- Output from `scripts/metrics_report.py`
- Aggregated statistics:
  - refusal rate
  - latency percentiles
  - top-score distribution
  - per-document behavior

**Why it matters**
- Demonstrates evaluation without labeled datasets
- Shows reliability and performance metrics
- Supports claims about system behavior at scale

---

## Deployment Evidence

### `docker_compose.jpg`
**What it shows**
- Multi-service Docker Compose setup
- API, Streamlit UI, and Phoenix running together

**Why it matters**
- Confirms containerized deployment
- Demonstrates reproducible environment setup

---

### `docker_logs.jpg`
**What it shows**
- Runtime logs from API and services
- Successful startup and request handling

**Why it matters**
- Confirms system health
- Shows Phoenix tracing initialization
- Useful for debugging and validation

---

### `aws_inbound_rules.jpg`
**What it shows**
- AWS EC2 security group inbound rules:
  - SSH (22)
  - FastAPI (8000)
  - Streamlit (8501)
  - Phoenix (6006 / 4317)

**Why it matters**
- Demonstrates cloud deployment configuration
- Confirms service exposure and access control
- Supports AWS deployment claims

---

## Summary

These assets collectively demonstrate:

- Evidence-first answering
- Strict refusal behavior
- Traceability and citations
- Observability via Phoenix
- Containerized and cloud deployment

All screenshots are included as **proof of behavior**, not marketing visuals.
