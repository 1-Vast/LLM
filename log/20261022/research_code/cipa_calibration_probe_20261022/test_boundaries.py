"""Synthetic boundary tests; never read real assay scalars or fit real models."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import model_probe as m


def row(site, drug="a", dose="1"):
    return dict(bundle_id=f"{site}|C|P|{drug}|{dose}", site=site, cell="C", platform="P", drug=drug, dose_code=dose, split="source" if site in "12345" else "dev")


class Boundaries(unittest.TestCase):
    def test_identity_projection_and_restricted_labels(self):
        records = []
        for site in ("1", "6"):
            r = row(site)
            r.update(ead_mean=.2, ddfpdc_available_fraction=.8, ddfpdc_mean=20, n_rows=4, n_ddfpdc_valid=3)
            records.append(r)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            with patch.object(m, "DATA", path):
                path.write_text(json.dumps({"bundles": records}))
                before_meta = m.metadata()
                before_source = m.labels_for([records[0]["bundle_id"]])
                records[1].update(ead_mean="UNPAID", ddfpdc_available_fraction="UNPAID", ddfpdc_mean="UNPAID", n_rows="UNPAID", n_ddfpdc_valid="UNPAID")
                path.write_text(json.dumps({"bundles": records}))
                self.assertEqual(before_meta, m.metadata())
                self.assertEqual(before_source, m.labels_for([records[0]["bundle_id"]]))
                self.assertTrue(all(set(r) == set(m.KEYS) for r in before_meta))

    def test_fit_and_proposals_receive_only_metadata(self):
        source = [row("1"), row("2"), row("3")]
        labels = {r["bundle_id"]: [i/10, .9, 10+i] for i, r in enumerate(source)}
        paid = [row("6", "a", "1")]
        feedback = {paid[0]["bundle_id"]: [.4, 1., 15.]}
        terminal = [row("6", "a", "2")]
        dictionary = m.make_dictionary(source + paid + terminal)
        summary = m.Summary(source, labels, "test")
        config = {"id": "offset:k1", "family": "offset", "kappa": 1}
        p1 = m.predict(config, source, labels, paid, feedback, terminal, summary, dictionary, "test", "6|C|P")
        p2 = m.predict(config, source, labels, paid, feedback, [dict(terminal[0])], summary, dictionary, "test", "6|C|P")
        np.testing.assert_array_equal(p1, p2)
        illegal = [dict(terminal[0], n_rows=3)]
        with self.assertRaises(AssertionError):
            m.predict(config, source, labels, paid, feedback, illegal, summary, dictionary, "test", "6|C|P")

    def test_nested_features_do_not_encode_own_site(self):
        source = [row("1"), row("2"), row("3")]
        labels = {r["bundle_id"]: [.1, .9, 10+i] for i, r in enumerate(source)}
        first = m.nested_vectors(source, labels, "test")
        changed = {key: list(value) for key, value in labels.items()}
        changed[source[0]["bundle_id"]] = [1., 0., 99999.]
        second = m.nested_vectors(source, changed, "test")
        np.testing.assert_array_equal(first[0], second[0])

    def test_missing_head_and_nonfinite_predictions(self):
        score = m.losses(np.array([[.2, .8, 10.]]), [[0., 1., None]], 2)
        self.assertIsNone(score["components"]["H"])
        self.assertAlmostEqual(score["combined"], .04)
        with self.assertRaises(AssertionError):
            m.losses(np.array([[.2, .8, np.nan]]), [[0., 1., None]], 2)

    def test_portfolio_balanced_and_deterministic(self):
        ids = [str(i) for i in range(8)]
        folds = m.portfolio_folds(ids)
        self.assertEqual([len(f) for f in folds], [2, 2, 2, 2])
        self.assertEqual(folds, m.portfolio_folds(list(reversed(ids))))
        self.assertEqual(sorted(sum(folds, [])), ids)

    def test_summary_fallback_is_source_only(self):
        source = [row("1"), row("2")]
        labels = {source[0]["bundle_id"]: [0., 0., None], source[1]["bundle_id"]: [1., 1., 10.]}
        summary = m.Summary(source, labels, "test")
        test = [row("6", "unseen")]
        p = summary.lookup(test, "cell_platform", normalized=False)
        np.testing.assert_array_equal(p, [[.5, .5, 10.]])
        self.assertEqual(summary.scale, 1.)
        self.assertTrue(np.isfinite(p).all())


if __name__ == "__main__":
    unittest.main()
