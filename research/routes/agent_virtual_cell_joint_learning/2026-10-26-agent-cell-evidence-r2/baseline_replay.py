"""E002B: paid paired-plate replay; source-only features; terminal scoring only.

Historical offline baselines, not a new Agent/VC algorithm or causal experiment.
"""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import sys
import time

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve, solve_triangular
from sklearn.ensemble import ExtraTreesRegressor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = ROOT / "research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv"
SEED = 20261026
TARGETS = ["A673", "BJ", "MSKEWS-66647", "SKNEP", "TC-71"]
CONTROLS = {"high control", "low control"}
COLS = ["Cell line", "Iteration", "file", "Well", "Drug 1", "Drug 2",
        "Conc 1 (uM)", "Conc 2 (uM)", "Failed QC", "Viability"]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def keys(frame):
    result = []
    for a, b, da, db in frame[["Drug 1", "Drug 2", "Conc 1 (uM)", "Conc 2 (uM)"]].itertuples(index=False, name=None):
        # 0 here is only a DMSO key sentinel, not an imputed measured concentration.
        aa = (str(a), 0.0 if a == "dmso" else float(da))
        bb = (str(b), 0.0 if b == "dmso" else float(db))
        result.append(tuple(sorted([aa, bb])))
    return result


def usable(frame):
    return frame[~frame["Drug 1"].isin(CONTROLS) & ~frame["Drug 2"].isin(CONTROLS)
                 & frame["Drug 1"].ne(frame["Drug 2"])].copy()


def observations(frame):
    valid = usable(frame[frame["Failed QC"].eq(False)])
    assert np.isfinite(valid.Viability).all(), "Nonfinite QC-pass response."
    return valid.groupby(["Cell line", "key"], sort=False).Viability.mean().reset_index(name="y")


def kernel(a, b):
    dist = np.maximum((a * a).sum(1)[:, None] + (b * b).sum(1)[None, :] - 2 * a @ b.T, 0)
    return .25 * np.exp(-dist / (2 * (a.shape[1] - 1)))


def top3(values):
    return np.argpartition(values, 2)[:3]


class SourceModel:
    def __init__(self, source):
        self.source = source
        self.cells = sorted(source["Cell line"].unique())
        self.cell_index = {c: i for i, c in enumerate(self.cells)}
        self.profile = {}
        values = defaultdict(dict)
        for cell, key, y in source.itertuples(index=False, name=None):
            a, b = key
            if a[0] == "dmso" or b[0] == "dmso":
                drug = b if a[0] == "dmso" else a
                values[drug][cell] = y
        self.global_mean = float(source.y.mean())
        for drug, v in values.items():
            avg = float(np.mean(list(v.values())))
            self.profile[drug] = np.array([v.get(c, avg) for c in self.cells])
        raw = self.features(source.key.tolist(), scale=False)
        self.center, self.scale = raw.mean(0), raw.std(0)
        self.scale[self.scale < 1e-8] = 1
        self.center[-1], self.scale[-1] = 0, 1
        self.x = self.features(source.key.tolist())
        self.xc = self.with_cells(self.x, source["Cell line"].tolist())
        self.forest = self.new_forest(64)
        self.forest.fit(self.xc, source.y.to_numpy())
        residual = source.y.to_numpy() - self.forest.predict(self.xc)
        coef = []
        for cell in self.cells:
            mask = source["Cell line"].eq(cell).to_numpy()
            x = self.x[mask]
            coef.append(np.linalg.solve(x.T @ x + np.eye(x.shape[1]), x.T @ residual[mask]))
        self.cov = np.cov(np.array(coef), rowvar=False) + .01 * np.eye(self.x.shape[1])
        self.precision = np.linalg.inv(self.cov)

    @staticmethod
    def new_forest(trees):
        return ExtraTreesRegressor(n_estimators=trees, min_samples_leaf=5,
                                   max_depth=24, random_state=SEED, n_jobs=2)

    def drug(self, drug):
        if drug[0] == "dmso":
            return np.ones(len(self.cells))
        return self.profile.get(drug, np.full(len(self.cells), self.global_mean))

    def features(self, key_list, scale=True):
        a = np.array([self.drug(k[0]) for k in key_list])
        b = np.array([self.drug(k[1]) for k in key_list])
        x = np.column_stack([(a + b) / 2, np.abs(a - b), a * b, np.ones(len(a))])
        return (x - self.center) / self.scale if scale else x

    def with_cells(self, x, cells):
        z = np.zeros((len(x), len(self.cells) + 1))
        for i, cell in enumerate(cells):
            z[i, self.cell_index.get(cell, len(self.cells))] = 1
        return np.column_stack([x, z])

    def predict(self, x, cell):
        return self.forest.predict(self.with_cells(x, [cell] * len(x)))

    def direct_mono(self, key_list, query, prior):
        measured, source_mean = {}, {}
        for _, key, y in query.itertuples(index=False, name=None):
            a, b = key
            if a[0] == "dmso" or b[0] == "dmso":
                drug = b if a[0] == "dmso" else a
                measured[drug] = y
                source_mean[drug] = float(self.drug(drug).mean())
        if len(measured) >= 2:
            xx = np.array([[source_mean[k], 1] for k in measured])
            ab = np.linalg.lstsq(xx, np.array(list(measured.values())), rcond=None)[0]
        else:
            ab = np.array([1., 0.])
        def estimate(drug):
            if drug[0] == "dmso":
                return 1.
            return measured.get(drug, float(self.drug(drug).mean()) * ab[0] + ab[1])
        old = np.array([self.drug(a).mean() * self.drug(b).mean() for a, b in key_list])
        new = np.array([estimate(a) * estimate(b) for a, b in key_list])
        return prior + new - old


