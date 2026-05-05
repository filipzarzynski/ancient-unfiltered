"""FastAPI entry point for the Local Diachronic Philology Engine.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from corpus import (
    CorpusValidationError,
    build_export,
    corpus_summary,
    import_corpus_patch,
    load_seed_corpus,
    validate_entry,
)
from database import get_cached_query, init_db, set_cached_query
from philology import build_response, normalize_word


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DOCS_DIR = BASE_DIR / "docs"

app = FastAPI(
    title="Ancient Unfiltered",
    version="0.3.0",
    description="Local-first ancient language lookup and matched-pair corpus explorer.",
)

init_db()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/demo", StaticFiles(directory=DOCS_DIR, html=True), name="demo")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/query")
async def query(
    word: str = Query(..., min_length=1, max_length=80),
    year: int = Query(..., ge=-3000, le=2100),
    language: str = Query("auto", pattern="^(auto|latin|greek)$"),
    context: str = Query("", max_length=2000),
    token_index: int | None = Query(None, ge=0),
) -> dict:
    normalized = normalize_word(word)
    if not normalized:
        raise HTTPException(status_code=400, detail="The query word contains no searchable letters.")

    cached = get_cached_query(normalized, year, language)
    if cached is not None:
        cached["local_context"] = {"sentence": context, "token_index": token_index}
        return cached

    response = await build_response(normalized, year, language, context, token_index)
    cached_response = {**response, "local_context": {"sentence": "", "token_index": None}}
    set_cached_query(normalized, year, cached_response, language)
    return response


@app.get("/api/corpus/seed")
async def seed_corpus() -> dict:
    corpus = load_seed_corpus()
    return {**corpus, "summary": corpus_summary(corpus)}


@app.post("/api/corpus/validate")
async def validate_corpus_entry(entry: dict = Body(...)) -> dict:
    try:
        validate_entry(entry)
    except CorpusValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors) from exc
    return {"status": "valid evidence proposal", "entry": entry}


@app.post("/api/corpus/export")
async def export_corpus_patch(payload: dict = Body(...)) -> dict:
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise HTTPException(status_code=422, detail=["entries must be a list"])
    source = payload.get("source", "local-browser")
    try:
        return build_export(entries, str(source))
    except CorpusValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors) from exc


@app.post("/api/corpus/import")
async def import_corpus(payload: dict = Body(...)) -> dict:
    try:
        return import_corpus_patch(payload)
    except CorpusValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors) from exc
