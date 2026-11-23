import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from conceptladder.cli import create_run, grade, load_suite, materialize
from conceptladder.reporting import inspect_runs


class ReportingTests(unittest.TestCase):
    def test_exact_value_reparse(self):
        from conceptladder.cli import fingerprint
        items=load_suite("ladder","db-hard",17,1)
        rows=[{"id":i["id"],"prediction":None,"raw_response":i["correct"],"error":"unparseable"} for i in items]
        run={"format":"conceptladder-run-v1","model":"value-only","suite":"ladder","variants":1,
             "seed":17,"answer_seed":17,"dataset_sha256":fingerprint(items),"responses":rows}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"values.json"
            path.write_text(json.dumps(run))
            output=inspect_runs([path])
            self.assertEqual(output["forms"][0]["correct"],12)
            self.assertEqual(output["forms"][0]["invalid"],0)

    def test_calibration_report_and_reparse(self):
        items=load_suite("ladder","db-hard",17,1)
        with tempfile.TemporaryDirectory() as folder:
            paths=[]
            for model, answers in [
                ("base", lambda x: materialize(x,63)[1]),
                ("candidate", lambda x: "A"),
            ]:
                rows=[]
                for item in items:
                    letter=answers(item)
                    rows.append({
                        "id":item["id"],
                        "prediction":None if model=="base" else letter,
                        "raw_response":letter+"\n\nA short explanation." if model=="base" else letter,
                        "error":"unparseable" if model=="base" else None,
                    })
                run={
                    "format":"conceptladder-run-v1",
                    "model":model,
                    "suite":"ladder",
                    "variants":1,
                    "seed":17,
                    "answer_seed":63,
                    "dataset_sha256":__import__("conceptladder.cli",fromlist=["fingerprint"]).fingerprint(items),
                    "responses":rows,
                }
                path=Path(folder)/(model+".json")
                path.write_text(json.dumps(run))
                paths.append(path)
            output=inspect_runs(paths)
            self.assertEqual(len(output["matched_pairs"]),1)
            self.assertEqual(output["models"]["base"]["accuracy_mean"],1.0)
            self.assertEqual(output["source_runs"],2)
            self.assertEqual(output["forms"][0]["correct"],12)
            raw=inspect_runs(paths,reparse_raw=False)
            self.assertEqual(raw["forms"][0]["invalid"],12)


if __name__=="__main__":
    unittest.main()
