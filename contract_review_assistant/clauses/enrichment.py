from __future__ import annotations

"""Clause Library guidance enrichment for deterministic scanner findings."""

import re

from contract_review_assistant.scanner import ScanResult

from .library import ClauseLibraryService, ClauseRecord, ClauseSearchFilters


class ClauseLibraryEnricher:
    """Attach approved/rejected clause-library guidance to scanner findings."""

    def __init__(self, service: ClauseLibraryService) -> None:
        self.service = service

    def enrich(self, results: list[ScanResult]) -> list[ScanResult]:
        """Mutate findings with best matching active clause guidance and return them."""

        if not results:
            return results
        clauses = self.service.search(ClauseSearchFilters(include_archived=False))
        if not clauses:
            return results
        for result in results:
            clause = self.match(result, clauses)
            if clause is not None:
                apply_clause_guidance(result, clause)
        return results

    def match(
        self,
        result: ScanResult,
        clauses: list[ClauseRecord] | None = None,
    ) -> ClauseRecord | None:
        """Return the strongest active clause match for a finding."""

        candidate_clauses = clauses or self.service.search(ClauseSearchFilters(include_archived=False))
        best_clause: ClauseRecord | None = None
        best_score = 0
        for clause in candidate_clauses:
            score = _match_score(result, clause)
            if score > best_score:
                best_clause = clause
                best_score = score
        return best_clause if best_score >= 45 else None


def enrich_findings_with_clause_library(
    results: list[ScanResult],
    service: ClauseLibraryService | None,
) -> list[ScanResult]:
    """Convenience wrapper for optional clause-library enrichment."""

    if service is None:
        return results
    return ClauseLibraryEnricher(service).enrich(results)


def apply_clause_guidance(result: ScanResult, clause: ClauseRecord) -> None:
    """Attach clause-library guidance fields to a scanner finding."""

    result.clause_library_id = clause.clause_id
    result.clause_library_name = clause.name
    result.preferred_wording = clause.company_wording
    result.rejected_wording = clause.rejected_wording
    result.clause_examples = list(clause.examples)
    result.clause_explanation = clause.ai_explanation


def _match_score(result: ScanResult, clause: ClauseRecord) -> int:
    result_category = _norm(result.category)
    clause_category = _norm(clause.category)
    result_phrase = _norm(result.phrase)
    finding_text = _norm(" ".join([result.phrase, result.category, result.note, result.context]))
    clause_text = _norm(
        " ".join(
            [
                clause.name,
                clause.category,
                clause.risk_level,
                clause.company_wording,
                clause.rejected_wording,
                clause.ai_explanation,
                *clause.examples,
            ]
        )
    )

    score = 0
    if result_category and result_category == clause_category:
        score += 65
    elif result_category and clause_category and (result_category in clause_category or clause_category in result_category):
        score += 35

    phrase_tokens = [token for token in _tokens(result_phrase) if len(token) >= 4]
    if result_phrase and result_phrase in clause_text:
        score += 45
    elif phrase_tokens:
        matches = sum(1 for token in phrase_tokens if token in clause_text)
        if matches:
            score += min(35, matches * 12)

    category_tokens = [token for token in _tokens(result_category) if len(token) >= 5]
    if category_tokens:
        score += min(20, sum(8 for token in category_tokens if token in clause_text))

    if clause.risk_level.casefold() == result.risk.casefold():
        score += 5

    # Avoid weak category-only matches when the finding phrase and clause wording
    # are unrelated. Strong exact category matches still pass the threshold, but
    # loose category containment needs at least one textual overlap.
    if score < 65 and not any(token in finding_text for token in _tokens(clause_text) if len(token) >= 7):
        return 0
    return score


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").casefold()).strip()
