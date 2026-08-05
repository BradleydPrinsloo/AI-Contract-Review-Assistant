from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from contract_review_assistant.repository import RepositoryEntry


def _entry(
    name: str,
    *,
    days_ago: int,
    rating: str,
    score: int,
    risk_count: int,
    categories: list[str] | None = None,
) -> RepositoryEntry:
    scanned_at = (datetime(2026, 8, 4, 12, 0, 0) - timedelta(days=days_ago)).isoformat()
    return RepositoryEntry(
        scan_id=name.lower().replace(" ", "-"),
        scanned_at=scanned_at,
        source_file=str(Path("contracts") / f"{name}.pdf"),
        source_name=f"{name}.pdf",
        risk_score=score,
        rating=rating,
        finding_count=risk_count + 1,
        risk_count=risk_count,
        protective_count=1,
        neutral_count=0,
        categories=categories or ["Indemnification"],
        top_phrases=["indemnify"],
        summary=f"{name} review summary",
        findings=[],
        search_text=name,
    )


def test_dashboard_summary_calculates_enterprise_kpis() -> None:
    from contract_review_assistant.dashboard.metrics import build_dashboard_summary

    summary = build_dashboard_summary(
        [
            _entry("Master Services", days_ago=0, rating="High", score=82, risk_count=4),
            _entry("Vendor SaaS", days_ago=4, rating="Moderate", score=47, risk_count=2),
            _entry("Clean NDA", days_ago=35, rating="Low", score=12, risk_count=0),
        ]
    )

    assert summary.total_contracts == 3
    assert summary.average_risk == 47
    assert summary.contracts_awaiting_review == 2
    assert summary.contracts_last_30_days == 2
    assert summary.high_risk_contracts == 1
    assert summary.risk_distribution == {"High": 1, "Moderate": 1, "Low": 1}
    assert [contract.name for contract in summary.recent_contracts] == [
        "Master Services.pdf",
        "Vendor SaaS.pdf",
        "Clean NDA.pdf",
    ]
    assert summary.recent_activity[0].title == "Master Services.pdf scanned"


def test_version_25_platform_uses_separate_executive_dashboard() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    from v2_main import VersionTwoContractPlatform

    app = QApplication.instance() or QApplication([])
    window = VersionTwoContractPlatform()
    window.show()
    app.processEvents()

    assert window.windowTitle() == "ContractIQ™ Platform — Version 2.5"
    assert window.pages.count() == len(window.NAV_ITEMS)

    dashboard = window.pages.widget(0)
    assert dashboard.objectName() == "executiveDashboardPage"
    dashboard_buttons = {button.text() for button in dashboard.findChildren(QPushButton)}
    assert "Open Contract" not in dashboard_buttons
    assert "Scan Contract" not in dashboard_buttons
    assert "Generate Report" not in dashboard_buttons

    label_text = "\n".join(label.text() for label in dashboard.findChildren(QLabel))
    assert "Executive Dashboard" in label_text
    assert "Average Risk" in label_text
    assert "Contracts Awaiting Review" in label_text
    assert "Risk Distribution" in label_text

    window._navigate(1)
    contracts_workspace = window.pages.widget(1)
    contract_buttons = {button.text() for button in contracts_workspace.findChildren(QPushButton)}
    assert "Open Contract" in contract_buttons
    assert "Scan Contract" in contract_buttons
    assert "Generate Report" in contract_buttons

    window.close()
