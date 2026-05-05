"""Lexicon source clients for CLD dictionary data.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from sources.chronology import filter_lexicon_entries
from sources.common import clean_text, strip_greek_diacritics


CLD_LEMMA_JSON_URL = "https://cld.bbaw.de/api/dictionary/lemma/{lemma}"

DICTIONARY_PREFERENCES = {
    "latin": ("Lewis Short",),
    "greek": ("LSJ", "Bailly"),
}


async def fetch_lexicon(
    client: httpx.AsyncClient,
    lemmas: list[str],
    word: str,
    language: str,
    cutoff_year: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    raw_entries: list[dict[str, str]] = []
    for lemma in unique_lookup_candidates(lemmas, word, language):
        entries = await fetch_cld_json_entries(client, lemma, language)
        if entries:
            raw_entries = entries
            break

    if not raw_entries:
        warnings.append("No lexicon source data returned.")
        return [], warnings

    return filter_lexicon_entries(raw_entries, cutoff_year, language), warnings


async def fetch_cld_json_entries(client: httpx.AsyncClient, lemma: str, language: str) -> list[dict[str, str]]:
    """Fetch CLD JSON and keep dictionary descriptions relevant to the language."""
    url = CLD_LEMMA_JSON_URL.format(lemma=quote(lemma, safe=""))
    language_param = "lat" if language == "latin" else "grc"
    try:
        response = await client.get(url, params={"language": language_param, "options": "case-sensitive"})
        if response.status_code != 200:
            return []
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return []

    entries: list[dict[str, str]] = []
    preferences = DICTIONARY_PREFERENCES.get(language, ())
    for record in payload.get("data", []):
        if not isinstance(record, dict):
            continue
        record_lemma = str(record.get("lemma") or lemma)
        descriptions = record.get("descriptions", [])
        for preferred in preferences:
            for description in descriptions:
                if not isinstance(description, dict):
                    continue
                dictionary = str(description.get("dictionary") or "")
                if dictionary != preferred:
                    continue
                text = BeautifulSoup(str(description.get("description") or ""), "html.parser").get_text(" ", strip=True)
                text = clean_text(text)
                if not text:
                    continue
                entries.append(
                    {
                        "lemma": record_lemma,
                        "source": f"CLD JSON / {dictionary}",
                        "definition": text,
                        "reference": str(description.get("reference") or ""),
                    }
                )
            if entries:
                return entries
    return entries


def unique_lookup_candidates(lemmas: list[str], word: str, language: str) -> list[str]:
    candidates: list[str] = []
    for value in [*lemmas, word]:
        if value and value not in candidates:
            candidates.append(value)

    if language == "greek":
        stripped_candidates = []
        for value in candidates:
            stripped = strip_greek_diacritics(value)
            if stripped and stripped not in candidates and stripped not in stripped_candidates:
                stripped_candidates.append(stripped)
        candidates.extend(stripped_candidates)

    return candidates[:8]
