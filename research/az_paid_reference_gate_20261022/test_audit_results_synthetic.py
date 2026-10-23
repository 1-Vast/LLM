"""Independent auditor tests; no real-data/ZIP access, fitting, or method imports."""
from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

import numpy as np

import audit_results as audit


PHASE = audit.ROOT / "log/20261022/az_paid_reference_gate"
FIXTURE = next(PHASE / f"SYNTHETIC_INDEPENDENT_AUDIT_{i:02d}" for i in range(1, 10000)
               if not (PHASE / f"SYNTHETIC_INDEPENDENT_AUDIT_{i:02d}").exists())


class AuditorTests(unittest.TestCase):
    def test_multiple_master_identity_order_regression(self):
        # Frozen role membership is stored in hash order. The evaluation's
        # canonical ID order must preserve identities, not compare by position.
        design = {"role_cells": {"test": ["B", "C", "A"]}}
        assigned = audit.canonical_assigned_masters(design)
        ep = np.repeat([0, 1, 2], 6)
        master = np.repeat(["B", "C", "A"], 6)
        y = np.repeat([2., 8., 1.], 6)
        result, _ = audit.score_independent(y, np.zeros(18), ep, master, np.zeros((18, 2)),
            np.ones(18, bool), {str(e): list(range(e * 6, e * 6 + 5)) for e in range(3)},
            assigned, np.arange(18))
        self.assertEqual(result["assigned_masters"], ["A", "B", "C"])
        self.assertEqual(result["per_master"]["mae"], [1., 2., 8.])
        self.assertEqual(result["mae"], 11. / 3.)
        # Identical ID membership after a different stored order gives identical
        # finite-seed intervals. Permuting unlabeled positions would not suffice.
        other = audit.canonical_assigned_masters({"role_cells": {"test": ["C", "A", "B"]}})
        self.assertEqual(other, assigned)
        boot = audit.bootstrap_independent(result["per_master"]["mae"], [2., 4., 10.])
        self.assertEqual(boot["gain"], 5. / 3.)

    def test_default_cli_refuses_before_any_file_access(self):
        with patch.object(sys, "argv", ["audit_results.py"]), patch.object(audit, "audit") as run:
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                audit.main()
        self.assertEqual(caught.exception.code, 2)
        run.assert_not_called()

    def test_episode_then_master_macro_and_complete_panel(self):
        # MASTER A has two episodes; MASTER B one. A row or episode macro is wrong.
        ep = np.repeat([0, 1, 2], [6, 6, 6])
        master = np.repeat(["A", "A", "B"], [6, 6, 6])
        y = np.repeat([1., 3., 9.], 6)
        effect = np.zeros((18, 2))
        pred = np.zeros(18)
        rows = np.arange(100, 118)
        actions = {str(e): rows[ep == e][:5].tolist() for e in range(3)}
        metrics, records = audit.score_independent(y, pred, ep, master, effect,
                                                  np.ones(18, bool), actions, ["A", "B"], rows)
        self.assertEqual(metrics["mae"], 5.5)
        self.assertEqual(metrics["per_master"]["mae"], [2., 9.])
        self.assertEqual(metrics["utility"], 5.5)
        self.assertEqual(metrics["regret"], 0.)
        self.assertTrue(metrics["coverage_pass"])
        # Missing one label still permits forecast but removes the full episode
        # from recommendation. Its sealed action map must remain present.
        missing = y.copy()
        missing[0] = np.nan
        metrics, records = audit.score_independent(missing, pred, ep, master, effect,
                                                  np.ones(18, bool), actions, ["A", "B"], rows)
        self.assertEqual(metrics["forecast"]["episodes"], 3)
        self.assertEqual(metrics["forecast"]["finite_target_rows"], 17)
        self.assertEqual(metrics["recommendation"]["episodes"], 2)
        self.assertEqual(metrics["per_master_episode_counts"]["recommendation"], [1, 1])
        self.assertFalse(metrics["coverage_pass"])
        self.assertFalse(records[0]["recommendation"])
        with self.assertRaisesRegex(ValueError, "prediction-only"):
            audit.score_independent(missing, pred, ep, master, effect, np.ones(18, bool),
                                    {"1": actions["1"], "2": actions["2"]}, ["A", "B"], rows)

    def test_paid_effect_ranking_global_tie_and_target_missing_no_reselection(self):
        # Scores tie exactly although predictions differ. Global rows, not input
        # order, must break ties. The missing target is still a selected action.
        rows = np.array([16, 10, 15, 12, 14, 11])
        effect = np.column_stack([np.arange(6.) / 10, np.zeros(6)])
        pred = np.max(effect, axis=1)
        y = np.array([.9, np.nan, .7, .6, .5, .4])
        action = {"7": [10, 11, 12, 14, 15]}
        result, _ = audit.score_independent(y, pred, np.full(6, 7), np.full(6, "A"),
                                            effect, np.ones(6, bool), action, ["A"], rows)
        self.assertEqual(result["forecast"]["episodes"], 1)
        self.assertEqual(result["recommendation"]["episodes"], 0)
        with self.assertRaisesRegex(ValueError, "prediction-only"):
            audit.score_independent(y, pred, np.full(6, 7), np.full(6, "A"), effect,
                                    np.ones(6, bool), {"7": [11, 12, 14, 15, 16]}, ["A"], rows)

    def test_common_abstention_and_assigned_master_not_dropped(self):
        ep = np.repeat([0, 1], 6)
        valid = np.repeat([True, False], 6)
        y = np.ones(12)
        pred = np.r_[np.zeros(6), np.full(6, np.nan)]
        effect = np.zeros((12, 2))
        result, _ = audit.score_independent(y, pred, ep, np.repeat(["A", "B"], 6), effect,
                                            valid, {"0": list(range(5))}, ["A", "B", "C"], np.arange(12))
        self.assertEqual(result["per_master"]["mae"], [1., None, None])
        self.assertEqual(result["input"]["zero_contributor_masters"], ["B", "C"])
        self.assertFalse(result["coverage_pass"])
        with self.assertRaisesRegex(ValueError, "Nonfinite prediction"):
            audit.score_independent(y, pred, ep, np.repeat(["A", "B"], 6), effect,
                                    np.ones(12, bool), {"0": list(range(5))}, ["A", "B"], np.arange(12))

    def test_bootstrap_pairing_and_seed(self):
        got = audit.bootstrap_independent([0., 3.], [2., 1.])
        self.assertEqual(got["gain"], 0.)
        self.assertEqual(got["ci95"], [-2., 2.])
        self.assertEqual(got["n_boot"], 10000)
        self.assertEqual(got["seed"], 20261022)
        self.assertEqual(got, audit.bootstrap_independent([0., 3.], [2., 1.]))
        with self.assertRaises(ValueError):
            audit.bootstrap_independent([0., None], [2., 1.])

    def test_gate_minimums_and_headroom(self):
        def item(mae, utility, regret):
            return {"coverage_pass": True, "mae": mae, "utility": utility, "regret": regret,
                    "per_master": {"mae": [mae] * 2, "utility": [utility] * 2}}
        metrics = {"effect__mae": item(.07, .04, .02), "direct__mae": item(.1, .01, .05),
                   "effect__utility": item(.07, .04, .02), "direct__utility": item(.1, .01, .05)}
        selection = {"ordinary": {e: {"arm": "direct"} for e in audit.ENDPOINTS}}
        self.assertTrue(audit.recompute_gates(metrics, selection)["gates"]["both"])
        metrics["direct__utility"]["regret"] = .02
        self.assertFalse(audit.recompute_gates(metrics, selection)["gates"]["utility"])
        metrics["direct__mae"]["coverage_pass"] = False
        self.assertEqual(audit.recompute_gates(metrics, selection)["comparisons"], {})

    def test_existing_synthetic_driver_compatibility_and_tamper(self):
        # Copy only the prior synthetic pipeline, never the real phase DATA.
        FIXTURE.mkdir(exist_ok=False)
        source = PHASE / "SYNTHETIC_DRIVER_03"
        names = ("DATA.npz", "EPISODE_META.json", "DESIGN.json", "TEST_PREDICTIONS.npz",
                 "TEST_ACTIONS.json", "TEST_TARGETS.npz", "SELECTION.json", "PREDICTIONS_SEAL.json",
                 "TEST_METRICS.json", "GATES.json", "ALL_PAIRED_COMPARISONS.json")
        for name in names:
            shutil.copyfile(source / name, FIXTURE / name)
        (FIXTURE / "ROWS.json").write_text(json.dumps({"synthetic_placeholder": True}), encoding="utf-8")
        for receipt_name, files in (("INPUTS_RECEIPT.json", ["DATA.npz", "EPISODE_META.json", "ROWS.json"]),
                                    ("TEST_TARGETS_RECEIPT.json", ["TEST_TARGETS.npz"])):
            (FIXTURE / receipt_name).write_text(json.dumps({"synthetic_surrogate_receipt": True,
                "outputs_sha256": {name: audit.digest(FIXTURE / name) for name in files}}), encoding="utf-8")
        result = audit.audit(FIXTURE, synthetic=True)
        audit.save_report(result, FIXTURE / "INDEPENDENT_RESULTS_AUDIT.json")
        self.assertEqual(result["status"], "PASS", json.dumps(result["comparison_with_saved_outputs"]))
        self.assertLessEqual(result["maxdiff"], 1e-12)
        # Tamper a new copied file and restore it; no frozen evidence changes.
        path = FIXTURE / "SELECTION.json"
        original = path.read_bytes()
        try:
            path.write_bytes(original + b" ")
            with self.assertRaisesRegex(ValueError, "Hash/seal"):
                audit.audit(FIXTURE, synthetic=True)
        finally:
            path.write_bytes(original)
        receipt_path = FIXTURE / "INPUTS_RECEIPT.json"
        original_receipt = receipt_path.read_bytes()
        try:
            receipt = json.loads(original_receipt)
            del receipt["outputs_sha256"]["ROWS.json"]
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "omits required"):
                audit.audit(FIXTURE, synthetic=True)
            failure_output = FIXTURE / "EXPECTED_FAILURE_RECEIPT.json"
            with patch.object(sys, "argv", ["audit_results.py", "--run-after-test-open",
                    "--synthetic-fixture", "--log-dir", str(FIXTURE), "--output", str(failure_output)]):
                self.assertEqual(audit.main(), 1)
            self.assertIn("omits required", audit.read_json(failure_output)["verification_error"])
        finally:
            receipt_path.write_bytes(original_receipt)


if __name__ == "__main__":
    unittest.main()
