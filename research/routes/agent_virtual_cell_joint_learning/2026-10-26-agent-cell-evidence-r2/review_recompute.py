"""Independent reviewer checks of frozen E002B accounting and key readouts.

Reuses the specified source-model implementation, but independently reconstructs
GP conditioning, terminal utility, policy aggregation, and intervals. No tuning.
"""
from pathlib import Path
import importlib.util
import itertools
import json
import hashlib

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("frozen_baseline", HERE / "baseline_replay.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def main():
    summary = json.loads((HERE / "BASELINE_RESULTS.json").read_text(encoding="utf-8"))
    metrics = pd.read_csv(HERE / "baseline_action_metrics.csv")
    policy = pd.read_csv(HERE / "baseline_policy_metrics.csv")
    raw = pd.read_csv(b.RAW, usecols=b.COLS, low_memory=False)
    raw["key"] = b.keys(raw)
    rounds = pd.to_numeric(raw.Iteration, errors="coerce")
    source = b.observations(raw[rounds.between(1, 10)])
    model = b.SourceModel(source)
    assert set(source["Cell line"]).isdisjoint(b.TARGETS)
    singles = {}
    for cell, key, y in source.itertuples(index=False, name=None):
        non_dmso = [d for d in key if d[0] != "dmso"]
        if len(non_dmso) == 1:
            singles.setdefault(non_dmso[0], {})[cell] = y
    for drug, values in singles.items():
        expected = [values.get(c, np.mean(list(values.values()))) for c in model.cells]
        np.testing.assert_allclose(model.profile[drug], expected, rtol=0, atol=0)
    old = b.usable(raw[rounds.between(1, 15)])
    old_keys = set(zip(old["Cell line"], old.key))
    terminal_design = b.usable(raw[raw.Iteration.eq("validation (random, round 15)")])
    terminal_design = terminal_design[terminal_design["Drug 1"].ne("dmso") & terminal_design["Drug 2"].ne("dmso")]
    terminal_design = terminal_design[[(c, k) not in old_keys for c, k in zip(terminal_design["Cell line"], terminal_design.key)]]
    terminal = b.observations(terminal_design)
    checks = []
    for budget in summary["budget"]:
        cell, action = budget["cell"], budget["action"]
        paid = raw[raw.file.isin(budget["files"])]
        assert len(paid) == budget["paid_well_records"]
        assert paid.file.nunique() == budget["physical_plates"] == 2
        assert set(paid["Cell line"]) == {cell}
        assert int(paid["Failed QC"].sum()) == budget["QC_failed_paid_records"]
        layout_columns = ["Well", "Drug 1", "Drug 2", "Conc 1 (uM)", "Conc 2 (uM)"]
        layouts = [sorted(tuple(map(str, r)) for r in g[layout_columns].itertuples(index=False, name=None)) for _, g in paid.groupby("file")]
        assert layouts[0] == layouts[1]
        query = b.observations(paid)
        assert len(query) == budget["valid_feedback_conditions"]
        test = terminal[terminal["Cell line"].eq(cell)]
        assert set(test.key).isdisjoint(query.key)
        xq, xt = model.features(query.key.tolist()), model.features(test.key.tolist())
        mq, mt = model.predict(xq, cell), model.predict(xt, cell)
        kqq = 0.25 * np.exp(-cdist(xq, xq, metric="sqeuclidean") / (2 * (xq.shape[1] - 1)))
        ktq = 0.25 * np.exp(-cdist(xt, xq, metric="sqeuclidean") / (2 * (xq.shape[1] - 1)))
        gp = mt + ktq @ np.linalg.solve(kqq + 0.01 * np.eye(len(xq)), query.y.to_numpy() - mq)
        yt = test.y.to_numpy()
        oracle = -np.sort(yt)[:3].mean()
        for name, pred in [("static", mt), ("GP", gp)]:
            expected = metrics[(metrics.cell == cell) & (metrics.action == action) & (metrics.model == name)].iloc[0]
            utility = -yt[np.argpartition(pred, 2)[:3]].mean()
            np.testing.assert_allclose([utility, oracle - utility, ((pred - yt) ** 2).mean()], [expected.utility, expected.regret, expected.mse], atol=1e-10, rtol=1e-9)
        checks.append({"cell": cell, "action": action, "paid_wells": len(paid), "failed_wells": int(paid["Failed QC"].sum())})
    for selection in summary["selection"]:
        for strategy, action in selection["selected"].items():
            group = metrics[(metrics.cell == selection["cell"]) & (metrics.model == "GP")].sort_values("action")
            assert int(group.iloc[np.argmax(group[strategy].to_numpy())].action) == action
        for model_name in metrics.model.unique():
            group = metrics[(metrics.cell == selection["cell"]) & (metrics.model == model_name)]
            for strategy in ["random", "uncertainty", "exploit", "KG"]:
                chosen = group if strategy == "random" else group[group.action == selection["selected"][strategy]]
                row = policy[(policy.cell == selection["cell"]) & (policy.model == model_name) & (policy.policy == strategy)].iloc[0]
                np.testing.assert_allclose(chosen[["utility", "regret", "mse"]].mean().to_numpy(), row[["utility", "regret", "mse"]].to_numpy(dtype=float), atol=1e-12)
    comparisons = {
        "GP_random_minus_static": ("GP", "random", "static", "random"),
        "GP_random_minus_direct_mono": ("GP", "random", "direct_mono", "random"),
        "GP_random_minus_hierarchical": ("GP", "random", "hierarchical", "random"),
        "GP_KG_minus_random": ("GP", "KG", "GP", "random"),
        "GP_uncertainty_minus_random": ("GP", "uncertainty", "GP", "random"),
    }
    intervals = {}
    for name, (ma, pa, mb, pb) in comparisons.items():
        a = policy[(policy.model == ma) & (policy.policy == pa)].set_index("cell").utility
        c = policy[(policy.model == mb) & (policy.policy == pb)].set_index("cell").utility
        d = (a - c).reindex(b.TARGETS).to_numpy()
        rng = np.random.default_rng(b.SEED)
        mc = rng.choice(d, size=(2000, 5), replace=True).mean(axis=1)
        reported = summary["contrasts"][name]
        np.testing.assert_allclose(d.mean(), reported["mean"], atol=1e-12)
        np.testing.assert_allclose(np.quantile(mc, [.025, .975]), reported["CI95_exploratory"], atol=1e-12)
        exact = np.array([np.mean(v) for v in itertools.product(d, repeat=5)])
        intervals[name] = {"mean": float(d.mean()), "reported_MC2000_CI_verified": True, "exact_3125_cell_bootstrap_percentiles_diagnostic": np.quantile(exact, [.025, .975]).tolist()}
    out = {
        "source_model_reused_not_independently_reimplemented": True,
        "source_profile_entries_independently_checked": len(singles),
        "GP_and_static_action_readouts_independently_recomputed": len(checks) * 2,
        "all_120_policy_rows_verified": len(policy) == 120,
        "all_30_action_budgets_verified": len(checks) == 30,
        "terminal_QC_failed_wells_in_target_cells": int(terminal_design.loc[terminal_design["Cell line"].isin(b.TARGETS), "Failed QC"].sum()),
        "per_action_paid_wells_range": [min(v["paid_wells"] for v in checks), max(v["paid_wells"] for v in checks)],
        "scenario_sum_paid_wells_not_per_policy_cost": sum(v["paid_wells"] for v in checks),
        "scenario_sum_failed_wells": sum(v["failed_wells"] for v in checks),
        "contrasts": intervals,
        "reviewed_result_sha256": hashlib.sha256((HERE / "BASELINE_RESULTS.json").read_bytes()).hexdigest(),
        "reviewed_code_sha256": hashlib.sha256((HERE / "baseline_replay.py").read_bytes()).hexdigest(),
    }
    (HERE / "review_recompute_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
