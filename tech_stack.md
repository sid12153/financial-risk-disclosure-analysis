# Tech Stack

## Core
- Python 3.12
- FastAPI (API layer)
- Uvicorn (local server)

## Document Processing
- pdfplumber (PDF text extraction)
- JSONL pipeline for chunk persistence (`chunks.jsonl`)

## Retrieval
- sentence-transformers (all-MiniLM-L6-v2 embeddings)
- FAISS (vector index and similarity search)

## UI
- Streamlit (interactive analyst-style query interface)

## Reliability and Monitoring
- Score-threshold refusals (confidence gating)
- Relevance guardrail (keyword coverage check)
- Query logging to CSV (`monitoring/query_log.csv`)
- Planned: Sentry (error tracking) + metrics dashboard (Prometheus/Grafana)
