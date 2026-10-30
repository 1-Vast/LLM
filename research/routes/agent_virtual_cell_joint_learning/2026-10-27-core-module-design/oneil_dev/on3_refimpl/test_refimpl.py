"""ON3-READY unit tests (14) for the reference implementation.

No ON3 effect analysis; synthetic fixtures only. Reads frozen ON2/ON3 design artifacts
(read-only) for fold inheritance and reconstruction denominators.
"""
from __future__ import annotations

import inspect
import json
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ONEIL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import refimpl as R  # noqa: E402
import selfcheck as SC  # noqa: E402


class TestMask(unittest.TestCase):
    def test_01_mask_deterministic(self):
        drugs = ["d%02d" % i for i in range(38)]
        a = R.select_masked_members(drugs)
        b = R.select_masked_members(list(reversed(drugs)))
        self.assertEqual(a, b)
        self.assertEqual(len(a), int(np.ceil(0.20 * 38)))

    def test_02_mask_rule_no_unmasked_contains_masked_drug(self):
        M = ["d01", "d05", "d09"]
        partners = np.array(["d00", "d02", "d03", "d04"])
        a = np.array(["d01", "d02", "d03", "d04"])
        ap = np.array(["d06", "d07", "d08", "d05"])
        masked = R.build_mask(partners, a, ap, M)
        for i in range(len(masked)):
            if not masked[i]:
                self.assertNotIn(partners[i], M)
                self.assertNotIn(a[i], M)
                self.assertNotIn(ap[i], M)


class TestReconstruction(unittest.TestCase):
    def test_03_reconstruction_audit_denominators_target30_perfold(self):
        p = os.path.join(HERE, "reconstruction_audit.json")
        self.assertTrue(os.path.exists(p), "run on3_refimpl/data_prep.py first")
        j = json.load(open(p, encoding='utf-8'))
        self.assertEqual(j["target_masked_units"], 157768)
        self.assertEqual(j["target_audit"]["masked_units"], 157768)
        self.assertEqual(j["target_audit"]["reconstructable_units"], 0)
        for f, v in j["folds"].items():
            self.assertGreater(v["masked_units"], 30000)
            self.assertEqual(v["audit"]["masked_units"], v["masked_units"])
            self.assertEqual(v["audit"]["reconstructable_units"], 0)

    def test_03b_reconstruction_positive_control(self):
        # masked unit (a,b) reconstructable from unmasked (a,c),(c,b) in same context -> audit catches it
        cells = ["c1", "c1", "c1"]
        partners = ["p", "p", "p"]
        a = ["a1", "a1", "a2"]
        ap = ["a2", "a3", "a3"]
        masked = np.array([True, False, False])
        out = R.reconstruction_audit(cells, partners, a, ap, masked)
        self.assertEqual(out["masked_units"], 1)
        self.assertGreaterEqual(out["reconstructable_units"], 1)


