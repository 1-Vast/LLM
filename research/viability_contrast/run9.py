"""Honest fixed-policy LTT pilot; clipped LMM is a score, not an e-process."""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

from . import prepare, run6, run8

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "outputs/viability_contrast_20261008/run9_pilot"
KEY = "viability-contrast-9"
GRID = np.geomspace(0.5, 64.0, 21)
ACQS = ("ginfo", "world", "random")
ALPHA, DELTA = 0.05, 0.05
FAMILY = len(GRID) * len(ACQS) * 2


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def upper(wrong, n, delta):
    if n == 0 or wrong == n:
        return 1.0
    return float(beta.ppf(1 - delta, wrong + 1, n - wrong))


def split_units(compounds, unit_of):
    units = sorted({unit_of[c] for c in compounds},
                   key=lambda u: run8.sha(f"{KEY}|split|{u}"))
    fit = set(units[:len(units) // 2])
    return ([c for c in compounds if unit_of[c] in fit],
            [c for c in compounds if unit_of[c] not in fit])


def outcome(episode, threshold):
    """Truth used only by evaluator; empty/unsupported episodes abstain."""
    if threshold is None:
        return {"decided": False, "wrong": False, "measurements": 0, "qc": 0}
    for score, cost in episode["trajectory"]:
        if threshold is not None and abs(score) >= threshold:
            return {"decided": True,
                    "wrong": (1 if score > 0 else -1) != episode["truth_sign"],
                    "measurements": cost,
                    "qc": episode["qc_prefix"][cost - 1]}
    cost = episode["trajectory"][-1][1] if episode["trajectory"] else 0
    return {"decided": False, "wrong": False, "measurements": cost,
            "qc": episode["qc_prefix"][-1] if cost else 0}


def calibrate(episodes):
    table = []
    for threshold in GRID:
        results = [outcome(e, float(threshold)) for e in episodes]
        d = sum(r["decided"] for r in results)
        w = sum(r["wrong"] for r in results)
        table.append({"threshold": float(threshold), "n": len(results),
                      "decided": d, "wrong": w,
                      "marginal_ucb": upper(w, len(results), DELTA / FAMILY),
                      "conditional_ucb": upper(w, d, DELTA / FAMILY)})
    selected = {}
    for endpoint in ("marginal", "conditional"):
        safe = [r for r in table if r[f"{endpoint}_ucb"] <= ALPHA]
        best = max(safe, key=lambda r: (r["decided"], -r["threshold"])) if safe else None
        selected[endpoint] = best["threshold"] if best else None
    return selected, table


def make_episodes(names, pack, labels, pool, classes, fw, tau, tau_pool, rivals):
    episodes = {a: [] for a in ACQS}
    for c in names:
        ci = int(labels[pack["index"][c]])
        base = {"compound": c, "unit": str(pack["meta"].loc[c, "unit"]),
                "truth_sign": 1, "trajectory": [], "qc_prefix": [], "pair": None}
        if ci not in rivals:
            for acq in ACQS:
                episodes[acq].append(dict(base))
            continue
        # The challenge still uses the annotated true class to construct its pair.
        # Canonical orientation prevents its position becoming a model input.
        first, second = sorted((ci, rivals[ci]))
        pair = (*run6.class_pair_templates(fw.med, fw.scale, fw.valid,
                 fw.med_p, fw.scale_p, pool, first, second), (first, second))
        base.update(truth_sign=1 if ci == first else -1, pair=[first, second])
        readings = pack["auc"][pack["index"][c], pool]
        scores = (pair[0][0] - pair[1][0]) ** 2 / (
            2 * (pair[0][1] ** 2 + pair[1][1] ** 2 + 2 * max(tau_pool, 1e-6)))
        gorder = sorted(range(len(pool)), key=lambda j: (-scores[j], run8.sha(f"{KEY}|{j}")))
        rand = list(range(len(pool)))
        np.random.default_rng(int(run8.sha(f"{KEY}|random|{c}")[:16], 16)).shuffle(rand)
        for acq in ACQS:
            world = fw.make_world() if acq == "world" else None
            # Scalar reads mark purchases; vector reads use purchased positions.
            traced = TracedReadings(readings)
            traj, _, qc = run8.run_episode_v8(traced, pair, (tau[first], tau[second]),
                acq, gorder if acq == "ginfo" else rand, world=world)
            observed = traced.observed
            prefix = np.cumsum([not np.isfinite(readings[j]) for j in observed]).tolist()
            assert len(prefix) == len(traj) and (prefix[-1] if prefix else 0) == qc
            episodes[acq].append({**base, "trajectory": traj, "qc_prefix": prefix})
    return episodes


class TracedReadings(np.ndarray):
    """Record scalar purchases; vector indexing is only for already bought data."""
    def __new__(cls, values):
        obj = np.asarray(values).view(cls)
        obj.observed = []
        return obj

    def __array_finalize__(self, obj):
        self.observed = getattr(obj, "observed", [])

    def __getitem__(self, index):
        if isinstance(index, (int, np.integer)) and int(index) not in self.observed:
            self.observed.append(int(index))
        value = super().__getitem__(index)
        return np.asarray(value) if isinstance(value, np.ndarray) else value


def check_freeze():
    freeze = json.loads((HERE / "freeze9_retry1.json").read_text(encoding="utf-8"))
    for relative, expected in freeze["files"].items():
        if digest(ROOT / relative) != expected:
            raise RuntimeError(f"Frozen input changed: {relative}")


def main():
    check_freeze()
    if OUT.exists():
        raise RuntimeError("Refusing to overwrite v9 pilot outputs")
    start = time.perf_counter()
    pack = prepare.load_pack()
    classes, idx = pack["menu"]["classes"], pack["index"]
    ci = {c: i for i, c in enumerate(classes)}
    labels = np.array([ci.get(pack["meta"].loc[c, "moa_main"], -1)
                       for c in pack["compounds"]])
    pool = np.array([pack["line_index"][l] for l in pack["menu"]["pool_lines"]
                     if l in pack["line_index"]])
    heldout = pack["folds"]["0"]
    unit_of = {c: str(pack["meta"].loc[c, "unit"]) for c in pack["compounds"]}
    assert len(set(unit_of.values())) == len(unit_of), "This protocol requires one row per unit"
    available = [c for c in pack["compounds"] if c not in set(heldout) and labels[idx[c]] >= 0]
    train, calib = split_units(available, unit_of)
    train_pos = np.array([idx[c] for c in train])
    by_class = [[idx[c] for c in train if labels[idx[c]] == i] for i in range(len(classes))]
    fw = run6.FoldWorld(pack["auc"], by_class, train_pos, pool, KEY,
                       pack["meta"]["unit"].to_numpy())
    tau, tau_pool = run8.estimate_tau2(pack["auc"], train_pos, labels,
        fw.med, fw.scale, fw.valid, fw.med_p, fw.scale_p, pool, len(classes))
    rivals = {}
    for i in range(len(classes)):
        r, _ = run6.select_rival(fw.med, fw.scale, fw.valid, pool, classes, i)
        if r is not None:
            rivals[i] = r
    cal = make_episodes(calib, pack, labels, pool, classes, fw, tau, tau_pool, rivals)
    selected, tables = {}, {}
    for a in ACQS:
        selected[a], tables[a] = calibrate(cal[a])
    # Commit choices to disk before evaluation outcomes are accessed.
    OUT.mkdir(parents=True)
    receipt = {"train": train, "calibration": calib, "evaluation": heldout,
               "rank": fw.rank, "weight": fw.weight, "rivals": rivals,
               "selected": selected, "tables": tables,
               "family_size": FAMILY, "zero_error_min_n": math.ceil(math.log(DELTA / FAMILY) / math.log(1 - ALPHA))}
    (OUT / "calibration.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    test = make_episodes(heldout, pack, labels, pool, classes, fw, tau, tau_pool, rivals)
    rows = []
    for a in ACQS:
        for endpoint, threshold in {**selected[a], "abstain": None}.items():
            for e in test[a]:
                rows.append({"acquisition": a, "endpoint": endpoint, "threshold": threshold,
                             "compound": e["compound"], "unit": e["unit"],
                             "supported": e["pair"] is not None, **outcome(e, threshold)})
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / "episodes.csv", index=False)
    arms = {}
    for (a, endpoint), group in frame.groupby(["acquisition", "endpoint"]):
        n, d, w = len(group), int(group.decided.sum()), int(group.wrong.sum())
        arms[f"{a}__{endpoint}"] = {"n": n, "decided": d, "wrong": w,
            "coverage": d / n, "marginal_wrong": w / n,
            "conditional_wrong": w / d if d else None,
            "marginal_ucb95": upper(w, n, .05), "conditional_ucb95": upper(w, d, .05),
            "measurements": int(group.measurements.sum()), "qc": int(group.qc.sum())}
    primary = arms["ginfo__marginal"]
    proceed = selected["ginfo"]["marginal"] is not None and primary["coverage"] >= .20 and primary["marginal_wrong"] <= .05 and primary["marginal_ucb95"] <= .15
    summary = {"arms": arms, "proceed_to_global": proceed,
               "runtime_sec": time.perf_counter() - start,
               "scope": "Previously exposed fold0; annotation-conditioned contrast; not STATE validation",
               "global_blocking_reason": None if proceed else "Registered risk/coverage pilot gate failed"}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "trajectories.json").write_text(json.dumps({"calibration": cal, "evaluation": test}), encoding="utf-8")
    check_freeze()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
