# Finance RAG Demo UI (Streamlit)

This folder contains the Streamlit interface for interacting with the Finance RAG system.

The UI is designed for fast demo and review:
- ask questions about SEC 10-K filings
- optionally filter by company and year
- view answers with citations
- expand and inspect the retrieved text excerpts that were used to generate the answer

## Planned UI Components

- Company selector (dropdown)
- Year selector (dropdown)
- Question input box
- Answer panel
- Citations panel (with source metadata)
- Retrieved excerpts panel (collapsible, readable)

## Why Streamlit

Streamlit keeps the focus on the data and the system behavior:
- quick iteration
- easy to run locally
- simple for recruiters to understand during a demo

The goal is a clean, transparent interface that makes it obvious how the answer was formed and what evidence supports it.