class TestLeakAndAblation(unittest.TestCase):
    def test_04_mask_perturbation_predictions_unchanged(self):
        M = ["d00", "d01"]
        rng = np.random.default_rng(3)
        train = {"cell_id": rng.integers(0, 4, 300), "pair_id": rng.integers(0, 20, 300),
                 "partner_id": rng.integers(0, 4, 300), "role_id": rng.integers(0, 2, 300),
                 "y": rng.normal(0, 0.2, 300)}
        b4 = R.fit_b4(train, rank=2, lam=0.1)
        units = {"cell_id": np.zeros(60, int), "pair_id": rng.integers(0, 20, 60),
                 "partner_id": rng.integers(0, 4, 60), "role_id": rng.integers(0, 2, 60),
                 "y": rng.normal(0, 0.2, 60)}
        c, U = R.fit_context_factors(units, b4, 0.1)
        p1 = R.predict_b4(units, b4, c, U)
        units2 = dict(units); units2["y"] = units["y"] + 1e6
        p2 = R.predict_b4(units2, b4, c, U)
        self.assertTrue(np.allclose(p1, p2))

    def test_05_context_ablation_runs_and_is_diagnostic(self):
        rng = np.random.default_rng(4)
        train = {"cell_id": rng.integers(0, 4, 400), "pair_id": rng.integers(0, 20, 400),
                 "partner_id": rng.integers(0, 4, 400), "role_id": rng.integers(0, 2, 400),
                 "y": rng.normal(0, 0.2, 400)}
        b4 = R.fit_b4(train, rank=2, lam=0.1)
        units = {"cell_id": np.zeros(80, int), "pair_id": rng.integers(0, 20, 80),
                 "partner_id": rng.integers(0, 4, 80), "role_id": rng.integers(0, 2, 80),
                 "y": rng.normal(0, 0.2, 80)}
        c, U = R.fit_context_factors(units, b4, 0.1)
        out = R.context_ablation(units, b4, c, U)
        for k in ("rho_with_context", "rho_ablated_context", "delta_rho_context"):
            self.assertIn(k, out)
            self.assertTrue(np.isfinite(out[k]))
        # classification: diagnostic output only; no pass/fail binary key
        self.assertNotIn("pass", out)


class TestSchemaAndDeterminism(unittest.TestCase):
    def test_06_schema_validation(self):
        ok, missing = R.validate_exec_schema({})
        self.assertFalse(ok)
        self.assertEqual(len(missing), len(R.EXEC_REQUIRED_KEYS))
        sample = {k: {} for k in R.EXEC_REQUIRED_KEYS}
        ok2, missing2 = R.validate_exec_schema(sample)
        self.assertTrue(ok2, missing2)

    def test_07_two_run_determinism(self):
        a = R.sha256_json(SC.run())
        b = R.sha256_json(SC.run())
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)

    def test_08_fold_inheritance_matches_on2(self):
        j = json.load(open(os.path.join(ONEIL, 'on2.json'), encoding='utf-8'))
        on2_folds = j['fold_design']['folds']
        import data_prep as DP
        for f in on2_folds:
            self.assertEqual(DP.FOLDS[f], on2_folds[f])
        self.assertEqual(len(on2_folds), 5)
        self.assertTrue(all(len(v) == 6 for v in on2_folds.values()))


class TestBoundaries(unittest.TestCase):
    def test_09_no_jaaks_response_path(self):
        dp = open(os.path.join(HERE, "data_prep.py"), encoding='utf-8').read()
        self.assertIn("usecols=['CELL_LINE_NAME']", dp)
        self.assertNotIn("SYNERGY_DELTA_EMAX", dp)
        for fn in ("refimpl.py", "selfcheck.py"):
            src = open(os.path.join(HERE, fn), encoding='utf-8').read()
            self.assertNotIn("jaaks", src.lower())
            self.assertNotIn("drugcomb", src.lower())

    def test_10_no_test_tuning_and_frozen_constants(self):
        self.assertEqual(R.N_PERM, 1000)
        self.assertEqual(R.BOOT_B, 5000)
        self.assertEqual(R.ALS_MAX_ITER, 25)
        self.assertAlmostEqual(R.MDE80, 0.0287644381, places=10)
        self.assertAlmostEqual(R.DELTA_MIN, 0.10, places=10)
        import inspect
        sig = inspect.signature(R.fit_b4)
        self.assertIn("train", sig.parameters)  # only training data passed to fit; no masked/test set
        self.assertNotIn("test", sig.parameters)
        self.assertNotIn("masked", sig.parameters)


