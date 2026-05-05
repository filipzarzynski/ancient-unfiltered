"""SQLite cache for the Local Diachronic Philology Engine.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(os.environ.get("DPE_CACHE_PATH", "cache.db"))


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Create the local cache table if it does not already exist."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                word TEXT NOT NULL,
                cutoff_year INTEGER NOT NULL,
                response_data TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (word, cutoff_year)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_v2 (
                word TEXT NOT NULL,
                cutoff_year INTEGER NOT NULL,
                language TEXT NOT NULL,
                response_data TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (word, cutoff_year, language)
            )
            """
        )


def get_cached_query(word: str, cutoff_year: int, language: str = "latin") -> dict[str, Any] | None:
    """Return a cached response for a normalized word/year pair."""
    normalized = word.casefold()
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT response_data
            FROM cache_v2
            WHERE word = ? AND cutoff_year = ? AND language = ?
            """,
            (normalized, cutoff_year, language),
        ).fetchone()

    if row is None:
        return None

    return json.loads(row["response_data"])


def set_cached_query(
    word: str,
    cutoff_year: int,
    response_data: dict[str, Any],
    language: str = "latin",
) -> None:
    """Store a JSON-serializable response for a normalized word/year pair."""
    normalized = word.casefold()
    serialized = json.dumps(response_data, ensure_ascii=False, sort_keys=True)
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO cache_v2 (word, cutoff_year, language, response_data)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(word, cutoff_year, language) DO UPDATE SET
                response_data = excluded.response_data,
                created_at = CURRENT_TIMESTAMP
            """,
            (normalized, cutoff_year, language, serialized),
        )
