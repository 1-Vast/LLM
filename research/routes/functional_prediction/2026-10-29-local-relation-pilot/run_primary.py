"""One frozen development pilot. Ordinary ridge models; no new-algorithm claim."""
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import csv
import hashlib
import io
import itertools
import json
import math
import platform
import time
import zipfile

import numpy as np

HERE = Path(__file__).resolve().parent
ZIP = HERE.parents[1] / "tmp/extq1/gsdc_well_stats.zip"
ZIP_SHA = "e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259"
SUPPORT_SHA = "c0c1e067330960bb43d63f739e0890a96630bcf1446ddf9232740f70a6e3d941"
MEMBER = "combo_well_stats_GDSC_007_05May22.csv"
MODELS = ("A", "L", "T", "C", "D")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            hasher.update(block)
    return hasher.hexdigest()


def read_responses():
    assert digest(ZIP) == ZIP_SHA
    observed, drug_mapping = {}, {}
    fields = ["PROJECT_ID", "MASTER_CELL_ID"] + [f"lib{s}_{n}" for s in (1, 2) for n in ("drug_id", "drug", "conc", "y")]
    with zipfile.ZipFile(ZIP) as archive, archive.open(MEMBER) as raw:
        rows = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
        header = next(rows)
        indices = {name: header.index(name) for name in fields}
        count = 0
        for values in itertools.islice(rows, 20000):
            row = {name: values[index] for name, index in indices.items()}
            del values
            count += 1
            for side in (1, 2):
                project, cell = row["PROJECT_ID"], row["MASTER_CELL_ID"]
                ref, drug = row[f"lib{side}_drug"], row[f"lib{side}_drug_id"]
                dose = Decimal(row[f"lib{side}_conc"])
                text = row[f"lib{side}_y"]
                value = Decimal(text)
                assert dose.is_finite() and dose > 0 and value.is_finite() and 0 <= value <= 1
                key = (project, cell, ref, dose)
                if key in observed:
                    assert observed[key][0] == text and observed[key][1] == value
                observed[key] = (text, value)
                identity = (project, cell, ref)
                if identity in drug_mapping:
                    assert drug_mapping[identity] == drug
                drug_mapping[identity] = drug
    assert count == 20000 and len(observed) == 5924
    return observed, drug_mapping


def hats(x, bounds):
    r = (x - bounds[0]) / (bounds[1] - bounds[0])
    assert np.all(r >= -1e-12) and np.all(r <= 1 + 1e-12)
    return np.column_stack((np.maximum(1 - 2 * r, 0), 1 - np.abs(2 * r - 1), np.maximum(2 * r - 1, 0)))


def features(kind, phi, source):
    z = source - 0.5
    if kind == "T":
        return phi
    additive = np.column_stack((phi, z))
    if kind == "A":
        return additive
    return np.column_stack((additive, z * (phi[:, 0] - phi[:, 1]), z * (phi[:, 2] - phi[:, 1])))


def predict_after_query(train_phi, train_source, train_target, test_phi, test_source, query_index, query_y):
    """Receives only one held-out target label; the scoring oracle is not passed."""
    phi = np.vstack((train_phi, test_phi[query_index]))
    source = np.append(train_source, test_source[query_index])
    target = np.append(train_target, query_y) - 0.5
    predictions = {}
    for kind in ("A", "L", "T"):
        design = features(kind, phi, source)
        theta = np.linalg.solve(design.T @ design + 0.01 * np.eye(design.shape[1]), design.T @ target)
        predictions[kind] = 0.5 + features(kind, test_phi, test_source) @ theta
    predictions["C"] = test_source + query_y - test_source[query_index]
    for prediction in predictions.values():
        prediction[query_index] = query_y
        assert np.all(np.isfinite(prediction))
    return predictions


def recommend(prediction, query_index, query_active):
    eligible = prediction >= 0.5
    eligible[query_index] = query_active
    hits = np.flatnonzero(eligible)
    return int(hits[0]) if len(hits) else -1


def decision_loss(choice, truth, log_doses):
    active = [index for index, value in enumerate(truth) if value]
    if choice < 0:
        return float(bool(active)), "missed" if active else "correct_abstention"
    if not truth[choice]:
        return 1.0, "inactive_recommendation"
    loss = float((log_doses[choice] - log_doses[active[0]]) / (log_doses[-1] - log_doses[0]))
    assert -1e-12 <= loss <= 1 + 1e-12
    return loss, "active_recommendation"


