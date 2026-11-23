import unittest
from collections import Counter
from types import SimpleNamespace
from unittest.mock import patch

from conceptladder.calibrated import load_ladder
from conceptladder.cli import create_run, fingerprint, grade, load_suite, materialize


class CalibrationSuiteTests(unittest.TestCase):
    def test_deterministic_with_distinct_hashes(self):
        orig = load_suite("hard", "all", 17, 4)
        calibrated = load_ladder(17, 4)
        self.assertEqual(len(calibrated), 240)
        self.assertEqual(fingerprint(orig), "7846cfd3ab316a452bcacd264f1ea4b90fc3dc7619369a713a6289bdcce0f2db")
        self.assertNotEqual(fingerprint(orig),fingerprint(calibrated))
        self.assertEqual(fingerprint(calibrated), fingerprint(load_ladder(17,4)))
        self.assertNotEqual(fingerprint(calibrated),fingerprint(load_ladder(41,4)))
        self.assertEqual(len(load_ladder(17,1, "sys-hard")),12)

    def test_level_one_choices(self):
        for seed in (17,41,91):
            items=load_ladder(seed,4)
            one=[i for i in items if i["level"]==1]
            self.assertEqual(len(one),60)
            self.assertTrue(all(len(i["wrong"])==3 and len({i["correct"],*i["wrong"]})==4 for i in one))
            self.assertTrue(all(all(len(v)==len(i["correct"]) for v in i["wrong"]) for i in one))
            letters=Counter(materialize(x,seed)[1] for x in items)
            self.assertTrue(all(letters[c]>=30 for c in "ABCD"))

    def test_answer_seed_is_separate(self):
        items=load_ladder(17,1)
        self.assertEqual(fingerprint(items),fingerprint(load_ladder(17,1)))
        self.assertNotEqual([materialize(x,17)[1] for x in items],[materialize(x,63)[1] for x in items])
        args=SimpleNamespace(url="http://localhost/v1",model="mock",api_key="",timeout=1,
                max_tokens=64,seed=17,answer_seed=63,suite="ladder",packs="all",variants=1,delay=0)
        with patch("conceptladder.cli.request_answer", return_value="A"):
            run=create_run(args,items)
        self.assertEqual(run["seed"],17)
        self.assertEqual(run["answer_seed"],63)
        self.assertEqual(run["suite"],"ladder")
        stats=grade(run,items)
        expected=sum(materialize(x,63)[1]=="A" for x in items)
        self.assertEqual(stats["correct"],expected)
        fallback=dict(run)
        fallback.pop("answer_seed")
        self.assertNotEqual(grade(fallback,items)["correct"],stats["correct"])


if __name__=="__main__":
    unittest.main()