def action_design(raw):
    # QC and outcomes never enter action availability or layout fingerprints.
    query = raw[pd.to_numeric(raw.Iteration, errors="coerce").between(11, 15)]
    layouts = defaultdict(list)
    for (cell, stage, file), frame in query.groupby(["Cell line", "Iteration", "file"], sort=True):
        rows = sorted(tuple(map(str, r)) for r in frame[["Well", "Drug 1", "Drug 2", "Conc 1 (uM)", "Conc 2 (uM)"]].itertuples(index=False, name=None))
        sig = hashlib.sha256(json.dumps(rows).encode()).hexdigest()
        layouts[(cell, str(stage), sig)].append(str(file))
    assert len(layouts) == 54 and all(len(files) == 2 for files in layouts.values())
    return layouts


def acquisition(model, xt, mt, query_keys, cell, seed):
    # This function has no response or QC argument.
    xq = model.features(query_keys)
    mq = model.predict(xq, cell)
    ktq, kqq = kernel(xt, xq), kernel(xq, xq)
    lower = np.linalg.cholesky(kqq + .01 * np.eye(len(xq)))
    a = solve_triangular(lower, ktq.T, lower=True).T
    rng = np.random.default_rng(seed)
    fantasy = mt[:, None] + a @ rng.normal(size=(len(xq), 16))
    kg = float(-np.partition(fantasy, 2, axis=0)[:3].mean() + mt[top3(mt)].mean())
    return {"uncertainty": float((a * a).sum() / len(xt)),
            "exploit": float(-mq[top3(mq)].mean()), "KG": kg}


