# Finance Risk Disclosure UI (Streamlit)

This folder contains the Streamlit frontend for the Finance Risk Disclosure Analysis system.

The UI is designed to surface **model decisions, evidence strength, and traceability** rather than acting as a generic chat interface.

---

## Purpose

The Streamlit app serves as:
- A thin client over the FastAPI RAG backend
- A visualization layer for model decisions and confidence
- A demo interface suitable for compliance, risk, and audit use cases

The UI intentionally prioritizes **interpretability over aesthetics**.

---

## Key Features

### Question Interface
- Select a specific SEC filing (company + year)
- Submit natural language questions
- Control the number of retrieved evidence chunks (Top-K)

---

### Decision KPIs (Above the Fold)

Each response surfaces model behavior explicitly:

- **Decision (Policy)**  
  ANSWERED or REFUSED  
  (Green for accepted, red for refused)

- **Evidence Strength**  
  Top retrieval similarity score  
  Used as a confidence proxy

- **Traceability**  
  Number of unique citation chunks used

- **Latency (E2E)**  
  End-to-end request latency in milliseconds

These KPIs are intentionally simple and defensible — suitable for ML and fintech review.

---

### Evidence-Centric Answers

- Answers are rendered as bullet points
- Every bullet ends with a citation `(chunk_id)`
- Evidence excerpts are displayed separately for inspection
- White-box behavior: users can verify claims directly

---

### Refusal UX

When a question is refused, the UI displays:
- Clear refusal status
- Reason for refusal (e.g. out-of-scope, insufficient evidence)
- No speculative or partial answers are shown

Refusals are treated as **successful outcomes**, not failures.

---

## API Integration

The UI communicates exclusively with the backend API:
- `GET /sources` for filing metadata
- `POST /ask` for question answering

All decision logic lives in the backend.  
The frontend does not implement business rules.

---

## Deployment

The Streamlit app is containerized and deployed via Docker Compose alongside:
- FastAPI backend
- Phoenix observability service

It has been verified locally and on AWS EC2.

---

## Design Principles

- No hallucinated answers
- No silent failures
- No hidden confidence

This UI is meant to demonstrate how LLM-backed systems should behave in regulated environments.
