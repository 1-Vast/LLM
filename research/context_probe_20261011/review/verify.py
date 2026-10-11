"""Independent artifact arithmetic audit; no producer model/report imports.

Run only after a completed commitment and evaluation. This verifies published
matrix replay arithmetic, not raw-assay isolation or biological independence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from random import Random

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close(actual, expected):
    if expected is None:
        assert actual is None, (actual, expected)
    else:
        np.testing.assert_allclose(actual, expected, rtol=1e-11, atol=1e-12)


def bootstrap(differences, labels, seed):
    names = sorted(set(labels))
    if len(names) < 2:
        return None
    sums = np.array([sum(value for value, label in zip(differences, labels) if label == name) for name in names])
    counts = np.array([labels.count(name) for name in names])
    rng = Random(seed)
    draws = []
    for _ in range(2000):
        sampled = [rng.randrange(len(names)) for _ in names]
        draws.append(float(sums[sampled].sum() / counts[sampled].sum()))
    draws.sort()
    return [draws[int(0.025 * 1999)], draws[int(0.975 * 1999)]]


def verify(out):
    freeze, receipt = read(out / "FREEZE.json"), read(out / "RECEIPT.json")
    commit_receipt = read(out / "COMMIT_RECEIPT.json")
    for relative, expected in freeze["files"].items():
        assert sha(ROOT / relative) == expected, relative
    assert sha(freeze["input_path"]) == freeze["input_sha256"]
    for filename, key in (("COMMITS.json", "commits_sha256"), ("predictions.npz", "predictions_sha256"), ("FIT_FREEZE.json", "fit_sha256")):
        assert sha(out / filename) == commit_receipt[key], filename
    for filename, key in (("RESULTS.json", "results_sha256"), ("ROWS.json", "rows_sha256")):
        assert sha(out / filename) == receipt[key], filename

    protocol = read(STUDY / "PROTOCOL.json")
    manifest = read(STUDY / "data/MANIFEST.json")
    for source in manifest["sources"]:
        assert sha(ROOT / source["path"]) == source["sha256"], source["path"]
    assert sha(STUDY / "data/prepare.py") == manifest["prepare_sha256"]
    assert sha(freeze["input_path"]) == manifest["output_npz_sha256"]
    for filename, expected in manifest["derived_file_sha256"].items():
        assert sha(STUDY / "data" / filename) == expected, filename

    # Open outcome values only after commitment/score artifact hashes validate.
    with np.load(freeze["input_path"], allow_pickle=False) as archive:
        data = {key: archive[key] for key in archive.files}
    with np.load(out / "predictions.npz", allow_pickle=False) as archive:
        predictions = archive["predictions"]
    assert np.isfinite(predictions).all()
    assert len(set(data["identity_key"])) == len(data["identity_key"])
    salt = manifest["context_roles"]["salt"]
    for identity, role in zip(data["identity_key"], data["role"]):
        value = int(hashlib.sha256(f"{salt}|{identity}".encode()).hexdigest(), 16) / 2**256
        assert role == ("reference" if value < 0.6 else "development" if value < 0.8 else "evaluation")
    observed_fraction = np.isfinite(data["y"][data["role"] == "reference"]).mean(axis=0)
    assert np.all(observed_fraction >= 0.95)
    np.testing.assert_array_equal(data["available"], np.isfinite(data["y"]))

    groups = read(STUDY / "data/drug_groups.json")
    eligible = [group for group in groups if group["eligible"]]
    assert [group["drug_id"] for group in eligible] == data["drug_id"].tolist()
    columns = [group["representative_column"] for group in eligible]
    sources = {source["name"]: ROOT / source["path"] for source in manifest["sources"]}
    metadata = pd.read_csv(sources["treatments"], keep_default_na=False).set_index("column_name")
    qualified = metadata.loc[columns]
    assert qualified.screen_id.eq("HTS").all() and qualified.dose.eq(2.5).all()
    contexts = pd.read_csv(STUDY / "data/contexts.csv")
    raw = pd.read_csv(sources["responses"], index_col=0)
    np.testing.assert_array_equal(raw.loc[contexts.response_row_id, columns].to_numpy(), data["y"])

    fit = read(out / "FIT_FREEZE.json")
    probes = fit["probe_indices"]
    assert len(set(probes)) == protocol["probe_count"] == 8
    assert data["drug_id"][probes].tolist() == fit["probe_ids"]
    probe_freeze = read(out / "PROBE_FREEZE.json")
    assert probe_freeze["probe_indices"] == probes and probe_freeze["probe_ids"] == fit["probe_ids"]
    assert probe_freeze["reference_context_ids"] == data["context_id"][data["role"] == "reference"].tolist()
    terminal = sorted(set(range(len(data["drug_id"]))) - set(probes))
    assert len(terminal) == fit["terminal_count"]
    evaluation = np.flatnonzero(data["role"] == "evaluation")
    arms = protocol["arms"]
    assert predictions.shape == (len(evaluation), len(arms), len(data["drug_id"]))
    records, rows, result = read(out / "COMMITS.json"), read(out / "ROWS.json"), read(out / "RESULTS.json")
    assert len(records) == len(rows) == len(evaluation) * len(arms) == receipt["arm_contexts"]
    assert len({(record["context"], record["arm"]) for record in records}) == len(records)
    for record, row in zip(records, rows):
        assert all(row[key] == value for key, value in record.items())
        index = record["index"]
        position = evaluation.tolist().index(index)
        arm_position = arms.index(record["arm"])
        prediction = predictions[position, arm_position]
        chosen = sorted(terminal, key=lambda drug: (prediction[drug], drug))[:protocol["top_k"]]
        assert chosen == record["selected_indices"]
        assert len(set(chosen)) == 10 and not set(chosen).intersection(probes)
        assert record["selected_ids"] == data["drug_id"][chosen].tolist()
        assert record["context"] == data["context_id"][index]
        assert record["lineage"] == data["lineage"][index]
        paid = record["arm"] != "zero_purchase"
        assert record["measurements"] == (8 if paid else 0)
        assert record["turnarounds"] == int(paid)
        assert record["resource"] == (10 if paid else 0)
        assert record["resource"] <= protocol["budget"]["total"]
        assert record["probe_indices"] == (probes if paid else [])
        truth = data["y"][index]
        expected_probes = [float(value) if np.isfinite(value) else None for value in truth[probes]]
        assert record["probe_values"] == (expected_probes if paid else [])
        assert record["probe_missing"] == (expected_probes.count(None) if paid else 0)
        finite_selected = [drug for drug in chosen if np.isfinite(truth[drug])]
        finite_terminal = [drug for drug in terminal if np.isfinite(truth[drug])]
        close(row["utility"], -sum(truth[drug] for drug in chosen) / 10 if len(finite_selected) == 10 else None)
        assert row["selected_missing"] == 10 - len(finite_selected)
        assert row["selected_measured"] == len(finite_selected)
        assert row["terminal_measured"] == len(finite_terminal)
        close(row["terminal_mse"], np.mean([(prediction[drug] - truth[drug]) ** 2 for drug in finite_terminal]))
        close(row["selected_mae"], np.mean([abs(prediction[drug] - truth[drug]) for drug in finite_selected]) if finite_selected else None)
        baseline = records[position * len(arms)]["selected_indices"]
        assert row["changed_selected"] == len(set(chosen) - set(baseline))
        if record["arm"] in {"zero_purchase", "paid_no_update", "offset"}:
            assert chosen == baseline
        if paid and None in expected_probes:
            assert record["update_status"] == "missing_probe_fallback"
            np.testing.assert_array_equal(prediction, predictions[position, 0])

    lookup = {(row["context"], row["arm"]): row for row in rows}
    for name, contrast in result["comparisons"].items():
        report = contrast["report"]
        candidate, other = name.split("_minus_", 1)
        reference, price_string = other.rsplit("_price_", 1)
        price = float(price_string)
        intended = data["context_id"][evaluation].tolist()
        complete = [context for context in intended if all(lookup[context, arm]["utility"] is not None for arm in (candidate, reference))]
        assert contrast["paired_contexts"] == len(complete)
        assert contrast["unscored_contexts"] == [context for context in intended if context not in complete]
        if not complete:
            assert report is None
            continue
        differences, labels, raw_differences = [], [], []
        for context in sorted(complete):
            left, right = lookup[context, reference], lookup[context, candidate]
            raw_difference = right["utility"] - left["utility"]
            raw_differences.append(raw_difference)
            differences.append(raw_difference - price * (right["resource"] - left["resource"]))
            labels.append(left["lineage"])
        assert report["campaigns"] == len(complete)
        close(report["raw_utility_increment"], np.mean(raw_differences))
        close(report["net_utility_increment"], np.mean(differences))
        close(report["cluster_bootstrap_95"], bootstrap(differences, labels, protocol["seed"]))
        assert contrast["improved"] == sum(value > 1e-12 for value in raw_differences)
        assert contrast["harmed"] == sum(value < -1e-12 for value in raw_differences)
        assert contrast["equal"] == sum(abs(value) <= 1e-12 for value in raw_differences)
    primary = [result["comparisons"][name] for name in ("lowrank_minus_paid_no_update_price_0", "lowrank_minus_shuffled_lowrank_price_0", "lowrank_minus_conditional_price_0", "lowrank_minus_zero_purchase_price_0.001")]
    complete = all(not contrast["unscored_contexts"] for contrast in primary)
    assert result["all_primary_contrasts_complete"] == complete
    positive = all(contrast["report"] and contrast["report"]["cluster_bootstrap_95"] and contrast["report"]["cluster_bootstrap_95"][0] > 0 for contrast in primary)
    assert result["status"] == ("PROMISING_EXPLORATORY_ONLY" if complete and positive else "NOT_ESTABLISHED")
    return {"status": "PASS_ARITHMETIC_AND_ARTIFACT_AUDIT", "study_status": result["status"], "contexts": len(evaluation), "arm_contexts": len(rows), "comparisons": len(result["comparisons"]), "source_response_alignment": "Exact including missing values", "reviewer_imports": "No producer model, runner, utility or inference imports", "verified": ["frozen source and artifact hashes", "metadata-only role hash and reference completeness", "exact-dose HTS source response alignment", "committed top10 and menu exclusion", "attempted probe charges and missing fallback", "all row utilities, errors and missingness", "paired contrasts and independently reconstructed cluster bootstrap", "rank-invariant offset", "full-population gate"], "not_verified": ["sign-flip p-values (not used in diagnostic status)", "raw publisher preprocessing isolation", "independent culture/plate units", "real monetary or latency cost", "prospective scientific benefit"], "scope": "All outcomes are exposed retrospective public data. Independent software audit does not create biological replication.", "files": {filename: sha(out / filename) for filename in ("FREEZE.json", "PROBE_FREEZE.json", "FIT_FREEZE.json", "COMMITS.json", "predictions.npz", "ROWS.json", "RESULTS.json", "RECEIPT.json")}, "verifier_sha256": sha(__file__)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.output)
    (HERE / "VERIFICATION.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "study_status", "contexts", "arm_contexts", "comparisons")}))
