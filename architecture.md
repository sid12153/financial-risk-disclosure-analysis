# Architecture

This project implements a strict evidence-first workflow for analyst-style risk and disclosure analysis of SEC 10-K filings.

Core rule:
**Every response must be grounded in retrieved excerpts from indexed filings and must include citations.**
If relevant evidence cannot be retrieved or verified, the system must refuse.

---

## System Components

### 1) Document Ingestion (PDF → Text)
- Input: SEC 10-K filings in PDF format stored in `data/raw`
- Extraction: `pdfplumber`
- Output: raw text per filing (document-level)

### 2) Chunking (Text → Overlapping Segments)
- Filing text is cleaned and split into overlapping character chunks.
- Each chunk stores:
  - `chunk_id` (deterministic)
  - `doc_id` and filename
  - company, filing year, filing type
  - chunk text and length
- Output: `data/processed/chunks.jsonl`

### 3) Embeddings (Chunks → Vectors)
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Embeddings are normalized for cosine similarity retrieval.
- Output: vectors aligned 1:1 with chunk metadata.

### 4) Vector Store (FAISS Index)
- Index type: `IndexFlatIP` (inner product on normalized embeddings = cosine similarity)
- Artifacts:
  - `data/processed/embeddings.faiss`
  - `data/processed/embeddings_meta.jsonl` (metadata aligned to FAISS ids)

---

## Multi-Agent /ask Workflow (Current)

### 5) Planner Agent (LLM)
- Classifies intent:
  - `risk_analysis` (in-scope)
  - `out_of_scope` (e.g., stock predictions, trivia, personal preferences)
- Rewrites the user question into a keyword-rich retrieval query.
- Chooses an appropriate `top_k` (bounded range).

### 6) Retrieval (FAISS)
Given the planner’s rewritten query:
- Embed query using the same embedding model
- Retrieve top-k chunk IDs from FAISS (optionally filtered by `doc_id`)
- Return chunks with similarity scores

### 7) Verifier Agent (LLM)
- Checks whether retrieved evidence is sufficient to answer from filings only.
- Enforces refusal when:
  - question is out-of-scope
  - top score is below threshold
  - evidence does not cover the requested topic

### 8) Summarizer Agent (LLM)
- Produces 3–6 bullet points in normal English
- Uses ONLY the retrieved evidence
- Every bullet ends with a citation `(chunk_id)`

---

## API + UI Layer

### FastAPI
- `/sources` lists available filings
- `/ask` runs multi-agent workflow and returns answer + citations + evidence
- `/health` health check

### Streamlit
- Filing selection (doc_id)
- Question input
- Answer panel + citations
- Evidence excerpts (raw + cleaned display)

---

## Monitoring (Current)
- CSV query logs in `monitoring/query_log.csv`
- Per-request latency breakdown:
  - planner_ms, retrieval_ms, verifier_ms, summary_ms
- Debug prints in API terminal for:
  - planner intent + rewritten query
  - top chunk preview and score
  - stage-level latencies

---

## Planned (Future)
- Arize Phoenix tracing + evaluation
- Docker containerization
- Production deployment (Streamlit Cloud + Docker; optional AWS EC2 for API)
