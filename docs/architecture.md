# Architecture

## Overview

AI Contract Scanner is a modular Windows desktop application that separates document extraction, rule evaluation, risk scoring, optional AI summarization, local persistence, reporting, and release packaging.

## Application pipeline

```text
PDF / DOCX / TXT
        │
        ▼
Document extraction
        │
        ├── Native text extraction
        └── OCR fallback for scanned PDF pages
        │
        ▼
Keyword and clause-pattern scanner
        │
        ├── Configurable rules and aliases
        ├── Operative-language checks
        ├── Negation and context checks
        ├── Confidence assignment
        └── Finding deduplication
        │
        ▼
Risk engine
        │
        ├── Category weighting
        ├── Severity multipliers
        ├── Finding-type multipliers
        ├── Category caps
        └── Recommendations
        │
        ├──────────────┬────────────────┬──────────────────┐
        ▼              ▼                ▼                  ▼
Desktop UI       Local repository   CSV/TXT/DOCX     Optional AI
                                      reports          summary
```

## Main components

- `main.py` — PySide6 desktop interface, background scan worker, findings table, summaries, repository browser, and exports
- `contract_review_assistant/scanner.py` — document extraction, OCR fallback, clause scanning, confidence handling, deduplication, and report generation
- `contract_review_assistant/risk_engine.py` — weighted scoring, ratings, top findings, and recommendations
- `contract_review_assistant/repository.py` — JSON scan records, legacy-report import, searching, and report-path updates
- `contract_review_assistant/keyword_library.py` — editable rule-library creation, normalization, and persistence
- `contract_review_assistant/ai_notes.py` — optional OpenAI summary with a deterministic local fallback
- `contract_review_assistant/app_paths.py` — development, packaged-build, export, and repository paths
- `contract_review_assistant/release_bundle.py` — portable release bundle, manifest, ZIP, and SHA-256 generation
- `contract_review_assistant/release_installer.py` — Inno Setup asset generation and signing-ready instructions

## Local storage

Packaged builds use:

```text
Documents\AI Contract Scanner Exports\
├── keyword-library\keywords.json
└── repository\*.json
```

The scanner records structured findings and searchable summary text locally. Real contracts and exported reports must not be committed to the repository.

## Optional AI behavior

AI assistance is optional. When `OPENAI_API_KEY` is unavailable or an API request fails, the application uses its rule-based summary instead. The deterministic scanner and risk engine remain the primary analysis path.

## Release pipeline

```text
Windows version metadata
          │
          ▼
Build AIContractScanner.exe
          │
          ▼
Validate release inputs
          │
          ▼
Create versioned portable bundle
          │
          ├── Copy executable and handoff documents
          ├── Generate START-HERE.cmd
          ├── Generate QUICK-START.txt
          ├── Generate RELEASE-MANIFEST.json
          └── Generate SHA-256 manifests
          │
          ▼
Create verified ZIP archive
          │
          ▼
Generate optional Inno Setup installer assets
```

## Integrity controls

The release tooling supports:

- Per-file SHA-256 hashes
- `BUNDLE-CONTENTS-SHA256.txt`
- `VERIFY-CHECKSUMS.ps1`
- Release metadata with file paths and sizes
- A separate checksum for the final ZIP
- Signed or unsigned release-state notes

## Security boundary

The public repository excludes credentials, `.env` files, private contracts, client databases, generated reports, executables, installers, and release archives. The application supports internal contract review and does not provide legal advice.
