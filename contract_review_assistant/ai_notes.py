from __future__ import annotations

import os

from dotenv import load_dotenv

from .risk_engine import calculate_risk_assessment

load_dotenv()


def openai_summary(results, risk_assessment=None) -> str:
    if risk_assessment is None:
        risk_assessment = calculate_risk_assessment(results)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return rule_summary(results, risk_assessment)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        findings_text = "\n".join(
            f"- {result.phrase} | {result.finding_type} | {result.category} | {result.risk} | score {result.score} | {result.location}: {result.context}"
            for result in results[:15]
        ) or "No findings."

        prompt = f"""
Create a concise internal contract review summary for a business reviewer.

Overall Risk Score: {risk_assessment.total_score}/100
Risk Rating: {risk_assessment.rating}
Risk Findings: {risk_assessment.risk_count}
Protective Findings: {risk_assessment.protective_count}
Neutral/Info Findings: {risk_assessment.neutral_count}

Findings:
{findings_text}

Return:
1. Executive summary
2. Top risk items
3. Protective clauses found
4. Practical review recommendations
5. Reminder that manual review is required and this is not legal advice
"""
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You summarize contract review findings for internal business use. Explain risks and protections clearly, but do not provide legal advice.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return rule_summary(results, risk_assessment)


def rule_summary(results, risk_assessment=None) -> str:
    if risk_assessment is None:
        risk_assessment = calculate_risk_assessment(results)

    lines = [
        "Contract Analysis Summary",
        "==============",
        "",
        f"Overall Risk Score: {risk_assessment.total_score}/100",
        f"Risk Rating: {risk_assessment.rating}",
        f"Total flagged items: {len(results)}",
        f"Risk Findings: {risk_assessment.risk_count}",
        f"Protective Findings: {risk_assessment.protective_count}",
        f"Neutral/Info Findings: {risk_assessment.neutral_count}",
        "",
        "Top review priorities:",
    ]

    if risk_assessment.top_findings:
        for item in risk_assessment.top_findings:
            lines.append(f"- {item.phrase} [{item.finding_type}/{item.risk}] +{item.score}: {item.summary}")
    else:
        lines.append("- No priority findings detected.")

    lines.extend(["", "Recommended actions:"])
    for rec in risk_assessment.recommendations:
        lines.append(f"- {rec}")

    lines.extend(["", "Disclaimer: This tool supports internal review and does not provide legal advice."])
    return "\n".join(lines)
