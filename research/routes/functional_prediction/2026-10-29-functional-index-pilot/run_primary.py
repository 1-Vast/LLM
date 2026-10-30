"""One frozen H_FI archival-development run. No core promotion implied."""
from decimal import Decimal
from itertools import combinations
from pathlib import Path
import csv
import hashlib
import io
import json
import sys
import time
import zipfile
import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE.parents[1] / "tmp/extq1/gsdc_well_stats.zip"
MEMBER = "combo_well_stats_GDSC_007_05May22.csv"
KINDS = ["constant", "knn5", "knn20", "knn50", "pav_up", "pav_down"]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def dump(name, obj):
    with (HERE / f"primary_{name}.json").open("x", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False,
                  default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x.item())
        f.write("\n")


def fit(kind, x, y):
    if kind == "constant":
        return {"kind": kind, "p": float(y.mean())}
    if kind.startswith("knn"):
        return {"kind": kind, "x": x.copy(), "y": y.copy()}
    sign = -1 if kind == "pav_down" else 1
    xs = x * sign
    ux, inverse, counts = np.unique(xs, return_inverse=True, return_counts=True)
    positives = np.bincount(inverse, weights=y, minlength=len(ux))
    blocks = []
    for value, count, positive in zip(ux, counts, positives):
        blocks.append([int(count), float(positive), float(value * count)])
        while len(blocks) > 1 and blocks[-2][1] / blocks[-2][0] > blocks[-1][1] / blocks[-1][0]:
            right = blocks.pop()
            left = blocks.pop()
            blocks.append([left[i] + right[i] for i in range(3)])
    return {"kind": kind, "sign": sign,
            "centers": np.array([b[2] / b[0] for b in blocks]),
            "probabilities": np.array([b[1] / b[0] for b in blocks])}


def predict(model, values):
    kind = model["kind"]
    if kind == "constant":
        return np.full(len(values), model["p"])
    if kind.startswith("knn"):
        order = np.argsort(abs(values[:, None] - model["x"][None, :]), axis=1, kind="stable")
        return model["y"][order[:, :min(int(kind[3:]), len(model["x"]))]].mean(axis=1)
    return np.interp(values * model["sign"], model["centers"], model["probabilities"])


def selfcheck():
    x = np.array([0., 1., 2.])
    y = np.array([0., 1., 0.])
    m = fit("pav_up", x, y)
    assert np.array_equal(m["centers"], [0., 1.5])
    assert np.array_equal(m["probabilities"], [0., .5])
    assert np.array_equal(predict(m, np.array([0., 1.5, 4.])), [0., .5, .5])
    m = fit("pav_up", np.array([0., 0., 1.]), np.array([0., 1., 1.]))
    assert np.array_equal(predict(m, np.array([0., 1.])), [.5, 1.])
    assert predict(fit("knn5", np.array([0., 0.]), np.array([0., 1.])), np.array([0.]))[0] == .5
    print("Three fixed numerical checks passed; no data opened")


