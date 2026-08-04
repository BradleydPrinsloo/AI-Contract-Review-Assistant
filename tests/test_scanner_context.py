from __future__ import annotations

from contract_review_assistant.scanner import scan_chunks


RULES = [
    {
        "phrase": "indemnify",
        "aliases": ["indemnification"],
        "category": "Liability",
        "finding_type": "Risk",
        "risk": "High",
        "note": "Review the indemnity obligation.",
    }
]


def test_binding_obligation_is_detected() -> None:
    results = scan_chunks(
        [("Document", "Supplier shall indemnify Customer against third-party claims.")],
        RULES,
    )

    assert len(results) == 1
    assert results[0].confidence >= 80


def test_casual_discussion_is_suppressed() -> None:
    results = scan_chunks(
        [
            (
                "Document",
                "Indemnification was mentioned for discussion only and does not create any obligation.",
            )
        ],
        RULES,
    )

    assert results == []


def test_negated_obligation_is_suppressed() -> None:
    results = scan_chunks(
        [("Document", "The Supplier shall not indemnify the Customer under this section.")],
        RULES,
    )

    assert results == []
