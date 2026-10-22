"""Synthetic access-contract tests. No real archive or response is opened."""
from collections import Counter
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import numpy as np

import prepare as p


HEADER = p.META + list(p.PAID) + ["lib1_yhat", "lib2_yhat", "Bliss", "INTENSITY"]
WORK = p.LOG / "synthetic_work"


def matrix(name, role, ids, dose_rows, values):
    rows = []
    for i, (doses, observed) in enumerate(zip(dose_rows, values), 1):
        r = {f: "fixed" for f in p.META}
        r.update(PROJECT_ID="GDSC007", PROJECT_NAME="synthetic", BARCODE=role,
                 cmatrix=name, MASTER_CELL_ID=role, CELL_ID=role,
                 CANCER_TYPE="synthetic", POSITION=str(i), treatment="combination")
        for axis, drug, dose in zip((1, 2), ids, doses):
            r.update({f"lib{axis}": drug, f"lib{axis}_drug_id": drug,
                      f"lib{axis}_dose": dose, f"lib{axis}_conc": dose})
        r.update(dict(zip(p.PAID, observed)))
        r.update({f: "FORBIDDEN" for f in HEADER if f not in r})
        rows.append(r)
    return rows


def selected_record(rows):
    r = rows[0]
    varying = {"POSITION", "lib1_dose", "lib1_conc", "lib2_dose", "lib2_conc"}
    counts = Counter(tuple(x[f] for f in ("lib1_dose", "lib1_conc", "lib2_dose", "lib2_conc")) for x in rows)
    return {"member": p.MEMBER, "PROJECT_ID": r["PROJECT_ID"], "BARCODE": r["BARCODE"],
            "cmatrix": r["cmatrix"], "metadata": [{f: r[f] for f in p.META if f not in varying}],
            "rows": len(rows), "positions": dict(Counter(x["POSITION"] for x in rows)),
            "dose_pairs": [dict(zip(("lib1_dose", "lib1_conc", "lib2_dose", "lib2_conc"), k), count=v) for k, v in counts.items()]}


def fixture():
    episodes, records, rows = [], [], []
    for role in ("train", "validation", "test", "reserve"):
        wa = matrix("wA", role, ("C", "A"), [("2", "1"), ("3", "1.0"), ("2", "10"), ("3", "10.0")],
                    [(".1", ".2", ".5"), (".2", "", ".6"), (".1", "0", ".3"), (".2", ".4", ".7")])
        wb = matrix("wB", role, ("B", "D"), [("5", "2"), ("5.0", "3"), ("50", "2"), ("50.0", "3")],
                    [(".3", ".05", ".4"), (".5", ".1", ".7"), (".6", ".05", ".75"), (".8", ".1", "1.2")])
        target = matrix("target", role, ("B", "A"), [("5", "1.00"), ("50", "1"), ("5", "10"), ("50", "10.00")],
                        [("FORBIDDEN", "FORBIDDEN", ".6"), ("FORBIDDEN", "FORBIDDEN", "NaN"),
                         ("FORBIDDEN", "FORBIDDEN", ".8"), ("FORBIDDEN", "FORBIDDEN", ".9")])
        group = [wa, wb, target]
        rs = [selected_record(x) for x in group]
        records.extend(rs)
        rows.extend(x for group_rows in group for x in group_rows)
        episodes.append({"cell": role, "cancer_type": "synthetic", "pair": ["A", "B"], "role": role,
                         "target": list(p.key(rs[2])), "witnesses": [list(p.key(rs[0])), list(p.key(rs[1]))]})
    design = {"target_pairs": [["A", "B"]], "query_pairs": [["A", "C"], ["B", "D"]], "member": p.MEMBER}
    selected = {p.key(r): r for r in records}
    schema = p.schema_from_metadata(design, records, "synthetic-metadata")
    return episodes, records, rows, design, selected, schema


def csv_text(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=HEADER)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def scan(rows, episodes, selected, targets_only=False):
    return p.scan_csv(io.StringIO(csv_text(rows)), p.routes_for(episodes, targets_only), selected)


