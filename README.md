# AI-Contract-Scanner

A Windows desktop application designed to assist with reviewing  contracts, identifying potentially important risk language, and presenting findings in a structured format for human review.

> **Portfolio status:** This repository is being prepared as a professional project showcase. The public documentation currently describes the verified release and handoff workflow. Application source code and screenshots will be added only after private information, client data, credentials, and generated build files have been removed.

## Verified capabilities

Based on the current release tooling, the project supports:

- Portable Windows delivery through `ContractReviewAssistant.exe`
- Versioned release bundle names
- Client-facing `START-HERE.cmd` and quick-start instructions
- Release metadata in `RELEASE-MANIFEST.json`
- SHA-256 checksums for individual bundle files and the final ZIP archive
- PowerShell-based checksum verification
- Signed and unsigned release notes
- Automated validation of required release inputs

## Release workflow

The release builder:

1. Reads the product version from Windows packaging metadata.
2. Validates that the executable, documentation, and verification script exist.
3. Creates a clean, versioned portable-release directory.
4. Copies the required client-delivery files.
5. Generates a launcher, quick-start guide, release manifest, and checksum manifest.
6. Compresses the release folder into a ZIP archive.
7. Generates a SHA-256 checksum for the completed ZIP.

See [`docs/architecture.md`](docs/architecture.md) for a more detailed explanation.

## Documentation

- [Architecture](docs/architecture.md)
- [Installation and release use](docs/installation.md)
- [User guide](docs/user-guide.md)
- [Roadmap](docs/roadmap.md)
- [Security policy](SECURITY.md)
- [Contributing guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Planned repository structure

```text
AI-Contract-Review-Assistant/
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── SECURITY.md
├── .gitignore
├── docs/
│   ├── architecture.md
│   ├── installation.md
│   ├── user-guide.md
│   └── roadmap.md
├── src/                  # Application source after security review
├── tests/                # Automated tests after review
├── packaging/            # Windows packaging configuration
└── assets/               # Screenshots and project graphics
```

## Important limitation

This software assists with contract review. It does not replace legal advice, legal interpretation, or professional judgment. Findings must be reviewed by a qualified person before business or legal decisions are made.

## Project owner

**Bradley Prinsloo**  
IT Support Specialist and software project builder based in Phoenix, Arizona.

## License

Copyright © Bradley Prinsloo. All rights reserved. See [`LICENSE`](LICENSE).
