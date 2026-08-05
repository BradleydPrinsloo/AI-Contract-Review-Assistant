# ContractIQ Release Notes

## 2.5 — Enterprise workspace foundation

- Added a dedicated read-only Executive Dashboard for platform KPIs.
- Removed scanner controls from the Dashboard by routing scanning workflows to the Contracts workspace.
- Added KPI cards for total contracts, average risk, contracts awaiting review, high-risk contracts, recent monthly volume, and review completion.
- Added risk distribution, recent contracts, recent activity, and review statistics panels.
- Added a modular Contracts workspace with guided Open → Scan → Review → Report steps, dedicated findings and executive-summary panels, and preserved service-backed report generation.
- Added a SQLite-backed Repository database foundation with filters for vendor, client, reviewer, risk, status, tags, department, review date, and version.
- Preserved backward compatibility by importing existing JSON repository records into SQLite idempotently.
- Updated product versioning to ContractIQ v2.5 and refreshed CI coverage for offscreen PySide6 shell tests.

## 2.0.0 — ContractIQ rebrand

- Rebranded the desktop product identity to ContractIQ.
- Added a new logo, icon, ICO file, and startup splash screen.
- Updated Qt window title, dashboard header, primary scan action, and About dialog.
- Updated report headers and decision-support notices for ContractIQ.
- Added Windows version metadata for branded executable builds.
- Added client handoff, quick-start, and checksum verification source files for portable releases.
