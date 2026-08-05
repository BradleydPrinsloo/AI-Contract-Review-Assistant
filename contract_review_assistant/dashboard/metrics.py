from __future__ import annotations

"""Dashboard-specific domain model and KPI calculations for ContractIQ."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from contract_review_assistant.repository import RepositoryEntry

HIGH_RISK_RATINGS = {"critical", "high", "elevated"}
CRITICAL_RISK_RATINGS = {"critical"}
REVIEWABLE_RISK_RATINGS = {"critical", "high", "elevated", "moderate", "medium"}
REPORT_EXTENSIONS = {".pdf": "PDF", ".docx": "DOCX", ".csv": "CSV", ".txt": "TXT"}


@dataclass(frozen=True)
class RecentContract:
    """Compact contract row used by the dashboard."""

    scan_id: str
    name: str
    scanned_at: str
    rating: str
    risk_score: int
    finding_count: int
    categories: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class RecentReport:
    """Recent exported report row used by the dashboard."""

    name: str
    kind: str
    exported_at: str
    path: str


@dataclass(frozen=True)
class RecentActivity:
    """Human-readable timeline item for recent platform activity."""

    title: str
    subtitle: str
    severity: str


@dataclass(frozen=True)
class DashboardSummary:
    """Aggregated metrics displayed on the Milestone 1 dashboard."""

    total_contracts: int
    contracts_last_30_days: int
    contracts_awaiting_review: int
    high_risk_contracts: int
    critical_contracts: int
    average_risk: int
    risk_distribution: dict[str, int]
    recent_contracts: list[RecentContract]
    recent_reports: list[RecentReport]
    recent_activity: list[RecentActivity]
    reports_generated: int = 0
    database_size_bytes: int = 0

    @property
    def contracts_scanned(self) -> int:
        """Alias for the top-level dashboard statistic."""

        return self.total_contracts

    @property
    def completion_rate(self) -> int:
        """Approximate review-throughput indicator until formal workflow states exist."""

        if self.total_contracts == 0:
            return 0
        completed = max(0, self.total_contracts - self.contracts_awaiting_review)
        return round((completed / self.total_contracts) * 100)

    @property
    def database_size_label(self) -> str:
        """Human-readable database size label for the dashboard statistics card."""

        return _format_bytes(self.database_size_bytes)


def build_dashboard_summary(
    entries: Iterable[RepositoryEntry],
    *,
    now: datetime | None = None,
    recent_limit: int = 6,
    exports_dir: Path | str | None = None,
    repository_dir: Path | str | None = None,
) -> DashboardSummary:
    """Build dashboard KPIs from local repository/export metadata.

    This module remains dashboard-specific: it reads already-persisted repository
    DTOs and optional file metadata only. It does not call scanner, OCR, report,
    Clause Library, Playbook, AI summary, or export business logic.
    """

    reference_time = now or datetime.now()
    ordered = sorted(list(entries), key=_entry_datetime, reverse=True)
    total = len(ordered)
    last_30_days_cutoff = reference_time - timedelta(days=30)
    contracts_last_30_days = sum(1 for entry in ordered if _entry_datetime(entry) >= last_30_days_cutoff)
    contracts_awaiting_review = sum(1 for entry in ordered if _awaits_review(entry))
    high_risk_contracts = sum(1 for entry in ordered if entry.rating.casefold() in HIGH_RISK_RATINGS)
    critical_contracts = sum(1 for entry in ordered if entry.rating.casefold() in CRITICAL_RISK_RATINGS)
    average_risk = round(sum(entry.risk_score for entry in ordered) / total) if total else 0
    distribution = dict(Counter(entry.rating or "Unknown" for entry in ordered))
    report_files = _recent_report_files(exports_dir, recent_limit=recent_limit)

    recent_contracts = [
        RecentContract(
            scan_id=entry.scan_id,
            name=entry.source_name,
            scanned_at=entry.scanned_at,
            rating=entry.rating,
            risk_score=entry.risk_score,
            finding_count=entry.finding_count,
            categories=tuple(entry.categories[:3]),
            status=entry.status,
        )
        for entry in ordered[:recent_limit]
    ]
    recent_activity = _build_recent_activity(ordered, report_files, recent_limit=recent_limit)

    return DashboardSummary(
        total_contracts=total,
        contracts_last_30_days=contracts_last_30_days,
        contracts_awaiting_review=contracts_awaiting_review,
        high_risk_contracts=high_risk_contracts,
        critical_contracts=critical_contracts,
        average_risk=average_risk,
        risk_distribution=distribution,
        recent_contracts=recent_contracts,
        recent_reports=report_files[:recent_limit],
        recent_activity=recent_activity,
        reports_generated=_report_count(exports_dir),
        database_size_bytes=_directory_size(repository_dir),
    )


def empty_dashboard_summary() -> DashboardSummary:
    """Return an empty dashboard model for first-run experiences."""

    return DashboardSummary(
        total_contracts=0,
        contracts_last_30_days=0,
        contracts_awaiting_review=0,
        high_risk_contracts=0,
        critical_contracts=0,
        average_risk=0,
        risk_distribution={},
        recent_contracts=[],
        recent_reports=[],
        recent_activity=[],
        reports_generated=0,
        database_size_bytes=0,
    )


def _awaits_review(entry: RepositoryEntry) -> bool:
    if entry.status.casefold() in {"approved", "rejected", "closed"}:
        return False
    return entry.risk_count > 0 or entry.rating.casefold() in REVIEWABLE_RISK_RATINGS


def _entry_datetime(entry: RepositoryEntry) -> datetime:
    value = entry.scanned_at.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return datetime.min
    if parsed.tzinfo is not None:
        return parsed.replace(tzinfo=None)
    return parsed


def _recent_report_files(exports_dir: Path | str | None, *, recent_limit: int) -> list[RecentReport]:
    if exports_dir is None:
        return []
    root = Path(exports_dir)
    if not root.exists():
        return []
    candidates = [path for path in root.rglob("*") if path.is_file() and path.suffix.casefold() in REPORT_EXTENSIONS]
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [_report_from_path(path) for path in candidates[:recent_limit]]


def _report_count(exports_dir: Path | str | None) -> int:
    if exports_dir is None:
        return 0
    root = Path(exports_dir)
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file() and path.suffix.casefold() in REPORT_EXTENSIONS)


def _report_from_path(path: Path) -> RecentReport:
    exported_at = datetime.fromtimestamp(path.stat().st_mtime).replace(microsecond=0).isoformat()
    return RecentReport(
        name=path.name,
        kind=REPORT_EXTENSIONS[path.suffix.casefold()],
        exported_at=exported_at,
        path=str(path),
    )


def _directory_size(path: Path | str | None) -> int:
    if path is None:
        return 0
    root = Path(path)
    if not root.exists():
        return 0
    if root.is_file():
        return root.stat().st_size
    return sum(candidate.stat().st_size for candidate in root.rglob("*") if candidate.is_file())


def _format_bytes(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    units = ["KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        size /= 1024
        if size < 1024:
            return f"{size:.1f} {unit}"
    return f"{size:.1f} PB"


def _build_recent_activity(
    entries: list[RepositoryEntry],
    reports: list[RecentReport],
    *,
    recent_limit: int,
) -> list[RecentActivity]:
    activities = [
        RecentActivity(
            title=f"{entry.source_name} scanned",
            subtitle=f"{entry.rating} · {entry.risk_score}/100 · {entry.finding_count} findings",
            severity=entry.rating,
        )
        for entry in entries[:recent_limit]
    ]
    activities.extend(
        RecentActivity(
            title=f"Generated Report: {report.name}",
            subtitle=f"{report.kind} export · {report.exported_at}",
            severity="Info",
        )
        for report in reports[: max(0, recent_limit - len(activities))]
    )
    return activities[:recent_limit]
