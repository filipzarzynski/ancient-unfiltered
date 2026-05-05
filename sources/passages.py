"""Passage and translation context retrieval.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from sources.common import clean_text, strip_greek_diacritics


PERSEUS_TEXT_URL = "https://www.perseus.tufts.edu/hopper/text"
PLATO_APOLOGY_GREEK = "Perseus:text:1999.01.0169:text=Apol.:section={section}"
PLATO_APOLOGY_ENGLISH = "Perseus:text:1999.01.0170:text=Apol.:section={section}"
PLATO_APOLOGY_RE = re.compile(r"\b(?:Pl\.|Plat\.)\s*(?:Ap\.|Apol\.)\s*(\d+[a-e])\b", re.IGNORECASE)


async def hydrate_lexicon_citations(
    client: httpx.AsyncClient,
    lexicon: list[dict[str, Any]],
    word: str,
    lemmas: list[str],
    language: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Attach source sentence estimates to citations where retrieval is supported."""
    translations: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen_translations: set[tuple[str, str]] = set()

    if language != "greek":
        return lexicon, translations, warnings

    for sense in lexicon:
        for citation in sense.get("citations", []):
            raw = citation.get("raw", "")
            estimate, translation, warning = await retrieve_source_sentence(client, raw, word, lemmas)
            if warning:
                warnings.append(warning)
            if estimate:
                citation["source_sentence"] = estimate
            if translation:
                key = (translation.get("passage", ""), translation.get("text", ""))
                if key not in seen_translations:
                    seen_translations.add(key)
                    translations.append(translation)

    return lexicon, translations, warnings


async def retrieve_source_sentence(
    client: httpx.AsyncClient,
    citation: str,
    word: str,
    lemmas: list[str],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    match = PLATO_APOLOGY_RE.search(citation)
    if not match:
        return None, None, None

    section = match.group(1).lower()
    greek_text = await fetch_perseus_text(client, PLATO_APOLOGY_GREEK.format(section=section))
    if not greek_text:
        return None, None, f"Source sentence unavailable for {citation}."

    strategy, confidence = match_strategy(greek_text, [word, *lemmas])
    estimate = {
        "text": greek_text,
        "provider": "Perseus Digital Library",
        "match_strategy": strategy,
        "confidence": confidence,
        "citation": f"Pl. Ap. {section}",
    }

    english_text = await fetch_perseus_text(client, PLATO_APOLOGY_ENGLISH.format(section=section))
    translation = None
    if english_text:
        translation = {
            "text": english_text,
            "source": "Perseus Digital Library / Plato Apology English translation",
            "passage": f"Pl. Ap. {section}",
            "role": "Translation context, not interpretation",
            "date_status": "translation date unverified",
        }

    return estimate, translation, None


async def fetch_perseus_text(client: httpx.AsyncClient, doc: str) -> str:
    try:
        response = await client.get(PERSEUS_TEXT_URL, params={"doc": doc})
        if response.status_code != 200:
            return ""
    except httpx.HTTPError:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    node = soup.select_one("#text_main")
    if not node:
        return ""

    text = node.get_text(" ", strip=True)
    text = re.sub(r"^Click on a word.*?\[\s*", "[", text)
    return clean_text(text)


def match_strategy(text: str, terms: list[str]) -> tuple[str, str]:
    normalized_text = strip_greek_diacritics(text).casefold()
    for term in terms:
        normalized = strip_greek_diacritics(term).casefold()
        if normalized and normalized in normalized_text:
            return "normalized token or lemma match", "high"

    stems = [strip_greek_diacritics(term).casefold()[:6] for term in terms if len(term) >= 6]
    for stem in stems:
        if stem and stem in normalized_text:
            return "normalized stem match", "medium"

    return "citation-only context", "medium"
