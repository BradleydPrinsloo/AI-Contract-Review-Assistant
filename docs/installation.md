# Installation and Release Use

## Public repository status

The repository contains the sanitized Python source used for the ContractIQ portfolio build. Generated executables, private contracts, credentials, build outputs, and client data are intentionally excluded.

## Developer setup

Create and activate a virtual environment, then install the published dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the desktop application from the project root:

```powershell
python main.py
```

For the service-backed report workflow, run:

```powershell
python service_main.py
```

For the Version 2 platform shell, run:

```powershell
python v2_main.py
```

The dependency list currently includes PySide6, PyMuPDF, python-docx, python-dotenv, OpenAI, and RapidOCR. A precise supported Python-version range will be added after the Windows build workflow is validated end to end.

## Optional AI summaries

ContractIQ works without an API key by generating a deterministic rule-based summary. To enable optional OpenAI summaries, set an environment variable before launching:

```powershell
$env:OPENAI_API_KEY = "your-key"
```

The model can be overridden with `OPENAI_MODEL`. Never commit keys or `.env` files.

## Local data

Packaged builds store editable rules and scan history under:

```text
Documents\ContractIQ Exports\
├── keyword-library\keywords.json
└── repository\
```

Development runs use the local project `exports/` directory. Exported CSV, TXT, PDF, and DOCX reports are saved to the location selected in the Save dialog.

## Portable Windows release

A prepared release bundle is intended to be used as follows:

1. Obtain the versioned release ZIP from a trusted source.
2. Verify the supplied `.sha256` value when available.
3. Extract the complete ZIP to a local folder.
4. Keep all delivered files together.
5. Double-click `START-HERE.cmd`.
6. Choose **Open Contract**.
7. Select an authorized PDF, DOCX, or TXT contract.
8. Choose **Scan Contract** and review the score, findings, and summary.
9. Choose **Generate Report** when the service-backed entry point is used.

## Branding and executable metadata

ContractIQ branding lives in source control under `assets/` and `contract_review_assistant/branding.py`. Windows version metadata for PyInstaller builds lives at `packaging/windows/file_version_info.txt` and stamps `ContractIQ.exe` with the ContractIQ product name, file description, and version.

## Integrity verification

The release workflow supports:

- `VERIFY-CHECKSUMS.ps1` for files inside the extracted bundle
- `BUNDLE-CONTENTS-SHA256.txt` for per-file hashes
- A separate `.sha256` file for the compressed ZIP

A matching checksum verifies file integrity but does not independently establish who produced the release.

## Windows SmartScreen

Unsigned Windows executables may trigger a SmartScreen warning. Only continue when the release source is trusted and the supplied checksum has been verified.

## Reproducible Windows build

The repository should retain its PyInstaller `.spec` file once the final build configuration is validated. Build artifacts such as `build/`, `dist/`, installers, portable ZIPs, and executables remain excluded from source control.
