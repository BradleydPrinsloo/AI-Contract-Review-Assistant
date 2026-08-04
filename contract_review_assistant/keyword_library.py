from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Iterable, Mapping

from contract_review_assistant.app_paths import default_exports_dir, external_or_bundled_path

KEYWORD_LIBRARY_DIRNAME = "keyword-library"
KEYWORD_LIBRARY_FILENAME = "keywords.json"
DEFAULT_CUSTOM_CATEGORY = "Custom"
DEFAULT_CUSTOM_RISK = "Medium"
DEFAULT_CUSTOM_FINDING_TYPE = "Risk"
DEFAULT_CUSTOM_NOTE = "Custom keyword match. Review the surrounding clause manually."


def bundled_keyword_library_path() -> Path:
    return external_or_bundled_path("data", "keywords.json")


def editable_keyword_library_path(exports_dir: Path | None = None) -> Path:
    base_dir = exports_dir or default_exports_dir()
    return base_dir / KEYWORD_LIBRARY_DIRNAME / KEYWORD_LIBRARY_FILENAME


def ensure_editable_keyword_library(source_path: Path | None = None, target_path: Path | None = None) -> Path:
    source = source_path or bundled_keyword_library_path()
    target = target_path or editable_keyword_library_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(source, target)
    return target


def parse_aliases(value: str | Iterable[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        candidates = value.replace("\n", ",").split(",")
    else:
        candidates = [str(item) for item in value]
    aliases: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        alias = str(raw).strip()
        alias_key = alias.casefold()
        if not alias or alias_key in seen:
            continue
        seen.add(alias_key)
        aliases.append(alias)
    return aliases


def normalize_keyword_rule(rule: Mapping[str, Any]) -> dict[str, Any]:
    phrase = str(rule.get("phrase", "")).strip()
    if not phrase:
        raise ValueError("Each keyword entry must include a phrase.")

    category = str(rule.get("category") or DEFAULT_CUSTOM_CATEGORY).strip() or DEFAULT_CUSTOM_CATEGORY
    risk = str(rule.get("risk") or DEFAULT_CUSTOM_RISK).strip() or DEFAULT_CUSTOM_RISK
    finding_type = str(rule.get("finding_type") or DEFAULT_CUSTOM_FINDING_TYPE).strip() or DEFAULT_CUSTOM_FINDING_TYPE
    note = str(rule.get("note") or DEFAULT_CUSTOM_NOTE).strip() or DEFAULT_CUSTOM_NOTE
    aliases = parse_aliases(rule.get("aliases"))

    return {
        "phrase": phrase,
        "category": category,
        "risk": risk,
        "finding_type": finding_type,
        "note": note,
        "aliases": aliases,
    }


def save_keyword_library(path: Path, rules: Iterable[Mapping[str, Any]]) -> Path:
    normalized_rules = [normalize_keyword_rule(rule) for rule in rules]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized_rules, indent=2) + "\n", encoding="utf-8")
    return path
