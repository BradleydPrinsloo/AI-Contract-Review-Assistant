from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from contract_review_assistant.repository import RepositoryEntry, build_repository_entry, load_repository_entries, record_scan
from contract_review_assistant.scanner import ScanResult


def _entry(
    scan_id: str,
    *,
    source_name: str,
    rating: str,
    risk_score: int,
    vendor: str = "",
    client: str = "",
    reviewer: str = "",
    status: str = "Awaiting Review",
    tags: list[str] | None = None,
    department: str = "Legal",
    review_date: str = "2026-08-05",
    version: str = "1.0",
) -> RepositoryEntry:
    return RepositoryEntry(
        scan_id=scan_id,
        scanned_at=f"2026-08-05T0{len(scan_id)}:00:00",
        source_file=str(Path("contracts") / source_name),
        source_name=source_name,
        risk_score=risk_score,
        rating=rating,
        finding_count=2,
        risk_count=1,
        protective_count=1,
        neutral_count=0,
        categories=["Payment", "Insurance"],
        top_phrases=["pay when paid"],
        summary=f"{source_name} summary for {vendor}",
        findings=[
            {
                "phrase": "pay when paid",
                "category": "Payment",
                "finding_type": "Risk",
                "risk": rating,
                "score": risk_score,
                "confidence": 90,
                "location": "Page 1",
                "note": "Review payment timing.",
                "context": "Payment depends on upstream payment.",
                "reason": "Matched configured rule",
            }
        ],
        search_text=" ".join([source_name, vendor, client, reviewer, department, rating]),
        vendor=vendor,
        client=client,
        reviewer=reviewer,
        status=status,
        tags=tags or [],
        department=department,
        review_date=review_date,
        version=version,
    )


def test_sqlite_repository_persists_contract_metadata_and_filters(tmp_path: Path) -> None:
    from contract_review_assistant.repository_database import (
        ContractRepositoryDatabase,
        RepositoryFilters,
        repository_database_path,
    )

    repository_dir = tmp_path / "repository"
    database = ContractRepositoryDatabase(repository_dir)
    database.upsert(_entry("msa", source_name="MSA.pdf", rating="High", risk_score=82, vendor="Acme", client="Prinsloo Group", reviewer="Alex", status="Awaiting Review", tags=["msa", "renewal"], department="Procurement", version="2"))
    database.upsert(_entry("nda", source_name="NDA.pdf", rating="Low", risk_score=12, vendor="Beta", client="Prinsloo Group", reviewer="Morgan", status="Approved", tags=["nda"], department="Legal", version="1"))

    assert repository_database_path(repository_dir).exists()

    high_risk = database.search(RepositoryFilters(query="acme payment", risk="High", status="Awaiting Review", vendor="acme", client="prinsloo", reviewer="alex", department="procurement", tag="renewal", version="2"))

    assert [entry.source_name for entry in high_risk] == ["MSA.pdf"]
    assert high_risk[0].vendor == "Acme"
    assert high_risk[0].client == "Prinsloo Group"
    assert high_risk[0].reviewer == "Alex"
    assert high_risk[0].status == "Awaiting Review"
    assert high_risk[0].tags == ["msa", "renewal"]
    assert high_risk[0].department == "Procurement"
    assert high_risk[0].version == "2"

    approved = database.search(RepositoryFilters(status="Approved"))
    assert [entry.source_name for entry in approved] == ["NDA.pdf"]


def test_load_repository_entries_imports_legacy_json_records_once(tmp_path: Path) -> None:
    from contract_review_assistant.repository_database import repository_database_path

    repository_dir = tmp_path / "repository"
    repository_dir.mkdir()
    legacy_entry = _entry("legacy", source_name="Legacy Vendor Agreement.pdf", rating="Moderate", risk_score=54, vendor="LegacyCo", client="ClientCo", reviewer="Jamie", status="In Review", tags=["legacy"], department="Operations")
    (repository_dir / "legacy.json").write_text(json.dumps(asdict(legacy_entry)), encoding="utf-8")

    first_load = load_repository_entries(repository_dir)
    second_load = load_repository_entries(repository_dir)

    assert repository_database_path(repository_dir).exists()
    assert [entry.scan_id for entry in first_load] == ["legacy"]
    assert [entry.scan_id for entry in second_load] == ["legacy"]
    assert second_load[0].vendor == "LegacyCo"
    assert second_load[0].status == "In Review"
    assert second_load[0].tags == ["legacy"]


def test_record_scan_writes_database_entry_with_default_metadata(tmp_path: Path) -> None:
    from contract_review_assistant.repository_database import repository_database_path

    repository_dir = tmp_path / "repository"
    result = ScanResult(
        phrase="additional insured",
        category="Insurance",
        finding_type="Risk",
        risk="High",
        score=65,
        confidence=92,
        location="Page 2",
        note="Confirm insurance obligations.",
        context="Supplier shall name Customer as additional insured.",
    )
    assessment = SimpleNamespace(
        total_score=65,
        rating="High",
        finding_count=1,
        risk_count=1,
        protective_count=0,
        neutral_count=0,
    )

    database_path = record_scan(
        "Vendor Master Agreement.pdf",
        [result],
        assessment,
        "High-risk insurance issue.",
        repository_dir,
        scanned_at="2026-08-05T12:00:00",
    )
    entries = load_repository_entries(repository_dir)

    assert database_path == repository_database_path(repository_dir)
    assert len(entries) == 1
    assert entries[0].source_name == "Vendor Master Agreement.pdf"
    assert entries[0].status == "Awaiting Review"
    assert entries[0].department == "Unassigned"
    assert entries[0].review_date == "2026-08-05"
    assert entries[0].version == "1.0"
