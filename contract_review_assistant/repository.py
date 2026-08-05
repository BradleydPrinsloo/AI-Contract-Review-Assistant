from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Iterable, List

from .branding import REPORT_FULL_TITLE
from .scanner import ScanResult


@dataclass
class RepositoryEntry:
    """Persisted contract review record used by the repository and dashboard."""

    scan_id: str
    scanned_at: str
    source_file: str
    source_name: str
    risk_score: int
    rating: str
    finding_count: int
    risk_count: int
    protective_count: int
    neutral_count: int
    categories: list[str]
    top_phrases: list[str]
    summary: str
    findings: list[dict]
    search_text: str
    report_path: str | None = None
    legacy_import: bool = False
    vendor: str = ""
    client: str = ""
    reviewer: str = ""
    status: str = "Awaiting Review"
    tags: list[str] = field(default_factory=list)
    department: str = "Unassigned"
    review_date: str = ""
    version: str = "1.0"


def record_scan(
    source_file: str,
    results: Iterable[ScanResult],
    risk_assessment,
    summary_text: str,
    repository_dir: Path,
    scanned_at: str | None = None,
    report_path: str | None = None,
) -> Path:
    entry = build_repository_entry(
        source_file,
        list(results),
        risk_assessment,
        summary_text,
        scanned_at,
        report_path,
    )
    return save_repository_entry(entry, repository_dir)


def build_repository_entry(
    source_file: str,
    results: List[ScanResult],
    risk_assessment,
    summary_text: str,
    scanned_at: str | None = None,
    report_path: str | None = None,
) -> RepositoryEntry:
    timestamp = scanned_at or datetime.now().replace(microsecond=0).isoformat()
    source_path = Path(source_file)
    findings = [asdict(result) for result in results]
    categories = sorted({result.category for result in results})
    top_phrases = _top_phrases(results)
    search_text = _build_search_text(
        source_file,
        source_path.name,
        risk_assessment.rating,
        categories,
        findings,
        summary_text,
        status="Awaiting Review",
        department="Unassigned",
        review_date=_date_from_timestamp(timestamp),
        version="1.0",
    )
    return RepositoryEntry(
        _scan_id(source_file, timestamp),
        timestamp,
        str(source_file),
        source_path.name,
        risk_assessment.total_score,
        risk_assessment.rating,
        risk_assessment.finding_count,
        risk_assessment.risk_count,
        risk_assessment.protective_count,
        risk_assessment.neutral_count,
        categories,
        top_phrases,
        summary_text,
        findings,
        search_text,
        report_path,
        False,
        status="Awaiting Review",
        department="Unassigned",
        review_date=_date_from_timestamp(timestamp),
        version="1.0",
    )


def save_repository_entry(entry: RepositoryEntry, repository_dir: Path) -> Path:
    """Persist a repository entry to the v2.5 SQLite contract database."""

    from .repository_database import ContractRepositoryDatabase

    return ContractRepositoryDatabase(repository_dir).upsert(entry)


def update_repository_report_path(record_path: Path | str, report_path: Path | str) -> None:
    """Update report linkage for legacy JSON records or the SQLite database file."""

    record_file = Path(record_path)
    if not record_file.exists():
        return
    if record_file.suffix.casefold() == ".json":
        payload = json.loads(record_file.read_text(encoding="utf-8"))
        payload["report_path"] = str(report_path)
        record_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_repository_entries(
    repository_dir: Path,
    legacy_reports_dir: Path | None = None,
) -> list[RepositoryEntry]:
    """Load repository entries from SQLite, importing legacy JSON records first."""

    from .repository_database import ContractRepositoryDatabase

    database = ContractRepositoryDatabase(repository_dir)
    database.import_json_records(repository_dir)
    entries = database.search()

    report_paths = {str(Path(entry.report_path).resolve()) for entry in entries if entry.report_path}
    if legacy_reports_dir and legacy_reports_dir.exists():
        for report_path in sorted(legacy_reports_dir.glob("*.txt")):
            if str(report_path.resolve()) in report_paths:
                continue
            legacy_entry = load_legacy_report_entry(report_path)
            if legacy_entry is not None:
                entries.append(legacy_entry)
    return sorted(entries, key=lambda entry: entry.scanned_at, reverse=True)


def load_json_repository_entries(
    repository_dir: Path,
    legacy_reports_dir: Path | None = None,
) -> list[RepositoryEntry]:
    """Load pre-v2.5 JSON repository records without touching SQLite storage."""

    entries: list[RepositoryEntry] = []
    report_paths = set()
    if repository_dir.exists():
        for path in sorted(repository_dir.glob("*.json")):
            entry = RepositoryEntry(**json.loads(path.read_text(encoding="utf-8")))
            setattr(entry, "_record_path", str(path))
            entries.append(entry)
            if entry.report_path:
                report_paths.add(str(Path(entry.report_path).resolve()))
    if legacy_reports_dir and legacy_reports_dir.exists():
        for report_path in sorted(legacy_reports_dir.glob("*.txt")):
            if str(report_path.resolve()) in report_paths:
                continue
            legacy_entry = load_legacy_report_entry(report_path)
            if legacy_entry is not None:
                entries.append(legacy_entry)
    return sorted(entries, key=lambda entry: entry.scanned_at, reverse=True)


