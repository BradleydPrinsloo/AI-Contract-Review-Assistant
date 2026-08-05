from __future__ import annotations

import os

import pytest


def test_selected_finding_surfaces_clause_library_guidance() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from contract_review_assistant.risk_engine import calculate_risk_assessment
    from contract_review_assistant.scanner import ScanResult
    from main import ContractScannerApp

    app = QApplication.instance() or QApplication([])
    window = ContractScannerApp()
    window.current_file = "sample-contract.txt"
    window.results = [
        ScanResult(
            phrase="additional insured",
            category="Insurance Burden",
            finding_type="Risk",
            risk="High",
            score=0,
            confidence=90,
            location="Document",
            note="Review additional insured obligations.",
            context="Contractor shall name Owner as additional insured on all policies.",
            clause_library_id="clause-123",
            clause_library_name="Additional Insured Guardrail",
            preferred_wording="Additional insured status must be project-specific and time-limited.",
            rejected_wording="Blanket additional insured status for all policies is not accepted.",
            clause_examples=["Project-specific endorsement", "Ongoing operations only"],
            clause_explanation="Narrow the obligation before signature.",
        )
    ]
    window.assessment = calculate_risk_assessment(window.results)
    window.summary = "summary"
    window.refresh_dashboard()
    window.table.selectRow(0)
    window.show_selected_finding()

    headers = [
        window.table.horizontalHeaderItem(index).text()
        for index in range(window.table.columnCount())
    ]
    assert "Library Standard" in headers
    library_column = headers.index("Library Standard")
    assert window.table.item(0, library_column).text() == "Additional Insured Guardrail"

    detail = window.detail_view.toPlainText()

    assert "Clause Library Guidance" in detail
    assert "Additional Insured Guardrail" in detail
    assert "Approved wording" in detail
    assert "Additional insured status must be project-specific" in detail
    assert "Rejected wording" in detail
    assert "Blanket additional insured status" in detail
    assert "Examples" in detail
    assert "Narrow the obligation" in detail

    window.close()
