"""Etymology retrieval from Wiktionary parse output.

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
from bs4 import BeautifulSoup, Tag

from sources.common import clean_text


WIKTIONARY_API_URL = "https://en.wiktionary.org/w/api.php"


async def fetch_etymology(client: httpx.AsyncClient, lemma: str, language: str) -> dict[str, Any]:
    """Fetch source etymology text without summarizing it."""
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
            return empty_etymology()
        html = response.json().get("parse", {}).get("text", {}).get("*", "")
    except (httpx.HTTPError, ValueError):
        return empty_etymology()

    soup = BeautifulSoup(html, "html.parser")
    etymology_text = extract_wiktionary_etymology(soup, "Latin" if language == "latin" else "Ancient Greek")
    if not etymology_text and language == "greek":
        etymology_text = extract_wiktionary_etymology(soup, "Greek")

    root = extract_root_phrase(etymology_text)
    items = []
    if etymology_text:
        items.append(
            {
                "text": etymology_text,
                "source": "Wiktionary parse API",
                "date_status": "unverified",
            }
        )

    return {
        "root": root,
        "literal_meaning": etymology_text,
        "items": items,
    }


def empty_etymology() -> dict[str, Any]:
    return {"root": "", "literal_meaning": "", "items": []}


def extract_wiktionary_etymology(soup: BeautifulSoup, language_heading: str) -> str:
    heading = soup.find(id=language_heading)
    if not heading:
        return ""

    language_section = heading.find_parent(["h2", "h3", "h4"])
    if not language_section:
        return ""

    for sibling in language_section.next_siblings:
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
