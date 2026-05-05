import json
import unittest
from collections import Counter
from pathlib import Path


CORPUS_PATH = Path(__file__).resolve().parents[1] / "docs" / "corpus" / "v0.3-seed.json"


class V03CorpusSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        cls.entries = cls.corpus["entries"]

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


if __name__ == "__main__":
    unittest.main()