class TestB6NullGate(unittest.TestCase):
    def test_11_b6_null_calibration_gate_delta_rho(self):
        # v1.1 (AMEND-001): gate object is delta_rho_null; fields must be delta_rho-named.
        rng = np.random.default_rng(11)
        centered = rng.normal(0, 0.02, 500)
        g1 = R.null_calibration_gate(centered, field_prefix="delta_rho")
        self.assertTrue(g1["pass"])
        self.assertIn("p2_5_delta_rho", g1)
        self.assertIn("p97_5_delta_rho", g1)
        self.assertIn("mean_abs_delta_rho", g1)
        self.assertNotIn("p2_5_rho", g1)
        self.assertNotIn("mean_abs_rho", g1)
        ok, missing = R.validate_null_gate_schema(g1)
        self.assertTrue(ok, missing)
        shifted = centered + 0.30
        g2 = R.null_calibration_gate(shifted, field_prefix="delta_rho")
        self.assertFalse(g2["pass"])


class TestPureCold(unittest.TestCase):
    def test_12_pure_cold_path_uses_b2_only(self):
        rng = np.random.default_rng(12)
        train = {"cell_id": rng.integers(0, 4, 300), "pair_id": rng.integers(0, 15, 300),
                 "partner_id": rng.integers(0, 4, 300), "role_id": rng.integers(0, 2, 300),
                 "y": rng.normal(0, 0.2, 300)}
        b4 = R.fit_b4(train, rank=2, lam=0.1)
        units = {"cell_id": np.zeros(50, int), "pair_id": rng.integers(0, 15, 50),
                 "partner_id": rng.integers(0, 4, 50), "role_id": rng.integers(0, 2, 50),
                 "y": rng.normal(0, 0.2, 50)}
        obs = units["y"]
        pred_b2 = R.predict_b2(b4["b2"], units)
        expected = {"rho": R.spearman(pred_b2, obs), "mae": R.mae(pred_b2, obs), "n_units": len(obs)}
        orig = R.predict_b4
        def _forbid(*a, **k):
            raise AssertionError("pure_cold_eval must not use B4/context")
        R.predict_b4 = _forbid
        try:
            out = R.pure_cold_eval(units, b4)
        finally:
            R.predict_b4 = orig
        self.assertAlmostEqual(out["rho"], expected["rho"], places=10)
        self.assertAlmostEqual(out["mae"], expected["mae"], places=10)
        self.assertEqual(out["n_units"], expected["n_units"])
        sig = inspect.signature(R.pure_cold_eval)
        self.assertNotIn("c", sig.parameters)
        self.assertNotIn("U", sig.parameters)

    def test_12b_schema_requires_pure_cold_cell(self):
        self.assertIn("pure_cold_cell", R.EXEC_REQUIRED_KEYS)
        sample = {k: {} for k in R.EXEC_REQUIRED_KEYS}
        ok, missing = R.validate_exec_schema(sample)
        self.assertTrue(ok, missing)
        del sample["pure_cold_cell"]
        ok2, missing2 = R.validate_exec_schema(sample)
        self.assertFalse(ok2)
        self.assertEqual(missing2, ["pure_cold_cell"])


class TestB5TargetEncoding(unittest.TestCase):
    def test_13_b5_te_uses_only_training_cells_no_masked_responses(self):
        # pair 99 appears ONLY in one cross-fit fold -> validation encoding must use global backoff (0.0),
        # never the pair's own (masked-like) mean 1.0.
        y = np.zeros(200)
        pair = np.zeros(200, dtype=int)
        pair[:20] = 99
        y[:20] = 1.0
        te = R.cross_fit_target_encoding(y, pair, n_folds=5, seed=20261130)
        # locate validation entries of pair 99 (the fold not used for training that pair)
        self.assertGreater(int(np.sum(te[pair == 99] < 0.99)), 0)
        for idx in np.where(pair == 99)[0]:
            self.assertAlmostEqual(float(te[idx]), 0.0, places=10)
        # deterministic
        te2 = R.cross_fit_target_encoding(y, pair, n_folds=5, seed=20261130)
        self.assertTrue(np.allclose(te, te2))
        # no masked-unit responses accepted
        sig = inspect.signature(R.cross_fit_target_encoding)
        self.assertNotIn("masked", sig.parameters)
        self.assertNotIn("masked_y", sig.parameters)


if __name__ == '__main__':
    unittest.main(verbosity=2)
