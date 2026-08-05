from __future__ import annotations

"""Playbook domain models and SQLite storage services for ContractIQ."""

import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from contract_review_assistant.clauses import ClauseLibraryService

PLAYBOOK_DATABASE_FILENAME = "contractiq_playbooks.sqlite3"
SCHEMA_VERSION = 1
RISK_TOLERANCES = ("Conservative", "Balanced", "Flexible")
PLAYBOOK_STATUSES = ("Draft", "Active", "Archived")
CLAUSE_REQUIREMENT_LEVELS = ("Required", "Preferred", "Escalate")


class PlaybookValidationError(ValueError):
    """Raised when a playbook record fails validation."""


@dataclass(frozen=True)
class PlaybookSearchFilters:
    """Search filters for review playbooks."""

    query: str = ""
    contract_type: str = ""
    risk_tolerance: str = ""
    status: str = ""
    include_archived: bool = False


@dataclass(frozen=True)
class PlaybookClauseRule:
    """Clause Library standard assigned to a playbook."""

    clause_id: str
    requirement_level: str = "Required"
    guidance: str = ""


@dataclass(frozen=True)
class PlaybookChecklistItem:
    """Checklist line item for playbook-driven review."""

    text: str
    required: bool = True
    owner_role: str = ""
    escalation: str = ""


@dataclass
class PlaybookRecord:
    """Reusable review playbook for a contract type."""

    playbook_id: str
    name: str
    description: str
    contract_type: str
    risk_tolerance: str
    clause_rules: list[PlaybookClauseRule] = field(default_factory=list)
    checklist_items: list[PlaybookChecklistItem] = field(default_factory=list)
    status: str = "Draft"
    active: bool = True
    version: int = 1
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class PlaybookHistoryEntry:
    """Immutable audit event for a playbook record."""

    history_id: int
    playbook_id: str
    action: str
    version: int
    changed_at: str
    snapshot: dict


