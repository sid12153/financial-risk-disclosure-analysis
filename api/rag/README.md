# RAG Core — Retrieval, Guardrails, and Answering Logic

This folder contains the core Retrieval-Augmented Generation (RAG) logic used by the Finance Risk Disclosure Analysis system.

It is designed to answer questions strictly from SEC 10-K filings while enforcing evidence-based guardrails, refusal logic, and traceable decision-making.

---

## Design Goals
- Ground all answers in retrieved filing text
- Refuse questions that are out of scope or insufficiently supported
- Make every decision inspectable (retrieval scores, refusal reason, citations)
- Keep the system reproducible and dependency-light

---

## Key Components

### `agents.py`
Implements the multi-stage RAG pipeline:

1. **Planner**
   - Classifies intent (in-scope vs out-of-scope)
   - Rewrites the query for retrieval
   - Selects retrieval depth (`top_k`)

2. **Retriever**
   - Queries a FAISS vector index using dense embeddings
   - Returns ranked chunks with similarity scores

3. **Verifier**
   - Checks whether retrieved evidence is sufficient
   - Enforces minimum confidence thresholds
   - Triggers refusal when evidence is weak or irrelevant

4. **Summarizer**
   - Generates the final answer strictly from retrieved chunks
   - Enforces citation requirements on every bullet
   - Refuses if grounded answering is not possible

Each stage emits latency metrics and decision metadata, which are later logged and traced.

---

### `faiss_store.py`
Handles vector-based retrieval:
- Loads FAISS index and embedding metadata
- Executes similarity search over normalized embeddings
- Supports optional document filtering (company, filing)

---

### `embeddings.py`
Manages text embedding:
- Uses a SentenceTransformer model for dense embeddings
- Ensures consistent normalization for FAISS search
- Centralized embedding logic for reproducibility

---

### `chunking.py`
Responsible for document chunking:
- Splits long filing text into semantically meaningful chunks
- Preserves chunk IDs for traceability and citation
- Tuned for financial disclosure structure

---

### `pdf_text.py`
Extracts raw text from SEC 10-K PDFs:
- Handles page-level extraction
- Normalizes whitespace and formatting
- Acts as the ingestion entrypoint

---

### `retrieve_lexical_baseline.py`
Implements a lexical (non-embedding) retrieval baseline:
- Used for comparison against dense retrieval
- Helps evaluate retrieval quality independently of embeddings

---

## Guardrails and Refusal Logic
The system refuses to answer when:
- The question is out of scope (e.g., stock predictions, opinions)
- Retrieval confidence falls below a defined threshold
- Evidence does not directly support the question
- Citations cannot be reliably attached

Refusals are treated as correct outcomes, not failures.

---

## Observability
Each RAG stage emits:
- Latency (per stage and end-to-end)
- Retrieval confidence (top similarity score)
- Refusal stage and reason (if applicable)

These signals are exported via OpenTelemetry and visualized in Phoenix for trace-level inspection.

---

## Why This Matters
This RAG design prioritizes:
- Answer correctness over fluency
- Explicit refusal over hallucination
- Inspectability over black-box generation

It reflects production concerns common in financial, legal, and compliance-focused AI systems.
