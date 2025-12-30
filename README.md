# Financial Risk and Disclosure Q&A from SEC Filings (Strict, Evidence-Grounded)

Analysts and consultants often need to read long financial filings to understand a company’s risks, regulatory exposure, and forward-looking concerns. These documents are dense, repetitive, and time-consuming to analyze, especially when comparing disclosures across companies.

This project turns SEC filings (10-K and later 10-Q) into a **queryable evidence base**. Users ask analyst-style questions, and the system returns concise answers that are explicitly grounded in retrieved excerpts, with chunk-level citations.

A core goal is **reliability over fluency**: the system is designed to refuse out-of-scope questions and avoid unsupported generation.

---

## Current Status (Day 13 — Multi-Agent Evidence RAG)

The current version implements a strict evidence-first workflow:

- PDFs are parsed from `data/raw`
- Text is chunked and stored in `data/processed/chunks.jsonl`
- Embeddings are generated using `sentence-transformers/all-MiniLM-L6-v2`
- A FAISS index is built and stored in `data/processed/embeddings.faiss`
- `/ask` runs a **multi-agent workflow** that enforces scope + evidence sufficiency
- Responses include chunk-level citations and the system refuses when evidence is weak or the question is out-of-scope

---

## Multi-Agent Workflow (LLM + Retrieval)

This project uses a small, production-style multi-agent pipeline to enforce a strict policy.

1) **Planner Agent (Mistral via Hugging Face Inference API)**
- Classifies intent: in-scope vs out-of-scope  
- Rewrites the question into a retrieval-friendly query  
- Chooses an appropriate `top_k` (bounded)

2) **Retriever (FAISS)**
- Retrieves top-k evidence chunks from indexed filings
- Returns similarity scores and chunk IDs

3) **Verifier Agent (Llama via Hugging Face Inference API)**
- Blocks answers when:
  - question is out-of-scope (stock predictions, trivia, personal preferences, etc.)
  - retrieval confidence is below threshold
  - evidence does not cover the requested topic

4) **Summarizer Agent (Llama via Hugging Face Inference API)**
- Produces 3–6 bullet points
- Uses only retrieved evidence
- Every bullet ends with a citation like `(chunk_id)`

---

## Guardrails and Monitoring (Current)

- **Retrieval confidence gating**: the API refuses if the top retrieval score is below `MIN_RETRIEVAL_SCORE`.
- **Scope enforcement**: the Planner/Verifier refuse out-of-scope questions by design.
- **Evidence-only answers**: the summarizer is instructed to use only evidence excerpts and include chunk citations.
- **Query logging**: requests are logged to `monitoring/query_log.csv`, including:
  - top retrieval score
  - refusal outcome
  - end-to-end latency
  - planner / retrieval / verifier / summarizer latency breakdown (ms)

Planned next: Arize Phoenix tracing for end-to-end observability.

---

## Evidence Presentation

Retrieved excerpts are post-processed for readability while preserving source fidelity.
The UI supports viewing both cleaned excerpts and raw chunk text.

---

## Scope: What This Can and Cannot Answer

### In scope (designed to answer)
- Risk factors and regulatory exposure
- Capital and liquidity disclosures
- Resolution planning and TLAC references (when present in evidence)
- Segment-level metrics and reported figures (when present in evidence)
- Policy language and compliance-related disclosures explicitly stated in filings

### Out of scope (designed to refuse)
- Stock price predictions or “next year” price targets
- Personal preferences (e.g., “CEO’s favorite food”)
- Any claim not supported by retrieved filing excerpts

These constraints are intentional and reflect compliance-style workflows where traceability matters more than free-form generation.

---

## Project Structure

- `api/` – FastAPI backend (retrieval + multi-agent guardrails + strict responses)
- `api/rag/` – retrieval store, HF LLM client, and multi-agent orchestration
- `streamlit/` – Streamlit UI for querying filings and reviewing evidence
- `data/raw/` – raw SEC filing PDFs (local only)
- `data/processed/` – chunk store + embeddings + FAISS index
- `monitoring/` – query logs for debugging and monitoring
- `architecture.md` – system design and data flow
- `data_sources.md` – documents used and scope

---

## Data Ingestion and Chunking

SEC filings (10-K) are ingested from PDF format and processed through a deterministic chunking pipeline. Each filing is extracted using `pdfplumber`, cleaned, and split into overlapping chunks for retrieval.

Each chunk stores:
- document identifier
- company name
- filing year and type
- deterministic chunk ID
- chunk text and length

Current dataset:
- Goldman Sachs 2023 10-K (1,789 chunks)
- JPMorgan Chase 2023 10-K (1,408 chunks)
- Morgan Stanley 2023 10-K (637 chunks)

Processed chunks are stored in `data/processed/chunks.jsonl` (3,834 chunks across 3 filings).

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
