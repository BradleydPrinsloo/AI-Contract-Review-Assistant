from __future__ import annotations

"""Clause Library domain models and storage services for ContractIQ."""

import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

CLAUSE_LIBRARY_DATABASE_FILENAME = "contractiq_clause_library.sqlite3"
SCHEMA_VERSION = 1
RISK_LEVELS = (
    "Critical",
    "High",
    "Elevated",
    "Moderate",
    "Medium",
    "Low",
    "Protective",
    "Neutral",
    "Info",
)


class ClauseValidationError(ValueError):
    """Raised when a clause library record fails validation."""


class ClauseExplanationProvider(Protocol):
    """Provider abstraction for optional AI-assisted clause explanations."""

    def explain(self, clause: "ClauseRecord") -> str:
        """Return an explanation for a clause record."""


@dataclass(frozen=True)
class ClauseSearchFilters:
    """Search filters for the professional clause library."""

    query: str = ""
    category: str = ""
    risk_level: str = ""
    include_archived: bool = False


@dataclass
class ClauseRecord:
    """Company-standard clause definition tracked by the Clause Library."""

    clause_id: str
    name: str
    category: str
    risk_level: str
    company_wording: str
    rejected_wording: str = ""
    examples: list[str] = field(default_factory=list)
    ai_explanation: str = ""
    active: bool = True
    version: int = 1
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class ClauseHistoryEntry:
    """Immutable audit event for a clause-library record."""

    history_id: int
    clause_id: str
    action: str
    version: int
    changed_at: str
    snapshot: dict


