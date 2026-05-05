"""v0.3 matched-pair corpus contract tests.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

import json
import unittest
from collections import Counter
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from corpus import CorpusValidationError, build_export, import_corpus_patch, validate_entry
from main import app


CORPUS_PATH = Path(__file__).resolve().parents[1] / "docs" / "corpus" / "v0.3-seed.json"


class V03CorpusSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        cls.entries = cls.corpus["entries"]

    def test_seed_version_is_v03_release(self):
        self.assertEqual(self.corpus["version"], "v0.3")

    def test_seed_has_four_subjects_with_four_entries_each(self):
        counts = Counter(entry["theme"] for entry in self.entries)
        self.assertEqual(len(self.entries), 16)
        self.assertEqual(
            counts,
            {
                "friendship": 4,
                "community": 4,
                "intelligence": 4,
                "love": 4,
            },
        )

    def test_entries_have_required_matched_pair_fields(self):
        required = {
            "id",
            "theme",
            "author",
            "work",
            "citation",
            "current_english",
            "critical_original",
            "path_options",
            "alternative_translations",
            "example_selected_output",
        }
        for entry in self.entries:
            with self.subTest(entry=entry["id"]):
                self.assertTrue(required.issubset(entry))
                self.assertEqual(entry["critical_original"]["language"], "grc")
                self.assertIn("source_url", entry["critical_original"])
                self.assertGreaterEqual(len(entry["path_options"]), 3)
                self.assertGreaterEqual(len(entry["alternative_translations"]), 3)

    def test_seed_language_avoids_authoritative_claims(self):
        joined = json.dumps(self.corpus, ensure_ascii=False).lower()
        banned = [
            "correct translation",
            "true interpretation",
            "definitive translation",
            "authoritative answer",
        ]
        for phrase in banned:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, joined)

    def test_entry_validation_rejects_missing_provenance(self):
        entry = deepcopy(self.entries[0])
        del entry["critical_original"]["source_url"]

        with self.assertRaises(CorpusValidationError) as context:
            validate_entry(entry)

        self.assertTrue(any("source_url" in error for error in context.exception.errors))

    def test_export_import_roundtrip_preserves_selected_paths(self):
        entry = deepcopy(self.entries[0])
        entry["selected_paths"] = {"φιλίας": "friendly relation", "κτῆσις": "securing"}

        exported = build_export([entry], "unit-test")
        imported = import_corpus_patch(exported)

        self.assertEqual(imported["entries"][0]["selected_paths"], entry["selected_paths"])
        self.assertEqual(imported["status"], "validated evidence proposal")

    def test_corpus_api_serves_seed_and_rejects_bad_import(self):
        client = TestClient(app)

        seed_response = client.get("/api/corpus/seed")
        self.assertEqual(seed_response.status_code, 200)
        self.assertEqual(seed_response.json()["summary"]["entry_count"], 16)

        bad_entry = deepcopy(self.entries[0])
        bad_entry["critical_original"]["source_url"] = ""
        import_response = client.post(
            "/api/corpus/import",
            json={"version": "v0.3-export", "entries": [bad_entry]},
        )
        self.assertEqual(import_response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
