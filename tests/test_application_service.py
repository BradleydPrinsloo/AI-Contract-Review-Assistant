from __future__ import annotations

import json
from pathlib import Path

import pytest

from contract_review_assistant.application_service import ContractAnalysisService


def write_rules(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "phrase": "indemnify",
                    "aliases": ["indemnification"],
                    "category": "Liability",
                    "finding_type": "Risk",
                    "risk": "High",
                    "note": "Review the indemnity obligation.",
                }
            ]
        ),
        encoding="utf-8",
    )


def test_analyze_txt_contract_returns_ui_independent_result(tmp_path: Path) -> None:
    rules = tmp_path / "keywords.json"
    contract = tmp_path / "contract.txt"
    write_rules(rules)
    contract.write_text(
        "Supplier shall indemnify Customer against third-party claims.",
        encoding="utf-8",
    )

    progress_events: list[tuple[str, int]] = []
    service = ContractAnalysisService(
        rules,
        summary_provider=lambda results, assessment: (
            f"Found {len(results)} item(s); score {assessment.total_score}."
        ),
    )

    analysis = service.analyze(
        contract,
        progress=lambda message, value: progress_events.append((message, value)),
    )

    assert analysis.source_file == str(contract)
    assert len(analysis.results) == 1
    assert analysis.results[0].phrase == "indemnify"
    assert analysis.risk_assessment.finding_count == 1
    assert "Found 1 item" in analysis.summary_text
    assert progress_events[0][1] == 10
    assert progress_events[-1] == ("Analysis complete.", 100)


def test_reassess_supports_false_positive_workflow(tmp_path: Path) -> None:
    rules = tmp_path / "keywords.json"
    contract = tmp_path / "contract.txt"
    write_rules(rules)
    contract.write_text("Supplier shall indemnify Customer.", encoding="utf-8")

    service = ContractAnalysisService(
        rules,
        summary_provider=lambda results, assessment: f"{len(results)} findings",
    )
    initial = service.analyze(contract)
    revised = service.reassess(contract, [])

    assert initial.risk_assessment.finding_count == 1
    assert revised.risk_assessment.finding_count == 0
    assert revised.summary_text == "0 findings"


def test_missing_contract_is_reported_clearly(tmp_path: Path) -> None:
    rules = tmp_path / "keywords.json"
    write_rules(rules)
    service = ContractAnalysisService(rules, summary_provider=lambda _r, _a: "")

    with pytest.raises(FileNotFoundError, match="Contract file does not exist"):
        service.analyze(tmp_path / "missing.txt")


def test_empty_contract_returns_zero_finding_analysis(tmp_path: Path) -> None:
    rules = tmp_path / "keywords.json"
    contract = tmp_path / "empty.txt"
    write_rules(rules)
    contract.write_text("", encoding="utf-8")
    service = ContractAnalysisService(
        rules,
        summary_provider=lambda results, assessment: (
            f"{len(results)} findings; score {assessment.total_score}"
        ),
    )

    analysis = service.analyze(contract)

    assert analysis.source_file == str(contract)
    assert analysis.results == []
    assert analysis.risk_assessment.finding_count == 0
    assert analysis.risk_assessment.total_score == 0
    assert analysis.summary_text == "0 findings; score 0"
