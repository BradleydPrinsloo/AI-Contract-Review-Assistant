# ContractIQ Client Handoff

## Deliverable identity

- **Product:** ContractIQ
- **Executable:** `ContractIQ.exe`
- **Primary workflow:** Open Contract → Scan Contract → Review Findings → Generate Report
- **Local data folder:** `Documents\ContractIQ Exports\`

## Included branding

- `assets/contractiq_logo.svg` — horizontal product logo
- `assets/contractiq_icon.svg` — source vector app mark
- `assets/contractiq_icon.png` — high-resolution PNG icon
- `assets/contractiq.ico` — Windows application icon
- `assets/contractiq_splash.png` — startup splash screen
- `packaging/windows/file_version_info.txt` — Windows version metadata for PyInstaller

## Operator notes

ContractIQ scans local files and produces decision-support findings. Reviewers should confirm every finding manually, remove false positives where appropriate, and escalate legal interpretation to a qualified reviewer.

## Release verification

Use `VERIFY-CHECKSUMS.ps1` inside a portable bundle to validate delivered files against `BUNDLE-CONTENTS-SHA256.txt`.
