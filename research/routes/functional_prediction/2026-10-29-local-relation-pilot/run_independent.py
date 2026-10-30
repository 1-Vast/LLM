"""Independent H_L rewrite: original fixed prefix only; no primary imports."""
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
import zipfile

import numpy as np


HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parents[1] / "tmp" / "extq1" / "gsdc_well_stats.zip"
MEMBER = "combo_well_stats_GDSC_007_05May22.csv"
EXPECTED_SHA = "e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259"
TAU = Decimal("0.5")
METHODS = ("A", "L", "T", "C", "D")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_prefix():
    digest = hashlib.sha256()
    with ARCHIVE.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    require(digest.hexdigest() == EXPECTED_SHA, "archive hash mismatch")
    labels = {}
    ref_drug = {}
    appearances = 0
    with zipfile.ZipFile(ARCHIVE) as archive:
        with archive.open(MEMBER) as binary:
            rows = csv.DictReader(io.TextIOWrapper(binary, encoding="utf-8-sig", newline=""))
            needed = {"PROJECT_ID", "MASTER_CELL_ID"}
            needed.update("lib%d_%s" % (side, field)
                          for side in (1, 2) for field in ("drug_id", "drug", "conc", "y"))
            require(needed.issubset(rows.fieldnames), "missing allowed columns")
            for number in range(20000):
                row = next(rows, None)
                require(row is not None, "prefix shorter than 20000 rows")
                project, cell = row["PROJECT_ID"], row["MASTER_CELL_ID"]
                require(bool(project) and bool(cell), "empty project/cell")
                for side in (1, 2):
                    stem = "lib%d_" % side
                    drug, ref = row[stem + "drug_id"], row[stem + "drug"]
                    raw_dose, raw_y = row[stem + "conc"], row[stem + "y"]
                    try:
                        dose, y = Decimal(raw_dose), Decimal(raw_y)
                    except InvalidOperation as error:
                        raise RuntimeError("invalid allowed numeric field") from error
                    require(bool(drug) and bool(ref), "empty drug/ref")
                    require(dose.is_finite() and dose > 0, "invalid physical concentration")
                    require(y.is_finite() and Decimal(0) <= y <= Decimal(1), "invalid exported response")
                    identity = (project, cell, ref)
                    if identity in ref_drug:
                        require(ref_drug[identity] == drug, "ref maps to conflicting drug")
                    ref_drug[identity] = drug
                    key = (project, cell, ref, dose)
                    value = (raw_y, y)
                    if key in labels:
                        require(labels[key] == value, "duplicate response conflict")
                    else:
                        labels[key] = value
                    appearances += 1
    require(appearances == 40000 and len(labels) == 5924, "prefix identity counts differ")
    return labels, ref_drug, appearances


def reconstruct_support(labels, ref_drug):
    candidates = defaultdict(set)
    for (project, cell, ref), drug in ref_drug.items():
        candidates[(project, cell, drug)].add(ref)
    selected = {key: min(refs) for key, refs in candidates.items()}
    curves = defaultdict(set)
    for project, cell, ref, dose in labels:
        drug = ref_drug[(project, cell, ref)]
        if selected[(project, cell, drug)] == ref:
            curves[(project, cell, drug)].add(dose)
    cells = defaultdict(set)
    drugs = defaultdict(set)
    for project, cell, drug in curves:
        cells[project].add(cell)
        drugs[(project, cell)].add(drug)
    pairs = []
    for project in sorted(cells):
        for source in sorted(cells[project]):
            for target in sorted(cells[project]):
                if source == target:
                    continue
                menus = {}
                for drug in sorted(drugs[(project, source)] & drugs[(project, target)]):
                    common = sorted(curves[(project, source, drug)] & curves[(project, target, drug)])
                    if len(common) >= 3:
                        menus[drug] = common
                if len(menus) >= 6:
                    pairs.append((project, source, target, menus))
    require(len(pairs) == 342, "directed-pair support differs")
    require(sum(len(item[3]) for item in pairs) == 3582, "LODO task support differs")
    require(Counter(len(item[3]) for item in pairs) == {11: 306, 6: 36}, "pair drug counts differ")
    require(Counter(len(menu) for item in pairs for menu in item[3].values()) == {7: 3240, 5: 342},
            "task dose counts differ")
    require(len({drug for item in pairs for drug in item[3]}) == 11, "drug count differs")
    return selected, pairs


