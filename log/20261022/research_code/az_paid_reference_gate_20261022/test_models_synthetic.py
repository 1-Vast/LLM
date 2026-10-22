"""Synthetic-only contract tests. This script never opens biological response files."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import unittest

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor

import models


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/az_paid_reference_gate/MODELS_SYNTHETIC.json"
FIT_AUDIT = []
REFERENCE_FITS = []


def fit(arm, param, data, mask):
    fitted = models.fit_model(arm, param, data, mask)
    FIT_AUDIT.append({"arm": arm, "solver_fits": fitted.solver_fits,
                      "fit_seconds": fitted.fit_seconds})
    return fitted


def synthetic_data(n=48):
    rng = np.random.default_rng(20261022)
    effect = rng.uniform(-0.4, 1.4, size=(n, 2))
    dose = rng.uniform(-0.5, 1.5, size=(n, 2))
    without_mono = rng.normal(size=(n, 3))
    full = np.column_stack([without_mono, effect])
    return {"full": full, "without_mono": without_mono, "effect": effect,
            "dose": dose, "y": 0.8 * effect[:, 0] - 0.2 * dose[:, 1] + 0.1,
            "episode": np.arange(n) // 4, "pair": np.arange(n) % 2,
            "role": np.repeat("synthetic", n)}


class GuardedTargets:
    def __init__(self, values, allowed):
        self.values = values
        self.allowed = np.asarray(allowed)
        self.accesses = []

    def __array__(self, *args, **kwargs):
        raise AssertionError("Whole target array must not be converted")

    def __getitem__(self, idx):
        selected = np.arange(len(self.values))[idx]
        if not np.all(self.allowed[selected]):
            raise AssertionError("A forbidden target was read")
        self.accesses.append(np.asarray(selected).tolist())
        return self.values[idx]


class SyntheticModelsTest(unittest.TestCase):
    def test_grids_are_fixed_and_separate(self):
        self.assertEqual(set(models.GRIDS), {"effect", "dose", "direct", "combo_direct"})
        self.assertTrue(all(len(grid) == 12 for grid in models.GRIDS.values()))
        self.assertEqual(len({(p["width"], p["alpha"]) for p in models.GRIDS["effect"]}), 12)
        self.assertEqual(sum(p["model"] == "extra_trees" for p in models.GRIDS["direct"]), 6)
        self.assertEqual(sum(p["model"] == "hist_gradient_boosting" for p in models.GRIDS["direct"]), 6)
        self.assertIsNot(models.GRIDS["effect"][0], models.GRIDS["dose"][0])
        self.assertIsNot(models.GRIDS["direct"][0], models.GRIDS["combo_direct"][0])

    def test_weighted_residuals_match_independent_reference(self):
        data = synthetic_data(12)
        data["episode"] = np.array([0, 0, 1, 1, 1, 1, 2, 2, 3, 3, 3, 3])
        data["pair"] = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
        data["y"][3] = np.nan
        mask = np.array([True] * 10 + [False] * 2)
        selected = np.array([0, 1, 2, 4, 5, 6, 7, 8, 9])
        # Episode masses are equal after dropping the NaN: counts 2,3,2,2.
        weights = np.array([9/8, 9/8, 9/12, 9/12, 9/12, 9/8, 9/8, 9/8, 9/8])
        param = {"width": 0.25, "alpha": 0.1}
        original_param = deepcopy(param)
        for arm in ("effect", "dose"):
            fitted = fit(arm, param, data, mask)
            coords = data[arm][selected]
            centers = np.array([(u, v) for u in (0, .25, .5, .75, 1)
                                for v in (0, .25, .5, .75, 1)])
            basis = np.column_stack([np.exp(-np.sum((coords[:, None] - centers) ** 2, axis=2)
                                              / (2 * .25 ** 2)), np.ones(len(selected))])
            e = data["effect"][selected]
            bliss = e[:, 0] + e[:, 1] - e[:, 0] * e[:, 1]
            expected = bliss.copy()
            for pair in (0, 1):
                take = data["pair"][selected] == pair
                x, w = basis[take], weights[take]
                beta = np.linalg.solve(x.T @ np.diag(w) @ x + .1 * np.eye(26),
                                       x.T @ np.diag(w) @ (data["y"][selected][take] - bliss[take]))
                np.testing.assert_allclose(fitted.coefficients[pair], beta, rtol=1e-10, atol=1e-10)
                expected[take] += x @ beta
            prediction_mask = np.zeros(12, dtype=bool)
            prediction_mask[selected] = True
            np.testing.assert_allclose(fitted.predict(data, prediction_mask), expected, rtol=1e-10, atol=1e-10)
            self.assertEqual(fitted.solver_fits, 2)
            self.assertGreaterEqual(fitted.fit_seconds, 0)
        self.assertEqual(param, original_param)

    def test_episode_weight_formula(self):
        episode = np.array([10, 10, 20, 20, 20, 30])
        actual = models._episode_weights(episode)
        np.testing.assert_allclose(actual, [1, 1, 2/3, 2/3, 2/3, 2])
        self.assertAlmostEqual(actual.mean(), 1)
        np.testing.assert_allclose([actual[episode == e].sum() for e in (10, 20, 30)], [2, 2, 2])

    def test_mask_isolation_and_prediction_reads_no_targets(self):
        data = synthetic_data()
        mask = np.arange(48) < 30
        data["y"][2] = np.nan
        guarded = GuardedTargets(data["y"], mask)
        data["y"] = guarded
        for arm in ("effect", "dose", "direct", "combo_direct"):
            fitted = fit(arm, models.GRIDS[arm][0], data, mask)
            forbidden = GuardedTargets(np.zeros(48), np.zeros(48, dtype=bool))
            prediction_data = dict(data, y=forbidden)
            predictions = fitted.predict(prediction_data, ~mask)
            self.assertEqual(len(predictions), 18)
            self.assertTrue(np.all(np.isfinite(predictions)))
            self.assertEqual(forbidden.accesses, [])
            self.assertEqual(len(fitted.predict(prediction_data, np.zeros(48, dtype=bool))), 0)
        self.assertEqual(len(guarded.accesses), 4)

    def test_unseen_pair_is_unclipped_bliss(self):
        data = synthetic_data()
        fitted = fit("effect", models.GRIDS["effect"][0], data, np.ones(48, dtype=bool))
        prediction_data = dict(data, pair=np.repeat(99, 48))
        prediction_data["effect"] = np.tile([[-1., .2], [2., -.5]], (24, 1))
        e = prediction_data["effect"]
        expected = e[:, 0] + e[:, 1] - e[:, 0] * e[:, 1]
        self.assertLess(expected.min(), 0)
        self.assertGreater(expected.max(), 1)
        np.testing.assert_array_equal(fitted.predict(prediction_data, np.ones(48, dtype=bool)), expected)

    def test_direct_features_raw_labels_and_weights(self):
        data = synthetic_data(64)
        data["episode"][:20] = 90
        data["y"][3] = np.nan
        mask = np.arange(64) < 56
        selected = np.flatnonzero(mask & np.isfinite(data["y"]))
        episodes = data["episode"][selected]
        weights = np.array([len(selected) / (len(np.unique(episodes)) * np.sum(episodes == e))
                            for e in episodes])
        before = deepcopy(models.GRIDS)
        for arm, key in (("direct", "full"), ("combo_direct", "without_mono")):
            for grid_idx, cls in ((0, ExtraTreesRegressor), (6, HistGradientBoostingRegressor)):
                param = models.GRIDS[arm][grid_idx]
                fitted = fit(arm, param, data, mask)
                kwargs = {k: v for k, v in param.items() if k != "model"}
                reference = cls(**kwargs).fit(data[key][selected], data["y"][selected], sample_weight=weights)
                REFERENCE_FITS.append({"arm": arm, "family": param["model"]})
                wanted = reference.predict(data[key][~mask])
                np.testing.assert_allclose(fitted.predict(data, ~mask), wanted, rtol=1e-12, atol=1e-12)
                self.assertEqual(fitted.estimator.n_features_in_, data[key].shape[1])
                other = dict(data)
                other["without_mono" if arm == "direct" else "full"] = np.full((64, 17), 999.)
                other["effect"] = np.full((64, 2), 999.)
                # Parallel tree reduction may differ by a few floating-point ulps.
                np.testing.assert_allclose(fitted.predict(other, ~mask), fitted.predict(data, ~mask),
                                           rtol=1e-12, atol=1e-12)
                self.assertEqual(fitted.solver_fits, 1)
                self.assertGreaterEqual(fitted.fit_seconds, 0)
        self.assertEqual(models.GRIDS, before)


if __name__ == "__main__":
    started = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticModelsTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    files = [Path(models.__file__), Path(__file__)]
    record = {"status": "PASS" if result.wasSuccessful() else "FAIL", "synthetic_only": True,
              "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "biological_response_file_reads": 0, "tests_run": result.testsRun,
              "failures": [{"test": str(test), "traceback": detail} for test, detail in result.failures],
              "errors": [{"test": str(test), "traceback": detail} for test, detail in result.errors],
              "runtime_seconds": time.perf_counter() - started,
              "synthetic_top_level_fits": len(FIT_AUDIT),
              "synthetic_internal_solver_fits": sum(f["solver_fits"] for f in FIT_AUDIT),
              "synthetic_reference_estimator_fits": len(REFERENCE_FITS),
              "reference_fit_audit": REFERENCE_FITS,
              "fit_audit": FIT_AUDIT,
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
              "note": "These synthetic checks are not biological performance evidence or a novelty claim."}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with (OUT.parent / "MODELS_SYNTHETIC_RUNS.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")
    OUT.write_text(json.dumps(record, indent=2), encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
