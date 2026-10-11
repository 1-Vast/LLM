"""Behavioral checks on paid feedback, terminal leakage, resource caps, and stopping."""
import copy
import unittest

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import study as S


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.limit = threadpool_limits(limits=1)
        cls.library, data = S.C.load_data()
        cls.datum = next(d for d in data if d[0].role == "development")
        cls.rows, cls.ledgers = S.run_campaign(cls.library, cls.datum)

    @classmethod
    def tearDownClass(cls):
        cls.limit.restore_original_limits()

    def test_terminal_truth_cannot_change_any_plan_or_prediction(self):
        query, primary, secondary = self.datum
        poisoned = primary.copy()
        poisoned[query.targets] += np.linspace(-100, 100, len(query.targets))
        _, ledgers = S.run_campaign(self.library, (query, poisoned, secondary))
        for original, changed in zip(self.ledgers, ledgers):
            self.assertEqual(original["events"], changed["events"])
            np.testing.assert_array_equal(original["prediction"], changed["prediction"])

    def test_two_stage_and_batch_respect_same_total_budget(self):
        rows = {row["arm"]: row for row in self.rows}
        self.assertEqual(rows["batch_gp_ivr_16"]["resource"], 18)
        self.assertEqual(rows["two_stage_kg_14"]["resource"], 18)
        self.assertEqual(rows["fixed_split_kg_14"]["resource"], 18)
        for row in self.rows:
            self.assertLessEqual(row["resource"], 18)
            self.assertLessEqual(row["rounds"], 2)

    def test_no_duplicate_or_terminal_purchase(self):
        query = self.datum[0]
        for ledger in self.ledgers:
            lines = [item["line"] for item in ledger["purchases"]]
            self.assertEqual(len(lines), len(set(lines)))
            self.assertTrue(set(lines).issubset(set(query.menu)))
            self.assertFalse(set(lines).intersection(set(query.targets)))

    def test_same_posterior_fixed_split_has_same_terminal_result(self):
        ledgers = {ledger["arm"]: ledger for ledger in self.ledgers}
        np.testing.assert_allclose(ledgers["batch_gp_kg_14"]["prediction"],
                                   ledgers["fixed_split_kg_14"]["prediction"], atol=1e-12)

    def test_all_actions_in_batch_are_fixed_before_feedback(self):
        query, primary, secondary = self.datum
        posterior = S.C.GaussianPosterior(self.library, query, **S.CFG)
        plan = S.stage_plan(posterior, 4)
        poisoned = primary.copy()
        poisoned[plan[0][0]] += 100
        env = S.C.MeasuredEnvironment(self.library, query, poisoned, secondary)
        event = S.buy_batch(posterior, env, plan, 1)
        self.assertEqual(event["plan"], [line for line, _ in plan])
        self.assertEqual([p["line"] for p in env.purchases], event["plan"])

    def test_gate_stops_when_lower_gain_does_not_exceed_cost(self):
        gate = {"gain_median": 1, "groups": [{"continue": False}, {"continue": True}]}
        self.assertEqual(S.continue_after_first(1.0, gate), (False, 0))
        self.assertEqual(S.continue_after_first(1.1, gate), (True, 1))

    def test_gate_fit_never_uses_exposed_replay_outcomes(self):
        rows = []
        for index in range(8):
            high = index >= 4
            for arm, utility in (("stop_after_4", 0), ("two_stage_kg_14", 0.04 if high else 0),
                                 ("batch_gp_ivr_16", 0.01)):
                rows.append(dict(drug=str(index), partition="fit", arm=arm, utility=utility,
                                 net_utility=utility, predicted_remaining_gain=int(high), risk_feature=0))
        fit = pd.DataFrame(rows)
        original = S.fit_gate(fit)
        exposed = fit.assign(partition="exposed_replay", utility=100, net_utility=100)
        self.assertEqual(original, S.fit_gate(pd.concat([fit, exposed])))
        self.assertFalse(original["groups"][0]["continue"])
        self.assertTrue(original["groups"][1]["continue"])

    def test_purchased_feedback_can_change_second_batch(self):
        query, primary, secondary = self.datum
        first = S.stage_plan(S.C.GaussianPosterior(self.library, query, **S.CFG), 4)
        plans = []
        for shift in (0, 10):
            posterior = S.C.GaussianPosterior(self.library, query, **S.CFG)
            changed = primary.copy()
            changed[first[0][0]] += shift
            env = S.C.MeasuredEnvironment(self.library, query, changed, secondary)
            S.buy_batch(posterior, env, first, 1)
            plans.append([line for line, _ in S.stage_plan(posterior, 10)])
        self.assertNotEqual(plans[0], plans[1])

    def test_planning_is_read_only(self):
        posterior = S.C.GaussianPosterior(self.library, self.datum[0], **S.CFG)
        original = copy.deepcopy(posterior)
        S.stage_plan(posterior, 10)
        self.assertEqual(posterior.bought, [])
        np.testing.assert_array_equal(posterior.mean, original.mean)
        np.testing.assert_array_equal(posterior.covariance, original.covariance)


if __name__ == "__main__":
    unittest.main()
