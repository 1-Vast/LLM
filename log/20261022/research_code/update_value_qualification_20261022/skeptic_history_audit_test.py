"""Small synthetic regression cases for independent historical arithmetic."""
import unittest
from skeptic_history_audit import extract, summarize


class HistoricalAuditTests(unittest.TestCase):
    def rows(self, second):
        first = ([3, 0], [0, 3], [3, 0], [0, 3])
        return [{"fold": i // 2, "campaign_index": i, "u1": list(a), "u2": list(b)}
                for i, (a, b) in enumerate(zip(first, second))]

    def test_stable_and_reversed_rank(self):
        stable = summarize(self.rows(([3, 0], [0, 3], [3, 0], [0, 3])))
        self.assertTrue(stable["descriptive_continuation_pass"])
        self.assertEqual(stable["strict_sign_agreement_rate"], 1.)
        self.assertEqual(stable["symmetric"]["gain_vs_hindsight_fixed"], 1.5)
        reversed_ = summarize(self.rows(([0, 3], [3, 0], [0, 3], [3, 0])))
        self.assertFalse(reversed_["descriptive_continuation_pass"])
        self.assertEqual(reversed_["symmetric"]["gain_vs_hindsight_fixed"], -1.5)
        self.assertEqual(reversed_["strict_sign_reversals"], 4)

    def test_tie_first_and_lofo(self):
        rows = [{"fold": 0, "campaign_index": 0, "u1": [1, 1], "u2": [2, 0]},
                {"fold": 1, "campaign_index": 0, "u1": [0, 3], "u2": [0, 3]}]
        result = summarize(rows)
        self.assertEqual(result["directions"]["1_to_2"]["choices"], ["ridge", "R1"])
        self.assertEqual(result["directions"]["1_to_2"]["lofo_choices"], ["R1", "ridge"])
        self.assertEqual(result["directions"]["1_to_2"]["gain_vs_lofo"], 2.5)

    def test_compound_sums_incomplete_and_bad_membership(self):
        record = {"fold": 2, "compounds": 65, "family": ["x"] * 65,
                  "campaign_sizes": [64, 1], "campaign_index": [list(range(64)), [64]]}
        for section in ("A_B3", "C_noise_seed2"):
            record[section] = {}
            for arm in ("ridge", "R1"):
                record[section][arm] = {"unmeasured": {"campaign_compounds": [64, 1],
                    "hits_c": [1] * 65, "campaign_hits": [64, 1], "hits": 65}}
        rows, excluded, _ = extract(record)
        self.assertEqual(len(rows), 1)
        self.assertEqual(excluded[0]["compounds"], 1)
        record["A_B3"]["ridge"]["unmeasured"]["campaign_hits"][0] = 63
        with self.assertRaisesRegex(ValueError, "hit sums"):
            extract(record)
        record["campaign_index"][1] = [0]
        with self.assertRaisesRegex(ValueError, "partition"):
            extract(record)


if __name__ == "__main__":
    unittest.main()