def physical_hats(menus):
    doses = sorted({dose for menu in menus.values() for dose in menu})
    logd = {dose: math.log10(float(dose)) for dose in doses}
    low, high = min(logd.values()), max(logd.values())
    require(high > low, "zero log-dose span")
    result = {}
    for dose, x in logd.items():
        r = (x - low) / (high - low)
        result[dose] = np.array([max(1 - 2 * r, 0), 1 - abs(2 * r - 1), max(2 * r - 1, 0)])
    return result


def design(method, hats, source_y):
    if method == "T":
        return np.asarray(hats, dtype=float)
    z = np.asarray(source_y, dtype=float) - 0.5
    phi = np.asarray(hats, dtype=float)
    base = np.column_stack((phi, z))
    if method == "A":
        return base
    return np.column_stack((base, z * (phi[:, 0] - phi[:, 1]), z * (phi[:, 2] - phi[:, 1])))


def predict(history_hats, history_source, history_target, heldout_hats,
            heldout_source, query_index, query_y, query_active):
    """No unqueried held-out target labels or evaluator object enter this function."""
    source = np.asarray(heldout_source, dtype=float)
    n = len(source)
    phi_train = np.vstack((history_hats, heldout_hats[query_index]))
    source_train = np.append(history_source, source[query_index])
    target_train = np.append(history_target, query_y) - 0.5
    predictions, choices = {}, {}
    for method in ("A", "L", "T"):
        x = design(method, phi_train, source_train)
        x_test = design(method, heldout_hats, source)
        # Full closed-form refit on all other-drug rows plus the sole observed q.
        theta = np.linalg.solve(x.T @ x + 0.01 * np.eye(x.shape[1]), x.T @ target_train)
        predictions[method] = 0.5 + x_test @ theta
    predictions["C"] = source + (query_y - source[query_index])
    for method in ("A", "L", "T", "C"):
        predictions[method][query_index] = query_y
        require(np.isfinite(predictions[method]).all(), "nonfinite model prediction")
        active = predictions[method] >= 0.5
        active[query_index] = query_active  # original Decimal decision, not rounded float
        candidates = np.flatnonzero(active)
        choices[method] = int(candidates[0]) if candidates.size else -1
    choices["D"] = query_index if query_active else -1
    predictions["D"] = [None] * n
    predictions["D"][query_index] = query_y
    return predictions, choices


def evaluate(choice, doses, truth):
    successes = [i for i, active in enumerate(truth) if active]
    if choice == -1:
        return float(bool(successes)), "abstain"
    if not truth[choice]:
        return 1.0, "failure"
    first = successes[0]
    loss = math.log(float(doses[choice] / doses[first])) / math.log(float(doses[-1] / doses[0]))
    require(math.isfinite(loss) and -1e-12 <= loss <= 1 + 1e-12, "loss out of range")
    return loss, "success"


