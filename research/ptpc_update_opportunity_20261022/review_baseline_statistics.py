"""Scalar audit of saved HCT116 OOF predictions; no fitting or abundance read."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def metrics(rows, name):
    y = np.array([r["label"] for r in rows], dtype=float)
    score = np.array([r["prediction"][name] for r in rows])
    # AP from distinct descending thresholds, independently of sklearn.
    positives, cumulative, ap = float(y.sum()), 0.0, 0.0
    seen = 0
    for threshold in sorted(set(score), reverse=True):
        block = y[score == threshold]
        cumulative += float(block.sum())
        seen += len(block)
        ap += float(block.sum()) / positives * cumulative / seen
    pos, neg = score[y == 1], score[y == 0]
    auc = float(((pos[:, None] > neg).sum() + 0.5 * (pos[:, None] == neg).sum()) / (len(pos) * len(neg)))
    order = sorted(range(len(rows)), key=lambda i: (-score[i], rows[i]["pert_id"]))
    return {"n": len(rows), "positive": int(positives), "prevalence": float(y.mean()),
            "average_precision": ap, "auroc": auc, "brier": float(np.mean((score - y) ** 2)),
            "precision_at_5": float(y[order[:5]].mean())}


def main():
    directory = Path("log/20261022/ptpc_update_opportunity")
    result_path = directory / "BASELINE_RESULT.json"
    prep_path = directory / "BASELINE_PREPARATION.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    prep = json.loads(prep_path.read_text(encoding="utf-8"))
    rows = result["predictions"]
    task_by_id = {t["pert_id"]: t for t in prep["tasks"]}
    assert len(task_by_id) == len(rows) == len(prep["tasks"]) == 601
    groups = defaultdict(set)
    for row in rows:
        task = task_by_id[row["pert_id"]]
        assert row["label"] == task["label"]
        assert row["chemical_group"] == task["chemical_group"]
        fold = int(hashlib.sha256(("PTPC_HCT116_DEV_V1|" + row["chemical_group"]).encode()).hexdigest(), 16) % 5
        assert row["fold"] == fold
        groups[row["chemical_group"]].add(fold)
    assert all(len(folds) == 1 for folds in groups.values())
    names = list(result["pooled"])
    pooled = {name: metrics(rows, name) for name in names}
    differences = []
    for name in names:
        differences.extend(abs(pooled[name][key] - value) for key, value in result["pooled"][name].items())
    folds = []
    for fold in range(5):
        subset = [r for r in rows if r["fold"] == fold]
        calculated = {name: metrics(subset, name) for name in names}
        folds.append({"fold": fold, "metrics": calculated})
        for saved in [r for r in result["model_folds"] if r["fold"] == fold]:
            name = saved["model"]
            differences.extend(abs(calculated[name][key] - saved[key]) for key in calculated[name])
            others = [r for r in rows if r["fold"] != fold]
            assert saved["source_n"] == len(others)
            assert saved["source_positive"] == sum(r["label"] for r in others)
            if name == "prior":
                assert all(r["prediction"][name] == saved["source_positive"] / saved["source_n"] for r in subset)
            else:
                candidates = saved["tuning"]
                for candidate in candidates:
                    assert abs(np.mean(candidate["source_fold_AP"]) - candidate["mean_AP"]) < 1e-12
                assert saved["C"] == max(candidates, key=lambda c: c["mean_AP"])["C"]
    assert max(differences) < 1e-12
    macro = {name: float(np.mean([fold["metrics"][name]["average_precision"] for fold in folds])) for name in names}
    pairs = [("proteins", "chemistry"), ("protein_masked", "chemistry_raw"), ("joint", "chemistry"),
             ("joint_masked", "chemistry_raw"), ("missingness", "proteins")]
    comparisons = {f"{a}_minus_{b}": [fold["metrics"][a]["average_precision"] - fold["metrics"][b]["average_precision"] for fold in folds] for a, b in pairs}
    summary = {"scope": "HCT116 saved-prediction scalar audit only, no abundance read and no refit",
               "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [result_path, prep_path]},
               "max_scalar_error": max(differences), "number_checked_scalars": len(differences),
               "n": len(rows), "chemical_groups": len(groups),
               "group_size_counts": dict(Counter(Counter(r["chemical_group"] for r in rows).values())),
               "pooled": pooled, "macro_fold_AP": macro, "folds": folds, "fold_AP_differences": comparisons,
               "missing_fraction": prep["missing_abundance_cells"] / (prep["missing_abundance_cells"] + prep["observed_abundance_cells"]),
               "evaluation_warning_count": len(result["warnings"])}
    path = directory / "review/BASELINE_SCALAR_AUDIT.json"
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ["max_scalar_error", "number_checked_scalars", "n", "chemical_groups", "group_size_counts", "macro_fold_AP", "fold_AP_differences", "missing_fraction"]}, indent=2))
    for fold in folds:
        print(json.dumps({"fold": fold["fold"], "n": fold["metrics"]["prior"]["n"], "positive": fold["metrics"]["prior"]["positive"], "AP": {name: fold["metrics"][name]["average_precision"] for name in names}}))


if __name__ == "__main__":
    main()
