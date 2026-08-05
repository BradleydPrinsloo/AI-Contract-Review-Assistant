from __future__ import annotations

import os

import pytest


def test_clause_library_page_replaces_placeholder_module() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget, QTextEdit, QLineEdit, QComboBox

    from v2_main import VersionTwoContractPlatform

    app = QApplication.instance() or QApplication([])
    window = VersionTwoContractPlatform()
    window._navigate(3)
    window.show()
    app.processEvents()

    page = window.pages.widget(3)
    assert page.objectName() == "clauseLibraryPage"

    labels = "\n".join(label.text() for label in page.findChildren(QLabel))
    assert "Clause Library" in labels
    assert "Company Wording" in labels
    assert "Rejected Wording" in labels
    assert "Examples" in labels
    assert "AI Explanation" in labels

    tables = {table.objectName() for table in page.findChildren(QTableWidget)}
    assert "clauseLibraryTable" in tables

    line_fields = {field.objectName() for field in page.findChildren(QLineEdit)}
    assert {"clauseNameField", "clauseCategoryField", "clauseSearchField"} <= line_fields

    combo_fields = {field.objectName() for field in page.findChildren(QComboBox)}
    assert {"clauseRiskField", "clauseStatusFilter"} <= combo_fields

    text_fields = {field.objectName() for field in page.findChildren(QTextEdit)}
    assert {
        "clauseCompanyWordingField",
        "clauseRejectedWordingField",
        "clauseExamplesField",
        "clauseExplanationField",
    } <= text_fields

    buttons = {button.text() for button in page.findChildren(QPushButton)}
    assert {"New Clause", "Save Clause", "Archive Clause", "Explain Clause"} <= buttons

    window.close()
