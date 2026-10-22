"""Prevent a triangle prerequisite and unpaid/incorrect reference covers."""
from pathlib import Path
import json
import unittest

from az_edge_cover import covers


def row(key, a, b, doses=(1, 2), stock="s"):
    return {"key": (key,), "member": "m", "project": "p", "cell": "c", "stock": stock,
            "plate": "plate", "axes": {a: set(doses), b: set(doses)}}


class EdgeCoverTests(unittest.TestCase):
    def accepted(self, records):
        return next(r["eligible_two_bundles"] for r in covers(records, True) if r["target"] == ("target",))

    def test_no_triangle_needed(self):
        self.assertTrue(self.accepted([row("target", "A", "B"), row("ac", "A", "C"), row("bd", "B", "D")]))

    def test_missing_dose_is_not_imputed(self):
        self.assertFalse(self.accepted([row("target", "A", "B"), row("ac", "A", "C", doses=(1,)), row("bd", "B", "D")]))

    def test_other_stock_cannot_supply_reference(self):
        self.assertFalse(self.accepted([row("target", "A", "B"), row("ac", "A", "C", stock="other"), row("bd", "B", "D")]))

    def test_target_replicate_is_excluded(self):
        self.assertFalse(self.accepted([row("target", "A", "B"), row("repeat", "A", "B")]))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EdgeCoverTests))
    out = Path(__file__).resolve().parents[2] / "log/20261022/intervention_program_renewal/az_design/EDGE_TEST.json"
    out.write_text(json.dumps({"tests_run": result.testsRun, "success": result.wasSuccessful(), "errors": len(result.errors), "failures": len(result.failures)}, indent=2), encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