def main():
    labels, ref_drug, appearances = read_prefix()
    selected, pairs = reconstruct_support(labels, ref_drug)
    per_drug = defaultdict(lambda: defaultdict(list))
    categories = {method: Counter() for method in METHODS}
    output = HERE / "independent_results.csv"
    fields = ["project", "source", "target", "drug", "n", "q", "doses", "truth_active",
              "N_other", "available_history_cost", "additional_cost"]
    fields += [name + "_" + method for method in METHODS for name in ("choice", "loss", "category", "minimum_cost", "predictions")]
    task_count = 0
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for project, source, target, menus in pairs:
            hats = physical_hats(menus)

            def curve(cell, drug):
                ref = selected[(project, cell, drug)]
                return [labels[(project, cell, ref, dose)][1] for dose in menus[drug]]

            for drug, doses in menus.items():
                n, q = len(doses), (len(doses) - 1) // 2
                history_hats, history_source, history_target = [], [], []
                for other, other_doses in menus.items():
                    if other == drug:
                        continue
                    history_hats.extend(hats[dose] for dose in other_doses)
                    history_source.extend(float(y) for y in curve(source, other))
                    history_target.extend(float(y) for y in curve(target, other))
                source_y = [float(y) for y in curve(source, drug)]
                target_ref = selected[(project, target, drug)]
                query_decimal = labels[(project, target, target_ref, doses[q])][1]
                predictions, choices = predict(
                    np.asarray(history_hats), history_source, history_target,
                    np.asarray([hats[dose] for dose in doses]), source_y,
                    q, float(query_decimal), query_decimal >= TAU)
                # Evaluation labels are accessed only after the prediction call returns.
                truth = [y >= TAU for y in curve(target, drug)]
                other_count = len(history_target)
                row = dict(project=project, source=source, target=target, drug=drug, n=n, q=q,
                           doses=json.dumps([str(dose) for dose in doses]), truth_active=json.dumps(truth),
                           N_other=other_count, available_history_cost=2 * other_count + n, additional_cost=1)
                for method in METHODS:
                    loss, category = evaluate(choices[method], doses, truth)
                    cost = (2 * other_count + n + 1 if method in ("A", "L") else
                            other_count + 1 if method == "T" else n + 1 if method == "C" else 1)
                    row["choice_" + method] = choices[method]
                    row["loss_" + method] = loss
                    row["category_" + method] = category
                    row["minimum_cost_" + method] = cost
                    row["predictions_" + method] = json.dumps(list(predictions[method]))
                    per_drug[drug][method].append(loss)
                    categories[method][category] += 1
                writer.writerow(row)
                task_count += 1
    drug_means = {drug: {method: float(np.mean(values[method])) for method in METHODS}
                  for drug, values in sorted(per_drug.items())}
    overall = {method: float(np.mean([values[method] for values in drug_means.values()])) for method in METHODS}
    drug_delta = {drug: values["A"] - values["L"] for drug, values in drug_means.items()}
    deltas = np.array(list(drug_delta.values()))
    generator = np.random.Generator(np.random.PCG64(20261029))
    indices = generator.integers(0, len(deltas), size=(2000, len(deltas)))
    bootstrap = np.mean(deltas[indices], axis=1)
    interval = np.percentile(bootstrap, [2.5, 97.5], method="linear")
    delta = float(np.mean(deltas))
    criteria = {"delta_at_least_0.05": delta >= 0.05, "sensitivity_lower_positive": bool(interval[0] > 0)}
    criteria.update({"L_strictly_below_" + method: overall["L"] < overall[method] - 1e-12 for method in ("T", "C", "D")})
    summary = {
        "role": "independent original-prefix rewrite; numerical replication is not scientific confirmation",
        "archive_sha256": EXPECTED_SHA, "member": MEMBER, "prefix_rows": 20000,
        "appearances": appearances, "unique_export_keys": len(labels), "directed_pairs": len(pairs),
        "tasks": task_count, "drugs": len(drug_means), "drug_equal_weight_mean_loss": overall,
        "per_drug_mean_loss": drug_means, "per_drug_delta_A_minus_L": drug_delta,
        "delta_A_minus_L": delta, "drug_cluster_sensitivity_interval": [float(x) for x in interval],
        "bootstrap": {"generator": "PCG64", "seed": 20261029, "replicates": 2000, "percentile": "linear"},
        "categories": {method: dict(value) for method, value in categories.items()},
        "criteria": criteria, "H_L_supported_under_frozen_joint_criterion": all(criteria.values()),
        "comparison_tolerance_frozen_before_execution": {"prediction_absolute": 1e-8, "loss_absolute": 1e-8, "choice": "exact"},
    }
    (HERE / "independent_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"completed": True, "tasks": task_count, "outputs": [output.name, "independent_summary.json"]}))


if __name__ == "__main__":
    main()
