"""Tests use synthetic exported utilities only, with meaningful negative controls."""
import unittest

import numpy as np

from historical_choice_audit import analyse, extract


def record(fold):
    result = {"fold": fold, "compounds": 65, "family": ["f"] * 65,
              "campaign_sizes": [64, 1], "campaign_index": [list(range(64)), [64]]}
    for section in ("A_B3", "C_noise_seed2"):
        result[section] = {}
        for arm in ("ridge", "R1"):
            result[section][arm] = {"unmeasured": {"hits_c": [1] + [0] * 63 + [1],
                "campaign_hits": [1, 1], "campaign_compounds": [64, 1]}}
    return result


class HistoricalChoiceTests(unittest.TestCase):
    def test_persistent_heterogeneity_has_transfer(self):
        one = np.array([[8, 0], [0, 8], [8, 0], [0, 8]])
        result = analyse([one, one], [2, 2, 3, 3])
        self.assertEqual(result["symmetric_gain_vs_hindsight_fixed"], 4)
        self.assertTrue(result["descriptive_both_direction_screen"])

    def test_anticorrelated_winners_lose(self):
        one = np.array([[8, 0], [0, 8], [8, 0], [0, 8]])
        result = analyse([one, one[:, ::-1]], [2, 2, 3, 3])
        self.assertEqual(result["symmetric_gain_vs_hindsight_fixed"], -4)
        self.assertEqual(result["strict_reversals"], 4)

    def test_exact_ties_choose_ridge_and_have_no_correlation(self):
        result = analyse(np.ones((2, 4, 2)), [2, 2, 3, 3])
        self.assertEqual(result["directions"]["1_to_2"]["chosen_arms"], ["ridge"] * 4)
        self.assertEqual(result["symmetric_gain_vs_leave_fold_fixed"], 0)
        self.assertIsNone(result["pearson_difference_correlation"])

    def test_fixed_choice_excludes_the_target_fold(self):
        one = np.array([[9, 0], [9, 0], [0, 6], [0, 6]])
        result = analyse([one, one], [2, 2, 3, 3])
        self.assertEqual(result["directions"]["1_to_2"]["leave_fold_fixed_arms"],
                         ["R1", "R1", "ridge", "ridge"])

    def test_incomplete_campaigns_excluded_without_repartition(self):
        u, labels, excluded = extract({f: record(f) for f in (2, 3, 4)})
        self.assertEqual(u.shape, (2, 3, 2))
        self.assertEqual(len(labels), 3)
        self.assertEqual([row["compounds"] for row in excluded], [1, 1, 1])

    def test_corrupt_campaign_hit_sum_rejected(self):
        records = {f: record(f) for f in (2, 3, 4)}
        records[2]["A_B3"]["ridge"]["unmeasured"]["campaign_hits"][0] = 2
        with self.assertRaisesRegex(ValueError, "hit total"):
            extract(records)

    def test_mismatched_section_membership_rejected(self):
        records = {f: record(f) for f in (2, 3, 4)}
        records[2]["C_noise_seed2"]["R1"]["unmeasured"]["campaign_compounds"] = [63, 2]
        with self.assertRaisesRegex(ValueError, "campaign keys"):
            extract(records)

    def test_overlapping_campaigns_rejected(self):
        records = {f: record(f) for f in (2, 3, 4)}
        records[2]["campaign_index"][1] = [0]
        with self.assertRaisesRegex(ValueError, "partition"):
            extract(records)


if __name__ == "__main__":
    unittest.main()
