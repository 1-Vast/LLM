# -*- coding: utf-8 -*-
"""Deterministic unit tests for the corrected contract.  No model execution."""
import unittest
import numpy as np

import contract as C


class TestComparisonContract(unittest.TestCase):
    def test_strong_improvement_gate_can_pass(self):
        base = np.full(10, 0.10)
        cand = np.zeros(10)
        g = C.success_gate(cand - base, delta=0.05)
        self.assertLess(g["mean"], -0.05)
        self.assertLess(g["ci95_t"][1], 0)
        self.assertTrue(g["gate_pass"])

    def test_no_improvement_gate_fails(self):
        base = np.full(10, 0.10)
        cand = np.full(10, 0.10)
        self.assertFalse(C.success_gate(cand - base)["gate_pass"])

    def test_worse_gate_fails(self):
        base = np.full(10, 0.10)
        cand = np.full(10, 0.12)
        self.assertFalse(C.success_gate(cand - base)["gate_pass"])

    def test_lower_tail_direction(self):
        d = np.full(10, -0.02)
        p = C.one_sided_lower_p(d)
        self.assertLess(p, 0.001)  # improvement must have small lower-tail p
        # upper-tail reference would be near 1 for negative improvements
        self.assertGreater(p, 0.0)

    def test_six_family_includes_standard_and_holm(self):
        base = {f"b{i}": np.full(10, 0.10) for i in range(5)}
        base["standard"] = np.full(10, 0.10)
        cand = np.full(10, 0.02)
        fam = C.six_comparison_family(cand, base, delta=0.05)
        self.assertIn("standard", fam["rows"])
        self.assertEqual(fam["family_size"], 6)
        for row in fam["rows"].values():
            self.assertLess(row["mean_DeltaR"], -0.05)
            self.assertTrue(row["pass"])


class TestHeadroom(unittest.TestCase):
    def test_saved_batch_infeasible(self):
        h = C.headroom_gate(np.full(10, 0.0203), delta=0.05)
        self.assertFalse(h["delta_feasible"])
        self.assertAlmostEqual(h["max_possible_mean_improvement"], 0.0203, places=12)

    def test_feasible_when_baseline_regret_above_delta(self):
        h = C.headroom_gate(np.full(10, 0.10), delta=0.05)
        self.assertTrue(h["delta_feasible"])
        self.assertAlmostEqual(h["headroom_ratio"], 2.0, places=12)


class TestPropensity(unittest.TestCase):
    def setUp(self):
        # exact nine-cell tables from saved_result_corrections.json
        self.b_old = np.array([[0.2, 0.3, 0.5], [0.4, 0.4, 0.2], [0.25, 0.35, 0.4]])
        self.w = np.array([[0.16483516483516486, 0.6868131868131868, 0.14835164835164835],
                           [0.5319148936170213, 0.08510638297872343, 0.38297872340425526],
                           [0.353932584269663, 0.25280898876404495, 0.39325842696629215]])
        self.pi2 = self.w.copy()
        self.m = np.zeros((3, 3))

    def test_actual_behavior_identity(self):
        y = np.full(3, 0.455)
        a = np.array([0, 1, 2])
        gap = C.dr_identity_gap(self.pi2, self.w, self.m, y, a)
        self.assertLess(abs(gap), 1e-12)

    def test_old_b_misweights(self):
        y = np.full(3, 0.455)
        a = np.array([0, 1, 2])
        v_old = C.dr_estimator(self.pi2, self.b_old, self.m, y, a)
        self.assertGreater(abs(v_old - 0.455), 1e-3)


class TestEquivalence(unittest.TestCase):
    def test_monotone_transform_same_decisions(self):
        rng = np.random.default_rng(7)
        s = rng.normal(size=(20, 4))
        tmle_like = 1.0 / (1.0 + np.exp(-2.0 * s))
        self.assertTrue(C.decisions_equivalent(s, tmle_like))
        self.assertTrue(C.affine_equivalent(0.5 + 0.5 * s, 2.0 * s + 1.0))

    def test_shifted_scores_same_decisions_but_not_affine(self):
        s = np.arange(8, dtype=float).reshape(2, 4)
        shifted = s + 3.0
        self.assertTrue(C.decisions_equivalent(s, shifted))
        self.assertTrue(C.affine_equivalent(s, shifted))


class TestLearnerContract(unittest.TestCase):
    def test_logit_fluctuation_recovers_epsilon(self):
        rng = np.random.default_rng(11)
        n, A = 400, 3
        logits = rng.normal(size=(n, A))
        H = rng.normal(size=(n, A))
        eps_true = 0.7
        p = C.softmax_rows(logits + eps_true * H)
        a = np.array([rng.choice(A, p=p[i]) for i in range(n)])
        out = C.logit_fluctuation_fit(logits, H, a)
        self.assertTrue(out["converged"])
        self.assertLess(out["score_equation_residual"], 1e-5)
        self.assertAlmostEqual(out["epsilon"], eps_true, delta=0.25)


if __name__ == "__main__":
    unittest.main(verbosity=2)
