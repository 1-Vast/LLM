"""Frozen repair pilot: conditional residual completion and fixed-sequence LTT.

Reuses the original acquisition simulator and working score. Neither this PRISM
proxy nor its clipped score supplies STATE or e-process validity claims.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import prepare, run6, run8, run9, world5b
from .conditional_world import ConditionalWorld

ROOT = prepare.ROOT
HERE = Path(__file__).resolve().parent
OUT = ROOT / "outputs/viability_contrast_20261008/run10_repair"
ARMS = ("legacy", "conditional", "fixed", "random")
SEQUENCES = len(ARMS) * 2
RANK = 8


def residual_prior(fw, auc, train_pos, labels, pool):
    """Estimate shared covariance after removing training-only class priors."""
    residuals = auc[np.ix_(train_pos, pool)] - fw.base_m[labels[train_pos]]
    center, basis, variance = world5b.fit_basis(residuals, RANK)
    return basis, variance, fw.base_m + center[None, :]


def episode(readings, pair, tau, arm, order, world, lines):
    traced = run9.TracedReadings(readings)
    mode = "world" if arm in ("legacy", "conditional") else (
        "ginfo" if arm == "fixed" else "random")
    trajectory, charged, qc = run8.run_episode_v8(traced, pair, tau, mode, order, world)
    purchased = traced.observed
    prefix = np.cumsum([not np.isfinite(readings[p]) for p in purchased]).tolist()
    assert len(purchased) == len(trajectory) == charged
    assert (prefix[-1] if prefix else 0) == qc
    return {"trajectory": trajectory, "qc_prefix": prefix,
            "purchase_positions": purchased,
            "purchase_lines": [lines[p] for p in purchased],
            "purchase_values": [float(readings[p]) if np.isfinite(readings[p]) else None
                                for p in purchased]}


def make_episodes(names, pack, labels, pool, fw, prior, tau, tau_pool, rivals):
    episodes = {a: [] for a in ARMS}
    lines = [pack["lines"][p] for p in pool]
    for c in names:
        ci = int(labels[pack["index"][c]])
        base = {"compound": c, "unit": str(pack["meta"].loc[c, "unit"]),
                "truth_sign": 1, "pair": None, "trajectory": [], "qc_prefix": [],
                "purchase_positions": [], "purchase_lines": [], "purchase_values": []}
        if ci not in rivals:
            for arm in ARMS:
                episodes[arm].append(dict(base))
            continue
        first, second = sorted((ci, rivals[ci]))
        pair = (*run6.class_pair_templates(fw.med, fw.scale, fw.valid,
                   fw.med_p, fw.scale_p, pool, first, second), (first, second))
        base.update(pair=[first, second], truth_sign=1 if ci == first else -1)
        score = (pair[0][0] - pair[1][0]) ** 2 / (
            2 * (pair[0][1] ** 2 + pair[1][1] ** 2 + 2 * max(tau_pool, 1e-6)))
        fixed = sorted(range(len(pool)), key=lambda p: (-score[p], run8.sha(f"{run9.KEY}|{p}")))
        random = list(range(len(pool)))
        np.random.default_rng(int(run8.sha(f"{run9.KEY}|random|{c}")[:16], 16)).shuffle(random)
        readings = pack["auc"][pack["index"][c], pool]
        for arm in ARMS:
            world = fw.make_world() if arm == "legacy" else (
                ConditionalWorld(*prior) if arm == "conditional" else None)
            result = episode(readings, pair, (tau[first], tau[second]), arm,
                             fixed if arm == "fixed" else random, world, lines)
            episodes[arm].append({**base, **result})
    return episodes


def threshold_order(training, endpoint):
    """Preorder candidates on proper-training only, never calibration outcomes."""
    ranked = []
    for threshold in run9.GRID:
        results = [run9.outcome(e, float(threshold)) for e in training]
        d, w = sum(r["decided"] for r in results), sum(r["wrong"] for r in results)
        denominator = len(results) if endpoint == "marginal" else d
        safe = denominator > 0 and w / denominator <= run9.ALPHA
        ranked.append((not safe, -d if safe else 0, -float(threshold), float(threshold)))
    return [r[-1] for r in sorted(ranked)]


def fixed_sequence(calibration, order, endpoint):
    """Reject unsafe null at delta/8; STOP at first nonrejection (no skipping)."""
    table, certified = [], []
    for threshold in order:
        results = [run9.outcome(e, threshold) for e in calibration]
        d, w = sum(r["decided"] for r in results), sum(r["wrong"] for r in results)
        n = len(results) if endpoint == "marginal" else d
        bound = run9.upper(w, n, run9.DELTA / SEQUENCES)
        row = {"threshold": threshold, "n": len(results), "decided": d,
               "wrong": w, "ucb": bound, "certified": bound <= run9.ALPHA}
        table.append(row)
        if not row["certified"]:
            break
        certified.append(row)
    best = max(certified, key=lambda r: (r["decided"], -r["threshold"])) if certified else None
    return best["threshold"] if best else None, table


def forecast_check(names, pack, labels, pool, fw, prior):
    """Equal input diagnostic: four preordered purchase attempts, all other outputs."""
    rows = []
    for c in names:
        ci = int(labels[pack["index"][c]])
        readings = pack["auc"][pack["index"][c], pool]
        order = sorted(range(len(pool)), key=lambda p: run8.sha(f"run10|forecast|{c}|{p}"))
        purchased = np.array(order[:4])
        observed = purchased[np.isfinite(readings[purchased])]
        remaining = np.array(order[4:])
        remaining = remaining[np.isfinite(readings[remaining])]
        for arm in ("legacy", "conditional", "template"):
            world = fw.make_world() if arm == "legacy" else (
                ConditionalWorld(*prior) if arm == "conditional" else None)
            if world is not None:
                world.update(readings[observed], observed)
                mean, scale = world.mean_scale()
            else:
                mean, scale = fw.base_m, fw.base_s
            errors = readings[remaining] - mean[ci, remaining]
            variance = np.maximum(scale[ci, remaining] ** 2, world5b.MIN_VAR)
            rows.append({"compound": c, "arm": arm, "outputs": len(remaining),
                         "mse": float(np.mean(errors ** 2)),
                         "nll": float(np.mean(.5 * (np.log(2 * np.pi * variance) + errors ** 2 / variance))),
                         "charged": 4, "qc": 4 - len(observed),
                         "supported_prior": bool(fw.valid[ci, pool].any())})
    return rows


def freeze_check():
    frozen = json.loads((HERE / "freeze10.json").read_text(encoding="utf-8"))
    for path, digest in frozen["files"].items():
        if run9.digest(ROOT / path) != digest:
            raise RuntimeError(f"Frozen dependency changed: {path}")


def main():
    freeze_check()
    if OUT.exists():
        raise RuntimeError("Repair output already exists; refuse overwrite")
    start = time.perf_counter()
    pack = prepare.load_pack()
    classes, idx = pack["menu"]["classes"], pack["index"]
    ci = {c: i for i, c in enumerate(classes)}
    labels = np.array([ci.get(pack["meta"].loc[c, "moa_main"], -1) for c in pack["compounds"]])
    heldout = pack["folds"]["0"]
    units = {c: str(pack["meta"].loc[c, "unit"]) for c in pack["compounds"]}
    assert len(set(units.values())) == len(units), "Protocol requires unique connectivity units"
    available = [c for c in pack["compounds"] if c not in set(heldout) and labels[idx[c]] >= 0]
    train, calib = run9.split_units(available, units)
    pool = np.array([pack["line_index"][l] for l in pack["menu"]["pool_lines"] if l in pack["line_index"]])
    pos = np.array([idx[c] for c in train])
    by_class = [[idx[c] for c in train if labels[idx[c]] == k] for k in range(len(classes))]
    fw = run6.FoldWorld(pack["auc"], by_class, pos, pool, run9.KEY, pack["meta"]["unit"].to_numpy())
    prior = residual_prior(fw, pack["auc"], pos, labels, pool)
    tau, tau_pool = run8.estimate_tau2(pack["auc"], pos, labels, fw.med, fw.scale,
        fw.valid, fw.med_p, fw.scale_p, pool, len(classes))
    rivals = {}
    for k in range(len(classes)):
        rival, _ = run6.select_rival(fw.med, fw.scale, fw.valid, pool, classes, k)
        if rival is not None:
            rivals[k] = rival
    training = make_episodes(train, pack, labels, pool, fw, prior, tau, tau_pool, rivals)
    orders = {a: {e: threshold_order(training[a], e) for e in ("marginal", "conditional")} for a in ARMS}
    OUT.mkdir(parents=True)
    (OUT / "orders.json").write_text(json.dumps({"orders": orders, "train": train,
        "calibration": calib, "evaluation": heldout, "rank": RANK,
        "legacy_rank": fw.rank, "legacy_weight": fw.weight, "rivals": rivals}, indent=2), encoding="utf-8")
    cal = make_episodes(calib, pack, labels, pool, fw, prior, tau, tau_pool, rivals)
    selections, tables = {}, {}
    for a in ARMS:
        selections[a], tables[a] = {}, {}
        for e, order in orders[a].items():
            selections[a][e], tables[a][e] = fixed_sequence(cal[a], order, e)
    (OUT / "calibration.json").write_text(json.dumps({"selected": selections, "tables": tables}, indent=2), encoding="utf-8")
    test = make_episodes(heldout, pack, labels, pool, fw, prior, tau, tau_pool, rivals)
    rows = [{"arm": a, "endpoint": endpoint, "compound": e["compound"], "unit": e["unit"],
             "supported": e["pair"] is not None, **run9.outcome(e, threshold)}
            for a in ARMS for endpoint, threshold in selections[a].items() for e in test[a]]
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "episodes.csv", index=False)
    forecasts = pd.DataFrame(forecast_check(heldout, pack, labels, pool, fw, prior))
    forecasts.to_csv(OUT / "forecasts.csv", index=False)
    arms = {}
    for (a, endpoint), group in frame.groupby(["arm", "endpoint"]):
        n, d, w = len(group), int(group.decided.sum()), int(group.wrong.sum())
        arms[f"{a}__{endpoint}"] = {"n": n, "decided": d, "wrong": w, "coverage": d / n,
            "conditional_wrong": w / d if d else None, "marginal_wrong": w / n,
            "conditional_ucb95": run9.upper(w, d, .05),
            "charged": int(group.measurements.sum()), "qc": int(group.qc.sum())}
    repaired = arms["conditional__conditional"]
    contrasts = {}
    pivot = forecasts.pivot(index="compound", columns="arm", values="mse")
    rng = np.random.default_rng(10)
    for baseline in ("legacy", "template"):
        delta = (pivot["conditional"] - pivot[baseline]).to_numpy()
        boot = np.mean(delta[rng.integers(0, len(delta), (2000, len(delta)))], axis=1)
        contrasts[baseline] = {"conditional_minus_baseline_mse": float(delta.mean()),
                              "paired_unit_ci95": np.quantile(boot, [.025, .975]).tolist()}
    summary = {"arms": arms, "forecast_means": forecasts.groupby("arm")[["mse", "nll"]].mean().to_dict("index"),
               "forecast_contrasts": contrasts,
               "proceed_to_global": selections["conditional"]["conditional"] is not None and repaired["coverage"] >= .20 and (repaired["conditional_wrong"] or 0) <= .05 and repaired["conditional_ucb95"] <= .15,
               "runtime_sec": time.perf_counter() - start,
               "scope": "Exposed fold0 development; annotation-conditioned PRISM proxy, not STATE or fresh confirmation"}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "trajectories.json").write_text(json.dumps({"training": training, "calibration": cal, "evaluation": test}), encoding="utf-8")
    freeze_check()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
