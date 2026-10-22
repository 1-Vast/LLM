"""Target-poison invariance and conflicting-design checks on synthetic rows."""
import csv
import io
import json
from pathlib import Path
import unittest

from az_design_census import FIELDS, project


class ProjectionTests(unittest.TestCase):
    def source(self, target, conflict=False):
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(FIELDS + ["inhibition", "INTENSITY", "lib1_RMSE"])
        row = {f: f for f in FIELDS}
        for i in range(2):
            row["POSITION"] = str(i + 1)
            row["lib1_conc"] = str(i + 1)
            row["MASTER_CELL_ID"] = str(i if conflict else 0)
            writer.writerow([row[f] for f in FIELDS] + [target, target, target])
        stream.seek(0)
        return stream

    def test_target_poison_cannot_change_design(self):
        reference = project(self.source("0.42"))
        for poison in ["NA", "", 'not-a-number,\"quoted\"', "1e99999999", "response\nmultiline"]:
            self.assertEqual(project(self.source(poison)), reference)
        self.assertEqual(len(reference), 1)
        self.assertEqual(reference[0]["rows"], 2)
        self.assertEqual(len(reference[0]["dose_pairs"]), 2)
        self.assertNotIn("inhibition", json.dumps(reference))

    def test_conflicting_identity_is_retained(self):
        records = project(self.source("arbitrary", conflict=True))
        self.assertEqual(len(records), 1)
        self.assertEqual(len(records[0]["metadata"]), 2)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProjectionTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    out = Path(__file__).resolve().parents[2] / "log/20261022/intervention_program_renewal/az_design/PROJECTION_TEST.json"
    out.write_text(json.dumps({"tests_run": result.testsRun, "success": result.wasSuccessful(), "failures": len(result.failures), "errors": len(result.errors)}, indent=2), encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