def main():
    start = time.perf_counter()
    assert sha(RAW) == "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"
    raw = pd.read_csv(RAW, usecols=COLS, low_memory=False)
    raw["key"] = keys(raw)
    rounds = pd.to_numeric(raw.Iteration, errors="coerce")
    source_raw = raw[rounds.between(1, 10)]
    assert not set(source_raw["Cell line"]) & set(TARGETS)
    source = observations(source_raw)
    layouts = action_design(raw)
    model = SourceModel(source)
    # Mutation check: future response/QC cannot change the metadata action map.
    mutated = raw.copy()
    mutated.loc[~rounds.between(1, 10), "Viability"] = 12345.
    mutated.loc[~rounds.between(1, 10), "Failed QC"] = ~mutated.loc[~rounds.between(1, 10), "Failed QC"]
    assert action_design(mutated) == layouts
    source_mut = observations(mutated[pd.to_numeric(mutated.Iteration, errors="coerce").between(1, 10)])
    pd.testing.assert_frame_equal(source, source_mut)
    observed_keys = set(zip(usable(raw[rounds.between(1, 15)])["Cell line"], usable(raw[rounds.between(1, 15)]).key))
    terminal_raw = usable(raw[raw.Iteration.eq("validation (random, round 15)")])
    terminal_raw = terminal_raw[~terminal_raw.apply(lambda r: (r["Cell line"], r.key) in observed_keys, axis=1)]
    terminal_raw = terminal_raw[terminal_raw["Drug 1"].ne("dmso") & terminal_raw["Drug 2"].ne("dmso")]
    terminal_mut = usable(mutated[mutated.Iteration.eq("validation (random, round 15)")])
    terminal_mut = terminal_mut[~terminal_mut.apply(lambda r: (r["Cell line"], r.key) in observed_keys, axis=1)]
    terminal_mut = terminal_mut[terminal_mut["Drug 1"].ne("dmso") & terminal_mut["Drug 2"].ne("dmso")]
    assert set(zip(terminal_raw["Cell line"], terminal_raw.key)) == set(zip(terminal_mut["Cell line"], terminal_mut.key))
    terminal = observations(terminal_raw)
    results, selections, accounting = [], [], []
    all_models = ["static", "direct_mono", "ridge_update", "hierarchical", "GP", "forest_retrain"]
    for cell in TARGETS:
        # Acquisition integrates over the complete design, never a QC-selected pool.
        plan_keys = sorted(set(terminal_raw.loc[terminal_raw["Cell line"].eq(cell), "key"]))
        plan_x = model.features(plan_keys)
        plan_mean = model.predict(plan_x, cell)
        test = terminal[terminal["Cell line"].eq(cell)]
        tkeys, yt = test.key.tolist(), test.y.to_numpy()
        assert len(yt) >= 3
        xt = model.features(tkeys)
        mt = model.predict(xt, cell)
        oracle = float(-yt[top3(yt)].mean())
        cell_actions = [(key, files) for key, files in layouts.items() if key[0] == cell]
        planned = []
        for index, (key, files) in enumerate(cell_actions):
            offered = usable(raw[raw.file.isin(files)])
            qkeys = sorted(set(offered.key))
            assert not set(qkeys) & set(tkeys), "query/terminal overlap"
            scores = acquisition(model, plan_x, plan_mean, qkeys, cell, SEED + index)
            planned.append((key, files, scores))
        # Select every policy before looking up any purchased target values.
        selected = {p: int(np.argmax([z[2][p] for z in planned])) for p in ["uncertainty", "exploit", "KG"]}
        for action_index, (key, files, scores) in enumerate(planned):
            paid = raw[raw.file.isin(files)]
            query = observations(paid)
            xq = model.features(query.key.tolist())
            mq = model.predict(xq, cell)
            residual = query.y.to_numpy() - mq
            factor = cho_factor(kernel(xq, xq) + .01 * np.eye(len(xq)))
            gp = mt + kernel(xt, xq) @ cho_solve(factor, residual)
            ridge = mt + xt @ np.linalg.solve(xq.T @ xq + np.eye(xq.shape[1]), xq.T @ residual)
            hier = mt + xt @ np.linalg.solve(model.precision + xq.T @ xq / .01, xq.T @ residual / .01)
            retrain = model.new_forest(64)
            retrain.fit(np.vstack([model.xc, model.with_cells(xq, [cell] * len(xq))]),
                        np.r_[source.y.to_numpy(), query.y.to_numpy()])
            preds = {"static": mt, "direct_mono": model.direct_mono(tkeys, query, mt),
                     "ridge_update": ridge, "hierarchical": hier, "GP": gp,
                     "forest_retrain": retrain.predict(model.with_cells(xt, [cell] * len(xt)))}
            for name, pred in preds.items():
                utility = float(-yt[top3(pred)].mean())
                results.append({"cell": cell, "action": action_index, "model": name,
                                "utility": utility, "regret": oracle - utility,
                                "mse": float(np.mean((pred - yt) ** 2)), "oracle": oracle,
                                "terminal_conditions": len(yt), **scores})
            accounting.append({"cell": cell, "action": action_index, "stage": key[1],
                               "layout_sha256": key[2], "files": files, "physical_plates": len(files),
                               "paid_well_records": len(paid), "QC_failed_paid_records": int(paid["Failed QC"].sum()),
                               "valid_feedback_conditions": len(query)})
            print(f"{cell} action {action_index + 1}/{len(planned)} done", flush=True)
        selections.append({"cell": cell, "actions": len(planned), "selected": selected,
                           "terminal_planned_conditions": len(plan_keys),
                           "terminal_scored_conditions": len(test),
                           "terminal_raw_nonoverlap_wells": int(terminal_raw["Cell line"].eq(cell).sum()),
                           "terminal_failed_wells": int(terminal_raw.loc[terminal_raw["Cell line"].eq(cell), "Failed QC"].sum())})
    frame = pd.DataFrame(results)
    frame.to_csv(HERE / "baseline_action_metrics.csv", index=False)
    policy_rows = []
    for entry in selections:
        for name in all_models:
            group = frame[frame.cell.eq(entry["cell"]) & frame.model.eq(name)]
            for policy in ["random", "uncertainty", "exploit", "KG"]:
                row = group if policy == "random" else group[group.action.eq(entry["selected"][policy])]
                policy_rows.append({"cell": entry["cell"], "model": name, "policy": policy,
                                    "utility": float(row.utility.mean()), "regret": float(row.regret.mean()),
                                    "mse": float(row.mse.mean())})
    policy_frame = pd.DataFrame(policy_rows)
    policy_frame.to_csv(HERE / "baseline_policy_metrics.csv", index=False)
    def contrast(model_a, policy_a, model_b, policy_b):
        a = policy_frame[policy_frame.model.eq(model_a) & policy_frame.policy.eq(policy_a)].set_index("cell").utility
        b = policy_frame[policy_frame.model.eq(model_b) & policy_frame.policy.eq(policy_b)].set_index("cell").utility
        delta = (a - b).reindex(TARGETS).to_numpy()
        rng = np.random.default_rng(SEED)
        boot = delta[rng.integers(0, len(delta), size=(2000, len(delta)))].mean(1)
        return {"mean": float(delta.mean()), "CI95_exploratory": np.quantile(boot, [.025, .975]).tolist(),
                "per_cell": dict(zip(TARGETS, delta.tolist()))}
    summary = {
        "status": "ordinary_baseline_exploration_not_new_algorithm_validation",
        "runtime": {"executable": sys.executable, "elapsed_seconds": time.perf_counter() - start},
        "freeze": {p.name: sha(p) for p in [RAW, HERE / "PROTOCOL.md", Path(__file__)]},
        "source_rows_aggregated": len(source), "source_cells": model.cells,
        "target_cells": TARGETS, "action_scenarios": len(accounting), "source_only_feature_dimensions": model.x.shape[1],
        "mutation_checks": {"future_labels_QC_leave_action_map_unchanged": True,
                            "future_labels_QC_leave_terminal_acquisition_pool_unchanged": True,
                            "source_observations_unchanged": True},
        "selection": selections, "budget": accounting,
        "means": policy_frame.groupby(["model", "policy"])[["utility", "regret", "mse"]].mean().reset_index().to_dict("records"),
        "contrasts": {
            "GP_random_minus_static": contrast("GP", "random", "static", "random"),
            "GP_random_minus_direct_mono": contrast("GP", "random", "direct_mono", "random"),
            "GP_random_minus_hierarchical": contrast("GP", "random", "hierarchical", "random"),
            "GP_KG_minus_random": contrast("GP", "KG", "GP", "random"),
            "GP_uncertainty_minus_random": contrast("GP", "uncertainty", "GP", "random")},
        "limits": ["Five same-source cell tasks, conditional bootstrap with shared source fit; no independent-source inference.",
                   "Historical action menu; original adaptive collection may select which actions were available.",
                   "Paid-well records are raw exported records, not culture-independent biological replicates.",
                   "Raw name/dose keys only; no compound alias or salt standardization.",
                   "No unseen-drug result, engagement or causal mechanism claim; no RSI or promotion.",
                   "Forest capacity matched at 64 trees; same assay budget/information, not equal measured compute.",
                   "Random uses exact uniform action expectation, not an ensemble that purchases every action."]}
    (HERE / "BASELINE_RESULTS.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"elapsed_seconds": summary["runtime"]["elapsed_seconds"], "contrasts": summary["contrasts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
