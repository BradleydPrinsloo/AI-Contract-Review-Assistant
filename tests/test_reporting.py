from types import SimpleNamespace

from contract_review_assistant.reporting import build_report_html
from contract_review_assistant.scanner import ScanResult


def _assessment():
    return SimpleNamespace(total_score=42, rating="Moderate")


def _findings():
    return [
        ScanResult(
            phrase="indemnify",
            category="Indemnification",
            finding_type="Risk",
            risk="High",
            score=27,
            confidence=85,
            location="Page 4",
            note="Review the scope of defense and indemnity obligations.",
            context="Provider shall indemnify, defend, and hold harmless Client.",
            clause_library_name="Mutual Indemnity Standard",
            preferred_wording="Indemnity should be mutual, fault-based, and limited to third-party claims.",
            rejected_wording="One-way broad-form indemnity is not accepted.",
            clause_examples=["Mutual third-party indemnity"],
            clause_explanation="Negotiate toward company-approved indemnity language.",
        ),
        ScanResult(
            phrase="limitation of liability",
            category="Liability Allocation",
            finding_type="Protective",
            risk="Low",
            score=2,
            confidence=70,
            location="Page 7",
            note="Confirm the liability cap and exclusions.",
            context="Liability shall not exceed fees paid in the prior twelve months.",
        ),
    ]


def test_executive_report_emphasizes_priority_items():
    report = build_report_html(
        _findings(),
        "sample_contract.pdf",
        _assessment(),
        "ContractIQ Analysis Summary\nRecommended actions:\n- Review indemnity.",
        report_type="executive",
    )

    assert "ContractIQ Executive Risk Brief" in report
    assert "Priority Review Items" in report
    assert "sample_contract.pdf" in report
    assert "indemnify" in report
    assert "42/100" in report
    assert "Detailed Findings" not in report


def test_full_report_includes_detailed_findings():
    report = build_report_html(
        _findings(),
        "sample_contract.pdf",
        _assessment(),
        "ContractIQ Analysis Summary",
        report_type="full",
        include_findings=True,
    )

    assert "ContractIQ Contract Analysis Report" in report
    assert "Detailed Findings" in report
    assert "Indemnification" in report
    assert "Liability Allocation" in report
    assert "Clause Library Guidance" in report
    assert "Mutual Indemnity Standard" in report
    assert "Indemnity should be mutual" in report
    assert "One-way broad-form indemnity" in report
    assert "Decision-support notice" in report
    assert "ContractIQ" in report