class PlaybookLibraryService:
    """SQLite-backed service for ContractIQ playbook management."""

    def __init__(
        self,
        database_path: Path | str,
        *,
        clause_library_service: ClauseLibraryService | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self.clause_library_service = clause_library_service
        self.initialize()

    def initialize(self) -> None:
        """Create the playbook schema if needed."""

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS playbook_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS playbooks (
                    playbook_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    contract_type TEXT NOT NULL,
                    risk_tolerance TEXT NOT NULL,
                    clause_rules_json TEXT NOT NULL DEFAULT '[]',
                    checklist_json TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'Draft',
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
                CREATE TABLE IF NOT EXISTS playbook_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playbook_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    changed_at TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    FOREIGN KEY(playbook_id) REFERENCES playbooks(playbook_id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                "INSERT OR REPLACE INTO playbook_meta(key, value) VALUES (?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )

    def create_playbook(
        self,
        *,
        name: str,
        description: str = "",
        contract_type: str,
        risk_tolerance: str,
        clause_rules: list[PlaybookClauseRule] | None = None,
        checklist_items: list[PlaybookChecklistItem] | None = None,
        status: str = "Draft",
    ) -> PlaybookRecord:
        """Create a validated playbook record."""

        now = _now()
        normalized_status = status.strip() or "Draft"
        record = PlaybookRecord(
            playbook_id=_playbook_id(name),
            name=name.strip(),
            description=description.strip(),
            contract_type=contract_type.strip(),
            risk_tolerance=risk_tolerance.strip(),
            clause_rules=_normalize_clause_rules(clause_rules or []),
            checklist_items=_normalize_checklist_items(checklist_items or []),
            status=normalized_status,
            active=normalized_status != "Archived",
            version=1,
            created_at=now,
            updated_at=now,
        )
        self._validate(record)
        self._upsert(record)
        self._record_history(record, "created")
        return record

    def update_playbook(self, playbook_id: str, **changes) -> PlaybookRecord:
        """Update a playbook and record an audit-history snapshot."""

        existing = self.get_playbook(playbook_id)
        if existing is None:
            raise KeyError(f"Playbook not found: {playbook_id}")
        status = str(changes.get("status", existing.status)).strip() or "Draft"
        active = bool(changes["active"]) if "active" in changes else status != "Archived"
        updated = PlaybookRecord(
            playbook_id=existing.playbook_id,
            name=str(changes.get("name", existing.name)).strip(),
            description=str(changes.get("description", existing.description)).strip(),
            contract_type=str(changes.get("contract_type", existing.contract_type)).strip(),
            risk_tolerance=str(changes.get("risk_tolerance", existing.risk_tolerance)).strip(),
            clause_rules=_normalize_clause_rules(changes.get("clause_rules", existing.clause_rules)),
            checklist_items=_normalize_checklist_items(changes.get("checklist_items", existing.checklist_items)),
            status=status,
            active=active,
            version=existing.version + 1,
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self._validate(updated)
        self._upsert(updated)
        self._record_history(updated, str(changes.get("history_action", "updated")))
        return updated

    def archive_playbook(self, playbook_id: str) -> PlaybookRecord:
        """Archive a playbook without deleting its audit history."""

        return self.update_playbook(
            playbook_id,
            status="Archived",
            active=False,
            history_action="archived",
        )

    def get_playbook(self, playbook_id: str) -> PlaybookRecord | None:
        """Return a playbook by ID, or None when not found."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM playbooks WHERE playbook_id = ?",
                (playbook_id,),
            ).fetchone()
        return _row_to_playbook(row) if row is not None else None

    def search(self, filters: PlaybookSearchFilters | None = None) -> list[PlaybookRecord]:
        """Search playbooks by text, contract type, risk tolerance, and status."""

        active_filters = filters or PlaybookSearchFilters()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM playbooks ORDER BY active DESC, contract_type ASC, name ASC"
            ).fetchall()
        playbooks = [_row_to_playbook(row) for row in rows]
        return [playbook for playbook in playbooks if _matches(playbook, active_filters)]

    def history(self, playbook_id: str) -> list[PlaybookHistoryEntry]:
        """Return chronological history snapshots for a playbook."""

        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM playbook_history WHERE playbook_id = ? ORDER BY history_id ASC",
                (playbook_id,),
            ).fetchall()
        return [
            PlaybookHistoryEntry(
                history_id=int(row["history_id"]),
                playbook_id=row["playbook_id"],
                action=row["action"],
                version=int(row["version"]),
                changed_at=row["changed_at"],
                snapshot=json.loads(row["snapshot_json"]),
            )
            for row in rows
        ]

    def _validate(self, record: PlaybookRecord) -> None:
        if not record.name:
            raise PlaybookValidationError("Playbook name is required.")
        if not record.contract_type:
            raise PlaybookValidationError("Contract type is required.")
        if record.risk_tolerance not in RISK_TOLERANCES:
            raise PlaybookValidationError(f"Unsupported risk tolerance: {record.risk_tolerance}")
        if record.status not in PLAYBOOK_STATUSES:
            raise PlaybookValidationError(f"Unsupported playbook status: {record.status}")

        seen_clause_ids: set[str] = set()
        for rule in record.clause_rules:
            if not rule.clause_id.strip():
                raise PlaybookValidationError("Clause standard is required.")
            if rule.requirement_level not in CLAUSE_REQUIREMENT_LEVELS:
                raise PlaybookValidationError(f"Unsupported clause requirement: {rule.requirement_level}")
            if rule.clause_id in seen_clause_ids:
                raise PlaybookValidationError(f"Duplicate clause standard: {rule.clause_id}")
            seen_clause_ids.add(rule.clause_id)
            if self.clause_library_service is not None and self.clause_library_service.get_clause(rule.clause_id) is None:
                raise PlaybookValidationError(f"Clause standard does not exist: {rule.clause_id}")

        for item in record.checklist_items:
            if not item.text.strip():
                raise PlaybookValidationError("Checklist item text is required.")

    def _upsert(self, record: PlaybookRecord) -> None:
        payload = _playbook_payload(record)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO playbooks (
                    playbook_id, name, description, contract_type, risk_tolerance,
                    clause_rules_json, checklist_json, status, active, version,
                    created_at, updated_at, search_text
                ) VALUES (
                    :playbook_id, :name, :description, :contract_type, :risk_tolerance,
                    :clause_rules_json, :checklist_json, :status, :active, :version,
                    :created_at, :updated_at, :search_text
                )
                ON CONFLICT(playbook_id) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description,
                    contract_type=excluded.contract_type,
                    risk_tolerance=excluded.risk_tolerance,
                    clause_rules_json=excluded.clause_rules_json,
                    checklist_json=excluded.checklist_json,
                    status=excluded.status,
                    active=excluded.active,
                    version=excluded.version,
                    updated_at=excluded.updated_at,
                    search_text=excluded.search_text
                """,
                payload,
            )

    def _record_history(self, record: PlaybookRecord, action: str) -> None:
        snapshot = _playbook_payload(record)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO playbook_history(playbook_id, action, version, changed_at, snapshot_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.playbook_id,
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


def playbook_database_path(exports_dir: Path | str) -> Path:
    """Return the default playbook database path under an exports directory."""

    return Path(exports_dir) / "playbooks" / PLAYBOOK_DATABASE_FILENAME


def _normalize_clause_rules(rules) -> list[PlaybookClauseRule]:
    normalized: list[PlaybookClauseRule] = []
    for rule in list(rules or []):
        if isinstance(rule, PlaybookClauseRule):
            normalized.append(
                PlaybookClauseRule(
                    clause_id=rule.clause_id.strip(),
                    requirement_level=rule.requirement_level.strip() or "Required",
                    guidance=rule.guidance.strip(),
                )
            )
        else:
            normalized.append(
                PlaybookClauseRule(
                    clause_id=str(rule.get("clause_id", "")).strip(),
                    requirement_level=str(rule.get("requirement_level", "Required")).strip() or "Required",
                    guidance=str(rule.get("guidance", "")).strip(),
                )
            )
    return normalized


def _normalize_checklist_items(items) -> list[PlaybookChecklistItem]:
    normalized: list[PlaybookChecklistItem] = []
    for item in list(items or []):
        if isinstance(item, PlaybookChecklistItem):
            normalized.append(
                PlaybookChecklistItem(
                    text=item.text.strip(),
                    required=bool(item.required),
                    owner_role=item.owner_role.strip(),
                    escalation=item.escalation.strip(),
                )
            )
        elif isinstance(item, str):
            normalized.append(PlaybookChecklistItem(text=item.strip()))
        else:
            normalized.append(
                PlaybookChecklistItem(
                    text=str(item.get("text", "")).strip(),
                    required=bool(item.get("required", True)),
                    owner_role=str(item.get("owner_role", "")).strip(),
                    escalation=str(item.get("escalation", "")).strip(),
                )
            )
    return normalized


def _matches(playbook: PlaybookRecord, filters: PlaybookSearchFilters) -> bool:
    if not filters.include_archived and not playbook.active:
        return False
    haystack = _search_text(playbook).casefold()
    tokens = [token for token in filters.query.casefold().split() if token]
    if tokens and not all(token in haystack for token in tokens):
        return False
    if filters.contract_type and filters.contract_type.casefold() not in playbook.contract_type.casefold():
        return False
    if filters.risk_tolerance and filters.risk_tolerance != playbook.risk_tolerance:
        return False
    if filters.status and filters.status != playbook.status:
        return False
    return True


def _playbook_payload(record: PlaybookRecord) -> dict[str, object]:
    return {
        "playbook_id": record.playbook_id,
        "name": record.name,
        "description": record.description,
        "contract_type": record.contract_type,
        "risk_tolerance": record.risk_tolerance,
        "clause_rules_json": json.dumps([rule.__dict__ for rule in record.clause_rules]),
        "checklist_json": json.dumps([item.__dict__ for item in record.checklist_items]),
        "status": record.status,
        "active": 1 if record.active else 0,
        "version": record.version,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "search_text": _search_text(record),
    }


def _search_text(record: PlaybookRecord) -> str:
    rule_parts: list[str] = []
    for rule in record.clause_rules:
        rule_parts.extend([rule.clause_id, rule.requirement_level, rule.guidance])
    checklist_parts: list[str] = []
    for item in record.checklist_items:
        checklist_parts.extend([item.text, item.owner_role, item.escalation])
    return "\n".join(
        [
            record.name,
            record.description,
            record.contract_type,
            record.risk_tolerance,
            record.status,
            *rule_parts,
            *checklist_parts,
        ]
    )


def _row_to_playbook(row: sqlite3.Row) -> PlaybookRecord:
    return PlaybookRecord(
        playbook_id=row["playbook_id"],
        name=row["name"],
        description=row["description"],
        contract_type=row["contract_type"],
        risk_tolerance=row["risk_tolerance"],
        clause_rules=_normalize_clause_rules(json.loads(row["clause_rules_json"] or "[]")),
        checklist_items=_normalize_checklist_items(json.loads(row["checklist_json"] or "[]")),
        status=row["status"],
        active=bool(row["active"]),
        version=int(row["version"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _playbook_id(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-") or "playbook"
    return f"{base}-{uuid4().hex[:8]}"


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()
