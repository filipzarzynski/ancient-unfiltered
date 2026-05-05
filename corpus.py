"""v0.3 matched-pair corpus validation and export helpers.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
import re
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
SEED_CORPUS_PATH = BASE_DIR / "docs" / "corpus" / "v0.3-seed.json"

CORPUS_VERSION = "v0.3"
EXPORT_VERSION = "v0.3-export"

ENTRY_REQUIRED_FIELDS = {
    "id",
    "theme",
    "author",
    "work",
    "citation",
    "current_english",
    "critical_original",
    "path_options",
    "alternative_translations",
    "example_selected_output",
}

CRITICAL_ORIGINAL_REQUIRED_FIELDS = {
    "language",
    "text",
    "source_label",
    "source_url",
}

BANNED_AUTHORITATIVE_PHRASES = [
    "correct translation",
    "true interpretation",
    "definitive translation",
    "authoritative answer",
]


class CorpusValidationError(ValueError):
    """Raised when an imported corpus patch cannot be treated as evidence."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def load_seed_corpus(path: Path = SEED_CORPUS_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validation_errors_for_entry(entry: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(entry, dict):
        return ["entry must be an object"]

    missing = sorted(ENTRY_REQUIRED_FIELDS - set(entry))
    if missing:
        errors.append(f"entry missing required fields: {', '.join(missing)}")

    entry_id = entry.get("id")
    if not isinstance(entry_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,80}", entry_id):
        errors.append("id must be a stable lowercase identifier")

    current_english = entry.get("current_english")
    if not isinstance(current_english, str) or not current_english.strip():
        errors.append("current_english is required")

    critical = entry.get("critical_original")
    if not isinstance(critical, dict):
        errors.append("critical_original must be an object")
    else:
        missing_critical = sorted(CRITICAL_ORIGINAL_REQUIRED_FIELDS - set(critical))
        if missing_critical:
            errors.append(f"critical_original missing required fields: {', '.join(missing_critical)}")
        if critical.get("language") not in {"grc", "lat"}:
            errors.append("critical_original.language must be grc or lat")
        for key in ("text", "source_label", "source_url"):
            if not isinstance(critical.get(key), str) or not critical.get(key, "").strip():
                errors.append(f"critical_original.{key} is required")
        source_url = critical.get("source_url", "")
        if isinstance(source_url, str) and source_url and not source_url.startswith(("http://", "https://")):
            errors.append("critical_original.source_url must be an http(s) URL")

    path_options = entry.get("path_options")
    if not isinstance(path_options, list) or not path_options:
        errors.append("path_options must contain at least one token path")
    else:
        for index, path in enumerate(path_options):
            if not isinstance(path, dict):
                errors.append(f"path_options[{index}] must be an object")
                continue
            for key in ("token", "lemma", "options"):
                if key not in path:
                    errors.append(f"path_options[{index}] missing {key}")
            options = path.get("options")
            if not isinstance(options, list) or not options:
                errors.append(f"path_options[{index}].options must contain at least one option")
            elif not all(isinstance(option, str) and option.strip() for option in options):
                errors.append(f"path_options[{index}].options must be non-empty strings")

    translations = entry.get("alternative_translations")
    if not isinstance(translations, list) or len(translations) < 1:
        errors.append("alternative_translations must contain at least one rendering")
    elif not all(isinstance(item, str) and item.strip() for item in translations):
        errors.append("alternative_translations must be non-empty strings")

    selected_paths = entry.get("selected_paths", {})
    if selected_paths and not isinstance(selected_paths, dict):
        errors.append("selected_paths must be an object when present")

    joined = json.dumps(entry, ensure_ascii=False).lower()
    for phrase in BANNED_AUTHORITATIVE_PHRASES:
        if phrase in joined:
            errors.append(f"authoritative phrase is not allowed: {phrase}")

    return errors


def validate_entry(entry: dict[str, Any]) -> dict[str, Any]:
    errors = validation_errors_for_entry(entry)
    if errors:
        raise CorpusValidationError(errors)
    return entry


def validate_corpus(corpus: Any) -> dict[str, Any]:
    if not isinstance(corpus, dict):
        raise CorpusValidationError(["corpus must be an object"])
    entries = corpus.get("entries")
    if not isinstance(entries, list):
        raise CorpusValidationError(["corpus.entries must be a list"])

    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, entry in enumerate(entries):
        entry_errors = validation_errors_for_entry(entry)
        entry_id = entry.get("id") if isinstance(entry, dict) else f"index {index}"
        if isinstance(entry_id, str):
            if entry_id in seen_ids:
                entry_errors.append("id must be unique inside a corpus patch")
            seen_ids.add(entry_id)
        for error in entry_errors:
            errors.append(f"{entry_id}: {error}")

    if errors:
        raise CorpusValidationError(errors)
    return corpus


def build_export(entries: list[dict[str, Any]], source: str = "local-user") -> dict[str, Any]:
    patch = {
        "version": EXPORT_VERSION,
        "created": date.today().isoformat(),
        "source": source,
        "status": "evidence proposal",
        "policy": [
            "Imported matched pairs are evidence proposals until provenance and schema review pass.",
            "Selected paths are reader experiments, not the app's judgment.",
        ],
        "entries": deepcopy(entries),
    }
    validate_corpus(patch)
    return patch


def import_corpus_patch(patch: dict[str, Any]) -> dict[str, Any]:
    validated = validate_corpus(patch)
    return {
        "version": validated.get("version", EXPORT_VERSION),
        "status": "validated evidence proposal",
        "entries": deepcopy(validated["entries"]),
    }


def corpus_summary(corpus: dict[str, Any]) -> dict[str, Any]:
    entries = corpus.get("entries", [])
    themes: dict[str, int] = {}
    for entry in entries:
        theme = entry.get("theme", "unlisted")
        themes[theme] = themes.get(theme, 0) + 1
    return {
        "version": corpus.get("version", CORPUS_VERSION),
        "entry_count": len(entries),
        "themes": themes,
    }
