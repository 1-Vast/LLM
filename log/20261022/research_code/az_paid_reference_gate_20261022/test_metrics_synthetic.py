"""Synthetic-only tests for locked recommendations, common panels and macro metrics."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import unittest

import numpy as np

import metrics


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/az_paid_reference_gate/METRICS_SYNTHETIC.json"


def example():
    episode = np.repeat([0, 1, 2], [6, 5, 7])
    master = np.repeat(["A", "A", "B"], [6, 5, 7])
    y = np.concatenate([np.arange(6), np.arange(10, 15), np.arange(20, 27)]).astype(float)
    pred = y + np.repeat([1., 3., 7.], [6, 5, 7])
    return dict(y=y, pred=pred, episode=episode, master=master,
                effect=np.zeros((18, 2)), valid_mask=np.ones(18, dtype=bool),
                assigned_masters=["A", "B"])


class SyntheticMetricsTest(unittest.TestCase):
    def test_actions_use_paid_effects_and_global_row_ties(self):
        episode = np.tile([1, 0], 6)
        pred = np.ones(12)
        effect = np.zeros((12, 2))
        effect[0] = [2, 2]
        actions = metrics.make_actions(pred, effect, episode, np.ones(12, dtype=bool))
        self.assertEqual(actions, {0: [1, 3, 5, 7, 9], 1: [2, 4, 6, 8, 10]})
        # Negative and >1 paid effects/predictions retain their numerical meaning.
        effect[10] = [-2, -2]
        pred[10] = -0.5
        self.assertEqual(metrics.make_actions(pred, effect, episode, np.ones(12, dtype=bool))[1][0], 10)

    def test_episode_then_master_macro_and_fixed_action_evaluation(self):
        data = example()
        actions = metrics.make_actions(data["pred"], data["effect"], data["episode"], data["valid_mask"])
        actions[0] = [0, 1, 2, 3, 4]  # A prespecified alternate anchor policy.
        before = deepcopy(actions)
        result = metrics.score(**data, nominal_actions=actions)
        self.assertEqual(actions, before)
        self.assertEqual(result["per_master"]["mae"], [2., 7.])
        self.assertEqual(result["forecast"]["mae"], 4.5)
        self.assertEqual(result["mae"], 4.5)
        self.assertEqual(result["per_master"]["utility"], [7., 24.])
        self.assertEqual(result["recommendation"]["utility"], 15.5)
        self.assertEqual(result["recommendation"]["oracle_utility"], 15.75)
        self.assertEqual(result["recommendation"]["regret"], .25)
        self.assertTrue(result["coverage_pass"])
        self.assertEqual(result["per_master_episode_counts"]["forecast"], [2, 1])
        json.dumps(result, allow_nan=False)

    def test_hidden_missing_targets_never_reselect_actions(self):
        data = example()
        actions = metrics.make_actions(data["pred"], data["effect"], data["episode"], data["valid_mask"])
        before = deepcopy(actions)
        data["y"][1] = np.nan
        result = metrics.score(**data, nominal_actions=actions)
        self.assertEqual(actions, before)
        self.assertEqual(result["forecast"]["episodes"], 3)  # Five finite y remain in episode 0.
        self.assertEqual(result["recommendation"]["episodes"], 2)  # Whole episode 0 abstains for U.
        self.assertEqual(result["per_master"]["utility"], [12., 24.])
        self.assertEqual(result["forecast"]["finite_target_rows"], 17)
        self.assertFalse(result["coverage_pass"])
        # Even missing targets outside the selected top five prevent whole-grid regret scoring.
        data = example()
        data["y"][0] = np.nan
        self.assertNotIn(0, actions[0])
        result = metrics.score(**data, nominal_actions=actions)
        self.assertEqual(result["recommendation"]["episodes"], 2)

    def test_input_abstentions_stay_in_nominal_denominators(self):
        episode = np.repeat(np.arange(20), 6)
        master = np.where(episode < 10, "A", "B")
        valid = episode != 0
        data = dict(y=np.ones(120), pred=np.ones(120), episode=episode, master=master,
                    effect=np.zeros((120, 2)), valid_mask=valid, assigned_masters=["A", "B"])
        data["pred"][~valid] = np.nan  # Unavailable input episodes have no prediction obligation.
        result = metrics.score(**data)
        self.assertEqual(result["nominal_episodes"], 20)
        self.assertEqual(result["nominal_rows"], 120)
        self.assertEqual(result["input"]["episode_coverage"], .95)
        self.assertEqual(result["forecast"]["finite_target_row_coverage"], .95)
        self.assertTrue(result["coverage_pass"])
        data["y"][6] = np.nan
        result = metrics.score(**data)
        self.assertEqual(result["forecast"]["episode_coverage"], .95)
        self.assertEqual(result["recommendation"]["episode_coverage"], .9)
        self.assertFalse(result["forecast"]["coverage_pass"])
        self.assertFalse(result["recommendation"]["coverage_pass"])

    def test_zero_contributor_master_and_assigned_order(self):
        data = example()
        data["assigned_masters"] = ["B", "C", "A"]
        result = metrics.score(**data)
        self.assertEqual(result["assigned_masters"], ["B", "C", "A"])
        self.assertEqual(result["per_master"]["mae"], [7., None, 2.])
        for panel in ("input", "forecast", "recommendation"):
            self.assertEqual(result[panel]["zero_contributor_masters"], ["C"])
            self.assertFalse(result[panel]["coverage_pass"])
        self.assertFalse(result["coverage_pass"])
        json.dumps(result, allow_nan=False)

    def test_invalid_prediction_does_not_make_a_favorable_panel(self):
        data = example()
        data["pred"][0] = np.nan
        with self.assertRaisesRegex(ValueError, "finite predictions"):
            metrics.score(**data)
        data = example()
        data["valid_mask"][0] = False
        with self.assertRaisesRegex(ValueError, "constant"):
            metrics.score(**data)

    def test_actions_must_be_nominal_complete_and_within_episode(self):
        data = example()
        actions = metrics.make_actions(data["pred"], data["effect"], data["episode"], data["valid_mask"])
        del actions[0]
        with self.assertRaisesRegex(ValueError, "every eligible nominal"):
            metrics.score(**data, nominal_actions=actions)
        actions = metrics.make_actions(data["pred"], data["effect"], data["episode"], data["valid_mask"])
        actions[0] = [1, 2, 3, 4, 7]
        with self.assertRaisesRegex(ValueError, "own episode"):
            metrics.score(**data, nominal_actions=actions)

    def test_fewer_than_five_finite_rows_and_empty_role(self):
        data = example()
        data["y"][6:8] = np.nan  # Episode 1 now has only three finite targets.
        result = metrics.score(**data)
        self.assertEqual(result["forecast"]["episodes"], 2)
        self.assertEqual(result["per_master"]["mae"], [1., 7.])
        empty = metrics.score(np.empty(0), np.empty(0), np.empty(0, dtype=int),
                              np.empty(0, dtype=str), np.empty((0, 2)), np.empty(0, dtype=bool),
                              assigned_masters=["A"])
        self.assertIsNone(empty["forecast"]["mae"])
        self.assertIsNone(empty["recommendation"]["utility"])
        self.assertFalse(empty["coverage_pass"])
        json.dumps(empty, allow_nan=False)

    def test_paired_bootstrap_direction_reproducibility_and_missing_rejection(self):
        result = metrics.paired_bootstrap([1., 3.], [3., 3.])
        self.assertEqual(result, {"gain": 1., "mean": 1., "ci95": [0., 2.], "lower": 0., "upper": 2.,
                                  "n_masters": 2, "n_boot": 10000, "seed": 20261022})
        self.assertEqual(result, metrics.paired_bootstrap([1., 3.], [3., 3.]))
        self.assertEqual(result, metrics.paired_bootstrap([3., 3.], [1., 3.], higher_is_better=True))
        with self.assertRaisesRegex(ValueError, "aligned finite"):
            metrics.paired_bootstrap([1., None], [3., 3.])


if __name__ == "__main__":
    started = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticMetricsTest))
    files = [Path(metrics.__file__), Path(__file__)]
    record = {"status": "PASS" if result.wasSuccessful() else "FAIL", "synthetic_only": True,
              "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "biological_response_file_reads": 0, "biological_fits": 0,
              "tests_run": result.testsRun,
              "failures": [{"test": str(test), "traceback": detail} for test, detail in result.failures],
              "errors": [{"test": str(test), "traceback": detail} for test, detail in result.errors],
              "runtime_seconds": time.perf_counter() - started,
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
              "note": "Synthetic metric contract checks; not biological evidence or full-driver authorization."}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with (OUT.parent / "METRICS_SYNTHETIC_RUNS.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record) + "\n")
    OUT.write_text(json.dumps(record, indent=2), encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
