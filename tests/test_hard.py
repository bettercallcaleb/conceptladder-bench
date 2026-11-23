import unittest
from collections import Counter

from conceptladder.cli import fingerprint, grade, materialize
from conceptladder.hardgen import BUILDERS, load_hard


class HardSuiteTests(unittest.TestCase):
    def test_all_families_and_variants(self):
        items=load_hard(seed=17,variants=4)
        self.assertEqual(len(BUILDERS),15)
        self.assertEqual(len(items),240)
        self.assertEqual(fingerprint(items), "7846cfd3ab316a452bcacd264f1ea4b90fc3dc7619369a713a6289bdcce0f2db")
        self.assertEqual(len({x["pack"] for x in items}),4)
        self.assertEqual(len({x["concept"] for x in items}),60)
        self.assertEqual(len({x["id"] for x in items}),240)
        self.assertTrue(all(len({x["correct"],*x["wrong"]})==4 for x in items))
        self.assertTrue(all(all(len(v)==len(x["correct"]) for v in x["wrong"]) for x in items))

    def test_deterministic_and_variable(self):
        a=load_hard(17,4)
        b=load_hard(17,4)
        c=load_hard(18,4)
        self.assertEqual(fingerprint(a),fingerprint(b))
        self.assertNotEqual(fingerprint(a),fingerprint(c))
        self.assertEqual(len(load_hard(17,1)),60)

    def test_balanced_not_predictable_by_level(self):
        items=load_hard(17,4)
        answer_counts=Counter(materialize(item,17)[1] for item in items)
        self.assertTrue(all(answer_counts[c]>40 for c in "ABCD"),answer_counts)
        for concept in {x["concept"] for x in items}:
            positions=[materialize(x,17)[1] for x in items if x["concept"]==concept]
            self.assertEqual(len(positions),4)
        sample=items[:12]
        self.assertGreater(len(set(materialize(x,17)[1] for x in sample)),2)

    def test_perfect_and_first_level_break(self):
        items=load_hard(17,1)
        run={"seed":17,"dataset_sha256":fingerprint(items),
             "responses":[{"id":x["id"],"prediction":materialize(x,17)[1]} for x in items]}
        result=grade(run,items)
        self.assertEqual(result["correct"],60)
        self.assertEqual(result["mean_contiguous_depth"],4.0)
        run["responses"][0]["prediction"]=None
        result=grade(run,items)
        self.assertEqual(result["correct"],59)
        self.assertEqual(result["depths"][f"{items[0]['pack']}/{items[0]['concept']}"],0)

    def test_oracles_survive_other_seeds(self):
        for seed in (1,7,17,91):
            items=load_hard(seed,2)
            self.assertEqual(len(items),120)
            self.assertTrue(all(x["prompt"] and x["correct"] not in x["wrong"] for x in items))


if __name__=="__main__":
    unittest.main()
