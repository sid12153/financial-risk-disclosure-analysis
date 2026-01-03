# Finance Risk Disclosure API (FastAPI)

This service exposes the backend API for the Finance Risk Disclosure Analysis system.

It provides a production-style Retrieval-Augmented Generation (RAG) interface for answering questions strictly from SEC 10-K filings, with built-in guardrails, refusal logic, observability, and traceability.

---

## What This API Does

- Accepts user questions about financial risk disclosures
- Retrieves relevant excerpts from indexed SEC 10-K filings
- Generates evidence-grounded answers with citations
- Refuses questions when evidence is insufficient or out of scope
- Logs metrics and traces for evaluation and monitoring

This API is intentionally designed for **correctness, transparency, and auditability**, not open-ended generation.

---

## Core Endpoints

### `GET /`
Basic service status endpoint.

---

### `GET /sources`
Returns metadata about the indexed filings, including:
- Company name
- Filing year
- Document identifiers available for retrieval

Used by the frontend to populate filters and validate scope.

---

### `POST /ask`
Main question-answering endpoint.

**Input**
- User question
- Optional document filter (company / filing)

**Output**
- Answer (if allowed)
- Citations (chunk IDs + document metadata)
- Retrieved evidence excerpts
- Refusal reason (if applicable)
- Latency and confidence metrics

The endpoint may **refuse** requests when:
- The question is out of scope
- Retrieval confidence is below threshold
- Evidence does not directly support the question

Refusals are treated as correct outcomes.

---

## Architecture Overview

Client (Streamlit)
↓
FastAPI (/ask)
↓
Planner → Retriever → Verifier → Summarizer
↓
FAISS Vector Index (local)
↓
SEC 10-K Filing Chunks


- Retrieval uses a local FAISS index for reproducibility
- No external vector databases or paid services
- All logic is deterministic and inspectable

---

## Observability and Monitoring

The API emits structured telemetry for each request:
- End-to-end latency
- Per-stage latency (planner, retrieval, verifier, summary)
- Retrieval confidence (top similarity score)
- Refusal stage and reason

Telemetry is exported via **OpenTelemetry** and visualized using **Phoenix**:
- Trace-level inspection of each RAG step
- Latency percentiles (P50 / P95 / P99)
- Refusal behavior analysis

---

## Deployment

The API is containerized and deployed using Docker Compose alongside:
- Streamlit frontend
- Phoenix observability service

It has been successfully deployed on AWS EC2 using:
- Ubuntu Linux
- Docker + Docker Compose
- Explicit security group rules for exposed services

---

## Design Philosophy

- Prefer refusal over hallucination
- Prefer evidence over fluency
- Prefer observability over black-box behavior

This service mirrors patterns used in regulated or high-stakes domains such as finance, compliance, and risk analysis.
