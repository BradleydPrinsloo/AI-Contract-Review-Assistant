# Architecture

## Scope of this document

This page documents the release and client-handoff architecture verified from the supplied `release_bundle.py` source file. It does not claim details about the scanning engine, graphical interface, storage layer, AI provider, or document parsers because those source files have not yet been reviewed for publication.

## Release components

The verified release workflow uses these primary inputs:

- `dist/ContractReviewAssistant.exe`
- Windows version metadata under `packaging/windows/`
- Client-facing handoff documents
- A PowerShell checksum-verification script

## Build pipeline

```text
Windows version metadata
          |
          v
Extract product version
          |
          v
Validate required inputs
          |
          v
Create clean versioned bundle directory
          |
          +--> Copy executable
          +--> Copy client documentation
          +--> Copy verification script
          +--> Generate START-HERE.cmd
          +--> Generate QUICK-START.txt
          +--> Generate RELEASE-MANIFEST.json
          +--> Generate per-file SHA-256 manifest
          |
          v
Create compressed portable ZIP
          |
          v
Generate ZIP SHA-256 checksum
```

## Integrity controls

The release builder calculates SHA-256 hashes for delivered files and records file paths, file sizes, and hashes in release metadata. It also creates:

- `BUNDLE-CONTENTS-SHA256.txt` for bundle-level file verification
- `VERIFY-CHECKSUMS.ps1` for client-side checking
- A separate `.sha256` file for the final ZIP archive

These controls help detect accidental corruption or modification after packaging.

## Client experience

The bundle is designed for a simple portable Windows handoff:

1. The client extracts the ZIP.
2. The client runs `START-HERE.cmd`.
3. The launcher checks that the executable remains beside the launcher.
4. The application opens without a traditional installer.
5. The client selects an authorized contract for review.

## Separation of concerns

The release tooling separates:

- Application execution
- Packaging and delivery
- Client instructions
- Integrity verification
- Release metadata

This separation makes the handoff reproducible and easier to audit.

## Architecture still to document

The following sections will be added after their source files are reviewed:

- Application-layer component diagram
- Contract ingestion and parsing flow
- Risk-rule evaluation pipeline
- Optional AI-assisted processing
- Persistence and export model
- User-interface structure
- Automated testing strategy
