# Financial Risk & Disclosure Analysis Using Public Filings
Analysts and consultants often need to read long financial filings to understand a company’s risks, regulatory exposure, and forward-looking concerns. These documents are dense, repetitive, and time-consuming to analyze, especially when comparing disclosures across reporting periods or companies.

This project explores how public financial filings such as SEC 10-K and 10-Q reports can be processed and queried in a structured way to support risk and disclosure analysis. The system retrieves relevant sections from source documents based on analyst-style questions and produces concise summaries that are explicitly grounded in the underlying text.

A key focus of this project is reliability rather than generation. The system is designed to surface evidence from filings, cite the source of each response, and avoid answering questions when the available documents do not provide sufficient information.

## Current Status (Evidence-First Retrieval)

The current version implements a strict evidence-first retrieval workflow:
- filings are parsed from PDFs stored in `data/raw`
- text is chunked into overlapping segments and saved to `data/processed/chunks.jsonl`
- embeddings are generated using `sentence-transformers/all-MiniLM-L6-v2`
- a FAISS vector index is built and stored in `data/processed/embeddings.faiss`
- the API returns the top retrieved excerpts with chunk-level citations
- the system refuses to answer if no relevant evidence is retrieved

Next step: add guardrails (refusal thresholds, citation enforcement, scope limits), then introduce multi-agent verification and evaluation.

### Evidence Presentation

Retrieved excerpts are post-processed to improve readability while preserving source fidelity.
Sentence-safe snippet extraction is used to avoid mid-word or mid-sentence starts caused by PDF formatting.

## Scope and Constraints

- The system answers questions using only the indexed filings and does not rely on external financial knowledge.
- Responses are grounded in retrieved text excerpts and include explicit citations.
- If relevant evidence cannot be retrieved, the system returns a refusal rather than generating an unsupported answer.

These constraints are intentional and reflect analyst and compliance-oriented workflows where traceability and evidence are more important than fluent text generation.

## Project Structure

- `api/` – FastAPI backend implementing document ingestion, retrieval, and strict evidence-based responses
- `streamlit/` – Streamlit user interface for querying filings and reviewing citations
- `data/raw/` – Raw SEC filing PDFs used for the current baseline
- `architecture.md` – System design and data flow
- `data_sources.md` – Description of source documents and scope

## Data Ingestion and Chunking

Public SEC filings (10-K) are ingested from PDF format and processed through a deterministic chunking pipeline. Each filing is extracted using `pdfplumber`, cleaned, and split into overlapping text chunks to support downstream retrieval.

For each chunk, the pipeline records:
- document identifier
- company name
- filing year and type
- character length
- deterministic chunk ID

The current dataset includes:
- Goldman Sachs 2023 10-K (1,789 chunks)
- JPMorgan Chase 2023 10-K (1,408 chunks)
- Morgan Stanley 2023 10-K (637 chunks)

Processed chunks are stored in `data/processed/chunks.jsonl` (3,834 chunks across 3 filings).

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
