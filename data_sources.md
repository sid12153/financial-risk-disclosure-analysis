# Data Sources

This project uses publicly available U.S. SEC filings (10-K) as the primary source documents. The system is designed to answer questions using only retrieved excerpts from these filings and must provide citations for every response.

## Primary Source Type
- **SEC Form 10-K (Annual Report)**
- Content includes risk factors, management discussion, legal proceedings, regulatory exposure, and forward-looking statements.

## Selected Companies and Filing Year
The initial demo scope is intentionally small and focused to ensure quality and traceability.

- **JPMorgan Chase and Co.** — **2023 Form 10-K** (filed in 2024)
- **Goldman Sachs Group, Inc.** — **2023 Form 10-K** (filed in 2024)
- **Morgan Stanley** — **2023 Form 10-K** (filed in 2024)

## Data Acquisition
Two acceptable acquisition methods are supported (choose one based on convenience):
1. **Manual download from the SEC EDGAR website** (PDF/HTML)
2. **Public dataset mirror** (e.g., Hugging Face SEC 10-K corpus) if it provides clean access to the same filings

Each document stored in this project is treated as a versioned source artifact with metadata:
- company name
- ticker (if available)
- form type (10-K)
- fiscal year (2023)
- filing date
- source URL (or dataset reference)

## Licensing and Usage Notes
- SEC filings are public disclosures. This project uses them for research, analysis, and demonstration.
- Outputs are generated for informational purposes and are not financial advice.
- The system is designed to refuse answers that are not supported by the indexed filings.

