import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from conceptladder.cli import create_run, fingerprint, grade, load_packs, materialize, parse_letter


class TestConceptLadder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = load_packs()

    def test_dataset_shape(self):
        self.assertEqual(len(self.items), 36)
        self.assertEqual(len({x["pack"] for x in self.items}), 3)
        self.assertEqual(len({(x["pack"], x["concept"]) for x in self.items}), 9)

    def test_balanced_answers(self):
        from collections import Counter
        self.assertEqual(Counter(materialize(i, 17)[1] for i in self.items), dict.fromkeys("ABCD", 9))

    def test_determinism(self):
        self.assertEqual(materialize(self.items[0], 17), materialize(self.items[0], 17))
        self.assertNotEqual(materialize(self.items[0], 17), materialize(self.items[0], 18))

    def test_parse(self):
        self.assertEqual(parse_letter("answer: c"), "C")
        self.assertEqual(parse_letter("D."), "D")
        self.assertEqual(parse_letter("B. Readers and one writer can proceed concurrently"), "B")
        self.assertEqual(parse_letter("Answer: A. A specific technical option"), "A")
        self.assertIsNone(parse_letter("B, because the standard says so"))
        self.assertIsNone(parse_letter("E"))

    def test_perfect_and_depth_gate(self):
        run = {
            "format": "conceptladder-run-v1",
            "seed": 17,
            "dataset_sha256": fingerprint(self.items),
            "responses": [{"id": i["id"], "prediction": materialize(i, 17)[1]} for i in self.items],
        }
        perfect = grade(run, self.items)
        self.assertEqual(perfect["accuracy"], 1.0)
        self.assertEqual(perfect["mean_contiguous_depth"], 4.0)
        first = self.items[0]
        run["responses"][0]["prediction"] = None
        partial = grade(run, self.items)
        self.assertEqual(partial["correct"], 35)
        self.assertEqual(partial["depths"][first["pack"] + "/" + first["concept"]], 0)

    def test_dataset_hash_guard(self):
        run = {"seed": 17, "dataset_sha256": "wrong", "responses": []}
        with self.assertRaises(ValueError):
            grade(run, self.items)


if __name__ == "__main__":
    unittest.main()
