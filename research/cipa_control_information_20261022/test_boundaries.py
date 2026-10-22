"""Synthetic API, weighted-objective and fold preprocessing checks; no assay reads."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import probe as m


def row(site, drug, dose="1", cell="AXG", platform="AXN"):
    return dict(bundle_id=f"{site}|{cell}|{platform}|{drug}|{dose}", site=site, cell=cell,
                platform=platform, drug=drug, dose_code=dose, split="source")


def synthetic():
    rows, labels = [], {}
    for site in "123":
        for cell in ("AXG", "CDI"):
            value = int(site) + (cell == "CDI") / 2
            for drug, dose in m.SLOTS:
                r = row(site, drug, dose, cell)
                rows.append(r)
                labels[r["bundle_id"]] = [.1 * value, .8, 10 * value]
            r = row(site, "target", cell=cell)
            rows.append(r)
            labels[r["bundle_id"]] = [.05 * value, .9, 20 * value]
    return rows, labels


class Boundaries(unittest.TestCase):
    def test_source_projection_does_not_read_dev_fields(self):
        source = row("1", "target")
        source.update(dict(zip(m.TARGETS, [.2, .8, 10.])))
        dev = {"site": "6", "split": "dev", "bundle_id": "poison"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.json"
            path.write_text(json.dumps({"bundles": [source, dev]}))
            with patch.object(m, "DATA", path):
                self.assertEqual(m.metadata(), [{k: source[k] for k in m.KEYS}])
                self.assertEqual(m.labels_for([source["bundle_id"]]), {source["bundle_id"]: [.2, .8, 10.]})
                with self.assertRaises(AssertionError):
                    m.labels_for(["poison"])

    def test_weighted_ridge_matches_unpenalized_intercept_normal_equations(self):
        rows, labels = synthetic()
        labels["1|CDI|AXN|target|1"][2] = None
        summary = m.old.Summary(rows, labels, "synthetic")
        model = m.Conditional(m.conditional_configs()[0], rows, labels, summary, "synthetic")
        context_rows = list(m.old.contexts(rows).values())
        raw = np.array([model.features(r, labels) for r in context_rows])
        x = (np.where(np.isfinite(raw), raw, model.imputation) - model.mean) / model.std
        y = np.array([next(labels[r["bundle_id"]][2] for r in context if r["drug"] == "target") for context in context_rows], dtype=float) / summary.scale
        valid = np.isfinite(y)
        design = np.column_stack([np.ones(len(x)), x])[valid]
        weights = np.full(valid.sum(), 1 / 6)
        penalty = np.eye(design.shape[1])
        penalty[0, 0] = 0
        coefficient = np.linalg.solve(design.T @ (weights[:, None] * design) + penalty, design.T @ (weights * y[valid]))
        fitted = model.models[(("target", "1"), 2)]
        np.testing.assert_allclose(fitted.predict(x), np.column_stack([np.ones(len(x)), x]) @ coefficient, atol=1e-12)
        self.assertAlmostEqual(m.CONDITIONAL_FITS[-1]["valid_weight_sum"], 5 / 6)

    def test_preprocessing_precedes_response_mask_and_missing_support_keeps_mask(self):
        rows, labels = synthetic()
        labels["1|AXG|AXN|target|1"][2] = None
        control_id = f"1|AXG|AXN|{m.SLOTS[0][0]}|{m.SLOTS[0][1]}"
        labels[control_id][2] = None
        summary = m.old.Summary(rows, labels, "synthetic")
        model = m.Conditional(m.conditional_configs()[0], rows, labels, summary, "synthetic")
        context_rows = list(m.old.contexts(rows).values())
        feature = np.array(model.features(context_rows[0], labels))
        self.assertTrue(np.isnan(feature[8]))
        self.assertEqual(feature[30], 0)
        self.assertEqual(len(feature), 38)
        self.assertEqual(model.mean[0], .5)
        self.assertEqual(len(m.PREPROCESSING[-1]["context_weights"]), 6)
        observed = [labels[f"{r[0]['site']}|{r[0]['cell']}|AXN|{m.SLOTS[0][0]}|{m.SLOTS[0][1]}"][2] for r in context_rows]
        self.assertAlmostEqual(model.imputation[8], np.nanmean(np.array(observed, dtype=float)) / summary.scale)

    def test_zero_and_one_valid_response_never_impute_target_truth(self):
        rows, labels = synthetic()
        targets = [r for r in rows if r["drug"] == "target"]
        for r in targets:
            labels[r["bundle_id"]][2] = None
        summary = m.old.Summary(rows, labels, "synthetic")
        model = m.Conditional(m.conditional_configs()[0], rows, labels, summary, "synthetic")
        self.assertAlmostEqual(model.models[(("target", "1"), 2)], summary.global_mean[2] / summary.scale)
        labels[targets[0]["bundle_id"]][2] = 77
        summary = m.old.Summary(rows, labels, "synthetic")
        model = m.Conditional(m.conditional_configs()[0], rows, labels, summary, "synthetic")
        self.assertAlmostEqual(model.models[(("target", "1"), 2)], 77 / summary.scale)

    def test_predict_accepts_only_eight_controls_and_heldout_identity(self):
        rows, labels = synthetic()
        summary = m.old.Summary(rows, labels, "synthetic")
        model = m.Conditional(m.conditional_configs()[0], rows, labels, summary, "synthetic")
        paid = [row("4", d, c) for d, c in m.SLOTS]
        feedback = {r["bundle_id"]: [.3, .8, 25.] for r in paid}
        terminal = [row("4", "target")]
        first = model.predict(paid, feedback, terminal)
        self.assertTrue(np.isfinite(first).all())
        np.testing.assert_array_equal(first, model.predict(paid, dict(feedback), terminal))
        with self.assertRaises(AssertionError):
            model.predict(paid, feedback, [dict(terminal[0], ddfpdc_mean=999)])
        with self.assertRaises(AssertionError):
            model.predict(paid[:-1], {r["bundle_id"]: feedback[r["bundle_id"]] for r in paid[:-1]}, terminal)
        with self.assertRaises(AssertionError):
            model.predict([row("1", d, c) for d, c in m.SLOTS], {f"1|AXG|AXN|{d}|{c}": [.3, .8, 25.] for d, c in m.SLOTS}, [row("1", "target")])

    def test_variant_dimensions_and_unseen_metadata_columns(self):
        rows, labels = synthetic()
        summary = m.old.Summary(rows, labels, "synthetic")
        for config, dimension in ((m.conditional_configs()[0], 38), (m.conditional_configs()[2], 14), (m.conditional_configs()[4], 6)):
            model = m.Conditional(config, rows, labels, summary, "synthetic")
            self.assertEqual(len(model.mean), dimension)
            self.assertEqual(model.mean[3], 0)
            self.assertEqual(model.std[3], 1)
            fitted = model.models[(("target", "1"), 0)]
            self.assertEqual(fitted.coef_[3], 0)

    def test_frozen_required_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / "FREEZE.json").write_text(json.dumps({"files": {}}))
            with patch.object(m, "OUT", out):
                with self.assertRaises(AssertionError):
                    m.verify_freeze()


if __name__ == "__main__":
    unittest.main()
