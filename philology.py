"""Fetching, parsing, and chronological filtering for ancient lexical data.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup, Tag


PERSEUS_MORPH_URL = "https://www.perseus.tufts.edu/hopper/xmlmorph"
CLD_LEMMA_JSON_URL = "https://cld.bbaw.de/api/dictionary/lemma/{lemma}"
CLD_LEMMA_HTML_URL = "https://cld.bbaw.de/lemma/lat/{lemma}"
WIKTIONARY_API_URL = "https://en.wiktionary.org/w/api.php"
USER_AGENT = "ancient-unfiltered/0.1 (+https://github.com/filipzarzynski/ancient-unfiltered)"

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

AUTHOR_YEARS = {
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

AUTHOR_ALIASES = sorted(AUTHOR_YEARS, key=len, reverse=True)
AUTHOR_RE = re.compile(
    r"\b("
    + "|".join(re.escape(alias) for alias in AUTHOR_ALIASES)
    + r")\.?(?!\w)(?:\s+[A-Z][A-Za-z]{0,12}\.)?(?:[^.;\n]{0,90})",
    re.IGNORECASE,
)

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


def normalize_word(word: str) -> str:
    """Normalize a clicked token while retaining Latin and Greek letters."""
    cleaned = unicodedata.normalize("NFC", word).strip()
    letter_ranges = "\u00c0-\u017e\u0391-\u03c9\u1f00-\u1fff"
    cleaned = re.sub(rf"^[^\w{letter_ranges}]+|[^\w{letter_ranges}]+$", "", cleaned, flags=re.UNICODE)
    return cleaned.casefold()


async def build_response(word: str, cutoff_year: int) -> dict[str, Any]:
    """Fetch external data and return the public API schema."""
    headers = {"User-Agent": USER_AGENT}
    timeout = httpx.Timeout(6.0, connect=3.0)
    async with httpx.AsyncClient(
        headers=headers,
        follow_redirects=True,
        timeout=timeout,
        trust_env=False,
    ) as client:
        morphology = await fetch_morphology(client, word)
        lemmas = unique_lemmas(morphology, word)
        lexicon = await fetch_lexicon(client, lemmas, cutoff_year)
        etymology = await fetch_etymology(client, lemmas[0] if lemmas else word)

    return {
        "word": word,
        "query_year": cutoff_year,
        "morphology": morphology,
        "etymology": etymology,
        "lexicon": lexicon,
    }


def unique_lemmas(morphology: list[dict[str, str]], fallback: str) -> list[str]:
    lemmas: list[str] = []
    for path in morphology:
        lemma = path.get("lemma", "").strip()
        if lemma and lemma not in lemmas:
            lemmas.append(lemma)
    if fallback and fallback not in lemmas:
        lemmas.append(fallback)
    return lemmas[:6]


async def fetch_morphology(client: httpx.AsyncClient, word: str) -> list[dict[str, str]]:
    """Fetch and parse Perseus morphology paths for a Latin token."""
    for params in ({"lang": "la", "lookup": word}, {"lang": "la", "text": word}):
        try:
            response = await client.get(PERSEUS_MORPH_URL, params=params)
            if response.status_code == 200 and response.text.strip():
                paths = parse_perseus_morphology(response.text)
                if paths:
                    return paths
        except httpx.HTTPError:
            continue
    return []


def parse_perseus_morphology(xml_text: str) -> list[dict[str, str]]:
    """Convert Perseus XML analyses into Morphological Paths."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    analyses = [node for node in root.iter() if local_name(node.tag) == "analysis"]
    if not analyses:
        analyses = [root]

    paths: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for node in analyses:
        lemma = first_child_text(node, "lemma")
        pos = first_child_text(node, "pos")
        if not lemma and not pos:
            continue

        detail_parts = []
        for field in (
            "form",
            "case",
            "number",
            "gender",
            "person",
            "tense",
            "mood",
            "voice",
            "degree",
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


async def fetch_lexicon(
    client: httpx.AsyncClient, lemmas: list[str], cutoff_year: int
) -> list[dict[str, Any]]:
    """Fetch dictionary entries and apply the chronological filter."""
    raw_entries: list[dict[str, str]] = []
    for lemma in lemmas:
        raw_entries.extend(await fetch_cld_json_entries(client, lemma))
        if not raw_entries:
            raw_entries.extend(await fetch_cld_html_entries(client, lemma))
        if raw_entries:
            break

    return filter_by_date(raw_entries, cutoff_year)


async def fetch_cld_json_entries(client: httpx.AsyncClient, lemma: str) -> list[dict[str, str]]:
    """Fetch CLD JSON and keep only dictionary descriptions."""
    url = CLD_LEMMA_JSON_URL.format(lemma=quote(lemma, safe=""))
    try:
        response = await client.get(url, params={"language": "lat", "options": "case-sensitive"})
        if response.status_code != 200:
            return []
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return []

    entries: list[dict[str, str]] = []
    for record in payload.get("data", []):
        if not isinstance(record, dict):
            continue
        record_lemma = str(record.get("lemma") or lemma)
        for description in record.get("descriptions", []):
            if not isinstance(description, dict):
                continue
            dictionary = str(description.get("dictionary") or "")
            if dictionary not in {"Lewis Short", "LSJ"}:
                continue
            text = BeautifulSoup(str(description.get("description") or ""), "html.parser").get_text(" ", strip=True)
            entries.extend(entries_from_text_blocks(record_lemma, [text], f"CLD JSON / {dictionary}"))
    return entries


async def fetch_cld_html_entries(client: httpx.AsyncClient, lemma: str) -> list[dict[str, str]]:
    """Fetch and parse the public CLD lemma page for Lewis and Short text."""
    try:
        response = await client.get(CLD_LEMMA_HTML_URL.format(lemma=quote(lemma, safe="")))
        if response.status_code != 200:
            return []
    except httpx.HTTPError:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    entries: list[dict[str, str]] = []
    for heading in soup.find_all(["h3", "h4"]):
        title = heading.get_text(" ", strip=True)
        if "Lewis Short" not in title and "LSJ" not in title:
            continue

        blocks: list[str] = []
        for sibling in heading.next_siblings:
            if isinstance(sibling, Tag) and sibling.name in {"h2", "h3", "h4"}:
                break
            if isinstance(sibling, Tag):
                if sibling.name == "li":
                    blocks.append(sibling.get_text(" ", strip=True))
                else:
                    blocks.extend(li.get_text(" ", strip=True) for li in sibling.find_all("li"))
                    if sibling.name in {"p", "div"}:
                        text = sibling.get_text(" ", strip=True)
                        if text:
                            blocks.append(text)

        entries.extend(entries_from_text_blocks(lemma, blocks, "CLD HTML"))

    return entries


def extract_strings(value: Any) -> list[str]:
    """Recursively pull human-readable strings from unknown JSON shapes."""
    strings: list[str] = []
    if isinstance(value, str):
        text = " ".join(value.split())
        if text:
            strings.append(text)
    elif isinstance(value, dict):
        for nested in value.values():
            strings.extend(extract_strings(nested))
    elif isinstance(value, list):
        for nested in value:
            strings.extend(extract_strings(nested))
    return strings


def entries_from_text_blocks(lemma: str, blocks: list[str], source: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for block in blocks:
        text = clean_text(block)
        if not text or text in seen:
            continue
        seen.add(text)
        entries.append(
            {
                "lemma": lemma,
                "source": source,
                "definition": text,
            }
        )
    return entries


async def fetch_etymology(client: httpx.AsyncClient, lemma: str) -> dict[str, str]:
    """Fetch the Latin etymology paragraph from Wiktionary without summarizing it."""
    params = {
        "action": "parse",
        "page": lemma,
        "prop": "text",
        "format": "json",
        "redirects": "1",
    }
    try:
        response = await client.get(WIKTIONARY_API_URL, params=params)
        if response.status_code != 200:
            return {"root": "", "literal_meaning": ""}
        html = response.json().get("parse", {}).get("text", {}).get("*", "")
    except (httpx.HTTPError, ValueError):
        return {"root": "", "literal_meaning": ""}

    soup = BeautifulSoup(html, "html.parser")
    etymology_text = extract_wiktionary_latin_etymology(soup)
    return {
        "root": extract_root_phrase(etymology_text),
        "literal_meaning": etymology_text,
    }


def extract_wiktionary_latin_etymology(soup: BeautifulSoup) -> str:
    latin_heading = soup.find(id="Latin")
    if not latin_heading:
        return ""

    latin_section = latin_heading.find_parent(["h2", "h3", "h4"])
    if not latin_section:
        return ""

    for sibling in latin_section.next_siblings:
        if isinstance(sibling, Tag) and sibling.name == "h2":
            break
        if not isinstance(sibling, Tag):
            continue
        heading_text = sibling.get_text(" ", strip=True)
        if sibling.name in {"h3", "h4"} and "Etymology" in heading_text:
            paragraphs: list[str] = []
            for ety_sibling in sibling.next_siblings:
                if isinstance(ety_sibling, Tag) and ety_sibling.name in {"h2", "h3", "h4"}:
                    break
                if isinstance(ety_sibling, Tag) and ety_sibling.name in {"p", "ul", "ol"}:
                    text = clean_text(ety_sibling.get_text(" ", strip=True))
                    if text:
                        paragraphs.append(text)
                if paragraphs:
                    break
            return " ".join(paragraphs)
    return ""


def extract_root_phrase(etymology_text: str) -> str:
    if not etymology_text:
        return ""
    match = re.search(r"\b(?:From|from)\s+([^.;]+)", etymology_text)
    if match:
        return clean_text(match.group(1))[:160]
    return ""


def filter_by_date(raw_entries: list[dict[str, str]], cutoff_year: int) -> list[dict[str, Any]]:
    """Drop lexicon segments that are securely later than the requested cutoff."""
    filtered: list[dict[str, Any]] = []
    for entry in raw_entries:
        definition = clean_text(entry.get("definition", ""))
        if not definition:
            continue

        kept_segments: list[str] = []
        kept_citations: list[str] = []
        for segment in split_definition_segments(definition):
            citations = extract_dated_citations(segment)
            if not citations:
                kept_segments.append(segment)
                continue

            dated = [citation for citation in citations if citation.year is not None]
            future_only = bool(dated) and all(citation.year is not None and citation.year > cutoff_year for citation in citations)
            if future_only:
                continue

            stripped_segment = strip_future_citations(segment, cutoff_year)
            if stripped_segment:
                kept_segments.append(stripped_segment)
            for citation in citations:
                if citation.year is None:
                    kept_citations.append(f"{citation.text} (date unverified)")
                elif citation.year <= cutoff_year:
                    kept_citations.append(f"{citation.text} ({format_year(citation.year)})")

        if not kept_segments:
            continue

        if not kept_citations:
            kept_citations = ["No dated citation parsed (date unverified)"]

        filtered.append(
            {
                "sense": f"{entry.get('lemma', 'Lemma')} / {entry.get('source', 'lexicon')} / Sense {len(filtered) + 1}",
                "definition": clean_text(" ".join(kept_segments)),
                "citations": dedupe_preserve_order(kept_citations),
            }
        )

    return filtered


def split_definition_segments(definition: str) -> list[str]:
    segments = re.split(r";\s*", definition)
    cleaned = [clean_text(segment) for segment in segments if clean_text(segment)]
    return cleaned or [definition]


def extract_dated_citations(text: str) -> list[DatedCitation]:
    citations: list[DatedCitation] = []
    for match in AUTHOR_RE.finditer(text):
        citation_text = clean_text(match.group(0).rstrip(" ,;:."))
        citations.append(DatedCitation(citation_text, parse_year_from_text(citation_text)))

    explicit_year = parse_year_from_text(text)
    if explicit_year is not None and not citations:
        citations.append(DatedCitation(clean_text(text[:120]), explicit_year))

    return dedupe_citations(citations)


def strip_future_citations(text: str, cutoff_year: int) -> str:
    """Remove securely future citation snippets from an otherwise retained block."""
    matches = list(AUTHOR_RE.finditer(text))
    if not matches:
        return text

    stripped = text
    for match in reversed(matches):
        citation_text = match.group(0)
        year = parse_year_from_text(citation_text)
        if year is None or year <= cutoff_year:
            continue

        start, end = match.span()
        while start > 0 and stripped[start - 1] in " ,;:\u2014-":
            start -= 1
        stripped = f"{stripped[:start]} {stripped[end:]}"

    return clean_text(stripped)


def parse_year_from_text(text: str) -> int | None:
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

    author_match = AUTHOR_RE.search(text)
    if author_match:
        alias = author_match.group(1).rstrip(".").casefold()
        return AUTHOR_YEARS.get(alias)

    return None


def format_year(year: int) -> str:
    if year < 0:
        return f"c. {abs(year)} BCE"
    return f"c. {year} CE"


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def dedupe_citations(citations: list[DatedCitation]) -> list[DatedCitation]:
    seen: set[str] = set()
    result: list[DatedCitation] = []
    for citation in citations:
        if citation.text in seen:
            continue
        seen.add(citation.text)
        result.append(citation)
    return result
