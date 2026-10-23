"""Integration checks with synthetic labels and fake estimators, never source data."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

import driver
from prepare import write


class DriverTests(unittest.TestCase):
    def test_endpoint_specific_selection(self):
        y = np.arange(6.)
        pred_a = y.copy()
        pred_a[0] = 4.9
        candidates = [{"config": i, "metrics": driver.score(y, p, np.zeros(6, int), np.full(6, "m"),
                      np.zeros((6, 2)), np.ones(6, bool), assigned_masters=["m"])}
                      for i, p in enumerate([pred_a, y+10])]
        self.assertEqual(driver.best(candidates, "mae")["config"], 0)
        self.assertEqual(driver.best(candidates, "utility")["config"], 1)

    def test_joint_configuration_offset_selection(self):
        y = np.arange(6.)
        candidates = []
        for ci, base in enumerate((y+.3, y-1.)):
            for eta in (0., 1.):
                result = driver.score(y, base+eta, np.zeros(6, int), np.full(6, "m"),
                                      np.zeros((6, 2)), np.ones(6, bool), assigned_masters=["m"])
                candidates.append({"config": ci, "eta": eta, "metrics": result})
        selected = driver.best(candidates, "mae")
        self.assertEqual((selected["config"], selected["eta"]), (1, 1.))

    def test_gate_margins_and_coverage(self):
        self.assertTrue(driver.endpoint_gate("mae", .03, .2, .01, True))
        self.assertTrue(driver.endpoint_gate("utility", .03, .1, .01, True))
        self.assertFalse(driver.endpoint_gate("mae", .01, .2, .001, True))
        self.assertFalse(driver.endpoint_gate("utility", .03, .02, .01, True))
        self.assertFalse(driver.endpoint_gate("utility", .03, .1, .01, False))
        self.assertFalse(driver.endpoint_gate("utility", .03, .1, 0., True))

    def test_unique_paid_means_and_roles(self):
        summaries = [{"key": ["matrix", str(i)], "role": role, "pair": ["a", "b"], "mean_residual": value}
                     for i, (role, value) in enumerate([("train", 1.), ("train", 3.), ("validation", 100.)])]
        meta = [{"episode_id": i, "valid": True, "query_pairs": [["a", "b"], ["unseen", "pair"]],
                 "query_residual_means": [5., 1.]} for i in range(3)]
        values, audit = driver.offset_values(meta, summaries, {"train"})
        np.testing.assert_array_equal(values, [2., 2., 2.])
        self.assertEqual(audit["unique_reference_matrices"], 2)
        self.assertEqual(len(audit["missing_historical_query_pairs"]), 3)
        with self.assertRaises(ValueError):
            driver.offset_values(meta, summaries + summaries[:1], {"train"})

    def test_historical_excludes_unrequested_targets_and_lex_ties(self):
        data = {"pair": np.array([0, 0, 0, 1]), "dose": np.array([[0, 0], [1, 0], [.5, 0], [.5, 0]]),
                "y": np.array([.1, .9, 999., np.nan])}
        pred = driver.historical(data, np.array([1, 1, 0, 0], bool), np.array([0, 0, 1, 1], bool))
        np.testing.assert_allclose(pred[2:], [.1, .5])

    def test_synthetic_pipeline_seals_without_test_labels(self):
        run = 1
        while (driver.LOG / f"SYNTHETIC_DRIVER_{run:02d}").exists():
            run += 1
        log = driver.LOG / f"SYNTHETIC_DRIVER_{run:02d}"
        log.mkdir()
        episode = np.repeat(np.arange(4), 6)
        role = np.repeat(["train", "train", "validation", "test"], 6)
        effect = np.tile(np.column_stack([np.linspace(.1, .6, 6), np.full(6, .2)]), (4, 1))
        y = effect.sum(axis=1) - effect.prod(axis=1) + np.tile([0, .1, 0, .1, 0, .1], 4)
        y[role == "test"] = np.nan
        data = {"episode": episode, "role": role, "effect": effect, "dose": effect,
                "raw_dose": 10**effect, "pair": np.zeros(24, int), "valid_mask": np.ones(24, bool),
                "y": y, "full": effect, "without_mono": effect}
        np.savez_compressed(log / "DATA.npz", **data)
        meta = [{"episode_id": i, "cell": str(i), "role": r, "valid": True,
                 "query_pairs": [["a", "c"], ["b", "d"]], "query_residual_means": [.1, .2],
                 "pair": ["a", "b"], "abstain_reason": "", "logical_bundles": 2, "logical_paid_rows": 12}
                for i, r in enumerate(["train", "train", "validation", "test"])]
        summaries = [{"key": [str(i)], "role": r, "pair": p, "mean_residual": v, "rows": 6}
                     for i, (r, p, v) in enumerate([("train", ["a", "c"], .05), ("train", ["b", "d"], .1)])]
        write(log / "EPISODE_META.json", meta)
        write(log / "PAID_SUMMARIES.json", summaries)
        write(log / "DESIGN.json", {"role_cells": {"train": ["0", "1"], "validation": ["2"], "test": ["3"]}})
        fits = []

        class FakeModel:
            fit_seconds = 0.
            solver_fits = 1

            def predict(self, d, mask):
                uv = d["effect"][mask]
                return uv.sum(axis=1) - uv.prod(axis=1)

        def fake_fit(arm, config, d, mask):
            self.assertFalse(np.any(mask & (d["role"] == "test")))
            self.assertTrue(np.isnan(d["y"][d["role"] == "test"]).all())
            fits.append((arm, tuple(sorted(config.items())), mask.copy()))
            return FakeModel()

        with patch.object(driver, "verify_freeze"), patch.object(driver, "fit_model", side_effect=fake_fit):
            driver.fit_stage(log)
        seal = json.loads((log / "PREDICTIONS_SEAL.json").read_text())
        self.assertEqual(seal["selection_fits"], 48)
        self.assertEqual(len(fits), 48 + seal["unique_final_fits"])
        self.assertLessEqual(seal["unique_final_fits"], 14)
        final_keys = [(a, p) for a, p, m in fits if np.any(m & (role == "validation"))]
        self.assertEqual(len(final_keys), len(set(final_keys)))
        actions = json.loads((log / "TEST_ACTIONS.json").read_text())
        for policy in actions.values():
            self.assertEqual(set(policy), {"3"})
            self.assertEqual(len(policy["3"]), 5)
            self.assertTrue(all(18 <= i < 24 for i in policy["3"]))
        self.assertTrue(np.isnan(driver.load(log)[0]["y"][role == "test"]).all())
        with self.assertRaises(RuntimeError), patch.object(driver, "verify_freeze"):
            driver.fit_stage(log)
        np.savez_compressed(log / "TEST_TARGETS.npz", y=np.nan_to_num(y, nan=.5))
        original = (log / "TEST_ACTIONS.json").read_bytes()
        (log / "TEST_ACTIONS.json").write_text("{}")
        with self.assertRaises(ValueError), patch.object(driver, "verify_freeze"):
            driver.evaluate_stage(log)
        self.assertFalse((log / "EVALUATION_STARTED.json").exists())
        (log / "TEST_ACTIONS.json").write_bytes(original)
        with patch.object(driver, "verify_freeze"):
            driver.evaluate_stage(log)
        self.assertTrue((log / "COSTS.json").exists())
        self.assertTrue((log / "SUPPORT_PLATEAU_DIAGNOSTICS.json").exists())
        write(log / "DESIGN.json", {"role_cells": {"train": ["0", "1"], "validation": ["2"], "test": ["3", "missing"]}})
        with self.assertRaises(ValueError):
            driver.load(log)
        write(log / "DESIGN.json", {"role_cells": {"train": ["0", "1"], "validation": ["2"], "test": ["3"]}})
        data["y"][-1] = .7
        np.savez_compressed(log / "DATA.npz", **data)
        with self.assertRaises(ValueError):
            driver.load(log)


if __name__ == "__main__":
    unittest.main(verbosity=2)
