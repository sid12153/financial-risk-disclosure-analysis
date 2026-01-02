![Zero Hallucination Policy](https://img.shields.io/badge/Policy-Zero%20Hallucination-brightgreen)
![Multi-Agent](https://img.shields.io/badge/Architecture-Multi--Agent-blue)
![LLM](https://img.shields.io/badge/LLM-Mistral%20%7C%20LLaMA-orange)
![Vector Search](https://img.shields.io/badge/Retrieval-FAISS-purple)
![Dockerized](https://img.shields.io/badge/Deployment-Docker-blue)
![Tracing](https://img.shields.io/badge/Observability-Arize%20Phoenix-red)
![AWS](https://img.shields.io/badge/Cloud-AWS%20EC2-yellow)

**Evidence-first financial intelligence over SEC filings.  
Every answer is cited or refused.**

---

# Financial Disclosure Intelligence  
**A zero-hallucination, multi-agent RAG system for SEC filings**

Analysts, risk teams, and compliance professionals rely on large SEC filings (10-K, 10-Q) to understand regulatory exposure, capital constraints, and material risks. These documents are long, repetitive, and difficult to interrogate programmatically.

This project implements a **production-style evidence retrieval system** that allows users to ask analyst-style questions and receive **strictly grounded answers** — or an explicit refusal when evidence is insufficient.

The system is designed around one principle:

> **If the answer cannot be proven from the filings, it must not be generated.**

---

## What This System Guarantees

- Answers are derived **only from retrieved filing excerpts**
- Every answer includes **chunk-level citations**
- Out-of-scope or speculative questions are **refused by policy**
- Each decision is **observable, traceable, and testable**

This mirrors how real-world financial and compliance systems must behave.

---

## Current Status (Day 14)

The system is now fully **containerized, observable, and policy-enforced**:

- Multi-agent RAG pipeline (Planner → Retriever → Verifier → Summarizer)
- FAISS-based semantic retrieval
- Strict refusal logic enforced by agents and unit tests
- Dockerized API and UI using Docker Compose
- Distributed tracing and latency analysis via **Arize Phoenix**
- Frontend KPIs exposing decision and evidence quality

---

## Multi-Agent Architecture

Each `/ask` request runs as a **single traced workflow** with distinct decision stages.

### 1. Planner Agent (Mistral – Hugging Face Inference API)
- Classifies intent: **in-scope vs out-of-scope**
- Rewrites the query into a retrieval-optimized form
- Dynamically selects top-k evidence size

Questions such as:
- *“What will the stock price be next year?”*  
are refused at this stage.

---

### 2. Retriever (FAISS)
- Embeds the rewritten query
- Retrieves top-k filing chunks using cosine similarity
- Returns similarity scores and chunk identifiers

Retrieval latency is measured independently.

---

### 3. Verifier Agent (Llama – Hugging Face Inference API)
- Evaluates evidence sufficiency
- Refuses if:
  - similarity score is below threshold
  - evidence does not cover the topic
  - planner intent was borderline

This stage prevents semantic false positives.

---

### 4. Summarizer Agent (Llama – Hugging Face Inference API)
- Produces **3–6 concise bullet points**
- Uses **only retrieved evidence**
- Every bullet ends with a citation `(doc_id::chunk_id)`
- Explicitly refuses if evidence is insufficient

---

## Zero-Hallucination Policy (Enforced)

This system enforces a **hard guarantee**:

**Either:**
- the answer is fully grounded and cited  
**or**
- the system refuses to answer

### Enforcement Layers
- Planner intent classification
- Retrieval confidence threshold
- Verifier evidence checks
- Summarizer evidence-only prompt
- Unit tests that fail on hallucination

A test explicitly asserts that **stock price predictions must be refused**.

---

## Observability and Monitoring (Added Day 13–14)

### Distributed Tracing (Arize Phoenix)
Each `/ask` request generates:
- One root trace
- Child spans for:
  - planner
  - retrieval
  - verifier
  - summarizer

Phoenix exposes:
- End-to-end latency (P50 / P99)
- Per-agent latency
- Refusal stage attribution
- Evidence score distributions

### Runtime Metrics
The API logs:
- top retrieval score
- refusal outcome
- total latency
- per-stage latency:
  - planner_ms
  - retrieval_ms
  - verifier_ms
  - summary_ms

These metrics are visible both in logs and Phoenix traces.

---

## Frontend Decision KPIs

The Streamlit UI surfaces **decision-relevant KPIs**, not vanity metrics:

- **Decision (ANSWERED / REFUSED)** — policy outcome
- **Evidence Strength** — top similarity score
- **Traceability** — number of cited evidence chunks
- **Latency (E2E)** — end-to-end request time

This allows users to assess **confidence, traceability, and cost** at a glance.

---

## Containerization (Added Day 14)

The system is fully containerized using **Docker Compose**:

- `api` service: FastAPI + FAISS + agents
- `ui` service: Streamlit frontend
- Environment-based configuration
- Service-to-service networking (`api:8000`)

This enables:
- reproducible local runs
- production-style deployment
- clean separation of concerns

---

## Scope and Constraints

### Designed to Answer
- Regulatory and compliance risks
- Capital and liquidity disclosures
- Resolution planning and TLAC (when present)
- Reported financial figures explicitly stated in filings
- Risk factor language

### Designed to Refuse
- Stock price predictions or targets
- Speculative or forward-looking claims
- Personal trivia
- Any statement not supported by retrieved evidence

---

## Dataset

Currently indexed filings:
- Goldman Sachs — 2023 Form 10-K (1,789 chunks)
- JPMorgan Chase — 2023 Form 10-K (1,408 chunks)
- Morgan Stanley — 2023 Form 10-K (637 chunks)

Total: **3,834 evidence chunks**

Processed chunks are stored in `data/processed/chunks.jsonl` (3,834 chunks across 3 filings).

---

## Project Structure

- `api/` – FastAPI application
- `api/rag/` – FAISS store, HF client, agent orchestration
- `streamlit/` – Analyst-facing UI
- `data/raw/` – Raw SEC PDFs
- `data/processed/` – Chunks, embeddings, FAISS index
- `monitoring/` – Logs and traces
- `architecture.md` – Detailed system design
- `data_sources.md` – Filing scope and provenance

---

## Data Ingestion and Chunking

SEC filings (10-K) are ingested from PDF format and processed through a deterministic chunking pipeline. Each filing is extracted using `pdfplumber`, cleaned, and split into overlapping chunks for retrieval.

Each chunk stores:
- document identifier
- company name
- filing year and type
- deterministic chunk ID
- chunk text and length
---

## How to Run Locally

Install dependencies:
```bash
python -m pip install -r requirements.txt
 ```

Build chunks:
```bash
python -m scripts.build_chunks
```

Build embeddings + FAISS index:
```bash
python -m scripts.build_faiss_index
```

Start the API:
```bash
uvicorn api.main:app --reload
```

Sanity check:
- `GET /sources` should list the 3 filings
- a sample `/ask` should return citations and evidence chunks

Start Streamlit:
```bash
streamlit run streamlit/app.py
```
