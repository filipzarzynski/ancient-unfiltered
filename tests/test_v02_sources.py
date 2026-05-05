"""v0.2 source routing and Greek parser tests.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

import unittest

from sources.chronology import filter_lexicon_entries, parse_year_from_text
from sources.common import detect_language, greek_to_perseus_lookup
from sources.morphology import parse_perseus_morphology
from sources.passages import PLATO_APOLOGY_RE, retrieve_source_sentence


class V02SourceTests(unittest.TestCase):
    def test_detect_language_prefers_script(self) -> None:
        self.assertEqual(detect_language("κατηγόρων")[0], "greek")
        self.assertEqual(detect_language("Gallia")[0], "latin")
        language, warnings = detect_language("λόγος logos")
        self.assertEqual(language, "greek")
        self.assertTrue(warnings)

    def test_greek_to_perseus_lookup_matches_morpheus_style(self) -> None:
        self.assertEqual(greek_to_perseus_lookup("κατηγόρων"), "kathgorwn")
        self.assertEqual(greek_to_perseus_lookup("λόγος"), "logos")
        self.assertEqual(greek_to_perseus_lookup("ἄνδρες"), "andres")

    def test_greek_author_dates_are_estimates(self) -> None:
        self.assertEqual(parse_year_from_text("Pl. Ap. 18a", "greek"), -399)
        self.assertEqual(parse_year_from_text("Hdt. 3.71", "greek"), -440)
        self.assertEqual(parse_year_from_text("PFlor. 6.6 (iii AD)", "greek"), 250)

    def test_greek_future_citations_are_removed_from_definition(self) -> None:
        raw = [
            {
                "lemma": "κατήγορος",
                "source": "fixture",
                "definition": "accuser, Hdt. 3.71, And. 4.16, Pl. Ap. 18a (pl.), Apoc. 12.10, PFlor. 6.6 (iii AD).",
            }
        ]

        filtered = filter_lexicon_entries(raw, -399, "greek")

        self.assertEqual(len(filtered), 1)
        self.assertIn("Pl. Ap. 18a", filtered[0]["definition"])
        self.assertNotIn("Apoc", filtered[0]["definition"])
        self.assertNotIn("PFlor", filtered[0]["definition"])
        self.assertEqual([citation["raw"] for citation in filtered[0]["citations"]], ["Hdt. 3.71", "And. 4.16", "Pl. Ap. 18a (pl.)"])

    def test_greek_morphology_shape_keeps_source_metadata(self) -> None:
        xml = """
        <analyses>
          <analysis>
            <form lang="greek">κατηγόρων</form>
            <lemma>κατήγορος</lemma>
            <expandedForm>κατηγόρων</expandedForm>
            <pos>adj</pos>
            <number>pl</number>
            <gender>masc</gender>
            <case>gen</case>
          </analysis>
        </analyses>
        """

        paths = parse_perseus_morphology(xml, "greek")

        self.assertEqual(paths[0]["lemma"], "κατήγορος")
        self.assertEqual(paths[0]["pos"], "Adjective")
        self.assertEqual(paths[0]["source"], "Perseus Morpheus")
        self.assertEqual(paths[0]["language"], "greek")

    def test_plato_apology_citation_regex(self) -> None:
        match = PLATO_APOLOGY_RE.search("Pl. Ap. 18a (pl.)")
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "18a")

    def test_unsupported_source_sentence_returns_unavailable_tuple(self) -> None:
        class UnusedClient:
            pass

        estimate, translation, warning = self.run_async(
            retrieve_source_sentence(UnusedClient(), "Hdt. 3.71", "κατηγόρων", ["κατήγορος"])
        )

        self.assertIsNone(estimate)
        self.assertIsNone(translation)
        self.assertIsNone(warning)

    @staticmethod
    def run_async(coro):
        import asyncio

        return asyncio.run(coro)


if __name__ == "__main__":
    unittest.main()
