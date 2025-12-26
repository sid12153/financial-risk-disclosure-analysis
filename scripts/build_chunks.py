# scripts/build_chunks.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from api.rag.pdf_text import load_documents
from api.rag.chunking import chunk_document_text

RAW_DIR = Path("data/raw")
OUT_PATH = Path("data/processed/chunks.jsonl")

def infer_metadata(doc_id: str, filename: str) -> Dict[str, str]:
    """
    Tries to parse: Company_2023_10K.pdf from doc_id or filename.
    If it can't infer, falls back safely.
    """
    stem = Path(filename).stem
    tokens = stem.replace("-", "_").split("_")

    company = tokens[0] if tokens else doc_id
    filing_year = "unknown"
    filing_type = "10K"

    for t in tokens:
        if t.isdigit() and len(t) == 4:
            filing_year = t
        if t.upper() in {"10K", "10Q"}:
            filing_type = t.upper()

    return {
        "company": company,
        "filing_year": filing_year,
        "filing_type": filing_type,
    }


def main():
    docs = load_documents(RAW_DIR, max_pages=None)
    if not docs:
        raise FileNotFoundError(f"No PDFs found in {RAW_DIR.resolve()}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if OUT_PATH.exists():
        OUT_PATH.unlink()

    total_chunks = 0

    for doc_id, doc in docs.items():
        meta = infer_metadata(doc_id=doc_id, filename=doc.filename)

        chunks = chunk_document_text(
            doc_text=doc.text,
            doc_id=doc.doc_id,
            filename=doc.filename,
            company=meta["company"],
            filing_year=meta["filing_year"],
            filing_type=meta["filing_type"],
            chunk_chars=1400,
            overlap_chars=200,
        )

        with OUT_PATH.open("a", encoding="utf-8") as f:
            for c in chunks:
                row = {
                    "chunk_id": c.chunk_id,
                    "doc_id": c.doc_id,
                    "filename": c.filename,
                    "company": c.company,
                    "filing_year": c.filing_year,
                    "filing_type": c.filing_type,
                    "n_chars": c.n_chars,
                    "text": c.text,
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        print(f"{doc.filename}: chunks={len(chunks)} chars={len(doc.text)}")
        total_chunks += len(chunks)

    print(f"\nWrote {total_chunks} chunks to {OUT_PATH}")


if __name__ == "__main__":
    main()

