from __future__ import annotations

import os

import pytest


def test_contracts_workspace_is_modular_and_action_focused() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPushButton

    from v2_main import VersionTwoContractPlatform

    app = QApplication.instance() or QApplication([])
    window = VersionTwoContractPlatform()
    window._navigate(1)
    window.show()
    app.processEvents()

    workspace = window.pages.widget(1)
    assert workspace.objectName() == "contractsWorkspacePage"

    panels = {panel.objectName() for panel in workspace.findChildren(QFrame)}
    assert "contractWorkflowPanel" in panels
    assert "contractMetricsPanel" in panels
    assert "contractFindingsPanel" in panels
    assert "contractSummaryPanel" in panels

    labels = "\n".join(label.text() for label in workspace.findChildren(QLabel))
    assert "Contracts Workspace" in labels
    assert "Open, scan, review, and report from one controlled workspace." in labels
    assert "1. Open" in labels
    assert "2. Scan" in labels
    assert "3. Review" in labels
    assert "4. Report" in labels

    buttons = {button.text() for button in workspace.findChildren(QPushButton)}
    assert {"Open Contract", "Scan Contract", "ContractIQ Summary", "Generate Report"} <= buttons
    assert "Export Word" not in {button.text() for button in workspace.findChildren(QPushButton) if button.isVisible()}
    assert "Export CSV" not in {button.text() for button in workspace.findChildren(QPushButton) if button.isVisible()}
    assert "Export Text" not in {button.text() for button in workspace.findChildren(QPushButton) if button.isVisible()}

    assert window.analyze_btn.isEnabled() is False
    assert window.generate_report_btn is not None
    assert window.generate_report_btn.isEnabled() is False

    window.close()


def test_contracts_workspace_preserves_scan_action_state_after_file_selection() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from v2_main import VersionTwoContractPlatform

    app = QApplication.instance() or QApplication([])
    window = VersionTwoContractPlatform()
    window._navigate(1)
    window.show()
    app.processEvents()

    window.current_file = "sample-contract.pdf"
    window.contract_value.setText("sample-contract.pdf")
    window.set_actions_enabled(False)

    assert window.open_btn.text() == "Open Contract"
    assert window.analyze_btn.text() == "Scan Contract"
    assert window.analyze_btn.isEnabled() is True
    assert window.summary_btn.isEnabled() is False
    assert window.generate_report_btn is not None
    assert window.generate_report_btn.isEnabled() is False

    window.close()
