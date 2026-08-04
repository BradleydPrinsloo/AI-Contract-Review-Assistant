from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass
class TopFinding:
    phrase: str
    category: str
    finding_type: str
    risk: str
    score: int
    summary: str


@dataclass
class RiskAssessment:
    total_score: int
    rating: str
    finding_count: int
    risk_count: int
    protective_count: int
    neutral_count: int
    top_findings: List[TopFinding]
    recommendations: List[str]


BASE_RISK_SCORES = {
    "Payment Terms": 10,
    "Insurance Requirements": 12,
    "Security & Payment": 9,
    "Schedule & Performance": 12,
    "Notice & Claims": 8,
    "Warranty & Remedies": 8,
    "Liability": 7,
    "Liability Allocation": 7,
    "Indemnification": 14,
    "Indemnity Exposure": 15,
    "Renewal": 8,
    "Term / Renewal": 8,
    "Payment": 7,
    "Payment / Retainage": 10,
    "Insurance Burden": 12,
    "Lien Risk": 9,
    "Delay Risk": 12,
    "Claims Deadline Risk": 8,
    "Termination": 7,
    "Termination Risk": 10,
    "Warranty / Backcharge": 8,
    "SLA": 3,
    "Service / Performance": 3,
    "Governing Law": 2,
    "Governing Law / Venue": 2,
    "Notice": 1,
    "Confidentiality": 2,
    "Employment": 10,
    "General": 4,
}

RISK_MULTIPLIER = {"Critical": 2.0, "High": 1.35, "Medium": 1.0, "Low": 0.45, "Info": 0.1}
TYPE_MULTIPLIER = {"Risk": 1.0, "Protective": 0.25, "Neutral": 0.2, "Info": 0.05}

MAX_PER_CATEGORY = {
    "Payment Terms": 18,
    "Insurance Requirements": 18,
    "Security & Payment": 16,
    "Schedule & Performance": 20,
    "Notice & Claims": 14,
    "Warranty & Remedies": 14,
    "Liability": 18,
    "Liability Allocation": 18,
    "Indemnification": 22,
    "Indemnity Exposure": 24,
    "Renewal": 12,
    "Term / Renewal": 12,
    "Payment": 12,
    "Payment / Retainage": 18,
    "Insurance Burden": 18,
    "Lien Risk": 16,
    "Delay Risk": 20,
    "Claims Deadline Risk": 14,
    "Termination": 10,
    "Termination Risk": 18,
    "Warranty / Backcharge": 14,
    "SLA": 5,
    "Service / Performance": 5,
    "Governing Law": 3,
    "Governing Law / Venue": 4,
    "Notice": 2,
    "Confidentiality": 4,
    "Employment": 15,
    "General": 6,
}


def calculate_risk_assessment(results) -> RiskAssessment:
    for result in results:
        result.score = calculate_result_score(result)
    category_totals = {}
    for result in results:
        current = category_totals.get(result.category, 0)
        category_totals[result.category] = min(MAX_PER_CATEGORY.get(result.category, 8), current + result.score)
    total = min(100, sum(category_totals.values()))
    rating = risk_rating(total)
    risk_count = sum(1 for result in results if result.finding_type == "Risk")
    protective_count = sum(1 for result in results if result.finding_type == "Protective")
    neutral_count = len(results) - risk_count - protective_count
    top = sorted([result for result in results if result.finding_type in ("Risk", "Protective")], key=lambda result: result.score, reverse=True)[:5]
    return RiskAssessment(total, rating, len(results), risk_count, protective_count, neutral_count, [TopFinding(result.phrase, result.category, result.finding_type, result.risk, result.score, _short_summary(result)) for result in top], build_recommendations(results, total, rating))


def calculate_result_score(result) -> int:
    base = BASE_RISK_SCORES.get(result.category, BASE_RISK_SCORES["General"])
    score = int(round(base * RISK_MULTIPLIER.get(result.risk, 1.0) * TYPE_MULTIPLIER.get(result.finding_type, 1.0)))
    text = f"{result.phrase} {result.context} {result.note}".lower()
    if result.finding_type == "Info":
        return 0
    if result.finding_type == "Risk":
        if "unlimited liability" in text and "not accepted" not in text:
            score += 25
        if result.category in {"Indemnification", "Indemnity Exposure"}:
            score += 4 if "defend" in text else 0
            score += 4 if "hold harmless" in text else 0
            if "sole negligence" in text and "shall not include" in text:
                score = max(score - 2, 0)
        if result.category in {"Payment", "Payment / Retainage", "Payment Terms"}:
            days = extract_days(text)
            if days:
                score += 14 if days > 90 else 10 if days > 60 else 7 if days > 45 else 4 if days > 30 else 0
            score += 6 if "retainage" in text else 0
            if any(term in text for term in ("pay if paid", "pay-if-paid", "pay when paid", "pay-when-paid")):
                score += 7
        if result.category in {"Renewal", "Term / Renewal"}:
            if any(term in text for term in ("automatically renew", "auto-renewal", "renews automatically")):
                score += 5
            elif any(term in text for term in ("successive", "continue", "year to year")):
                score += 3
            days = extract_days(text)
            if days and days >= 60:
                score += 2
        if result.category in {"Insurance Burden", "Insurance Requirements"}:
            score += 6 if "additional insured" in text else 0
            score += 5 if "waiver of subrogation" in text else 0
            score += 4 if "primary and non-contributory" in text else 0
            score += 3 if "completed operations" in text else 0
            score += 2 if "10 years" in text or "5 years" in text else 0
        if result.category in {"Lien Risk", "Security & Payment"}:
            score += 8 if "unconditional waiver" in text else 5 if "conditional lien waiver" in text or "lien waiver" in text else 0
            score += 2 if "progress payment" in text or "final payment" in text else 0
        if result.category in {"Delay Risk", "Schedule & Performance"}:
            score += 10 if "liquidated damages" in text else 0
            score += 8 if "delay damages" in text else 0
            score += 5 if "time is of the essence" in text else 0
            score += 3 if "back on schedule" in text or "recovery schedule" in text else 0
        if result.category in {"Claims Deadline Risk", "Notice & Claims"}:
            score += 5 if "notice within" in text or "written notice of all claims" in text else 0
            days = extract_days(text)
            if days:
                score += 5 if days <= 3 else 3 if days <= 10 else 1 if days <= 30 else 0
        if result.category in {"Termination", "Termination Risk"}:
            score += 8 if "terminate for default" in text or "termination for convenience" in text else 0
            score += 6 if "effective immediately upon notice" in text else 0
            score += 8 if "without opportunity to cure" in text else 0
            score += 4 if "take over" in text and "work" in text else 0
        if result.category in {"Warranty / Backcharge", "Warranty & Remedies"}:
            score += 6 if "back charge" in text or "backcharge" in text else 0
            score += 4 if "correct at its own expense" in text or "make good without cost" in text else 0
            score += 2 if "warranty" in text else 0
        if result.category == "Employment" and ("non-compete" in text or "competing business" in text):
            score += 6
    if result.finding_type == "Protective" and result.category in {"Liability", "Liability Allocation"}:
        score = min(score + 1, 5)
    if result.finding_type == "Neutral":
        score = min(score, 3)
    if getattr(result, "confidence", 50) < 35:
        score = int(score * 0.35)
    return max(0, min(score, 40))


