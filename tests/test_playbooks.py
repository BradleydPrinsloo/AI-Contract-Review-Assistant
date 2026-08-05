from __future__ import annotations

from pathlib import Path

import pytest


def _clause_service(tmp_path: Path):
    from contract_review_assistant.clauses import ClauseLibraryService

    service = ClauseLibraryService(tmp_path / "clauses.sqlite3")
    insurance = service.create_clause(
        name="Project-Specific Additional Insured",
        category="Insurance Burden",
        risk_level="High",
        company_wording="Additional insured status must be project-specific and tied to the work.",
        rejected_wording="Blanket additional insured status applies to all operations.",
        examples=["Attach CG 20 10 and CG 20 37 endorsements."],
    )
    payment = service.create_clause(
        name="Retainage Release Standard",
        category="Payment Exposure",
        risk_level="Elevated",
        company_wording="Retainage must release after substantial completion and acceptance.",
        rejected_wording="Owner may hold retainage indefinitely.",
        examples=["Release retainage within 30 days of acceptance."],
    )
    return service, insurance, payment


def test_playbook_crud_search_archive_and_history(tmp_path: Path) -> None:
    from contract_review_assistant.playbooks import (
        PlaybookChecklistItem,
        PlaybookClauseRule,
        PlaybookLibraryService,
        PlaybookSearchFilters,
    )

    clause_service, insurance, payment = _clause_service(tmp_path)
    service = PlaybookLibraryService(
        tmp_path / "playbooks.sqlite3",
        clause_library_service=clause_service,
    )

    created = service.create_playbook(
        name="Construction Subcontract Playbook",
        description="Default review standard for subcontract risk triage.",
        contract_type="Construction Subcontract",
        risk_tolerance="Conservative",
        clause_rules=[
            PlaybookClauseRule(
                clause_id=insurance.clause_id,
                requirement_level="Required",
                guidance="Escalate if endorsements are missing or blanket-only.",
            )
        ],
        checklist_items=[
            PlaybookChecklistItem(
                text="Confirm certificate of insurance and endorsements are attached.",
                required=True,
                owner_role="Reviewer",
                escalation="Escalate missing COI before signature.",
            )
        ],
        status="Active",
    )

    assert service.database_path.exists()
    assert created.playbook_id
    assert created.active is True
    assert created.version == 1
    assert created.clause_rules[0].clause_id == insurance.clause_id
    assert created.checklist_items[0].required is True

    updated = service.update_playbook(
        created.playbook_id,
        risk_tolerance="Balanced",
        clause_rules=[
            *created.clause_rules,
            PlaybookClauseRule(
                clause_id=payment.clause_id,
                requirement_level="Preferred",
                guidance="Use the retainage release standard when payment terms are one-sided.",
            ),
        ],
        checklist_items=[
            *created.checklist_items,
            PlaybookChecklistItem(
                text="Check retainage release and pay-if-paid conditions.",
                required=False,
                owner_role="Commercial",
                escalation="Escalate indefinite retainage to leadership.",
            ),
        ],
    )

    assert updated.version == 2
    assert updated.risk_tolerance == "Balanced"
    assert [rule.clause_id for rule in updated.clause_rules] == [insurance.clause_id, payment.clause_id]

    matches = service.search(
        PlaybookSearchFilters(query="retainage endorsements", contract_type="subcontract", risk_tolerance="Balanced")
    )
    assert [playbook.playbook_id for playbook in matches] == [created.playbook_id]

    service.archive_playbook(created.playbook_id)
    assert service.get_playbook(created.playbook_id).active is False
    assert service.search(PlaybookSearchFilters(include_archived=False)) == []
    assert service.search(PlaybookSearchFilters(include_archived=True))[0].playbook_id == created.playbook_id

    history = service.history(created.playbook_id)
    assert [item.action for item in history] == ["created", "updated", "archived"]
    assert history[0].snapshot["contract_type"] == "Construction Subcontract"
    assert history[-1].version == 3


def test_playbook_validation_and_clause_reference_checks(tmp_path: Path) -> None:
    from contract_review_assistant.playbooks import (
        PlaybookChecklistItem,
        PlaybookClauseRule,
        PlaybookLibraryService,
        PlaybookValidationError,
    )

    clause_service, insurance, _payment = _clause_service(tmp_path)
    service = PlaybookLibraryService(
        tmp_path / "playbooks.sqlite3",
        clause_library_service=clause_service,
    )

    with pytest.raises(PlaybookValidationError, match="Playbook name is required"):
        service.create_playbook(
            name="",
            description="Missing name.",
            contract_type="Construction Subcontract",
            risk_tolerance="Conservative",
        )

    with pytest.raises(PlaybookValidationError, match="Unsupported risk tolerance"):
        service.create_playbook(
            name="Bad Risk Tolerance",
            description="Invalid tolerance.",
            contract_type="Construction Subcontract",
            risk_tolerance="Aggressive",
        )

    with pytest.raises(PlaybookValidationError, match="Unsupported clause requirement"):
        service.create_playbook(
            name="Bad Clause Rule",
            description="Invalid rule level.",
            contract_type="Construction Subcontract",
            risk_tolerance="Balanced",
            clause_rules=[PlaybookClauseRule(clause_id=insurance.clause_id, requirement_level="Maybe")],
        )

    with pytest.raises(PlaybookValidationError, match="Checklist item text is required"):
        service.create_playbook(
            name="Bad Checklist",
            description="Invalid checklist.",
            contract_type="Construction Subcontract",
            risk_tolerance="Balanced",
            checklist_items=[PlaybookChecklistItem(text="")],
        )

    with pytest.raises(PlaybookValidationError, match="Clause standard does not exist"):
        service.create_playbook(
            name="Unknown Clause",
            description="References a missing clause.",
            contract_type="Construction Subcontract",
            risk_tolerance="Balanced",
            clause_rules=[PlaybookClauseRule(clause_id="missing-clause", requirement_level="Required")],
        )

    with pytest.raises(PlaybookValidationError, match="Duplicate clause standard"):
        service.create_playbook(
            name="Duplicate Clause",
            description="References the same clause twice.",
            contract_type="Construction Subcontract",
            risk_tolerance="Balanced",
            clause_rules=[
                PlaybookClauseRule(clause_id=insurance.clause_id, requirement_level="Required"),
                PlaybookClauseRule(clause_id=insurance.clause_id, requirement_level="Preferred"),
            ],
        )