class GuardedRow(list):
    def __init__(self, values, forbidden):
        super().__init__(values)
        self.forbidden = forbidden

    def __getitem__(self, index):
        if index in self.forbidden:
            raise AssertionError("Forbidden response field indexed")
        return super().__getitem__(index)


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.episodes, self.records, self.rows, self.design, self.selected, self.schema = fixture()

    def test_routed_access_guards_and_conversion_counts(self):
        guarded = [HEADER]
        for r in self.rows:
            forbidden = {HEADER.index(f) for f in HEADER if f not in p.META + list(p.PAID)}
            if r["cmatrix"] == "target":
                forbidden |= {HEADER.index("lib1_y"), HEADER.index("lib2_y")}
                if r["BARCODE"] == "test":
                    forbidden.add(HEADER.index("inhibition"))
            if r["BARCODE"] == "reserve":
                forbidden |= {HEADER.index(f) for f in p.PAID}
            guarded.append(GuardedRow([r[f] for f in HEADER], forbidden))
        with patch.object(p.csv, "reader", return_value=iter(guarded)):
            found, ledger = p.scan_csv(None, p.routes_for(self.episodes), self.selected)
        self.assertEqual(set(ledger), {"paid:train", "paid:validation", "paid:test", "target:train", "target:validation"})
        self.assertEqual(set(ledger["target:train"]), {"inhibition"})
        self.assertEqual(ledger["paid:train"]["inhibition"]["finite_outside_0_1"], 1)
        self.assertEqual(ledger["paid:train"]["lib2_y"]["missing_or_nonfinite"], 1)
        self.assertEqual(len(found), 9)
        data, rows, meta, summaries, observations = p.assemble(self.episodes, found, self.schema)
        self.assertTrue(np.isnan(data["y"][data["role"] == "test"]).all())
        self.assertTrue(data["valid_mask"].all())
        self.assertEqual(len(rows), 12)
        self.assertEqual(len(meta), 3)
        self.assertEqual(len(summaries), 6)
        self.assertEqual(len(observations), 6)

    def test_forbidden_poison_invariance(self):
        base, _ = scan(self.rows, self.episodes, self.selected)
        changed = copy.deepcopy(self.rows)
        for r in changed:
            if r["cmatrix"] == "target":
                r["lib1_y"], r["lib2_y"] = "1e300", "-999"
                if r["BARCODE"] == "test":
                    r["inhibition"] = "777"
            if r["BARCODE"] == "reserve":
                for f in p.PAID:
                    r[f] = "999"
            for f in HEADER:
                if f not in p.META + list(p.PAID):
                    r[f] = "1e300"
        other, _ = scan(changed, self.episodes, self.selected)
        a = p.assemble(self.episodes, base, self.schema)
        b = p.assemble(self.episodes, other, self.schema)
        for field in a[0]:
            np.testing.assert_equal(a[0][field], b[0][field])
        self.assertEqual(a[1:], b[1:])

    def test_exact_dose_mean_residual_and_missing_masks(self):
        found, _ = scan(self.rows, self.episodes, self.selected)
        summary = p.paid_summary(found[tuple(self.episodes[0]["witnesses"][0])], self.schema)
        self.assertAlmostEqual(summary["mono"][("A", p.Decimal("1.00"))], .2)
        self.assertAlmostEqual(summary["mono"][("A", p.Decimal("10"))], .2)
        self.assertAlmostEqual(summary["mean_residual"], .205)
        full = summary["full"].reshape(49, 9)
        np.testing.assert_array_equal(full[1, [2, 5, 6]], [0, 1, 0])  # missing observation
        np.testing.assert_array_equal(full[2, [2, 5, 6]], [0, 1, 1])  # observed zero
        np.testing.assert_array_equal(full[4, [2, 5, 6]], [0, 0, 0])  # absent grid position
        np.testing.assert_array_equal(summary["without_mono"].reshape(49, 5), full[:, [0, 1, 4, 5, 8]])
        data, _, _, _, _ = p.assemble(self.episodes, found, self.schema)
        np.testing.assert_allclose(data["effect"][:4], [[.2, .4], [.2, .7], [.2, .4], [.2, .7]])
        np.testing.assert_allclose(data["dose"][:4], [[0, 0], [0, 1], [1, 0], [1, 1]])
        np.testing.assert_allclose(data["raw_dose"][:4], [[1, 5], [1, 50], [10, 5], [10, 50]])
        self.assertTrue(data["valid_mask"][:4].all())  # target missingness is not an input abstention
        self.assertTrue(np.isnan(data["y"][1]))

    def test_common_whole_episode_abstention_with_no_retarget(self):
        for failure in ("mono", "partner_mono", "combination"):
            rows = copy.deepcopy(self.rows)
            for r in rows:
                if r["BARCODE"] == "train" and r["cmatrix"] == "wA":
                    if failure == "mono" and p.Decimal(r["lib2_conc"]) == 1:
                        r["lib2_y"] = "NaN"
                    if failure == "partner_mono" and p.Decimal(r["lib1_conc"]) == 2:
                        r["lib1_y"] = "NaN"
                    if failure == "combination" and r["POSITION"] == "2":
                        r["inhibition"] = "inf"
            found, _ = scan(rows, self.episodes, self.selected)
            data, row_map, meta, _, _ = p.assemble(self.episodes, found, self.schema)
            self.assertFalse(data["valid_mask"][:4].any())
            self.assertTrue(data["valid_mask"][4:].all())
            self.assertFalse(meta[0]["valid"])
            self.assertEqual(meta[0]["logical_bundles"], 2)
            self.assertEqual(meta[0]["query_keys"], self.episodes[0]["witnesses"])
            self.assertEqual(len(row_map), 12)
            self.assertTrue(np.isfinite(data["full"]).all())
            self.assertTrue(np.isfinite(data["without_mono"]).all())

    def test_axis_reversal_and_direct_attribution_information(self):
        found, _ = scan(self.rows, self.episodes, self.selected)
        r = found[tuple(self.episodes[0]["witnesses"][0])][0]
        swapped = copy.deepcopy(r)
        for field in ("", "_dose", "_drug_id", "_conc"):
            swapped["lib1" + field], swapped["lib2" + field] = r["lib2" + field], r["lib1" + field]
        swapped["observed"]["lib1_y"], swapped["observed"]["lib2_y"] = r["observed"]["lib2_y"], r["observed"]["lib1_y"]
        self.assertEqual(p.canonical(r), p.canonical(swapped))
        a = p.assemble(self.episodes, found, self.schema)[0]
        changed = copy.deepcopy(found)
        for w in self.episodes[0]["witnesses"]:
            for row in changed[tuple(w)]:
                for f in ("lib1_y", "lib2_y"):
                    if row["observed"][f] is not None:
                        row["observed"][f] += .1
        b = p.assemble(self.episodes, changed, self.schema)[0]
        np.testing.assert_array_equal(a["without_mono"], b["without_mono"])
        np.testing.assert_array_equal(a["valid_mask"], b["valid_mask"])
        self.assertFalse(np.array_equal(a["full"], b["full"]))

    def test_reject_role_overlap_and_metadata_drift(self):
        overlap = copy.deepcopy(self.episodes)
        overlap[0]["target"] = overlap[0]["witnesses"][0]
        with self.assertRaises(ValueError):
            p.routes_for(overlap)
        overlap = copy.deepcopy(self.episodes)
        overlap[1]["witnesses"][0] = overlap[0]["witnesses"][0]
        with self.assertRaises(ValueError):
            p.routes_for(overlap)
        rows = copy.deepcopy(self.rows)
        rows[0]["CELL_ID"] = "drifted"
        with self.assertRaises(ValueError):
            scan(rows, self.episodes, self.selected)

    def test_test_target_access_and_mapping(self):
        found, _ = scan(self.rows, self.episodes, self.selected)
        _, rows_map, _, _, _ = p.assemble(self.episodes, found, self.schema)
        targets, ledger = scan(self.rows, self.episodes, self.selected, targets_only=True)
        self.assertEqual(set(ledger), {"test_target:test"})
        self.assertEqual(set(ledger["test_target:test"]), {"inhibition"})
        y = p.extract_test_targets(rows_map, targets)
        self.assertEqual(y.shape, (12,))
        self.assertTrue(np.isnan(y[:8]).all())
        np.testing.assert_allclose(y[8:], [.6, np.nan, .8, .9], equal_nan=True)

    def test_synthetic_stages_seal_binding_receipts_and_no_overwrite(self):
        WORK.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="prepare_", dir=WORK) as temporary:
            log = Path(temporary)
            archive = log / "synthetic.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr(p.MEMBER, csv_text(self.rows))
            p.write(log / "EPISODES.json", self.episodes)
            p.write(log / "SELECTED_DESIGN.json", self.records)
            design = dict(self.design, episode_file_sha256=p.sha(log / "EPISODES.json"),
                          selected_design_sha256=p.sha(log / "SELECTED_DESIGN.json"), source_projection_sha256="synthetic-metadata")
            p.write(log / "DESIGN.json", design)
            p.write(log / "FEATURE_SCHEMA.json", self.schema)
            (log / "MEASURED_PROTOCOL.md").write_text("Synthetic protocol only.", encoding="utf-8")
            with patch.object(p, "ARCHIVE", archive), patch.object(p, "ARCHIVE_SHA", p.sha(archive)):
                p.run(log, "inputs")
                with self.assertRaises(RuntimeError):
                    p.run(log, "inputs")
                access = json.loads((log / "ACCESS_INPUTS.json").read_text())
                self.assertFalse(access["target_attached_mono_or_fitted_fields_indexed"])
                np.savez_compressed(log / "TEST_PREDICTIONS.npz", synthetic=np.zeros(12))
                p.write(log / "PREDICTIONS_SEAL.json", {"predictions_sha256": "bad-hash"})
                with patch.object(p.zipfile, "ZipFile", side_effect=AssertionError("Source opened before seal")):
                    with self.assertRaises(ValueError):
                        p.run(log, "test-targets")
                self.assertFalse((log / "TEST_TARGETS_STARTED.json").exists())
                p.write(log / "TEST_ACTIONS.json", {"synthetic": []})
                p.write(log / "SELECTION.json", {"synthetic": True})
                p.write(log / "PREDICTIONS_SEAL.json", {"predictions_sha256": p.sha(log / "TEST_PREDICTIONS.npz"),
                                                       "actions_sha256": p.sha(log / "TEST_ACTIONS.json"),
                                                       "selection_sha256": p.sha(log / "SELECTION.json")})
                for name in ("TEST_ACTIONS.json", "SELECTION.json"):
                    original = (log / name).read_bytes()
                    (log / name).write_bytes(original + b"\n")
                    with patch.object(p.zipfile, "ZipFile", side_effect=AssertionError("Source opened before action seal check")):
                        with self.assertRaises(ValueError):
                            p.run(log, "test-targets")
                    (log / name).write_bytes(original)
                    self.assertFalse((log / "TEST_TARGETS_STARTED.json").exists())
                for name in ("ROWS.json", "MEASURED_PROTOCOL.md", "FEATURE_SCHEMA.json"):
                    original = (log / name).read_bytes()
                    (log / name).write_bytes(original + b"\n")
                    with patch.object(p.zipfile, "ZipFile", side_effect=AssertionError("Source opened before binding check")):
                        with self.assertRaises(ValueError):
                            p.run(log, "test-targets")
                    (log / name).write_bytes(original)
                    self.assertFalse((log / "TEST_TARGETS_STARTED.json").exists())
                p.run(log, "test-targets")
                with np.load(log / "DATA.npz", allow_pickle=False) as data, np.load(log / "TEST_TARGETS.npz", allow_pickle=False) as target:
                    self.assertEqual(target["y"].shape, data["y"].shape)
                    self.assertTrue(np.isnan(data["y"][data["role"] == "test"]).all())
                    np.testing.assert_allclose(target["y"][-4:], [.6, np.nan, .8, .9], equal_nan=True)
                receipt = json.loads((log / "TEST_TARGETS_RECEIPT.json").read_text())
                self.assertEqual(receipt["predictions_sha256"], p.sha(log / "TEST_PREDICTIONS.npz"))

    def test_schema_uses_all_design_doses_and_rejects_nonpositive(self):
        extra = copy.deepcopy(self.records[0])
        extra["dose_pairs"][0]["lib2_conc"] = "1000"
        schema = p.schema_from_metadata(self.design, self.records + [extra], "synthetic-metadata")
        self.assertEqual(schema["drug_log10_uM_ranges"]["A"], [0, 3])
        self.assertEqual(len(schema["full_columns"]), schema["dimensions"]["full"])
        self.assertEqual(len(schema["without_mono_columns"]), schema["dimensions"]["without_mono"])
        extra["dose_pairs"][0]["lib2_conc"] = "0"
        with self.assertRaises(ValueError):
            p.schema_from_metadata(self.design, [extra], "synthetic-metadata")


if __name__ == "__main__":
    unittest.main(verbosity=2)
