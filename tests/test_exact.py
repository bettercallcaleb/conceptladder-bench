import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from conceptladder.cli import create_run, fingerprint, grade, load_suite, materialize
from conceptladder.exact import load_exact, normalize_exact, parse_exact_response
from conceptladder.reporting import inspect_runs


class ExactSuiteTests(unittest.TestCase):
    def test_seeded_suite_and_old_hashes(self):
        old_hashes = {
            "classic": "158500c2f341adb653914ead56867ee83a60fe6b830b9c25cb81fb64db609a8a",
            "hard": "7846cfd3ab316a452bcacd264f1ea4b90fc3dc7619369a713a6289bdcce0f2db",
            "ladder": "b12651a8b59483e0a8af1f454b2e44e92c4b46c94c5d241b4ed7e6f8749dd62e",
        }
        for suite, sha in old_hashes.items():
            self.assertEqual(fingerprint(load_suite(suite, "all", 17, 4)), sha)
        items = load_exact(17, 4)
        self.assertEqual(len(items), 240)
        self.assertEqual(fingerprint(items), "437d994c1a2c027902951811f2fd43b45468bc2ed4fd78f3d90e63c97743011a")
        self.assertEqual(fingerprint(items), fingerprint(load_exact(17, 4)))
        self.assertNotEqual(fingerprint(items), fingerprint(load_exact(41, 4)))
        self.assertEqual(len({x["id"] for x in items}), 240)
        self.assertTrue(all("wrong" not in x and x["response_mode"] == "exact" for x in items))

    def test_no_exposed_options(self):
        for seed in (17, 41, 91):
            items = load_exact(seed, 4)
            for item in items:
                prompt, answer = materialize(item, 63)
                self.assertEqual(answer, item["correct"])
                self.assertEqual(prompt, item["prompt"])
                self.assertFalse(any(line.startswith(("A. ", "B. ", "C. ", "D. ")) for line in prompt.splitlines()))
                self.assertIsNotNone(normalize_exact(item["correct"], item["answer_format"]))

    def test_exact_parsing(self):
        cases = [
            ("008", "integer", "8"),
            ("Answer: 8\n\nHere is why.", "integer", "8"),
            ("First, count the segments.\nFINAL: 8", "integer", "8"),
            ("0x00a7", "hex4", "00A7"),
            ("0o644", "octal", "0644"),
            ("644", "octal", "0644"),
            ("if07", "interface", "if07"),
            ("517", "error_code", "0517"),
            ("zx", "text2", "zx"),
            ("Answer: 010011", "bitstring", "010011"),
        ]
        for raw, kind, expected in cases:
            item = {"response_mode": "exact", "answer_format": kind}
            self.assertEqual(parse_exact_response(raw, item), expected)
        invalid = [
            ("A", "integer"),
            ("8 or 9", "integer"),
            ("The answer is 8", "integer"),
            ("Answer: 8 and then 9", "integer"),
            ("0001", "text2"),
            ("0xzz00", "hex4"),
            ("xyz", "interface"),
            ("xyz", "octal"),
            ("01023", "bitstring"),
        ]
        for raw, kind in invalid:
            self.assertIsNone(parse_exact_response(raw, {"response_mode": "exact", "answer_format": kind}))

    def test_exact_grade_and_reparse(self):
        items = load_exact(17, 1, "db-hard")
        run = {
            "format": "conceptladder-run-v1",
            "model": "synthetic",
            "seed": 17,
            "answer_seed": 63,
            "suite": "exact",
            "variants": 1,
            "dataset_sha256": fingerprint(items),
            "responses": [{"id": item["id"], "prediction": item["correct"], "raw_response": item["correct"]}
                          for item in items],
        }
        self.assertEqual(grade(run, items)["correct"], 12)
        for row in run["responses"]:
            row["prediction"] = None
        self.assertEqual(grade(run, items)["correct"], 0)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.json"
            path.write_text(json.dumps(run))
            output = inspect_runs([path])
            self.assertEqual(output["forms"][0]["correct"], 12)
            self.assertEqual(output["forms"][0]["answer_positions"], {})

    def test_blind_baseline_guard(self):
        from conceptladder.audit import blind_audit
        audit = blind_audit(train_seeds=(17, 41), test_seeds=(91,), variants=4)
        self.assertLess(audit["aggregate_accuracy"], 0.20)
        self.assertEqual(audit["aggregate_total"], 240)
        self.assertEqual(audit["aggregate_correct"], 31)

    def test_exact_run_inference(self):
        items = load_exact(17, 1, "sys-hard")
        args = SimpleNamespace(url="http://unused", model="mock", api_key="",
                               timeout=1, max_tokens=64, seed=17, answer_seed=63,
                               suite="exact", packs="sys-hard", variants=1, delay=0)
        answer = {item["prompt"]: item["correct"] for item in items}
        def fake(url, model, prompt, api_key, timeout, max_tokens, hard=False, exact=False):
            self.assertTrue(exact)
            self.assertNotIn("\nA. ", prompt)
            return answer[prompt]
        with patch("conceptladder.cli.request_answer", side_effect=fake):
            run = create_run(args, items)
        self.assertEqual(grade(run, items)["correct"], 12)
        self.assertTrue(all(row["error"] is None for row in run["responses"]))

    def test_nonconstant_advanced_cases(self):
        for family, level in (("sqlite-wal-snapshots", 3), ("kubernetes-rbac-scope", 4)):
            values = Counter()
            for seed in (17, 41, 91):
                for item in load_exact(seed, 4):
                    if item["concept"].startswith(family) and item["level"] == level:
                        values[item["correct"]] += 1
            self.assertGreaterEqual(len(values), 3, (family, level, values))
        for seed in (17, 41, 91):
            rows = [i for i in load_exact(seed, 4) if i["concept"].startswith("sqlite-wal-snapshots") and i["level"] == 3]
            self.assertTrue(all(i["correct"] in ("0000", "0005", "0517") for i in rows))

    def test_variable_first_level_scenarios(self):
        for family in ("ipv4-fragment-offset", "kubernetes-rbac-scope", "tcp-send-window"):
            values = Counter()
            for seed in (17, 41, 91, 123, 777):
                for item in load_exact(seed, 4):
                    if item["concept"].startswith(family) and item["level"] == 1:
                        values[item["correct"]] += 1
            self.assertGreaterEqual(len(values), 3, (family, values))


if __name__ == "__main__":
    unittest.main()
