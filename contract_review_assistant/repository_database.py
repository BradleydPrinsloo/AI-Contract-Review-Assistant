from __future__ import annotations

"""SQLite-backed contract repository storage for ContractIQ."""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .repository import RepositoryEntry

DATABASE_FILENAME = "contractiq_repository.sqlite3"
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RepositoryFilters:
    """Search and filter options for the local contract database."""

    query: str = ""
    vendor: str = ""
    client: str = ""
    reviewer: str = ""
    risk: str = ""
    status: str = ""
    tag: str = ""
    department: str = ""
    review_date_from: str = ""
    review_date_to: str = ""
    version: str = ""


class ContractRepositoryDatabase:
    """SQLite repository for persisted contract scan history and metadata."""

    def __init__(self, repository_dir: Path | str) -> None:
        self.repository_dir = Path(repository_dir)
        self.path = repository_database_path(self.repository_dir)

    def initialize(self) -> None:
        """Create or migrate the local repository schema."""

        self.repository_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS repository_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS contracts (
                    scan_id TEXT PRIMARY KEY,
                    scanned_at TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    rating TEXT NOT NULL,
                    finding_count INTEGER NOT NULL,
                    risk_count INTEGER NOT NULL,
                    protective_count INTEGER NOT NULL,
                    neutral_count INTEGER NOT NULL,
                    categories_json TEXT NOT NULL,
                    top_phrases_json TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    findings_json TEXT NOT NULL,
                    search_text TEXT NOT NULL,
                    report_path TEXT,
                    legacy_import INTEGER NOT NULL DEFAULT 0,
                    vendor TEXT NOT NULL DEFAULT '',
                    client TEXT NOT NULL DEFAULT '',
                    reviewer TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'Awaiting Review',
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    department TEXT NOT NULL DEFAULT 'Unassigned',
                    review_date TEXT NOT NULL DEFAULT '',
                    version TEXT NOT NULL DEFAULT '1.0',
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT OR REPLACE INTO repository_meta(key, value) VALUES (?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )

    def upsert(self, entry: RepositoryEntry) -> Path:
        """Insert or update a contract repository entry."""

        self.initialize()
        normalized = normalize_entry_metadata(entry)
        payload = _entry_payload(normalized)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO contracts (
                    scan_id, scanned_at, source_file, source_name, risk_score, rating,
                    finding_count, risk_count, protective_count, neutral_count,
                    categories_json, top_phrases_json, summary, findings_json, search_text,
                    report_path, legacy_import, vendor, client, reviewer, status, tags_json,
                    department, review_date, version, updated_at
                ) VALUES (
                    :scan_id, :scanned_at, :source_file, :source_name, :risk_score, :rating,
                    :finding_count, :risk_count, :protective_count, :neutral_count,
                    :categories_json, :top_phrases_json, :summary, :findings_json, :search_text,
                    :report_path, :legacy_import, :vendor, :client, :reviewer, :status, :tags_json,
                    :department, :review_date, :version, :updated_at
                )
                ON CONFLICT(scan_id) DO UPDATE SET
                    scanned_at=excluded.scanned_at,
                    source_file=excluded.source_file,
                    source_name=excluded.source_name,
                    risk_score=excluded.risk_score,
                    rating=excluded.rating,
                    finding_count=excluded.finding_count,
                    risk_count=excluded.risk_count,
                    protective_count=excluded.protective_count,
                    neutral_count=excluded.neutral_count,
                    categories_json=excluded.categories_json,
                    top_phrases_json=excluded.top_phrases_json,
                    summary=excluded.summary,
                    findings_json=excluded.findings_json,
                    search_text=excluded.search_text,
                    report_path=excluded.report_path,
                    legacy_import=excluded.legacy_import,
                    vendor=excluded.vendor,
                    client=excluded.client,
                    reviewer=excluded.reviewer,
                    status=excluded.status,
                    tags_json=excluded.tags_json,
                    department=excluded.department,
                    review_date=excluded.review_date,
                    version=excluded.version,
                    updated_at=excluded.updated_at
                """,
                payload,
            )
        return self.path

    def search(self, filters: RepositoryFilters | None = None) -> list[RepositoryEntry]:
        """Return contracts matching text and metadata filters."""

        self.initialize()
        active_filters = filters or RepositoryFilters()
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM contracts ORDER BY scanned_at DESC").fetchall()
        entries = [_row_to_entry(row, self.path) for row in rows]
        return [entry for entry in entries if _matches(entry, active_filters)]

    def import_json_records(self, repository_dir: Path | str | None = None) -> int:
        """Import legacy JSON records into SQLite using scan_id as idempotency key."""

        source_dir = Path(repository_dir) if repository_dir is not None else self.repository_dir
        if not source_dir.exists():
            return 0
        imported = 0
        for path in sorted(source_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                entry = RepositoryEntry(**payload)
            except Exception:
                continue
            self.upsert(entry)
            imported += 1
        return imported

    def update_report_path(self, scan_id: str, report_path: Path | str) -> None:
        """Update a report path for a persisted scan if it exists."""

        self.initialize()
        with self._connect() as connection:
            connection.execute(
                "UPDATE contracts SET report_path = ?, updated_at = ? WHERE scan_id = ?",
                (str(report_path), datetime.now().isoformat(timespec="seconds"), scan_id),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection


def repository_database_path(repository_dir: Path | str) -> Path:
    """Return the SQLite database path for a repository directory."""

    return Path(repository_dir) / DATABASE_FILENAME


def normalize_entry_metadata(entry: RepositoryEntry) -> RepositoryEntry:
    """Fill enterprise metadata defaults on an existing repository entry."""

    entry.vendor = (entry.vendor or "").strip()
    entry.client = (entry.client or "").strip()
    entry.reviewer = (entry.reviewer or "").strip()
    entry.status = (entry.status or "Awaiting Review").strip()
    entry.tags = [str(tag).strip() for tag in (entry.tags or []) if str(tag).strip()]
    entry.department = (entry.department or "Unassigned").strip()
    entry.review_date = (entry.review_date or _date_from_timestamp(entry.scanned_at)).strip()
    entry.version = (entry.version or "1.0").strip()
    entry.search_text = _metadata_search_text(entry)
    return entry


def _entry_payload(entry: RepositoryEntry) -> dict[str, object]:
    return {
        "scan_id": entry.scan_id,
        "scanned_at": entry.scanned_at,
        "source_file": entry.source_file,
        "source_name": entry.source_name,
        "risk_score": entry.risk_score,
        "rating": entry.rating,
        "finding_count": entry.finding_count,
        "risk_count": entry.risk_count,
        "protective_count": entry.protective_count,
        "neutral_count": entry.neutral_count,
        "categories_json": json.dumps(entry.categories),
        "top_phrases_json": json.dumps(entry.top_phrases),
        "summary": entry.summary,
        "findings_json": json.dumps(entry.findings),
        "search_text": entry.search_text,
        "report_path": entry.report_path,
        "legacy_import": 1 if entry.legacy_import else 0,
        "vendor": entry.vendor,
        "client": entry.client,
        "reviewer": entry.reviewer,
        "status": entry.status,
        "tags_json": json.dumps(entry.tags),
        "department": entry.department,
        "review_date": entry.review_date,
        "version": entry.version,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }


def _row_to_entry(row: sqlite3.Row, record_path: Path) -> RepositoryEntry:
    entry = RepositoryEntry(
        scan_id=row["scan_id"],
        scanned_at=row["scanned_at"],
        source_file=row["source_file"],
        source_name=row["source_name"],
        risk_score=int(row["risk_score"]),
        rating=row["rating"],
        finding_count=int(row["finding_count"]),
        risk_count=int(row["risk_count"]),
        protective_count=int(row["protective_count"]),
        neutral_count=int(row["neutral_count"]),
        categories=json.loads(row["categories_json"] or "[]"),
        top_phrases=json.loads(row["top_phrases_json"] or "[]"),
        summary=row["summary"],
        findings=json.loads(row["findings_json"] or "[]"),
        search_text=row["search_text"],
        report_path=row["report_path"],
        legacy_import=bool(row["legacy_import"]),
        vendor=row["vendor"],
        client=row["client"],
        reviewer=row["reviewer"],
        status=row["status"],
        tags=json.loads(row["tags_json"] or "[]"),
        department=row["department"],
        review_date=row["review_date"],
        version=row["version"],
    )
    setattr(entry, "_record_path", str(record_path))
    return entry


def _matches(entry: RepositoryEntry, filters: RepositoryFilters) -> bool:
    haystack = entry.search_text.casefold()
    tokens = [token for token in filters.query.casefold().split() if token]
    if tokens and not all(token in haystack for token in tokens):
        return False
    comparisons = (
        (filters.vendor, entry.vendor),
        (filters.client, entry.client),
        (filters.reviewer, entry.reviewer),
        (filters.risk, entry.rating),
        (filters.status, entry.status),
        (filters.department, entry.department),
        (filters.version, entry.version),
    )
    for expected, actual in comparisons:
        if expected and expected.casefold() not in actual.casefold():
            return False
    if filters.tag and filters.tag.casefold() not in {tag.casefold() for tag in entry.tags}:
        return False
    if filters.review_date_from and entry.review_date < filters.review_date_from:
        return False
    if filters.review_date_to and entry.review_date > filters.review_date_to:
        return False
    return True


def _metadata_search_text(entry: RepositoryEntry) -> str:
    parts: list[str] = [
        entry.search_text,
        entry.source_file,
        entry.source_name,
        entry.rating,
        entry.summary,
        entry.vendor,
        entry.client,
        entry.reviewer,
        entry.status,
        entry.department,
        entry.review_date,
        entry.version,
        *entry.categories,
        *entry.top_phrases,
        *entry.tags,
    ]
    for finding in entry.findings:
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
            )
        )
    return "\n".join(part for part in parts if part)


def _date_from_timestamp(value: str) -> str:
    if not value:
        return datetime.now().date().isoformat()
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date().isoformat()
    except ValueError:
        return value[:10] if len(value) >= 10 else datetime.now().date().isoformat()
