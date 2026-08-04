# AI Contract Scanner

A Windows desktop application for analyzing PDF, DOCX, and TXT contracts, identifying potentially important clauses, calculating a structured risk score, and generating professional review reports.

> **Current engine:** deterministic keyword and clause-pattern analysis with confidence scoring and OCR fallback for scanned PDFs. The application assists human review; it does not provide legal advice.

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
        ├───────────────┬──────────────────┐
        ▼               ▼                  ▼
Review dashboard   Scan repository   CSV/TXT/DOCX reports
```

## Application areas

The scanner is being generalized for multiple contract types, including:

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
├── contract_review_assistant/
│   ├── scanner.py
│   ├── risk_engine.py
│   ├── repository.py
│   ├── keyword_library.py
│   └── app_paths.py
├── packaging/
│   └── release_bundle.py
├── docs/
│   ├── architecture.md
│   ├── installation.md
│   ├── user-guide.md
│   └── roadmap.md
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

The release tooling creates versioned portable Windows bundles, generates client launch instructions, records included files in a release manifest, calculates SHA-256 checksums, and produces a verified ZIP archive. Separate installer tooling generates an Inno Setup script and signing-ready release instructions.

## Documentation

- [Architecture](docs/architecture.md)
- [Installation and release use](docs/installation.md)
- [User guide](docs/user-guide.md)
- [Roadmap](docs/roadmap.md)
- [Security policy](SECURITY.md)
- [Contributing guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Planned v2 work

- Complete visible rebrand to **AI Contract Scanner**
- General-purpose category names
- Contract-type keyword-library profiles
- Modernized dashboard and summary cards
- Improved repository filters and reviewer notes
- Expanded automated tests
- CI validation through GitHub Actions
- Optional AI-assisted explanations as a separate, clearly identified feature

## Important limitation

This software supports contract review and triage. It does not replace legal advice, legal interpretation, or professional judgment. Every finding and recommendation must be reviewed by an appropriately qualified person before a legal or business decision is made.

## Project owner

**Bradley Prinsloo**  
IT Support Specialist and software project builder based in Phoenix, Arizona.

## License

Copyright © Bradley Prinsloo. All rights reserved. See [`LICENSE`](LICENSE).
