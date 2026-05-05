"""Chronological citation parsing and filtering.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sources.common import clean_text, dedupe_preserve_order


LATIN_AUTHOR_YEARS = {
    "amm": 380,
    "ammianus": 380,
    "apul": 170,
    "apuleius": 170,
    "aug": 400,
    "augustine": 400,
    "caes": -50,
    "caesar": -50,
    "catull": -55,
    "catullus": -55,
    "cat": -55,
    "cic": -50,
    "cicero": -50,
    "col": 60,
    "columella": 60,
    "charis": 360,
    "charisius": 360,
    "dig": 533,
    "digest": 533,
    "gell": 170,
    "gellius": 170,
    "hor": -20,
    "horace": -20,
    "just": 150,
    "justin": 150,
    "liv": 10,
    "livy": 10,
    "lucr": -55,
    "lucretius": -55,
    "mart": 90,
    "martial": 90,
    "naev": -220,
    "naevius": -220,
    "nep": -40,
    "nepos": -40,
    "ov": 8,
    "ovid": 8,
    "plaut": -200,
    "plautus": -200,
    "plin": 77,
    "pliny": 77,
    "quint": 90,
    "quintilian": 90,
    "sall": -40,
    "sallust": -40,
    "sen": 50,
    "seneca": 50,
    "suet": 120,
    "suetonius": 120,
    "tac": 110,
    "tacitus": 110,
    "ter": -160,
    "terence": -160,
    "ulp": 220,
    "ulpian": 220,
    "varr": -40,
    "varro": -40,
    "verg": -20,
    "virg": -20,
    "virgil": -20,
    "vitr": -25,
    "vitruvius": -25,
}

GREEK_AUTHOR_YEARS = {
    "aesch": -470,
    "aeschylus": -470,
    "and": -400,
    "andocides": -400,
    "apoc": 95,
    "arist": -335,
    "aristotle": -335,
    "dem": -340,
    "demosthenes": -340,
    "eur": -430,
    "euripides": -430,
    "hdt": -440,
    "herodotus": -440,
    "hes": -700,
    "hesiod": -700,
    "hom": -750,
    "homer": -750,
    "isoc": -360,
    "isocrates": -360,
    "lys": -390,
    "lysias": -390,
    "pind": -470,
    "pindar": -470,
    "pflor": 250,
    "pl": -399,
    "plat": -399,
    "plato": -399,
    "soph": -440,
    "sophocles": -440,
    "th": -420,
    "thuc": -420,
    "thucydides": -420,
    "xen": -380,
    "xenophon": -380,
}

EXPLICIT_YEAR_RE = re.compile(
    r"\b(?:(?:c\.|ca\.|circa)\s*)?(\d{1,4})\s*(B\.?\s*C\.?|BCE|A\.?\s*D\.?|CE)\b",
    re.IGNORECASE,
)
AD_YEAR_RE = re.compile(r"\bA\.?\s*D\.?\s*(\d{1,4})\b", re.IGNORECASE)
CENTURY_RE = re.compile(
    r"\b(early|mid|middle|late)?\s*(\d{1,2})(?:st|nd|rd|th)\s+cent\.?(?:ury)?\s*(B\.?\s*C\.?|BCE|A\.?\s*D\.?|CE)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DatedCitation:
    text: str
    year: int | None
    date_status: str


def author_years_for(language: str = "any") -> dict[str, int]:
    if language == "latin":
        return LATIN_AUTHOR_YEARS
    if language == "greek":
        return GREEK_AUTHOR_YEARS
    return {**LATIN_AUTHOR_YEARS, **GREEK_AUTHOR_YEARS}


def author_regex(language: str = "any") -> re.Pattern[str]:
    aliases = sorted(author_years_for(language), key=len, reverse=True)
    return re.compile(
        r"(?<![A-Z]\.\s)\b("
        + "|".join(re.escape(alias) for alias in aliases)
        + r")\.?(?!\w)"
        + r"(?:\s+[A-Z][A-Za-z]{0,12}\.)?"
        + r"(?:\s*\d+[a-e]?(?:[.,]\s*\d+[a-e]?){0,5})?"
        + r"(?:\s*\([^)]+\))?",
        re.IGNORECASE,
    )


def parse_year_from_text(text: str, language: str = "any") -> int | None:
    ad_match = AD_YEAR_RE.search(text)
    if ad_match:
        return int(ad_match.group(1))

    explicit = EXPLICIT_YEAR_RE.search(text)
    if explicit:
        year = int(explicit.group(1))
        era = explicit.group(2).lower()
        return -year if "b" in era else year

    century = CENTURY_RE.search(text)
    if century:
        modifier, century_text, era = century.groups()
        century_number = int(century_text)
        offset = {"early": 25, "mid": 50, "middle": 50, "late": 75}.get(
            (modifier or "mid").lower(),
            50,
        )
        year = (century_number - 1) * 100 + offset
        return -year if "b" in era.lower() else year

    author_match = author_regex(language).search(text)
    if author_match:
        alias = author_match.group(1).rstrip(".").casefold()
        return author_years_for(language).get(alias)

    return None


def extract_dated_citations(text: str, language: str = "any") -> list[DatedCitation]:
    citations: list[DatedCitation] = []
    for match in author_regex(language).finditer(text):
        citation_text = clean_text(match.group(0).rstrip(" ,;:."))
        year = parse_year_from_text(citation_text, language)
        citations.append(DatedCitation(citation_text, year, "estimated" if year is not None else "unverified"))

    explicit_year = parse_year_from_text(text, language)
    if explicit_year is not None and not citations:
        citations.append(DatedCitation(clean_text(text[:120]), explicit_year, "estimated"))

    return dedupe_citations(citations)


def filter_lexicon_entries(
    raw_entries: list[dict[str, str]],
    cutoff_year: int,
    language: str = "latin",
) -> list[dict[str, Any]]:
    """Drop lexicon segments that are securely later than the requested cutoff."""
    filtered: list[dict[str, Any]] = []
    for entry in raw_entries:
        definition = clean_text(entry.get("definition", ""))
        if not definition:
            continue

        kept_segments: list[str] = []
        kept_citations: list[dict[str, Any]] = []
        for segment in split_definition_segments(definition):
            citations = extract_dated_citations(segment, language)
            if not citations:
                kept_segments.append(segment)
                continue

            dated = [citation for citation in citations if citation.year is not None]
            future_only = bool(dated) and all(
                citation.year is not None and citation.year > cutoff_year for citation in citations
            )
            if future_only:
                continue

            stripped_segment = strip_future_citations(segment, cutoff_year, language)
            if stripped_segment:
                kept_segments.append(stripped_segment)

            for citation in citations:
                if citation.year is None:
                    kept_citations.append(citation_payload(citation))
                elif citation.year <= cutoff_year:
                    kept_citations.append(citation_payload(citation))

        if not kept_segments:
            continue

        if not kept_citations:
            kept_citations = [
                {
                    "raw": "No dated citation parsed",
                    "estimated_year": None,
                    "date_status": "unverified",
                    "source_sentence": unavailable_sentence(),
                }
            ]

        source = entry.get("source", "lexicon")
        filtered.append(
            {
                "sense": f"{entry.get('lemma', 'Lemma')} / {source} / Sense {len(filtered) + 1}",
                "definition": clean_text(" ".join(kept_segments)),
                "source": source,
                "date_status": "verified" if any(c["estimated_year"] is not None for c in kept_citations) else "unverified",
                "citations": dedupe_citation_payloads(kept_citations),
            }
        )

    return filtered


def filter_legacy_entries(
    raw_entries: list[dict[str, str]],
    cutoff_year: int,
    language: str = "latin",
) -> list[dict[str, Any]]:
    """Compatibility shape used by v0.1 tests and older UI assumptions."""
    modern = filter_lexicon_entries(raw_entries, cutoff_year, language)
    legacy: list[dict[str, Any]] = []
    for entry in modern:
        citations = []
        for citation in entry["citations"]:
            raw = citation["raw"]
            year = citation["estimated_year"]
            if year is None:
                citations.append(f"{raw} (date unverified)")
            else:
                citations.append(f"{raw} ({format_year(year)})")
        legacy.append(
            {
                "sense": entry["sense"],
                "definition": entry["definition"],
                "citations": dedupe_preserve_order(citations),
            }
        )
    return legacy


def citation_payload(citation: DatedCitation) -> dict[str, Any]:
    return {
        "raw": citation.text,
        "estimated_year": citation.year,
        "date_status": citation.date_status,
        "source_sentence": unavailable_sentence(),
    }


def unavailable_sentence() -> dict[str, Any]:
    return {
        "text": "",
        "provider": "",
        "match_strategy": "source sentence unavailable",
        "confidence": "unavailable",
    }


def split_definition_segments(definition: str) -> list[str]:
    segments = re.split(r";\s*", definition)
    cleaned = [clean_text(segment) for segment in segments if clean_text(segment)]
    return cleaned or [definition]


def strip_future_citations(text: str, cutoff_year: int, language: str = "any") -> str:
    matches = list(author_regex(language).finditer(text))
    if not matches:
        return text

    stripped = text
    for match in reversed(matches):
        citation_text = match.group(0)
        year = parse_year_from_text(citation_text, language)
        if year is None or year <= cutoff_year:
            continue

        start, end = match.span()
        while start > 0 and stripped[start - 1] in " ,;:\u2014-":
            start -= 1
        stripped = f"{stripped[:start]} {stripped[end:]}"

    return clean_text(stripped)


def format_year(year: int) -> str:
    if year < 0:
        return f"c. {abs(year)} BCE"
    return f"c. {year} CE"


def dedupe_citations(citations: list[DatedCitation]) -> list[DatedCitation]:
    seen: set[str] = set()
    result: list[DatedCitation] = []
    for citation in citations:
        if citation.text in seen:
            continue
        seen.add(citation.text)
        result.append(citation)
    return result


def dedupe_citation_payloads(citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for citation in citations:
        raw = citation.get("raw", "")
        if raw in seen:
            continue
        seen.add(raw)
        result.append(citation)
    return result