def extract_days(text: str):
    match = re.search(r"\((\d{1,3})\)\s*days?", text) or re.search(r"(\d{1,3})\s*days?", text)
    if match:
        return int(match.group(1))
    words = {"three": 3, "five": 5, "seven": 7, "ten": 10, "fifteen": 15, "thirty": 30, "twenty-four": 24, "twenty four": 24, "forty-five": 45, "forty five": 45, "sixty": 60, "ninety": 90, "one hundred twenty": 120, "hundred twenty": 120, "one hundred and twenty": 120}
    for word, value in words.items():
        if word in text and "day" in text:
            return value
    return None


def risk_rating(score: int) -> str:
    if score <= 20:
        return "Low"
    if score <= 40:
        return "Moderate"
    if score <= 60:
        return "Elevated"
    if score <= 80:
        return "High"
    return "Critical"


def build_recommendations(results, total, rating):
    recs = []
    risk_categories = {result.category for result in results if result.finding_type == "Risk"}
    protective_categories = {result.category for result in results if result.finding_type == "Protective"}
    all_text = " ".join(f"{result.phrase} {result.context}" for result in results).lower()
    if not results:
        return ["No configured findings were detected, but manual review is still required.", "If the file was a scanned PDF, verify OCR extraction is enabled and the scan is legible."]
    rules = [
        ({"Payment", "Payment / Retainage", "Payment Terms"}, "Review payment timing, retainage percentage, pay-if-paid conditions, and release triggers."),
        ({"Lien Risk", "Security & Payment"}, "Review conditional versus unconditional lien waiver timing and what must be released at each payment step."),
        ({"Renewal", "Term / Renewal"}, "Review renewal language, renewal term length, and required non-renewal notice window."),
        ({"Liability", "Liability Allocation"}, "Review liability provisions for uncapped exposure, carve-outs, and excluded damages."),
        ({"Indemnification", "Indemnity Exposure"}, "Review defense obligations, indemnity scope, negligence carve-outs, and third-party claim exposure."),
        ({"Insurance Burden", "Insurance Requirements"}, "Review additional insured, primary/non-contributory, waiver of subrogation, completed operations, and duration obligations."),
        ({"Delay Risk", "Schedule & Performance"}, "Review liquidated damages, actual delay damages, schedule milestones, and time-is-of-the-essence language."),
        ({"Claims Deadline Risk", "Notice & Claims"}, "Review notice deadlines, claim windows, and whether missing the deadline waives compensation or time extensions."),
        ({"Termination", "Termination Risk"}, "Review default triggers, cure periods, immediate termination rights, and takeover rights."),
        ({"Warranty / Backcharge", "Warranty & Remedies"}, "Review corrective-work obligations, warranty duration, remedies, and backcharge rights."),
    ]
    for categories, recommendation in rules:
        if categories & risk_categories:
            recs.append(recommendation)
    if {"Liability", "Liability Allocation"} & protective_categories:
        recs.append("Liability limitation language appears protective, but confirm the cap and carve-outs are acceptable.")
    all_categories = {result.category for result in results}
    if {"SLA", "Service / Performance"} & all_categories:
        recs.append("Review service level commitments, remedies, and service credit language.")
    if {"Governing Law", "Governing Law / Venue"} & all_categories:
        recs.append("Confirm governing law, venue, arbitration, or mediation terms are acceptable.")
    if "unlimited liability" in all_text and "not accepted" not in all_text:
        recs.insert(0, "Escalate any unlimited liability language for priority manual review.")
    recs.append("Consider routing this contract to legal or senior management before approval." if total >= 61 else "Manual review should focus on the top findings before approval." if total >= 21 else "Overall score is low, but the reviewer should still confirm required protections are present.")
    return list(dict.fromkeys(recs))


def _short_summary(result):
    text = result.context.strip()
    return text if len(text) <= 130 else text[:127] + "..."