def main():
    started, cpu = time.monotonic(), time.process_time()
    roles_path = HERE / "menu_roles_frozen.json"
    spec = json.loads(roles_path.read_text(encoding="utf-8"))
    assert spec["protocol_sha256"] == sha(HERE / "protocol_hfi_v1.md")
    assert spec["clarifications_sha256"] == sha(HERE / "protocol_clarifications.md")
    freeze = json.loads((HERE / "execution_freeze.json").read_text(encoding="utf-8"))
    assert freeze["primary_script_sha256"] == sha(Path(__file__))
    assert freeze["menu_roles_sha256"] == sha(roles_path)
    assert not (HERE / "primary_summary.json").exists(), "No automatic replay"
    assert sha(RAW) == "e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259"
    records, drugs = spec["cells"], spec["drugs"]
    n, d = len(records), len(drugs)
    wanted = {(r["cell"], r["refs"][drug], Decimal(spec["doses_uM"][drug])): (i, j)
              for i, r in enumerate(records) for j, drug in enumerate(drugs)}
    assert len(wanted) == n * d
    observed, dose_cache = {}, {}
    rows = appearances = 0
    with zipfile.ZipFile(RAW) as z, z.open(MEMBER) as f:
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", newline="")):
            rows += 1
            if row["PROJECT_ID"].strip() != "2":
                continue
            cell = row["MASTER_CELL_ID"].strip()
            for side in (1, 2):
                text = row[f"lib{side}_conc"].strip()
                if text not in dose_cache:
                    dose_cache[text] = Decimal(text)
                key = (cell, row[f"lib{side}_drug"].strip(), dose_cache[text])
                if key not in wanted:
                    continue
                appearances += 1
                i, j = wanted[key]
                assert row[f"lib{side}_drug_id"].strip() == drugs[j]
                response = row[f"lib{side}_y"].strip()
                if key in observed:
                    assert observed[key] == response, "Conflicting response strings"
                else:
                    value = Decimal(response)
                    assert value.is_finite(), "Nonfinite response"
                    observed[key] = response
            if rows % 10000 == 0:
                assert time.process_time() - cpu < 120 and time.monotonic() - started < 180
    assert set(observed) == set(wanted), "Missing selected response"
    x = np.empty((n, d))
    labels = np.empty((n, d), dtype=np.int8)
    for key, response in observed.items():
        i, j = wanted[key]
        value = Decimal(response)
        x[i, j], labels[i, j] = float(value), int(value >= Decimal(".5"))
    qc = {"rows": rows, "selected_appearances": appearances, "unique_coordinates": len(observed),
          "repeated_appearances": appearances - len(observed), "response_conflicts": 0,
          "finite_outside_zero_one": int(((x < 0) | (x > 1)).sum()),
          "data_limit": "Processed export QC; no source-well/culture independence or hard process isolation"}
    dump("qc", qc)
    train = np.array([r["role"] == "train" for r in records])
    tx, ty = x[train], labels[train]
    folds = np.array([r["inner_fold"] for r in records])[train]
    assert train.any() and (~train).any()
    oof = np.zeros((d, d, len(tx)))
    choices = np.zeros((d, d), dtype=np.int8)
    blind = np.zeros((len(tx), d))
    for fold in range(5):
        a, v = folds != fold, folds == fold
        assert a.any() and v.any(), "Empty inner fold"
        blind[v] = ty[a].mean(axis=0)
    for j in range(d):
        for t in range(d):
            if j == t:
                continue
            probabilities = np.zeros((len(KINDS), len(tx)))
            for fold in range(5):
                a, v = folds != fold, folds == fold
                for k, kind in enumerate(KINDS):
                    probabilities[k, v] = predict(fit(kind, tx[a, j], ty[a, t]), tx[v, j])
            errors = ((probabilities >= .5) != ty[:, t]).sum(axis=1)
            k = int(np.argmin(errors))
            choices[j, t], oof[j, t] = k, probabilities[k]
    candidates = []
    for a, b in combinations(range(d), 2):
        state_counts = np.bincount(ty[:, a] * 2 + ty[:, b], minlength=4)
        if min(state_counts) < 10:
            continue
        da = int(((oof[a, b] >= .5) != ty[:, b]).sum())
        db = int(((oof[b, a] >= .5) != ty[:, a]).sum())
        bl = int(((blind[:, [a, b]] >= .5) != ty[:, [a, b]]).sum())
        for q in range(d):
            if q in (a, b):
                continue
            rr = int(((oof[q, [a, b]].T >= .5) != ty[:, [a, b]]).sum())
            candidates.append({"a": a, "b": b, "q": q, "minimum_error_count_gain": min(da-rr, db-rr, bl-rr),
                               "errors": {"reference": rr, "direct_a": da, "direct_b": db, "blind": bl},
                               "joint_state_counts": state_counts.tolist()})
    candidates.sort(key=lambda r: (-r["minimum_error_count_gain"], drugs[r["a"]], drugs[r["b"]], drugs[r["q"]]))
    selection = {"kinds": KINDS, "choice_matrix": choices, "drugs": drugs, "candidates": candidates,
                 "training_cells": int(train.sum()), "development_cells": int((~train).sum()),
                 "training_coordinates_used_for_selection": int(train.sum()) * d,
                 "development_values_used_in_selection": False}
    dump("training_selection", selection)
    if not candidates or candidates[0]["minimum_error_count_gain"] <= 0:
        dump("summary", {"status": "training_precondition_absent", "H_FI": "not_evaluated_on_development",
                         "best_training_candidate": candidates[:1], "qc": qc,
                         "wall_seconds": time.monotonic()-started, "cpu_seconds": time.process_time()-cpu})
        return
    best = candidates[0]
    a, b, q = best["a"], best["b"], best["q"]
    models = {(j, t): fit(KINDS[int(choices[j, t])], tx[:, j], ty[:, t])
              for j, t in [(q, a), (q, b), (a, b), (b, a)]}
    dump("models_frozen", {f"{drugs[j]}->{drugs[t]}": m for (j, t), m in models.items()})
    dx, truth = x[~train], labels[~train][:, [a, b]]
    if len(dx) < 50 or any(min(np.bincount(truth[:, t], minlength=2)) < 5 for t in (0, 1)):
        dump("summary", {"status": "development_design_insufficient", "H_FI": "undecided", "best": best})
        return
    predictions = {"reference": np.column_stack([predict(models[q, t], dx[:, q]) >= .5 for t in (a, b)]),
                   "direct_a": np.column_stack([truth[:, 0], predict(models[a, b], dx[:, a]) >= .5]),
                   "direct_b": np.column_stack([predict(models[b, a], dx[:, b]) >= .5, truth[:, 1]]),
                   "blind": np.tile(ty[:, [a, b]].mean(axis=0) >= .5, (len(dx), 1))}
    losses = {k: (v != truth).mean(axis=1) for k, v in predictions.items()}
    rng = np.random.Generator(np.random.PCG64(20261029))
    indexes = rng.integers(0, len(dx), size=(1999, len(dx)))
    comparisons = {}
    for k in ("direct_a", "direct_b", "blind"):
        diff = losses[k] - losses["reference"]
        comparisons[k] = {"mean_loss_reduction": float(diff.mean()),
                          "composition_q025": float(np.quantile(diff[indexes].mean(axis=1), .025, method="linear"))}
    supported = all(v["mean_loss_reduction"] >= .025 and v["composition_q025"] > 0 for v in comparisons.values())
    dump("development", {"cells": [r["cell"] for r in records if r["role"] != "train"],
                         "actions": {"reference": drugs[q], "direct_a": drugs[a], "direct_b": drugs[b], "blind": drugs[q]},
                         "truth": truth, "predictions": predictions, "losses": losses,
                         "policy_coordinates_per_cell": 1, "direct_both_coordinates": 2, "direct_both_export_loss": 0})
    dump("summary", {"status": "H_FI_development_supported" if supported else "H_FI_not_supported",
                     "H_FI": bool(supported), "best_training_candidate": best,
                     "selected_drugs": {"a": drugs[a], "b": drugs[b], "q": drugs[q]},
                     "mean_losses": {k: float(v.mean()) for k, v in losses.items()}, "comparisons": comparisons,
                     "training_coordinates_used_for_selection": int(train.sum()) * d,
                     "fixed_task_minimum_history": {"reference": int(train.sum()) * 3, "direct": int(train.sum()) * 2},
                     "wall_seconds": time.monotonic()-started, "cpu_seconds": time.process_time()-cpu,
                     "scientific_limit": "Fixed-family archival conditional information, not new algorithm, shared-feedback or independent drug benefit"})


if __name__ == "__main__":
    if sys.argv[1:] == ["--selfcheck"]:
        selfcheck()
    else:
        main()
