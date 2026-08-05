from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from contract_review_assistant.clauses import (
    ClauseLibraryService,
    enrich_findings_with_clause_library,
)
from contract_review_assistant.risk_engine import calculate_risk_assessment
from contract_review_assistant.scanner import (
    ScanResult,
    extract_document,
    load_keywords,
    scan_chunks,
)


ProgressCallback = Callable[[str, int], None]


class SummaryProvider(Protocol):
    def __call__(self, results: list[ScanResult], assessment: object) -> str: ...


@dataclass(frozen=True)
class ContractAnalysis:
    """UI-independent result returned by the contract analysis service."""

    source_file: str
    results: list[ScanResult]
    risk_assessment: object
    summary_text: str


class ContractAnalysisService:
    """Coordinates extraction, scanning, scoring, and summary generation.

    The service contains no PySide6 code and can therefore be reused by the
    desktop UI, a command-line interface, an API, automated tests, or a future
    buyer integration.
    """

    def __init__(
        self,
        keyword_path: str | Path,
        *,
        summary_provider: SummaryProvider | None = None,
        clause_library_service: ClauseLibraryService | None = None,
    ) -> None:
        self.keyword_path = Path(keyword_path)
        self.summary_provider = summary_provider
        self.clause_library_service = clause_library_service

    def analyze(
        self,
        source_file: str | Path,
        *,
        progress: ProgressCallback | None = None,
    ) -> ContractAnalysis:
        source = Path(source_file)
        if not source.exists():
            raise FileNotFoundError(f"Contract file does not exist: {source}")
        if not self.keyword_path.exists():
            raise FileNotFoundError(f"Rule library does not exist: {self.keyword_path}")

        notify = progress or (lambda _message, _value: None)

        notify("Loading rule library…", 10)
        rules = load_keywords(self.keyword_path)

        notify("Extracting contract text…", 35)
        chunks = extract_document(source)
        if not chunks:
            raise ValueError("No readable contract text could be extracted.")

        notify("Analyzing clauses…", 65)
        results = scan_chunks(chunks, rules)
        notify("Applying clause-library guidance…", 78)
        results = enrich_findings_with_clause_library(results, self.clause_library_service)
        assessment = calculate_risk_assessment(results)

        notify("Preparing review summary…", 90)
        summary = self._create_summary(results, assessment)

        notify("Analysis complete.", 100)
        return ContractAnalysis(
            source_file=str(source),
            results=results,
            risk_assessment=assessment,
            summary_text=summary,
        )

    def reassess(
        self,
        source_file: str | Path,
        results: list[ScanResult],
    ) -> ContractAnalysis:
        """Recalculate score and summary after reviewer changes."""

        results = enrich_findings_with_clause_library(list(results), self.clause_library_service)
        assessment = calculate_risk_assessment(results)
        summary = self._create_summary(results, assessment)
        return ContractAnalysis(
            source_file=str(source_file),
            results=results,
            risk_assessment=assessment,
            summary_text=summary,
        )

    def _create_summary(self, results: list[ScanResult], assessment: object) -> str:
        if self.summary_provider is not None:
            return self.summary_provider(results, assessment)

        # Import lazily so rule-based analysis remains usable without loading
        # the optional OpenAI integration during tests or non-AI deployments.
        from contract_review_assistant.ai_notes import openai_summary

        return openai_summary(results, assessment)
