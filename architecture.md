# Architecture

This project implements a strict Retrieval-Augmented Generation (RAG) workflow for evidence-based analysis of SEC filings.

The guiding rule is simple:
**Every answer must be supported by retrieved excerpts from indexed filings and must include citations.**
If the system cannot retrieve relevant evidence, it should refuse to answer.

---

## High-Level System Components

### 1) Document Ingestion
- Input: SEC 10-K filings (PDF/HTML converted to text)
- Output: clean text + metadata per filing

Key ingestion outputs:
- normalized text
- document ID (company + fiscal year)
- filing metadata (form type, filing date, source reference)

### 2) Chunking and Indexing
- Filing text is split into overlapping chunks sized for retrieval.
- Each chunk stores:
  - chunk ID
  - document ID
  - section label (if available, e.g., “Risk Factors”)
  - chunk text
- Chunks are embedded and stored in a local vector index.

### 3) Retrieval
Given a user question:
- compute query embedding
- retrieve top-k most relevant chunks (optionally filtered by company/year)
- return retrieved excerpts and metadata

### 4) Answer Generation (Grounded)
- LLM receives:
  - the user question
  - retrieved chunks (only)
  - strict instructions to cite evidence
- Output must include:
  - a concise answer
  - citations referencing chunk IDs and document metadata
  - refusal if evidence is insufficient

### 5) Guardrails (Reliability Layer)
Guardrails enforce:
- **Citation requirement**: every claim must map to retrieved text
- **Scope restriction**: no external knowledge beyond the indexed filings
- **Refusal behavior**: if retrieval confidence is low or evidence is missing
- **Transparency**: return the retrieved excerpts alongside the answer

### 6) UI + API Layer
- **FastAPI backend** provides:
  - `/ask` for Q&A with citations
  - `/sources` to list available filings
  - `/health` health check
- **Streamlit UI** provides:
  - company/year selection
  - question input
  - answer display + citations
  - expandable retrieved excerpts panel

---

## Data Flow Summary

1. Download filings → convert to text  
2. Chunk text → embed chunks → build vector index  
3. User asks question → retrieve top chunks  
4. Generate answer using only retrieved chunks  
5. Return answer + citations + evidence excerpts

---

## What “Strict” Means in This Project

The system must:
- answer only from retrieved text
- include citations for every response
- refuse when evidence is not present

This constraint is intentional and mirrors compliance-focused workflows in finance and consulting where traceability matters as much as correctness.

