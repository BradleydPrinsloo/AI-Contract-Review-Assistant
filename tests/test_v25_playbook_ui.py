from __future__ import annotations

import os
from uuid import uuid4

import pytest


def test_playbook_page_replaces_placeholder_and_exposes_editor_controls() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget, QTextEdit, QLineEdit, QComboBox

    from v2_main import VersionTwoContractPlatform

    app = QApplication.instance() or QApplication([])
    window = VersionTwoContractPlatform()
    window._navigate(4)
    window.show()
    app.processEvents()

    page = window.pages.widget(4)
    assert page.objectName() == "playbookPage"
    assert window.playbook_page is page

    labels = "\n".join(label.text() for label in page.findChildren(QLabel))
    assert "Playbooks" in labels
    assert "Contract Type" in labels
    assert "Risk Tolerance" in labels
    assert "Clause Standards" in labels
    assert "Checklist Items" in labels

    tables = {table.objectName() for table in page.findChildren(QTableWidget)}
    assert {"playbookTable", "playbookClauseRulesTable"} <= tables

    line_fields = {field.objectName() for field in page.findChildren(QLineEdit)}
    assert {"playbookSearchField", "playbookNameField", "playbookContractTypeField"} <= line_fields

    combo_fields = {field.objectName() for field in page.findChildren(QComboBox)}
    assert {
        "playbookRiskToleranceField",
        "playbookStatusField",
        "playbookFilterRiskToleranceField",
        "playbookClauseStandardSelector",
        "playbookClauseRequirementField",
    } <= combo_fields

    text_fields = {field.objectName() for field in page.findChildren(QTextEdit)}
    assert {
        "playbookDescriptionField",
        "playbookClauseGuidanceField",
        "playbookChecklistField",
    } <= text_fields

    buttons = {button.text() for button in page.findChildren(QPushButton)}
    assert {
        "New Playbook",
        "Save Playbook",
        "Archive Playbook",
        "Add Clause Standard",
        "Remove Clause Standard",
    } <= buttons

    window.close()


def test_playbook_page_can_save_clause_backed_playbook_offscreen() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    from v2_main import VersionTwoContractPlatform

    app = QApplication.instance() or QApplication([])
    window = VersionTwoContractPlatform()
    window._navigate(4)
    page = window.playbook_page
    suffix = uuid4().hex[:8]
    page._new_playbook()

    clause = window.clause_library_service.create_clause(
        name=f"Smoke Pay-if-Paid Guardrail {suffix}",
        category="Payment Exposure",
        risk_level="High",
        company_wording="Payment obligations must not depend solely on owner payment.",
        rejected_wording="Payment is due only if and when owner pays contractor.",
    )
    page.refresh_clause_options()
    playbook_name = f"Smoke Construction Subcontract {suffix}"
    page.name_field.setText(playbook_name)
    page.contract_type_field.setText("Construction Subcontract")
    page.risk_tolerance_field.setCurrentText("Conservative")
    page.status_field.setCurrentText("Active")
    page.description_field.setPlainText("Smoke playbook for subcontract payment review.")
    page.clause_selector.setCurrentText(f"{clause.name} — {clause.category}")
    page.clause_requirement_field.setCurrentText("Required")
    page.clause_guidance_field.setPlainText("Escalate one-sided pay-if-paid language.")
    page._add_clause_rule()
    page.checklist_field.setPlainText("Confirm payment trigger wording|Required|Reviewer|Escalate if owner-pay-only")
    page._save_playbook()

    matches = [playbook for playbook in page.service.search() if playbook.name == playbook_name]
    assert matches
    saved = matches[0]
    assert saved.name == playbook_name
    assert saved.clause_rules[0].clause_id == clause.clause_id
    assert saved.checklist_items[0].text == "Confirm payment trigger wording"
    assert page.table.rowCount() >= 1

    window.close()