class ClauseLibraryService:
    """SQLite-backed service for ContractIQ clause library management."""

    def __init__(
        self,
        database_path: Path | str,
        *,
        explanation_provider: ClauseExplanationProvider | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self.explanation_provider = explanation_provider
        self.initialize()

    def initialize(self) -> None:
        """Create the clause library schema if needed."""

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS clause_library_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS clauses (
                    clause_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    company_wording TEXT NOT NULL,
                    rejected_wording TEXT NOT NULL DEFAULT '',
                    examples_json TEXT NOT NULL DEFAULT '[]',
                    ai_explanation TEXT NOT NULL DEFAULT '',
                    active INTEGER NOT NULL DEFAULT 1,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    search_text TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS clause_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clause_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    changed_at TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    FOREIGN KEY(clause_id) REFERENCES clauses(clause_id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                "INSERT OR REPLACE INTO clause_library_meta(key, value) VALUES (?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )

    def create_clause(
        self,
        *,
        name: str,
        category: str,
        risk_level: str,
        company_wording: str,
        rejected_wording: str = "",
        examples: list[str] | None = None,
        ai_explanation: str = "",
    ) -> ClauseRecord:
        """Create a validated clause-library record."""

        now = _now()
        record = ClauseRecord(
            clause_id=_clause_id(name, now),
            name=name.strip(),
            category=category.strip(),
            risk_level=risk_level.strip(),
            company_wording=company_wording.strip(),
            rejected_wording=rejected_wording.strip(),
            examples=_normalize_examples(examples or []),
            ai_explanation=ai_explanation.strip(),
            active=True,
            version=1,
            created_at=now,
            updated_at=now,
        )
        _validate(record)
        self._upsert(record)
        self._record_history(record, "created")
        return record

    def update_clause(self, clause_id: str, **changes) -> ClauseRecord:
        """Update a clause and record an audit-history snapshot."""

        existing = self.get_clause(clause_id)
        if existing is None:
            raise KeyError(f"Clause not found: {clause_id}")
        updated = ClauseRecord(
            clause_id=existing.clause_id,
            name=str(changes.get("name", existing.name)).strip(),
            category=str(changes.get("category", existing.category)).strip(),
            risk_level=str(changes.get("risk_level", existing.risk_level)).strip(),
            company_wording=str(changes.get("company_wording", existing.company_wording)).strip(),
            rejected_wording=str(changes.get("rejected_wording", existing.rejected_wording)).strip(),
            examples=_normalize_examples(changes.get("examples", existing.examples)),
            ai_explanation=str(changes.get("ai_explanation", existing.ai_explanation)).strip(),
            active=bool(changes.get("active", existing.active)),
            version=existing.version + 1,
            created_at=existing.created_at,
            updated_at=_now(),
        )
        _validate(updated)
        self._upsert(updated)
        self._record_history(updated, str(changes.get("history_action", "updated")))
        return updated

    def archive_clause(self, clause_id: str) -> ClauseRecord:
        """Archive a clause without deleting its history."""

        return self.update_clause(clause_id, active=False, history_action="archived")

    def explain_clause(self, clause_id: str) -> ClauseRecord:
        """Generate and persist an explanation through the configured provider abstraction."""

        clause = self.get_clause(clause_id)
        if clause is None:
            raise KeyError(f"Clause not found: {clause_id}")
        if self.explanation_provider is None:
            explanation = (
                "No AI explanation provider is configured. Add an OpenAI, Azure OpenAI, "
                "Ollama, Anthropic, or other provider adapter to generate explanations."
            )
        else:
            explanation = self.explanation_provider.explain(clause).strip()
        return self.update_clause(
            clause_id,
            ai_explanation=explanation,
            history_action="explained",
        )

    def get_clause(self, clause_id: str) -> ClauseRecord | None:
        """Return a clause by ID, or None when not found."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM clauses WHERE clause_id = ?",
                (clause_id,),
            ).fetchone()
        return _row_to_clause(row) if row is not None else None

    def search(self, filters: ClauseSearchFilters | None = None) -> list[ClauseRecord]:
        """Search clauses by text, category, risk level, and archive status."""

        active_filters = filters or ClauseSearchFilters()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM clauses ORDER BY active DESC, category ASC, name ASC"
            ).fetchall()
        clauses = [_row_to_clause(row) for row in rows]
        return [clause for clause in clauses if _matches(clause, active_filters)]

    def history(self, clause_id: str) -> list[ClauseHistoryEntry]:
        """Return chronological history snapshots for a clause."""

        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM clause_history WHERE clause_id = ? ORDER BY history_id ASC",
                (clause_id,),
            ).fetchall()
        return [
            ClauseHistoryEntry(
                history_id=int(row["history_id"]),
                clause_id=row["clause_id"],
                action=row["action"],
                version=int(row["version"]),
                changed_at=row["changed_at"],
                snapshot=json.loads(row["snapshot_json"]),
            )
            for row in rows
        ]

    def _upsert(self, record: ClauseRecord) -> None:
        payload = _clause_payload(record)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO clauses (
                    clause_id, name, category, risk_level, company_wording,
                    rejected_wording, examples_json, ai_explanation, active,
                    version, created_at, updated_at, search_text
                ) VALUES (
                    :clause_id, :name, :category, :risk_level, :company_wording,
                    :rejected_wording, :examples_json, :ai_explanation, :active,
                    :version, :created_at, :updated_at, :search_text
                )
                ON CONFLICT(clause_id) DO UPDATE SET
                    name=excluded.name,
                    category=excluded.category,
                    risk_level=excluded.risk_level,
                    company_wording=excluded.company_wording,
                    rejected_wording=excluded.rejected_wording,
                    examples_json=excluded.examples_json,
                    ai_explanation=excluded.ai_explanation,
                    active=excluded.active,
                    version=excluded.version,
                    updated_at=excluded.updated_at,
                    search_text=excluded.search_text
                """,
                payload,
            )

    def _record_history(self, record: ClauseRecord, action: str) -> None:
        snapshot = _clause_payload(record)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO clause_history(clause_id, action, version, changed_at, snapshot_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.clause_id,
                    action,
                    record.version,
                    record.updated_at,
                    json.dumps(snapshot, sort_keys=True),
                ),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


def clause_library_database_path(exports_dir: Path | str) -> Path:
    """Return the default clause library database path under an exports directory."""

    return Path(exports_dir) / "clause-library" / CLAUSE_LIBRARY_DATABASE_FILENAME


def _validate(record: ClauseRecord) -> None:
    if not record.name:
        raise ClauseValidationError("Clause name is required.")
    if not record.category:
        raise ClauseValidationError("Clause category is required.")
    if record.risk_level not in RISK_LEVELS:
        raise ClauseValidationError(f"Unsupported risk level: {record.risk_level}")
    if not record.company_wording:
        raise ClauseValidationError("Company wording is required.")


def _normalize_examples(examples) -> list[str]:
    if isinstance(examples, str):
        values = re.split(r"\r?\n", examples)
    else:
        values = list(examples or [])
    return [str(value).strip() for value in values if str(value).strip()]


def _matches(clause: ClauseRecord, filters: ClauseSearchFilters) -> bool:
    if not filters.include_archived and not clause.active:
        return False
    haystack = "\n".join(
        [
            clause.name,
            clause.category,
            clause.risk_level,
            clause.company_wording,
            clause.rejected_wording,
            clause.ai_explanation,
            *clause.examples,
        ]
    ).casefold()
    tokens = [token for token in filters.query.casefold().split() if token]
    if tokens and not all(token in haystack for token in tokens):
        return False
    if filters.category and filters.category.casefold() not in clause.category.casefold():
        return False
    if filters.risk_level and filters.risk_level != clause.risk_level:
        return False
    return True


def _clause_payload(record: ClauseRecord) -> dict[str, object]:
    return {
        "clause_id": record.clause_id,
        "name": record.name,
        "category": record.category,
        "risk_level": record.risk_level,
        "company_wording": record.company_wording,
        "rejected_wording": record.rejected_wording,
        "examples_json": json.dumps(record.examples),
        "ai_explanation": record.ai_explanation,
        "active": 1 if record.active else 0,
        "version": record.version,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "search_text": "\n".join(
            [
                record.name,
                record.category,
                record.risk_level,
                record.company_wording,
                record.rejected_wording,
                record.ai_explanation,
                *record.examples,
            ]
        ),
    }


def _row_to_clause(row: sqlite3.Row) -> ClauseRecord:
    return ClauseRecord(
        clause_id=row["clause_id"],
        name=row["name"],
        category=row["category"],
        risk_level=row["risk_level"],
        company_wording=row["company_wording"],
        rejected_wording=row["rejected_wording"],
        examples=json.loads(row["examples_json"] or "[]"),
        ai_explanation=row["ai_explanation"],
        active=bool(row["active"]),
        version=int(row["version"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _clause_id(name: str, timestamp: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-") or "clause"
    return f"{base}-{uuid4().hex[:8]}"


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()
