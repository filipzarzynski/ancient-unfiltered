"""Morphology source client and XML parser.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx

from sources.common import greek_to_perseus_lookup


PERSEUS_MORPH_URL = "https://www.perseus.tufts.edu/hopper/xmlmorph"

POS_LABELS = {
    "adj": "Adjective",
    "adjective": "Adjective",
    "adv": "Adverb",
    "adverb": "Adverb",
    "conj": "Conjunction",
    "noun": "Noun",
    "part": "Particle",
    "prep": "Preposition",
    "pron": "Pronoun",
    "verb": "Verb",
}


async def fetch_morphology(
    client: httpx.AsyncClient,
    word: str,
    language: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Fetch and parse source-reported morphology paths."""
    warnings: list[str] = []
    lang_param = "la" if language == "latin" else "greek"
    lookup_candidates = [word]

    if language == "greek":
        transliterated = greek_to_perseus_lookup(word)
        if transliterated and transliterated not in lookup_candidates:
            lookup_candidates.insert(0, transliterated)

    for lookup in lookup_candidates:
        for key in ("lookup", "text"):
            try:
                response = await client.get(PERSEUS_MORPH_URL, params={"lang": lang_param, key: lookup})
            except httpx.HTTPError as exc:
                warnings.append(f"Perseus morphology request failed for {lookup}: {exc.__class__.__name__}.")
                continue

            if response.status_code != 200 or not response.text.strip():
                continue

            paths = parse_perseus_morphology(response.text, language=language)
            if paths:
                if lookup != word:
                    warnings.append(f"Greek morphology used Perseus transliteration lookup: {lookup}.")
                return paths, warnings

    warnings.append("No morphology source data returned.")
    return [], warnings


def parse_perseus_morphology(xml_text: str, language: str = "latin") -> list[dict[str, Any]]:
    """Convert Perseus XML analyses into equal-weight morphology paths."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    analyses = [node for node in root.iter() if local_name(node.tag) == "analysis"]
    if not analyses:
        analyses = [root]

    paths: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for node in analyses:
        lemma = first_child_text(node, "lemma")
        pos = first_child_text(node, "pos")
        if not lemma and not pos:
            continue

        detail_parts = []
        for field in (
            "form",
            "expandedForm",
            "case",
            "number",
            "gender",
            "person",
            "tense",
            "mood",
            "voice",
            "degree",
            "dialect",
            "feature",
        ):
            value = first_child_text(node, field)
            if value:
                detail_parts.append(f"{field}: {value}")

        details = ", ".join(detail_parts) if detail_parts else "No additional morphology fields returned."
        entry = (
            lemma or "unlisted",
            POS_LABELS.get(pos.casefold(), pos or "Unlisted"),
            details,
        )
        if entry in seen:
            continue
        seen.add(entry)
        paths.append(
            {
                "path": f"Path {chr(65 + len(paths))}" if len(paths) < 26 else f"Path {len(paths) + 1}",
                "pos": entry[1],
                "lemma": entry[0],
                "details": entry[2],
                "source": "Perseus Morpheus",
                "confidence": "source-reported",
                "language": language,
            }
        )

    return paths


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def first_child_text(node: ET.Element, name: str) -> str:
    for child in node.iter():
        if local_name(child.tag) == name and child.text:
            return " ".join(child.text.split())
    return ""
