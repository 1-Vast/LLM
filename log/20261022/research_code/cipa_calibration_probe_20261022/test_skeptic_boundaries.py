"""Independent synthetic-only review checks; no assay file reads or model fits."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

SPEC = importlib.util.spec_from_file_location("reviewed_probe", Path(__file__).with_name("model_probe.py"))
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def row(site, drug="Other", dose="1", cell="A"):
    return dict(bundle_id=f"{site}|{cell}|P|{drug}|{dose}", site=site, cell=cell,
                platform="P", drug=drug, dose_code=dose, split="source" if site in "12345" else "dev")


class RestrictedRow(dict):
    def __getitem__(self, key):
        if key not in probe.KEYS:
            raise AssertionError("Unpaid numerical field accessed")
        return super().__getitem__(key)


class SkepticBoundaries(unittest.TestCase):
    def setUp(self):
        probe.SUMMARIES.clear()
        probe.FITS.clear()

    def test_metadata_and_paid_label_projection(self):
        unpaid = RestrictedRow(row("6"))
        paid = dict(row("6", dose="2"), ead_mean=.25,
                    ddfpdc_available_fraction=.5, ddfpdc_mean=None)
        with patch.object(probe, "read", return_value={"bundles": [unpaid, paid]}):
            meta = probe.metadata()
            self.assertTrue(all(set(r) == set(probe.KEYS) for r in meta))
            self.assertEqual(probe.labels_for([paid["bundle_id"]]), {paid["bundle_id"]: [.25, .5, None]})

    def test_manifest_exact_pools_balanced_folds_and_budgets(self):
        drugs = sorted(probe.CONTROLS) + ["Ibutilide"] + [f"Other{i}" for i in range(23)]
        meta = [row(s, d, str(c), "CDI" if s == "3" else "A")
                for s in "1234567" for d in drugs for c in range(1, 5)
                if (s, d, c) != ("3", "Ibutilide", 1)]
        for r in meta:
            if r["site"] == "3":
                r["platform"] = "MCS"
                r["bundle_id"] = f"3|CDI|MCS|{r['drug']}|{r['dose_code']}"
        manifest = probe.make_manifest(meta)
        for context, cm in manifest["contexts"].items():
            self.assertEqual(len(cm["pool"]), 16)
            self.assertEqual(len(cm["terminal"]), 95 if context == "3|CDI|MCS" else 96)
            self.assertFalse(set(cm["pool"]) & set(cm["terminal"]))
            self.assertEqual([len(f) for f in cm["portfolio_folds"]], [2] * 4)
            for ids in cm["metadata_policies"].values():
                self.assertEqual(len(set(ids)), 8)
                self.assertLessEqual(set(ids), set(cm["pool"]))

    def test_brier_conditional_h_and_no_selective_prediction_mask(self):
        pred = np.array([[.25, .5, 10.], [.75, .25, 999.]])
        score = probe.losses(pred, [[.5, .25, 14.], [1., 0., None]], 2.)
        self.assertAlmostEqual(score["components"]["E"], (.3125 + .0625) / 2)
        self.assertAlmostEqual(score["components"]["M"], (.25 + .0625) / 2)
        self.assertEqual(score["components"]["H"], 2.)
        self.assertEqual(score["raw_H_MAE"], 4.)
        self.assertEqual(score["coverage"]["H"], {"valid": 1, "total": 2})
        missing = probe.losses(pred, [[.5, .25, None], [1., 0., None]], 2.)
        self.assertIsNone(missing["components"]["H"])
        self.assertAlmostEqual(missing["combined"], np.mean([missing["components"]["E"], missing["components"]["M"]]))
        pred[0, 2] = np.nan
        with self.assertRaises(AssertionError):
            probe.losses(pred, [[.5, .25, 14.], [1., 0., None]], 2.)

    def test_nested_features_exclude_entire_own_site(self):
        source = [row(s, dose=d, cell=c) for s in "12345" for c in ("A", "B") for d in ("1", "2")]
        labels = {r["bundle_id"]: [int(r["site"]) / 5., .5, int(r["site"]) * int(r["dose_code"])] for r in source}
        original = probe.nested_vectors(source, labels, "synthetic")
        mutated = {bid: list(y) for bid, y in labels.items()}
        for r in source:
            if r["site"] == "2":
                mutated[r["bundle_id"]] = [.99, .99, 999999.]
        changed = probe.nested_vectors(source, mutated, "synthetic_mutated")
        own = [i for i, r in enumerate(source) if r["site"] == "2"]
        np.testing.assert_array_equal(original[own], changed[own])
        for log in probe.SUMMARIES:
            excluded = log["stage"].rsplit("_", 1)[1]
            self.assertNotIn(excluded, log["source_sites"])

    def test_source_cv_physical_site_boundary_without_solver_fits(self):
        meta, manifest, labels = [], {"contexts": {}}, {}
        for site in "12345":
            for cell in (("A", "B") if site == "1" else ("A",)):
                paid = [row(site, d, c, cell) for d in sorted(probe.CONTROLS) for c in ("1", "4")]
                terminal = [row(site, "Other", c, cell) for c in ("1", "2")]
                meta.extend(paid + terminal)
                for r in paid + terminal:
                    labels[r["bundle_id"]] = [.2, .8, float(site) + int(r["dose_code"])]
                manifest["contexts"][f"{site}|{cell}|P"] = {
                    "metadata_policies": {"fixed": [r["bundle_id"] for r in paid]},
                    "terminal": [r["bundle_id"] for r in terminal]}

        def restricted_predict(config, source, source_labels, paid, paid_labels, test_meta, summary, dictionary, stage, context, nested):
            heldout = context.split("|")[0]
            self.assertTrue(all(r["site"] != heldout for r in source))
            self.assertEqual(set(source_labels), {r["bundle_id"] for r in source})
            self.assertEqual(set(paid_labels), {r["bundle_id"] for r in paid})
            self.assertTrue(all(r["site"] == heldout for r in paid + test_meta))
            self.assertFalse(set(paid_labels) & {r["bundle_id"] for r in test_meta})
            self.assertNotIn(heldout, {r["site"] for r in summary.rows})
            return probe.bounded(summary.lookup(test_meta, normalized=False))

        with patch.object(probe, "labels_for", side_effect=lambda ids: {bid: labels[bid] for bid in ids}), patch.object(probe, "predict", side_effect=restricted_predict):
            choices = probe.source_cv(meta, manifest, probe.make_dictionary(meta))
        self.assertEqual(probe.FITS, [])
        self.assertEqual(len(choices["families"]), 7)
        for cid, bysite in choices["scores"].items():
            self.assertEqual(set(bysite), set("12345"))
            self.assertAlmostEqual(choices["mean_physical_site_combined"][cid], np.mean([x["combined"] for x in bysite.values()]))


if __name__ == "__main__":
    unittest.main()
