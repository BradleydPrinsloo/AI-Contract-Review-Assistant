from __future__ import annotations

from pathlib import Path

import pytest


class FakeExplanationProvider:
    def explain(self, clause) -> str:
        return f"Provider explanation for {clause.name}: negotiate from approved wording."


def test_clause_library_crud_search_and_history(tmp_path: Path) -> None:
    from contract_review_assistant.clauses import (
        ClauseLibraryService,
        ClauseSearchFilters,
    )

    service = ClauseLibraryService(tmp_path / "clauses.sqlite3")
    created = service.create_clause(
        name="Mutual Indemnity",
        category="Indemnification",
        risk_level="High",
        company_wording="Each party indemnifies the other for third-party claims caused by its negligence.",
        rejected_wording="Supplier indemnifies customer for all claims regardless of fault.",
        examples=["Mutual third-party indemnity", "Fault-based defense obligation"],
        ai_explanation="Prefer mutual, fault-based indemnity language.",
    )

    assert created.clause_id
    assert created.active is True
    assert created.examples == ["Mutual third-party indemnity", "Fault-based defense obligation"]

    updated = service.update_clause(
        created.clause_id,
        risk_level="Critical",
        rejected_wording="Supplier indemnifies customer for all claims, including customer negligence.",
        examples=["One-way broad-form indemnity"],
    )

    assert updated.risk_level == "Critical"
    assert updated.version == 2
    assert updated.rejected_wording.startswith("Supplier indemnifies")

    matches = service.search(
        ClauseSearchFilters(query="broad-form", category="indemn", risk_level="Critical")
    )
    assert [clause.clause_id for clause in matches] == [created.clause_id]

    service.archive_clause(created.clause_id)
    assert service.get_clause(created.clause_id).active is False
    assert service.search(ClauseSearchFilters(include_archived=False)) == []
    assert service.search(ClauseSearchFilters(include_archived=True))[0].clause_id == created.clause_id

    history = service.history(created.clause_id)
    assert [item.action for item in history] == ["created", "updated", "archived"]
    assert history[0].version == 1
    assert history[1].version == 2


def test_clause_library_validates_required_fields_and_risk_levels(tmp_path: Path) -> None:
    from contract_review_assistant.clauses import ClauseLibraryService, ClauseValidationError

    service = ClauseLibraryService(tmp_path / "clauses.sqlite3")

    with pytest.raises(ClauseValidationError, match="Clause name is required"):
        service.create_clause(
            name="",
            category="Payment",
            risk_level="High",
            company_wording="Pay within 30 days.",
        )

    with pytest.raises(ClauseValidationError, match="Unsupported risk level"):
        service.create_clause(
            name="Payment Term",
            category="Payment",
            risk_level="Severe",
            company_wording="Pay within 30 days.",
        )

    with pytest.raises(ClauseValidationError, match="Company wording is required"):
        service.create_clause(
            name="Payment Term",
            category="Payment",
            risk_level="High",
            company_wording="",
        )


def test_clause_library_uses_explanation_provider_abstraction(tmp_path: Path) -> None:
    from contract_review_assistant.clauses import ClauseLibraryService

    service = ClauseLibraryService(
        tmp_path / "clauses.sqlite3",
        explanation_provider=FakeExplanationProvider(),
    )
    clause = service.create_clause(
        name="Termination for Convenience",
        category="Termination",
        risk_level="Elevated",
        company_wording="Termination for convenience requires thirty days' notice and payment for work performed.",
        rejected_wording="Customer may terminate immediately without payment.",
    )

    explained = service.explain_clause(clause.clause_id)

    assert explained.ai_explanation == (
        "Provider explanation for Termination for Convenience: negotiate from approved wording."
    )
    assert service.get_clause(clause.clause_id).ai_explanation == explained.ai_explanation
    assert service.history(clause.clause_id)[-1].action == "explained"
