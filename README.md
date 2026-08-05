# ContractIQ

ContractIQ is a Windows desktop contract-intelligence application for analyzing PDF, DOCX, and TXT contracts, identifying important clauses, calculating an explainable risk score, and generating professional review reports.

> **Current engine:** deterministic keyword and clause-pattern analysis with confidence scoring and OCR fallback for scanned PDFs. Optional AI summaries are available when configured. ContractIQ assists human review; it does not provide legal advice.

## Rebrand status

**ContractIQ identity complete:** the product name, Qt window title, dashboard header, app icon, startup splash, report headers, Windows version metadata, release naming, and documentation now use the ContractIQ brand.

**Version 2.5 milestone 1:** the platform now has a separate Executive Dashboard with KPI cards, risk distribution, recent contracts, recent activity, and review statistics. Scanner controls live in the Contracts workspace instead of the Dashboard.

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
- CSV, TXT, PDF, and formatted DOCX report exports
- Rule-based summaries with optional OpenAI assistance
- Portable Windows release bundle tooling with manifests and SHA-256 verification
- Branded Windows metadata for `ContractIQ.exe`

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
        ├───────────────┬──────────────────┬────────────────────┬─────────────┐
        ▼               ▼                  ▼                    ▼             ▼
Review dashboard   Scan repository   CSV/TXT/PDF/DOCX      Splash/About   Optional AI
                                        reports              branding       summary
```

## Application areas

ContractIQ is designed to support rule libraries for multiple contract types, including:

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
├── assets/
│   ├── contractiq_logo.svg
│   ├── contractiq_icon.svg
│   ├── contractiq_icon.png
│   ├── contractiq.ico
│   └── contractiq_splash.png
├── main.py
├── service_main.py
├── v2_main.py
├── contract_review_assistant/
│   ├── branding.py
│   ├── dashboard/
│   ├── ui/
│   ├── ai_notes.py
│   ├── app_paths.py
│   ├── application_service.py
│   ├── keyword_library.py
│   ├── reporting.py
│   ├── repository.py
│   ├── risk_engine.py
│   └── scanner.py
├── packaging/
│   ├── release_bundle.py
│   └── windows/
│       ├── file_version_info.txt
│       └── VERIFY-CHECKSUMS.ps1
├── docs/
├── tests/
├── README-FIRST.md
├── CLIENT-HANDOFF.md
├── RELEASE-NOTES.md
├── requirements.txt
└── README.md
```

The Python package retains its existing internal name temporarily to avoid breaking imports and packaging scripts during the public rebrand.

## Branding assets

- **Logo:** `assets/contractiq_logo.svg`
- **Application icon:** `assets/contractiq.ico` and `assets/contractiq_icon.png`
- **Startup splash:** `assets/contractiq_splash.png`
- **Current version:** `ContractIQ v2.5`
- **Windows metadata:** `packaging/windows/file_version_info.txt`

## Reporting

ContractIQ reports can contain:

- Overall risk score and rating
- Finding counts by type
- Executive summary
- Category breakdown
- Top review priorities
- Recommendations
- Detailed findings with location, context, confidence, and review priority
- Reviewer sign-off fields in DOCX output
- ContractIQ decision-support notice

## Release workflow

The release tooling creates versioned portable Windows bundles, generates launch instructions, records included files in a release manifest, calculates SHA-256 checksums, and produces a verified ZIP archive. `packaging/windows/file_version_info.txt` stamps the branded executable metadata for PyInstaller builds.

## Documentation

- [Architecture](docs/architecture.md)
- [Installation and release use](docs/installation.md)
- [User guide](docs/user-guide.md)
- [Platform roadmap](docs/platform-roadmap.md)
- [Security policy](SECURITY.md)
- [Contributing guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Important limitation

ContractIQ supports contract review and triage. It does not replace legal advice, legal interpretation, or professional judgment. Every finding and recommendation must be reviewed by an appropriately qualified person before a legal or business decision is made.

## Project owner

**Bradley Prinsloo**  
IT Support Specialist and software project builder based in Phoenix, Arizona.

## License

Copyright © Bradley Prinsloo. All rights reserved. See [`LICENSE`](LICENSE).
