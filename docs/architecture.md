# Architecture

## Overview

ContractIQ is a modular Windows desktop application that separates document extraction, rule evaluation, risk scoring, optional AI summarization, local persistence, reporting, branding, and release packaging.

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
        ├── Finding deduplication
        └── Clause Library guidance enrichment
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
        ├──────────────┬────────────────┬──────────────────┬──────────────┐
        ▼              ▼                ▼                  ▼              ▼
Desktop UI       Local repository   CSV/TXT/PDF/DOCX  Brand assets   Optional AI
                                      reports           + metadata     summary
```

## Main components

- `main.py` — PySide6 application shell adapter, startup splash, About dialog, background scan worker, repository browser, and legacy export actions
- `service_main.py` — service-backed desktop entry point with report-generation workflow
- `v2_main.py` — Version 2.5 platform shell with separate Executive Dashboard, Contracts workspace, Repository, and Clause Library routing
- `contract_review_assistant/branding.py` — ContractIQ product constants, report titles, executable naming, and decision-support notices
- `contract_review_assistant/clauses/library.py` — SQLite-backed Clause Library domain service, validation, CRUD, audit history, and explanation-provider abstraction
- `contract_review_assistant/clauses/enrichment.py` — deterministic matching that attaches active Clause Library guidance to scanner findings
- `contract_review_assistant/contracts/workspace.py` — dedicated Contracts workspace UI composition for Open → Scan → Review → Report workflows
- `contract_review_assistant/dashboard/metrics.py` — repository-derived executive dashboard KPI calculations
- `contract_review_assistant/ui/clause_library_page.py` — professional PySide6 Clause Library editor page
- `contract_review_assistant/ui/dashboard_page.py` — read-only PySide6 Executive Dashboard page
- `contract_review_assistant/ui/charts.py` — lightweight dashboard chart widgets
- `contract_review_assistant/scanner.py` — document extraction, OCR fallback, clause scanning, confidence handling, deduplication, and simple report generation
- `contract_review_assistant/reporting.py` — branded HTML/PDF/DOCX report templates
- `contract_review_assistant/risk_engine.py` — weighted scoring, ratings, top findings, and recommendations
- `contract_review_assistant/repository.py` — repository DTOs, scan-record persistence API, legacy-report import, search compatibility, and report-path helpers
- `contract_review_assistant/repository_database.py` — SQLite-backed contract database, metadata filters, and idempotent JSON-record import
- `contract_review_assistant/keyword_library.py` — editable rule-library creation, normalization, and persistence
- `contract_review_assistant/ai_notes.py` — optional OpenAI summary with a deterministic local fallback
- `contract_review_assistant/app_paths.py` — development, packaged-build, export, and repository paths
- `packaging/release_bundle.py` — portable release bundle, manifest, ZIP, and SHA-256 generation
- `packaging/windows/file_version_info.txt` — Windows version metadata for `ContractIQ.exe`

## Brand assets

```text
assets/
├── contractiq_logo.svg
├── contractiq_icon.svg
├── contractiq_icon.png
├── contractiq.ico
└── contractiq_splash.png
```

The Qt app uses `contractiq.ico` for the window/application icon and `contractiq_splash.png` for the startup splash screen when the asset is present.

## Local storage

Packaged builds use:

```text
Documents\ContractIQ Exports\
├── keyword-library\keywords.json
├── repository\contractiq_repository.sqlite3
└── clause-library\contractiq_clause_library.sqlite3
```

The scanner records structured findings, searchable summary text, Clause Library guidance, and enterprise metadata locally in SQLite. Existing JSON records under `repository\*.json` are imported into the database idempotently for backward compatibility. The Clause Library stores company wording standards, rejected wording, examples, explanation notes, and versioned audit events in its own SQLite database. Active Clause Library records are matched deterministically against findings by category, detected phrase, and wording overlap; matched guidance is attached to findings before scoring summaries, repository persistence, and report export. Real contracts, exported reports, and generated local databases must not be committed to the repository.

## Optional AI behavior

AI assistance is optional. When `OPENAI_API_KEY` is unavailable or an API request fails, the application uses its rule-based summary instead. The deterministic scanner and risk engine remain the primary analysis path.

## Release pipeline

```text
ContractIQ brand assets + Windows version metadata
          │
          ▼
Build ContractIQ.exe
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

The public repository excludes credentials, `.env` files, private contracts, client databases, generated reports, executables, installers, and release archives. ContractIQ supports internal contract review and does not provide legal advice.
