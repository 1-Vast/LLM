"""Independent audit of saved late-information outputs; no abundance or fits."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "log/20261022/ptpc_late_information"
PANELS = ("C", "Craw", "E", "M", "V")
FAMILIES = ("logistic", "rbf")
GRID = (.1, 1., 10.)


def assigned(group, salt, count):
    return int(hashlib.sha256((salt + "|" + group).encode()).hexdigest(), 16) % count


def metrics(rows, family, panel):
    y = np.array([r["label"] for r in rows], dtype=float)
    score = np.array([r["scores"][family][panel] for r in rows])
    varied = len(set(y)) == 2
    ap, auc = None, None
    if varied:
        total, hits, ap = float(y.sum()), 0.0, 0.0
        seen = 0
        for threshold in sorted(set(score), reverse=True):
            block = y[score == threshold]
            hits += float(block.sum())
            seen += len(block)
            ap += float(block.sum()) / total * hits / seen
        positive, negative = score[y == 1], score[y == 0]
        auc = float(((positive[:, None] > negative).sum() + .5 * (positive[:, None] == negative).sum()) / (len(positive) * len(negative)))
    order = sorted(range(len(rows)), key=lambda i: (-score[i], rows[i]["pert_id"]))
    return {"n": len(rows), "positive": int(y.sum()), "AP": ap, "AUROC": auc,
            "P_at_5": float(y[order[:min(5, len(rows))]].mean())}


def main():
    result_path, prep_path = DIRECTORY / "RESULT.json", DIRECTORY / "PREPARATION.json"
    assert result_path.exists(), "Wait for root's terminal-result notification; do not run evaluation"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    preparation = json.loads(prep_path.read_text(encoding="utf-8"))
    rows = result["predictions"]
    tasks = preparation["tasks"]
    task_by_id = {task["pert_id"]: task for task in tasks}
    assert len(task_by_id) == len(tasks) == len(rows) == 600
    assert len({row["pert_id"] for row in rows}) == len(rows)
    groups = defaultdict(set)
    for row in rows:
        task = task_by_id[row["pert_id"]]
        assert row["label"] == task["label"]
        assert row["chemical_group"] == task["chemical_group"]
        assert row["fold"] == assigned(row["chemical_group"], "PTPC_HCT116_DEV_V1", 5)
        assert set(row["scores"]) == set(FAMILIES)
        for family in FAMILIES:
            assert set(row["scores"][family]) == set(PANELS)
            assert all(np.isfinite(value) for value in row["scores"][family].values())
        groups[row["chemical_group"]].add(row["fold"])
    assert all(len(folds) == 1 for folds in groups.values())

    errors = []
    def compare(calculated, saved):
        for key, value in calculated.items():
            if value is None:
                assert saved[key] is None
            else:
                errors.append(abs(value - saved[key]))

    pooled = {family: {panel: metrics(rows, family, panel) for panel in PANELS} for family in FAMILIES}
    calculated_folds = {}
    fold_rows = result["fold_results"]
    assert len(fold_rows) == 5 * len(PANELS) * len(FAMILIES)
    assert len({(r["family"], r["panel"], r["outer"]) for r in fold_rows}) == len(fold_rows)
    for family in FAMILIES:
        for panel in PANELS:
            compare(pooled[family][panel], result["pooled"][family][panel])
            for fold in range(5):
                subset = [r for r in rows if r["fold"] == fold]
                calculated_folds[family, panel, fold] = metrics(subset, family, panel)
    for row in fold_rows:
        compare(calculated_folds[row["family"], row["panel"], row["outer"]], row)

    ledger = result["fit_ledger"]
    classifier_keys = [(r["outer"], r["inner"], r["family"], r["panel"], r["C"])
                       for r in ledger if r.get("mode") == "classifier"]
    assert len(classifier_keys) == len(set(classifier_keys))
    counts = Counter()
    entries = defaultdict(list)
    for record in ledger:
        fold, inner = record["outer"], record["inner"]
        source = [r for r in rows if r["fold"] != fold]
        if inner is None:
            validation = [r for r in rows if r["fold"] == fold]
        else:
            validation = [r for r in source if assigned(r["chemical_group"], "INNER", 3) == inner]
            source = [r for r in source if assigned(r["chemical_group"], "INNER", 3) != inner]
        if record.get("status") == "unscorable_validation_skipped":
            assert not source or not validation or len({r["label"] for r in validation}) < 2
            counts["skipped"] += 1
            continue
        assert record["family"] in FAMILIES and record["panel"] in PANELS and record["C"] in GRID
        assert record["n_train"] == len(source) and record["n_test"] == len(validation)
        expected_mode = "classifier" if len({r["label"] for r in source}) == 2 else "source_prevalence_fallback"
        assert record["mode"] == expected_mode
        counts[expected_mode] += 1
        entries[record["family"], record["panel"]].append(record)
    assert result["classifier_fit_count"] == counts["classifier"]
    assert result["fallback_count"] == counts["source_prevalence_fallback"]
    assert result["unscorable_inner_splits"] == counts["skipped"]
    assert len({len(value) for value in entries.values()}) == 1
    assert set(entries) == {(family, panel) for family in FAMILIES for panel in PANELS}

    for saved in fold_rows:
        family, panel, fold = saved["family"], saved["panel"], saved["outer"]
        assert [candidate["C"] for candidate in saved["tuning"]] == list(GRID)
        for candidate in saved["tuning"]:
            inner_records = sorted((r for r in entries[family, panel] if r["outer"] == fold and r["inner"] is not None and r["C"] == candidate["C"]), key=lambda r: r["inner"])
            assert candidate["inner_AP"] == [r["AP"] for r in inner_records]
            expected = float(np.mean(candidate["inner_AP"])) if candidate["inner_AP"] else None
            if expected is None:
                assert candidate["mean_AP"] is None
            else:
                errors.append(abs(candidate["mean_AP"] - expected))
        valid = [r for r in saved["tuning"] if r["mean_AP"] is not None]
        chosen = max(valid, key=lambda r: r["mean_AP"])["C"] if valid else GRID[0]
        assert chosen == saved["C"]

    gates, macros = {}, {}
    for family in FAMILIES:
        macros[family] = {}
        for panel in PANELS:
            values = [calculated_folds[family, panel, fold]["AP"] for fold in range(5)]
            macros[family][panel] = float(np.mean([v for v in values if v is not None]))
            errors.append(abs(macros[family][panel] - result["macro_AP"][family][panel]))
        differences = {panel: pooled[family]["V"]["AP"] - pooled[family][panel]["AP"] for panel in PANELS if panel != "V"}
        directions = {panel: sum(calculated_folds[family, "V", fold]["AP"] is not None and calculated_folds[family, panel, fold]["AP"] is not None and calculated_folds[family, "V", fold]["AP"] > calculated_folds[family, panel, fold]["AP"] for fold in range(5)) for panel in differences}
        gate = all(calculated_folds[family, panel, fold]["AP"] is not None for panel in PANELS for fold in range(5)) and min(differences.values()) >= .02 and min(directions.values()) >= 4
        gates[family] = {"AP_differences": differences, "positive_folds": directions, "pass": gate}
        saved = result["gates"][family]
        assert saved["positive_folds"] == directions and saved["pass"] == gate
        errors.extend(abs(differences[p] - saved["AP_differences"][p]) for p in differences)
    assert max(errors) <= 1e-12, max(errors)

    bootstrap_checks = {}
    for family in FAMILIES:
        bootstrap_checks[family] = {}
        for panel in ("E", "M"):
            saved = result["bootstrap"][family][panel]
            low, high = saved["percentile_95"]
            assert 0 < saved["valid_draws"] <= 2000 and -1 <= low <= high <= 1
            bootstrap_checks[family][panel] = {"definition": "fixed OOF paired chemical-group resampling, V minus comparator; no new draw performed", **saved}
    summary = {"scope": "600 exposed HCT116 labels/scores and preparation metadata only; no NPZ values, evaluator import, fits or bootstrap redraw",
               "input_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (result_path, prep_path)},
               "n": len(rows), "positive": sum(r["label"] for r in rows), "chemical_groups": len(groups),
               "scalar_comparisons": len(errors), "max_scalar_error": max(errors),
               "pooled": pooled, "macro_AP": macros,
               "folds": [{"family": f, "panel": p, "outer": k, **value} for (f, p, k), value in calculated_folds.items()],
               "gates": gates, "primary_gate_pass": gates["logistic"]["pass"], "rbf_cannot_rescue_primary": True,
               "ledger_count": len(ledger), "counts": dict(counts),
               "budget_per_family_panel": {f"{f}/{p}": len(v) for (f, p), v in entries.items()},
               "planned_classifier_fits": 500, "bootstrap_checks": bootstrap_checks,
               "warning_count": len(result["warnings"])}
    output = DIRECTORY / "source/SCALAR_AUDIT.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        assert json.loads(output.read_text(encoding="utf-8")) == summary, "Preserve previous audit; inputs or calculations changed"
    else:
        output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("n", "positive", "chemical_groups", "scalar_comparisons", "max_scalar_error", "ledger_count", "counts", "budget_per_family_panel", "primary_gate_pass", "gates", "pooled", "macro_AP", "warning_count")}, indent=2))


if __name__ == "__main__":
    main()
