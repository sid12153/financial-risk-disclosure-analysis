# Scripts

This directory contains utility scripts used to build, validate, and evaluate
the Financial Disclosure Intelligence system.

All scripts are designed to be run explicitly and reproducibly.
No background jobs or hidden preprocessing steps are used.

---

## Scripts Overview

scripts/

├── build_chunks.py


├── build_faiss_index.py

├── metrics_report.py

└── script_test_retrieval.py

---

## `build_chunks.py`

**Purpose**
- Converts raw SEC 10-K PDFs into clean, overlapping text chunks

**What it does**
1. Loads PDFs from `data/raw/`
2. Extracts text using `pdfplumber`
3. Cleans and normalizes text
4. Splits text into semantically meaningful chunks
5. Writes results to `data/processed/chunks.jsonl`

**Why this matters**
- Chunk boundaries directly affect retrieval quality
- Chunk IDs become permanent citation anchors used throughout the system

---

## `build_faiss_index.py`

**Purpose**
- Builds the semantic retrieval index

**What it does**
1. Loads chunks from `chunks.jsonl`
2. Generates embeddings using `sentence-transformers`
3. Normalizes vectors for cosine similarity
4. Builds a FAISS index
5. Persists:
   - `embeddings.faiss`
   - `embeddings_meta.jsonl`

**Why this matters**
- Retrieval quality depends on embedding consistency
- Metadata alignment ensures every vector can be traced back to source text

---

## `metrics_report.py`

**Purpose**
- Offline evaluation of system behavior using production logs

**Input**
- `monitoring/query_log.csv`

**Metrics computed**
- Total request count
- Refusal rate
- Latency percentiles (P50 / P95 / P99)
- Top-score distribution histogram
- Per-document refusal and score statistics

**Output**
- Console summary suitable for screenshots and reporting
- No external dependencies or dashboards required

**Why this matters**
- Demonstrates observability without labeled datasets
- Shows production-style monitoring using real queries
- Supports claims about reliability and latency

---

## `script_test_retrieval.py`

**Purpose**
- Lightweight sanity checks for retrieval behavior

**What it tests**
- Embedding generation
- FAISS search execution
- Basic score sanity (non-empty, ordered results)

**Why this matters**
- Ensures indexing and retrieval work before running the API
- Acts as a quick diagnostic tool during development

---

## Design Principles

- Explicit execution (no hidden automation)
- Deterministic inputs and outputs
- Clear separation between:
  - data preparation
  - indexing
  - evaluation

These scripts form the backbone of the system’s reproducibility and auditability.
