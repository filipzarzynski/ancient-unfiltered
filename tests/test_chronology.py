"""Core parser tests for the Local Diachronic Philology Engine.

Copyright (C) 2026 Filip Zarzynski

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
"""

from __future__ import annotations

import unittest

from philology import filter_by_date, normalize_word, parse_perseus_morphology, parse_year_from_text


class ChronologyTests(unittest.TestCase):
    def test_author_dates_use_integer_timeline(self) -> None:
        self.assertEqual(parse_year_from_text("Plaut. Bacch. 3, 3"), -200)
        self.assertEqual(parse_year_from_text("Cic. Fam. 5, 20, 6"), -50)
        self.assertEqual(parse_year_from_text("Plin. 10, 61, 81"), 77)

    def test_explicit_dates_and_centuries_are_parsed(self) -> None:
        self.assertEqual(parse_year_from_text("c. 200 B.C."), -200)
        self.assertEqual(parse_year_from_text("A.D. 150"), 150)
        self.assertEqual(parse_year_from_text("late 1st cent. A.D."), 75)

    def test_future_only_sense_is_dropped(self) -> None:
        raw = [
            {
                "lemma": "testis",
                "source": "fixture",
                "definition": "A future usage only, Plin. 10, 61, 81.",
            },
            {
                "lemma": "testis",
                "source": "fixture",
                "definition": "An early usage, Plaut. Bacch. 3, 3.",
            },
        ]

        filtered = filter_by_date(raw, -50)

        self.assertEqual(len(filtered), 1)
        self.assertIn("early usage", filtered[0]["definition"])
        self.assertIn("c. 200 BCE", filtered[0]["citations"][0])

    def test_unknown_dates_are_retained_and_flagged(self) -> None:
        raw = [
            {
                "lemma": "testis",
                "source": "fixture",
                "definition": "A poorly anchored usage in an abbreviated scholion.",
            }
        ]

        filtered = filter_by_date(raw, -50)

        self.assertEqual(len(filtered), 1)
        self.assertIn("date unverified", filtered[0]["citations"][0])

    def test_future_citations_are_stripped_from_mixed_blocks(self) -> None:
        raw = [
            {
                "lemma": "rivalis",
                "source": "fixture",
                "definition": "An early anchor, Plaut. Stich. 3, 1, 30; a later anchor, Suet. Oth. 3.",
            }
        ]

        filtered = filter_by_date(raw, -50)

        self.assertEqual(len(filtered), 1)
        self.assertIn("Plaut", filtered[0]["definition"])
        self.assertNotIn("Suet", filtered[0]["definition"])
        self.assertNotIn("Oth", filtered[0]["definition"])
        self.assertEqual(len(filtered[0]["citations"]), 1)

    def test_perseus_morphology_xml_is_flattened(self) -> None:
        xml = """
        <analyses>
          <analysis>
            <form>Gallia</form>
            <lemma>Gallia</lemma>
            <pos>noun</pos>
            <case>nom</case>
            <number>sg</number>
            <gender>fem</gender>
          </analysis>
        </analyses>
        """

        paths = parse_perseus_morphology(xml)

        self.assertEqual(paths[0]["path"], "Path A")
        self.assertEqual(paths[0]["lemma"], "Gallia")
        self.assertEqual(paths[0]["pos"], "Noun")
        self.assertIn("case: nom", paths[0]["details"])

    def test_normalize_word_keeps_letters_and_strips_punctuation(self) -> None:
        self.assertEqual(normalize_word("Gallia,"), "gallia")
        self.assertEqual(normalize_word("r\u012bv\u0101lem"), "r\u012bv\u0101lem")


if __name__ == "__main__":
    unittest.main()