def load_legacy_report_entry(report_path: Path) -> RepositoryEntry | None:
    text = report_path.read_text(encoding="utf-8", errors="ignore")
    if (
        REPORT_FULL_TITLE not in text
        and "Contract Analysis Report" not in text
        and "Construction Contract Risk Report" not in text
    ):
        return None
    source_file = _extract_line_value(text, "Source file:") or str(report_path)
    generated = _extract_line_value(text, "Generated:") or datetime.fromtimestamp(
        report_path.stat().st_mtime
    ).replace(microsecond=0).isoformat(sep=" ")
    risk_score = _extract_int(text, r"Overall Risk Score:\s*(\d+)/100")
    rating = _extract_line_value(text, "Risk Rating:") or "Unknown"
    finding_count = _extract_int(text, r"Finding Count:\s*(\d+)")
    risk_count = _extract_int(text, r"Risk Findings:\s*(\d+)")
    protective_count = _extract_int(text, r"Protective Findings:\s*(\d+)")
    neutral_count = _extract_int(text, r"Neutral/Info Findings:\s*(\d+)")
    categories = sorted(set(re.findall(r"^Category:\s*(.+)$", text, flags=re.MULTILINE)))
    top_phrases = re.findall(r"^\d+\.\s+(.+?)\s+\[", text, flags=re.MULTILINE)
    summary = _legacy_summary(text)
    source_name = Path(source_file).name or report_path.stem
    review_date = _date_from_timestamp(generated)
    return RepositoryEntry(
        _scan_id(str(source_file), generated),
        generated,
        str(source_file),
        source_name,
        risk_score,
        rating,
        finding_count,
        risk_count,
        protective_count,
        neutral_count,
        categories,
        top_phrases,
        summary,
        [],
        _build_search_text(
            str(source_file),
            source_name,
            rating,
            categories,
            [],
            text,
            status="Legacy Import",
            review_date=review_date,
            version="legacy",
        ),
        str(report_path),
        True,
        status="Legacy Import",
        review_date=review_date,
        version="legacy",
    )


def search_repository(
    entries: Iterable[RepositoryEntry],
    query: str = "",
    filters=None,
) -> list[RepositoryEntry]:
    tokens = [token for token in re.split(r"\s+", query.lower().strip()) if token]
    active_filters = filters
    results: list[RepositoryEntry] = []
    for entry in entries:
        haystack = entry.search_text.lower()
        if tokens and not all(token in haystack for token in tokens):
            continue
        if active_filters is not None and not _matches_filters(entry, active_filters):
            continue
        results.append(entry)
    return results


def _matches_filters(entry: RepositoryEntry, filters) -> bool:
    comparisons = (
        (getattr(filters, "vendor", ""), entry.vendor),
        (getattr(filters, "client", ""), entry.client),
        (getattr(filters, "reviewer", ""), entry.reviewer),
        (getattr(filters, "risk", ""), entry.rating),
        (getattr(filters, "status", ""), entry.status),
        (getattr(filters, "department", ""), entry.department),
        (getattr(filters, "version", ""), entry.version),
    )
    for expected, actual in comparisons:
        if expected and expected.casefold() not in actual.casefold():
            return False
    tag = getattr(filters, "tag", "")
    if tag and tag.casefold() not in {value.casefold() for value in entry.tags}:
        return False
    review_date_from = getattr(filters, "review_date_from", "")
    review_date_to = getattr(filters, "review_date_to", "")
    if review_date_from and entry.review_date < review_date_from:
        return False
    if review_date_to and entry.review_date > review_date_to:
        return False
    return True


def _top_phrases(results: Iterable[ScanResult]) -> list[str]:
    ranked = sorted(
        results,
        key=lambda result: (-result.score, -result.confidence, result.phrase.lower()),
    )
    phrases, seen = [], set()
    for result in ranked:
        lowered = result.phrase.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        phrases.append(result.phrase)
        if len(phrases) == 10:
            break
    return phrases


def _build_search_text(
    source_file: str,
    source_name: str,
    rating: str,
    categories: Iterable[str],
    findings: Iterable[dict],
    summary_text: str,
    *,
    vendor: str = "",
    client: str = "",
    reviewer: str = "",
    status: str = "",
    tags: Iterable[str] = (),
    department: str = "",
    review_date: str = "",
    version: str = "",
) -> str:
    parts = [
        source_file,
        source_name,
        rating,
        summary_text,
        vendor,
        client,
        reviewer,
        status,
        department,
        review_date,
        version,
        *categories,
        *tags,
    ]
    for finding in findings:
        parts.extend(
            str(finding.get(key, ""))
            for key in (
                "phrase",
                "category",
                "risk",
                "note",
                "context",
                "location",
                "reason",
                "clause_library_name",
                "preferred_wording",
                "rejected_wording",
                "clause_examples",
                "clause_explanation",
            )
        )
    return "\n".join(str(part) for part in parts if part)


def _extract_line_value(text: str, prefix: str) -> str | None:
    match = re.search(rf"^{re.escape(prefix)}\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_int(text: str, pattern: str) -> int:
    match = re.search(pattern, text)
    return int(match.group(1)) if match else 0


def _legacy_summary(text: str) -> str:
    summary_lines = []
    for line in (line.rstrip() for line in text.splitlines()):
        if line.startswith("1. "):
            break
        summary_lines.append(line)
    return "\n".join(summary_lines).strip()


def _scan_id(source_file: str, scanned_at: str) -> str:
    digest = sha256(f"{source_file}|{scanned_at}".encode("utf-8")).hexdigest()[:12]
    base = re.sub(r"[^a-z0-9]+", "-", Path(source_file).stem.lower()).strip("-") or "scan"
    return f"{base}-{digest}"


def _date_from_timestamp(value: str) -> str:
    if not value:
        return datetime.now().date().isoformat()
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date().isoformat()
    except ValueError:
        return value[:10] if len(value) >= 10 else datetime.now().date().isoformat()
