# Data Directory

This directory contains the source documents and derived artifacts used by the
Financial Disclosure Intelligence system.

The data is intentionally small, curated, and reproducible to support
transparent evaluation and explainability.

---

## Directory Structure

data/

├── raw/

│   ├── GoldmanSachs_2023_10K.pdf

│   ├── JPMorganChase_2023_10K.pdf

│   └── MorganStanley_2023_10K.pdf

├── processed/

│   ├── chunks.jsonl

│   ├── embeddings_meta.jsonl

│   └── embeddings.faiss

└── README.md


---

## `raw/`

Contains original SEC filings used as the sole source of truth.

**Files**
- `GoldmanSachs_2023_10K.pdf`
- `JPMorganChase_2023_10K.pdf`
- `MorganStanley_2023_10K.pdf`

**Notes**
- Documents are publicly available SEC 10-K filings
- No external text sources are used
- All answers must be grounded in these documents only

---

## `processed/`

Contains derived artifacts produced during indexing and retrieval.

### `chunks.jsonl`
Line-delimited JSON file where each entry represents a text chunk.

Each chunk includes:
- `chunk_id`
- `doc_id`
- page number (if available)
- cleaned and raw text

Chunks are created to balance:
- semantic coherence
- retrieval quality
- citation traceability

---

### `embeddings_meta.jsonl`
Metadata aligned with vector embeddings.

Includes:
- `chunk_id`
- `doc_id`
- page / section metadata
- preprocessing information

Used to map retrieved vectors back to human-readable evidence.

---

### `embeddings.faiss`
FAISS vector index built over embedded text chunks.

- Enables fast semantic retrieval
- Stored locally for reproducibility
- No external vector database is used

---

## Data Integrity and Scope

- No synthetic or generated data
- No post-hoc edits to filing content
- No mixing across companies or years
- All answers and refusals are derived strictly from indexed filings

This design ensures the system is:
- auditable
- deterministic at retrieval time
- suitable for compliance-oriented use cases
