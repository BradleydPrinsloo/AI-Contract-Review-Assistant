from __future__ import annotations

"""Executive dashboard domain model and KPI calculations for ContractIQ."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from contract_review_assistant.repository import RepositoryEntry

HIGH_RISK_RATINGS = {"critical", "high", "elevated"}
REVIEWABLE_RISK_RATINGS = {"critical", "high", "elevated", "moderate", "medium"}


@dataclass(frozen=True)
class RecentContract:
    """Compact contract row used by the executive dashboard."""

    name: str
    scanned_at: str
    rating: str
    risk_score: int
    finding_count: int
    categories: tuple[str, ...]


@dataclass(frozen=True)
class RecentActivity:
    """Human-readable timeline item for recent platform activity."""

    title: str
    subtitle: str
    severity: str


@dataclass(frozen=True)
class DashboardSummary:
    """Aggregated metrics displayed on the Version 2.5 executive dashboard."""

    total_contracts: int
    contracts_last_30_days: int
    contracts_awaiting_review: int
    high_risk_contracts: int
    average_risk: int
    risk_distribution: dict[str, int]
    recent_contracts: list[RecentContract]
    recent_activity: list[RecentActivity]

    @property
    def completion_rate(self) -> int:
        """Approximate review-throughput indicator until formal workflow states exist."""

        if self.total_contracts == 0:
            return 0
        completed = max(0, self.total_contracts - self.contracts_awaiting_review)
        return round((completed / self.total_contracts) * 100)


def build_dashboard_summary(
    entries: Iterable[RepositoryEntry],
    *,
    now: datetime | None = None,
    recent_limit: int = 6,
) -> DashboardSummary:
    """Build executive dashboard KPIs from repository entries.

    The current repository model does not yet store approval status. Until the
    Phase 8 workflow module introduces explicit states, a contract is treated as
    awaiting review when it contains risk findings or carries a moderate-or-worse
    rating. This keeps the KPI useful without inventing unavailable data.
    """

    reference_time = now or datetime.now()
    ordered = sorted(list(entries), key=_entry_datetime, reverse=True)
    total = len(ordered)
    last_30_days_cutoff = reference_time - timedelta(days=30)
    contracts_last_30_days = sum(1 for entry in ordered if _entry_datetime(entry) >= last_30_days_cutoff)
    contracts_awaiting_review = sum(1 for entry in ordered if _awaits_review(entry))
    high_risk_contracts = sum(1 for entry in ordered if entry.rating.casefold() in HIGH_RISK_RATINGS)
    average_risk = round(sum(entry.risk_score for entry in ordered) / total) if total else 0
    distribution = dict(Counter(entry.rating or "Unknown" for entry in ordered))

    recent_contracts = [
        RecentContract(
            name=entry.source_name,
            scanned_at=entry.scanned_at,
            rating=entry.rating,
            risk_score=entry.risk_score,
            finding_count=entry.finding_count,
            categories=tuple(entry.categories[:3]),
        )
        for entry in ordered[:recent_limit]
    ]
    recent_activity = [
        RecentActivity(
            title=f"{entry.source_name} scanned",
            subtitle=f"{entry.rating} · {entry.risk_score}/100 · {entry.finding_count} findings",
            severity=entry.rating,
        )
        for entry in ordered[:recent_limit]
    ]

    return DashboardSummary(
        total_contracts=total,
        contracts_last_30_days=contracts_last_30_days,
        contracts_awaiting_review=contracts_awaiting_review,
        high_risk_contracts=high_risk_contracts,
        average_risk=average_risk,
        risk_distribution=distribution,
        recent_contracts=recent_contracts,
        recent_activity=recent_activity,
    )


def empty_dashboard_summary() -> DashboardSummary:
    """Return an empty dashboard model for first-run experiences."""

    return DashboardSummary(
        total_contracts=0,
        contracts_last_30_days=0,
        contracts_awaiting_review=0,
        high_risk_contracts=0,
        average_risk=0,
        risk_distribution={},
        recent_contracts=[],
        recent_activity=[],
    )


def _awaits_review(entry: RepositoryEntry) -> bool:
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
