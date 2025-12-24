# Financial Risk & Disclosure Analysis Using Public Filings
Analysts and consultants often need to read long financial filings to understand a company’s risks, regulatory exposure, and forward-looking concerns. These documents are dense, repetitive, and time-consuming to analyze, especially when comparing disclosures across reporting periods or companies.

This project explores how public financial filings such as SEC 10-K and 10-Q reports can be processed and queried in a structured way to support risk and disclosure analysis. The system retrieves relevant sections from source documents based on analyst-style questions and produces concise summaries that are explicitly grounded in the underlying text.

A key focus of this project is reliability rather than generation. The system is designed to surface evidence from filings, cite the source of each response, and avoid answering questions when the available documents do not provide sufficient information.

## Current Status (Baseline)

The current version implements a strict evidence-first baseline:
- filings are parsed from PDFs stored in `data/raw`
- text is chunked and retrieved using keyword overlap (no embeddings yet)
- the API returns the top retrieved excerpts with chunk-level citations
- the system refuses to answer if no relevant evidence is retrieved

Next step: replace keyword retrieval with embeddings + vector search, then add generation with guardrails.

## Scope and Constraints

- The system answers questions using only the indexed filings and does not rely on external financial knowledge.
- Responses are grounded in retrieved text excerpts and include explicit citations.
- If relevant evidence cannot be retrieved, the system returns a refusal rather than generating an unsupported answer.

These constraints are intentional and reflect analyst and compliance-oriented workflows where traceability and evidence are more important than fluent text generation.

## Project Structure

- `api/` – FastAPI backend implementing document ingestion, retrieval, and strict evidence-based responses
- `streamlit/` – Streamlit user interface for querying filings and reviewing citations
- `data/raw/` – Raw SEC filing PDFs (not committed if large)
- `architecture.md` – System design and data flow
- `data_sources.md` – Description of source documents and scope
