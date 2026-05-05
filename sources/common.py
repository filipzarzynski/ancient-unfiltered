"""Shared normalization helpers for source clients.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

import re
import unicodedata


GREEK_RANGES = (
    (0x0370, 0x03FF),
    (0x1F00, 0x1FFF),
)

LATIN_RANGES = (
    (0x0041, 0x005A),
    (0x0061, 0x007A),
    (0x00C0, 0x024F),
)

GREEK_TO_PERSEUS = {
    "α": "a",
    "β": "b",
    "γ": "g",
    "δ": "d",
    "ε": "e",
    "ζ": "z",
    "η": "h",
    "θ": "q",
    "ι": "i",
    "κ": "k",
    "λ": "l",
    "μ": "m",
    "ν": "n",
    "ξ": "c",
    "ο": "o",
    "π": "p",
    "ρ": "r",
    "σ": "s",
    "ς": "s",
    "τ": "t",
    "υ": "u",
    "φ": "f",
    "χ": "x",
    "ψ": "y",
    "ω": "w",
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_word(word: str) -> str:
    """Normalize a clicked token while retaining Latin and Greek letters."""
    cleaned = unicodedata.normalize("NFC", word).strip()
    letter_ranges = "\u00c0-\u024f\u0370-\u03ff\u1f00-\u1fff"
    cleaned = re.sub(rf"^[^\w{letter_ranges}]+|[^\w{letter_ranges}]+$", "", cleaned, flags=re.UNICODE)
    return cleaned.casefold()


def strip_diacritics(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", stripped)


def strip_greek_diacritics(text: str) -> str:
    return strip_diacritics(text).replace("\u03c2", "\u03c3")


def char_in_ranges(ch: str, ranges: tuple[tuple[int, int], ...]) -> bool:
    code = ord(ch)
    return any(start <= code <= end for start, end in ranges)


def detect_language(text: str, requested: str = "auto") -> tuple[str, list[str]]:
    """Return latin, greek, or undetermined plus source warnings."""
    requested = requested.casefold()
    if requested in {"latin", "greek"}:
        return requested, []

    greek = sum(1 for ch in text if char_in_ranges(ch, GREEK_RANGES))
    latin = sum(1 for ch in text if char_in_ranges(ch, LATIN_RANGES))

    if greek and not latin:
        return "greek", []
    if latin and not greek:
        return "latin", []
    if greek and latin:
        return "greek", ["Mixed Greek and Latin characters detected; routed by Greek script presence."]
    return "undetermined", ["No Greek or Latin letters detected."]


def greek_to_perseus_lookup(text: str) -> str:
    """Convert Greek Unicode to the transliteration Perseus Morpheus accepts."""
    stripped = strip_greek_diacritics(text.casefold())
    return "".join(GREEK_TO_PERSEUS.get(ch, ch) for ch in stripped if ch.isalpha())


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