def main():
    start, cpu_start = time.perf_counter(), time.process_time()
    assert not (HERE / "primary_results.csv").exists()
    assert digest(HERE / "support_frozen.json") == SUPPORT_SHA
    approval = json.loads((HERE / "run_admission.json").read_text(encoding="utf-8"))
    assert approval["primary_run_admitted"] is True
    assert approval["script_sha256"] == digest(Path(__file__))
    assert approval["protocol_sha256"] == digest(HERE / approval["protocol_file"])
    support = json.loads((HERE / "support_frozen.json").read_text(encoding="utf-8"))
    observed, mapping = read_responses()
    output, grouped, arithmetic_packet = [], defaultdict(list), []
    for pair in support["pairs"]:
        project, source_cell, target_cell = pair["project"], pair["source_cell"], pair["target_cell"]
        curves = []
        all_x = []
        for item in pair["drugs"]:
            doses = [Decimal(value) for value in item["concentrations_micromolar"]]
            x = np.log10(np.array([float(dose) for dose in doses]))
            assert mapping[(project, source_cell, item["source_ref"])] == item["drug"]
            assert mapping[(project, target_cell, item["target_ref"])] == item["drug"]
            source = np.array([float(observed[(project, source_cell, item["source_ref"], dose)][1]) for dose in doses])
            target_exact = [observed[(project, target_cell, item["target_ref"], dose)][1] for dose in doses]
            curves.append((item, x, source, target_exact))
            all_x.extend(x)
        bounds = (min(all_x), max(all_x))
        for holdout, (item, x, source, target_exact) in enumerate(curves):
            training = [entry for index, entry in enumerate(curves) if index != holdout]
            train_x = np.concatenate([entry[1] for entry in training])
            train_source = np.concatenate([entry[2] for entry in training])
            train_target = np.array([float(value) for entry in training for value in entry[3]])
            query = (len(x) - 1) // 2
            query_y = float(target_exact[query])
            truth = [value >= Decimal("0.5") for value in target_exact]
            predictions = predict_after_query(hats(train_x, bounds), train_source, train_target,
                                              hats(x, bounds), source, query, query_y)
            choices = {kind: recommend(prediction, query, truth[query]) for kind, prediction in predictions.items()}
            choices["D"] = query if truth[query] else -1
            # The common history uses 2 distinct-cell keys per training point plus held-out source keys.
            initial_cost = 2 * len(train_x) + len(x)
            row = {"project": project, "source_cell": source_cell, "target_cell": target_cell,
                   "drug": item["drug"], "source_ref": item["source_ref"], "target_ref": item["target_ref"],
                   "menu_size": len(x), "query_index": query, "query_active": int(truth[query]),
                   "truth_first_active": next((i for i, value in enumerate(truth) if value), -1),
                   "train_drugs": len(training), "initial_paid_keys": initial_cost, "additional_paid_keys": 1,
                   "common_total_keys": initial_cost + 1, "C_minimum_required_keys": len(x) + 1,
                   "D_minimum_required_keys": 1, "T_minimum_required_keys": len(train_x) + 1}
            for kind in MODELS:
                loss, category = decision_loss(choices[kind], truth, x)
                row.update({f"choice_{kind}": choices[kind], f"loss_{kind}": loss, f"category_{kind}": category})
                if kind != "D":
                    row[f"prediction_{kind}"] = json.dumps(predictions[kind].tolist(), separators=(",", ":"))
            output.append(row)
            grouped[item["drug"]].append({kind: row[f"loss_{kind}"] for kind in MODELS})
            if len(arithmetic_packet) < 16:
                arithmetic_packet.append({"id": f"fixed-task-{len(arithmetic_packet)+1:02d}",
                                          "project": project, "source_cell": source_cell, "target_cell": target_cell,
                                          "drug": item["drug"], "actual_active_flags": truth,
                                          "normalized_log_doses": ((x - x[0]) / (x[-1] - x[0])).tolist(),
                                          "choice_A": choices["A"], "choice_L": choices["L"]})
    assert len(output) == 3582 and len(grouped) == 11
    per_drug = {drug: {kind: float(np.mean([row[kind] for row in rows])) for kind in MODELS}
                for drug, rows in sorted(grouped.items())}
    means = {kind: float(np.mean([row[kind] for row in per_drug.values()])) for kind in MODELS}
    delta = np.array([row["A"] - row["L"] for row in per_drug.values()])
    rng = np.random.Generator(np.random.PCG64(20261029))
    resampled = delta[rng.integers(0, len(delta), size=(2000, len(delta)))].mean(axis=1)
    interval = np.percentile(resampled, [2.5, 97.5], method="linear").tolist()
    gates = {"mean_gain_at_least_005": float(np.mean(delta)) >= 0.05,
             "drug_resampling_lower_positive": interval[0] > 0,
             "L_better_than_each_simple_control": all(means["L"] < means[kind] - 1e-12 for kind in ("T", "C", "D"))}
    with (HERE / "primary_results.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    summary = {"hypothesis": "H_L", "scope": "Development prerequisite only, fixed same-screen exported labels; no new-algorithm or active-query claim",
               "tasks": len(output), "drug_clusters": len(per_drug), "per_drug_mean_loss": per_drug,
               "drug_equal_mean_loss": means, "A_minus_L_mean": float(np.mean(delta)),
               "drug_resampling_sensitivity_interval": interval, "gate": gates, "H_L_supported": all(gates.values()),
               "protocol_file": approval["protocol_file"], "protocol_sha256": approval["protocol_sha256"],
               "script_sha256": digest(Path(__file__)), "support_sha256": SUPPORT_SHA, "data_sha256": ZIP_SHA,
               "python": platform.python_version(), "numpy": np.__version__,
               "cpu_seconds": time.process_time() - cpu_start, "wall_seconds": time.perf_counter() - start,
               "confirmatory_biological_or_clinical_evidence": False, "new_algorithm_evidence": False}
    (HERE / "primary_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (HERE / "arithmetic_packet.json").write_text(json.dumps({"selection": "First16 frozen task-order entries, not response-selected; arithmetic only", "items": arithmetic_packet}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "per_drug_mean_loss"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
