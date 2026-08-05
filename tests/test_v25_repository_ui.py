from __future__ import annotations

import os

import pytest


def test_repository_dialog_exposes_enterprise_database_filters() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit

    from v2_main import VersionTwoContractPlatform

    app = QApplication.instance() or QApplication([])
    window = VersionTwoContractPlatform()
    dialog = window.repository_dialog

    text_filters = {field.objectName() for field in dialog.findChildren(QLineEdit)}
    assert {
        "repositorySearchBox",
        "repositoryVendorFilter",
        "repositoryClientFilter",
        "repositoryReviewerFilter",
        "repositoryDepartmentFilter",
        "repositoryTagFilter",
        "repositoryVersionFilter",
    } <= text_filters

    combo_filters = {field.objectName() for field in dialog.findChildren(QComboBox)}
    assert {"repositoryRiskFilter", "repositoryStatusFilter"} <= combo_filters

    headers = [
        dialog.table.horizontalHeaderItem(index).text()
        for index in range(dialog.table.columnCount())
    ]
    assert headers == [
        "Scanned",
        "Contract",
        "Vendor",
        "Client",
        "Reviewer",
        "Status",
        "Risk",
        "Score",
        "Department",
        "Review Date",
        "Version",
        "Tags",
    ]

    window.close()
