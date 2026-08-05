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
    status: str = "Awaiting Review",
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
        status=status,
    )


def test_dashboard_summary_calculates_milestone_one_kpis(tmp_path: Path) -> None:
    from contract_review_assistant.dashboard.metrics import build_dashboard_summary

    exports_dir = tmp_path / "exports"
    reports_dir = exports_dir / "reports"
    reports_dir.mkdir(parents=True)
    for index, suffix in enumerate(("pdf", "docx", "csv", "txt")):
        report = reports_dir / f"review-{index}.{suffix}"
        report.write_text(f"report {suffix}", encoding="utf-8")

    repository_dir = exports_dir / "repository"
    repository_dir.mkdir()
    database = repository_dir / "contractiq_repository.sqlite3"
    database.write_bytes(b"contractiq-db-bytes")

    summary = build_dashboard_summary(
        [
            _entry("Master Services", days_ago=0, rating="High", score=82, risk_count=4),
            _entry("Vendor SaaS", days_ago=4, rating="Moderate", score=47, risk_count=2, status="In Review"),
            _entry("Clean NDA", days_ago=35, rating="Low", score=12, risk_count=0, status="Approved"),
        ],
        now=datetime(2026, 8, 4, 12, 0, 0),
        exports_dir=exports_dir,
        repository_dir=repository_dir,
    )

    assert summary.total_contracts == 3
    assert summary.contracts_scanned == 3
    assert summary.average_risk == 47
    assert summary.contracts_awaiting_review == 2
    assert summary.contracts_last_30_days == 2
    assert summary.critical_contracts == 0
    assert summary.high_risk_contracts == 1
    assert summary.reports_generated == 4
    assert summary.database_size_bytes == len(b"contractiq-db-bytes")
    assert summary.database_size_label.endswith("B")
    assert summary.risk_distribution == {"High": 1, "Moderate": 1, "Low": 1}
    assert [contract.name for contract in summary.recent_contracts] == [
        "Master Services.pdf",
        "Vendor SaaS.pdf",
        "Clean NDA.pdf",
    ]
    assert summary.recent_contracts[0].scan_id == "master-services"
    assert summary.recent_contracts[1].status == "In Review"
    assert {report.kind for report in summary.recent_reports} == {"PDF", "DOCX", "CSV", "TXT"}
    assert summary.recent_activity[0].title == "Master Services.pdf scanned"


def test_milestone_one_dashboard_shell_layout_and_widgets() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QListWidget, QPushButton, QTableWidget

    from v2_main import VersionTwoContractPlatform

    app = QApplication.instance() or QApplication([])
    window = VersionTwoContractPlatform()
    window.show()
    app.processEvents()

    assert window.windowTitle() == "ContractIQ™ Platform — Version 2.5"
    assert window.pages.count() == len(window.NAV_ITEMS)
    assert [label for label, _description in window.NAV_ITEMS] == [
        "Dashboard",
        "Contracts",
        "Clause Library",
        "Playbooks",
        "Reports",
        "Repository",
        "Settings",
        "Help",
    ]

    header = window.findChild(QLabel, "appHeaderLogo")
    assert header is not None
    assert "ContractIQ" in header.text()
    assert window.findChild(QLineEdit, "globalSearchField") is not None
    assert window.findChild(QPushButton, "settingsButton") is not None
    assert window.findChild(QPushButton, "themeToggleButton") is not None

    status_text = "\n".join(label.text() for label in window.findChildren(QLabel) if label.objectName().startswith("bottomStatus"))
    assert "Ready" in status_text
    assert "Database Connected" in status_text
    assert "Version 2.5" in status_text

    dashboard = window.pages.widget(0)
    assert dashboard.objectName() == "executiveDashboardPage"
    assert dashboard.findChild(QTableWidget, "recentContractsTable") is not None
    assert dashboard.findChild(QListWidget, "recentReportsList") is not None
    assert dashboard.findChild(QLabel, "dashboardRiskGaugeValue") is not None

    card_names = {widget.objectName() for widget in dashboard.findChildren(QLabel)}
    assert {
        "quickActionsTitle",
        "statisticsTitle",
        "recentContractsTitle",
        "recentReportsTitle",
        "riskOverviewTitle",
        "recentActivityTitle",
    } <= card_names

    buttons = {button.text().replace("&", "") for button in dashboard.findChildren(QPushButton)}
    assert {
        "Scan Contract",
        "Open Repository",
        "Clause Library",
        "New Playbook",
        "Import Contracts",
    } <= buttons

    recent_contracts = dashboard.findChild(QTableWidget, "recentContractsTable")
    assert recent_contracts.contextMenuPolicy() == Qt.CustomContextMenu
    assert recent_contracts.toolTip()
    assert [recent_contracts.horizontalHeaderItem(index).text() for index in range(recent_contracts.columnCount())] == [
        "Name",
        "Risk",
        "Date",
        "Status",
    ]

    window._navigate(1)
    contracts_workspace = window.pages.widget(1)
    contract_buttons = {button.text() for button in contracts_workspace.findChildren(QPushButton)}
    assert "Open Contract" in contract_buttons
    assert "Scan Contract" in contract_buttons
    assert "Generate Report" in contract_buttons

    window.close()
