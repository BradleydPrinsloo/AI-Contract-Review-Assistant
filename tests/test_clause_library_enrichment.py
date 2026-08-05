from __future__ import annotations

import json
from pathlib import Path

from contract_review_assistant.application_service import ContractAnalysisService
from contract_review_assistant.clauses import ClauseLibraryService


def _write_rules(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "phrase": "additional insured",
                    "aliases": ["additional-insured endorsement"],
                    "category": "Insurance Burden",
                    "finding_type": "Risk",
                    "risk": "High",
                    "note": "Review additional insured obligations and duration.",
                }
            ]
        ),
        encoding="utf-8",
    )


def test_contract_analysis_enriches_findings_with_clause_library_guidance(tmp_path: Path) -> None:
    rules = tmp_path / "keywords.json"
    contract = tmp_path / "subcontract.txt"
    _write_rules(rules)
    contract.write_text(
        "Contractor shall name Owner as additional insured on all general liability policies.",
        encoding="utf-8",
    )

    clause_service = ClauseLibraryService(tmp_path / "clause-library.sqlite3")
    clause = clause_service.create_clause(
        name="Additional Insured Guardrail",
        category="Insurance Burden",
        risk_level="High",
        company_wording="Additional insured status must be limited to ongoing operations and project-specific claims.",
        rejected_wording="Contractor shall name Owner as additional insured on all policies without limitation.",
        examples=["additional insured endorsement", "project-specific insurance obligation"],
        ai_explanation="Use the approved wording to narrow insurance obligations before signature.",
    )

    service = ContractAnalysisService(
        rules,
        clause_library_service=clause_service,
        summary_provider=lambda results, _assessment: results[0].preferred_wording,
    )

    analysis = service.analyze(contract)

    assert len(analysis.results) == 1
    finding = analysis.results[0]
    assert finding.clause_library_id == clause.clause_id
    assert finding.clause_library_name == "Additional Insured Guardrail"
    assert finding.preferred_wording == clause.company_wording
    assert finding.rejected_wording == clause.rejected_wording
    assert finding.clause_examples == clause.examples
    assert finding.clause_explanation == clause.ai_explanation
    assert analysis.summary_text == clause.company_wording


def test_contract_analysis_leaves_findings_unenriched_without_matching_clause(tmp_path: Path) -> None:
    rules = tmp_path / "keywords.json"
    contract = tmp_path / "subcontract.txt"
    _write_rules(rules)
    contract.write_text(
        "Contractor shall name Owner as additional insured on all general liability policies.",
        encoding="utf-8",
    )
    clause_service = ClauseLibraryService(tmp_path / "clause-library.sqlite3")
    clause_service.create_clause(
        name="Payment Timing Standard",
        category="Payment / Retainage",
        risk_level="Medium",
        company_wording="Payment should be due within thirty days after approval.",
    )

    service = ContractAnalysisService(
        rules,
        clause_library_service=clause_service,
        summary_provider=lambda _results, _assessment: "summary",
    )

    finding = service.analyze(contract).results[0]

    assert finding.clause_library_id == ""
    assert finding.preferred_wording == ""
    assert finding.rejected_wording == ""
    assert finding.clause_examples == []
