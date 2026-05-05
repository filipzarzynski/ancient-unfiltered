"""High-level orchestration for ancient lexical source data.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

from typing import Any

import httpx

from sources.chronology import filter_legacy_entries, parse_year_from_text
from sources.common import detect_language, normalize_word
from sources.etymology import fetch_etymology
from sources.lexica import fetch_lexicon
from sources.morphology import fetch_morphology, parse_perseus_morphology
from sources.passages import hydrate_lexicon_citations


USER_AGENT = "ancient-unfiltered/0.2 (+https://github.com/filipzarzynski/ancient-unfiltered)"


async def build_response(
    word: str,
    cutoff_year: int,
    language: str = "auto",
    local_context: str = "",
    token_index: int | None = None,
) -> dict[str, Any]:
    """Fetch external data and return the v0.2 public API schema."""
    resolved_language, warnings = detect_language(word, language)
    if resolved_language == "undetermined":
        resolved_language = "latin"

    headers = {"User-Agent": USER_AGENT}
    timeout = httpx.Timeout(8.0, connect=4.0)
    async with httpx.AsyncClient(
        headers=headers,
        follow_redirects=True,
        timeout=timeout,
        trust_env=False,
    ) as client:
        morphology, morph_warnings = await fetch_morphology(client, word, resolved_language)
        warnings.extend(morph_warnings)

        lemmas = unique_lemmas(morphology, word)
        lexicon, lexicon_warnings = await fetch_lexicon(client, lemmas, word, resolved_language, cutoff_year)
        warnings.extend(lexicon_warnings)

        lexicon, translations, passage_warnings = await hydrate_lexicon_citations(
            client,
            lexicon,
            word,
            lemmas,
            resolved_language,
        )
        warnings.extend(passage_warnings)

        etymology = await fetch_etymology(client, lemmas[0] if lemmas else word, resolved_language)

    return {
        "word": word,
        "display_word": word,
        "language": resolved_language,
        "query_year": cutoff_year,
        "local_context": {
            "sentence": local_context,
            "token_index": token_index,
        },
        "morphology": morphology,
        "etymology": etymology,
        "lexicon": lexicon,
        "translations": translations,
        "warnings": dedupe_warnings(warnings),
    }


def unique_lemmas(morphology: list[dict[str, Any]], fallback: str) -> list[str]:
    lemmas: list[str] = []
    for path in morphology:
        lemma = str(path.get("lemma", "")).strip()
        if lemma and lemma not in lemmas:
            lemmas.append(lemma)
    if fallback and fallback not in lemmas:
        lemmas.append(fallback)
    return lemmas[:8]


def filter_by_date(raw_entries: list[dict[str, str]], cutoff_year: int) -> list[dict[str, Any]]:
    """v0.1-compatible chronological filter wrapper."""
    return filter_legacy_entries(raw_entries, cutoff_year, "latin")


def dedupe_warnings(warnings: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for warning in warnings:
        if not warning or warning in seen:
            continue
        seen.add(warning)
        result.append(warning)
    if not result:
        result.append("No single branch is selected as correct.")
    elif "No single branch is selected as correct." not in result:
        result.append("No single branch is selected as correct.")
    return result
