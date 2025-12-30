# Tech Stack

## Core (Current)
- Python 3.12
- FastAPI (API layer)
- Uvicorn (local server)
- Pydantic (request/response schemas)

## Document Processing (Current)
- pdfplumber (PDF text extraction)
- JSONL pipeline for chunk persistence (`data/processed/chunks.jsonl`)

## Retrieval (Current)
- sentence-transformers (`all-MiniLM-L6-v2`) for embeddings
- FAISS (vector index + cosine similarity via normalized inner product)
- Metadata alignment via `embeddings_meta.jsonl`

## Multi-Agent Reasoning (Current)
- Hugging Face Inference API (remote hosted LLMs)
- Planner Agent: Mistral (intent classification + query rewrite)
- Verifier Agent: Llama (evidence sufficiency + out-of-scope blocking)
- Summarizer Agent: Llama (grounded bullet answer with citations)

## UI (Current)
- Streamlit (interactive query interface)

## Reliability, Guardrails, Monitoring (Current)
- Intent-based refusal (out-of-scope questions blocked by Planner)
- Verifier-based refusal (insufficient evidence blocked)
- Retrieval confidence threshold gating (min similarity score)
- Citation enforcement (answer requires chunk citations)
- Latency tracking per stage (planner, retrieval, verifier, summarizer)
- Query logging to CSV (`monitoring/query_log.csv`)

## Planned (Future)
- Arize Phoenix (RAG tracing and evaluation)
- Sentry (error tracking)
- Docker (containerized deployment)
- Deployment options: Streamlit Cloud + Docker, and optionally AWS EC2 for API hosting
