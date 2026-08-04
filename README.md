# AI Contract Scanner

A Windows desktop application for analyzing PDF, DOCX, and TXT contracts, identifying potentially important clauses, calculating a structured risk score, and generating professional review reports.

> **Current engine:** deterministic keyword and clause-pattern analysis with confidence scoring and OCR fallback for scanned PDFs. Optional AI summaries are available when configured. The application assists human review; it does not provide legal advice.

## Project status

**Phase 1 complete:** the product, interface, report branding, Windows metadata, export paths, release naming, and AI prompts have been generalized under the **AI Contract Scanner** name.

**Next phase:** modern dashboard redesign, summary cards, contract-type rule profiles, improved repository filters, automated tests, and CI validation.

## Core capabilities

- PDF, DOCX, and TXT document extraction
- OCR fallback when a PDF does not contain usable embedded text
- Configurable keyword library with aliases, categories, risk levels, finding types, and review notes
- Built-in clause-pattern detection
- Operative-language and negation checks to reduce obvious false positives
- Confidence scoring and duplicate-finding reduction
- Weighted 0–100 risk assessment with category caps
- Low, Moderate, Elevated, High, and Critical ratings
- Prioritized findings and practical review recommendations
- Searchable local scan repository
- CSV, TXT, and formatted DOCX report exports
- Rule-based summaries with optional OpenAI assistance
- Portable Windows release bundles with manifests and SHA-256 verification
- Inno Setup installer asset generation and code-signing workflow documentation

## Analysis pipeline

```text
PDF / DOCX / TXT
        │
        ▼
Document extraction
        │
        ├── Native PDF text
        └── OCR fallback for scanned PDF pages
        │
        ▼
Keyword and clause-pattern scanner
        │
        ├── Operative-language checks
        ├── Negation/context checks
        ├── Confidence assignment
        └── Finding deduplication
        │
        ▼
Risk engine
        │
        ├── Category weighting
        ├── Severity and finding-type multipliers
        ├── Category score caps
        └── Recommendations
        │
        ├───────────────┬──────────────────┬─────────────────┐
        ▼               ▼                  ▼                 ▼
Review dashboard   Scan repository   CSV/TXT/DOCX     Optional AI
                                        reports          summary
```

## Application areas

The scanner is designed to support rule libraries for multiple contract types, including:

- General commercial agreements
- Vendor and supplier agreements
- Service agreements
- Employment agreements
- NDAs and confidentiality agreements
- Software and licensing agreements
- Procurement agreements
- Lease agreements
- Construction and subcontract agreements
- Custom organization-specific rule libraries

## Current source structure

```text
AI-Contract-Scanner/
├── main.py
├── contract_review_assistant/
│   ├── ai_notes.py
│   ├── app_paths.py
│   ├── keyword_library.py
│   ├── repository.py
│   ├── risk_engine.py
│   ├── scanner.py
│   ├── release_bundle.py
│   └── release_installer.py
├── packaging/
│   └── windows/
│       └── file_version_info.txt
├── docs/
│   ├── architecture.md
│   ├── installation.md
│   ├── user-guide.md
│   └── roadmap.md
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── .gitignore
```

The Python package retains its existing internal name temporarily to avoid breaking imports and packaging scripts during the public rebrand.

## Reporting

The application can produce structured reports containing:

- Overall risk score and rating
- Finding counts by type
- Executive summary
- Category breakdown
- Top review priorities
- Recommendations
- Detailed findings with location, context, confidence, and review priority
- Reviewer sign-off fields in DOCX output

## Release workflow

The release tooling creates versioned portable Windows bundles, generates launch instructions, records included files in a release manifest, calculates SHA-256 checksums, and produces a verified ZIP archive. Separate installer tooling generates an Inno Setup script and signing-ready release instructions.

## Documentation

- [Architecture](docs/architecture.md)
- [Installation and release use](docs/installation.md)
- [User guide](docs/user-guide.md)
- [Roadmap](docs/roadmap.md)
- [Security policy](SECURITY.md)
- [Contributing guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Phase 2 roadmap

- Modernized dashboard and summary cards
- Contract-type keyword-library profiles
- Improved repository filters and reviewer notes
- Expanded automated tests
- CI validation through GitHub Actions
- Sanitized screenshots and release documentation
- Reproducible Windows build configuration

## Important limitation

This software supports contract review and triage. It does not replace legal advice, legal interpretation, or professional judgment. Every finding and recommendation must be reviewed by an appropriately qualified person before a legal or business decision is made.

## Project owner

**Bradley Prinsloo**  
IT Support Specialist and software project builder based in Phoenix, Arizona.

## License

Copyright © Bradley Prinsloo. All rights reserved. See [`LICENSE`](LICENSE).
