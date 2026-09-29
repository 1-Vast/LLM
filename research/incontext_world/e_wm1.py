"""E-WM1: predict a held-out compound's shift at one condition from its measured shift at another.

File summary
- Path: research/incontext_world/e_wm1.py
- Purpose: run and analyse spec.json's E-WM1 on SciPlex3 (16 conditions, split-half noise ceiling)
  and L1000 (8 conditions, no ceiling).
- Core points:
  - Items: held-out compound x, prompt p, target c != p, both QC-passed for x. Transitions are
    fitted per (fold, p, c) on other-fold compounds measured at both, so no held-out shift enters
    a fit.
  - Every arm of `transition.ARMS` predicts every item, so arms are compared on identical items.
  - Unit weighting: each unit's items are averaged before the unit bootstrap (spec.json).
  - The noise ceiling is the split-half Pearson (Tahoe-x1's definition) and split-half centred
    cosine of the target measurement itself.
- Interfaces: `run_dataset`, `analyse`, `posthoc_ceiling`; CLI
  `python -m research.incontext_world.e_wm1 run [--folds ...] [--suffix ...] | analyse | ceiling`
- Depends on: transition.py, metrics.py, research/protocol_v2 (loaders), research/external_validation/statistics.py
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import metrics as M
from . import transition as TR

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/incontext_world_20260927/e_wm1"
SEED = 20260927
DRAWS = 10_000
FOLDS = (0, 1, 2, 3, 4)
"""The registered folds. The first run used 1-5 (spec.json's wording): fold 5 is empty and fold 0 was added later."""


def _dataset(dataset: str):
    """(data, detected flags, condition keys, units) for one dataset, via the registered loaders."""
    from research.belief_planning import tasks as T
    from research.protocol_v2 import tasks_v21 as TV
    C, LP = TV.C, TV.LP
    if dataset == "sciplex3":
        data = C.load()
        spec = C.load_protocol()
        detected = C.detected_flags(data, C.detection_null(data, spec))
        tiers = C.tiers(data, spec)
        keys = tuple(sorted(set(tiers["A"].keys) | set(tiers["B"].keys)))
    else:
        data = LP.load()
        detected = data.conditions.detected.to_numpy(bool)
        keys = tuple(LP.TIERS["LT"]["keys"])
    units = T.units(dataset)[T.UNIT[dataset]].astype(str).to_dict()
    qc = np.array([C.qc_passed(data, i) for i in range(len(data.conditions))])
    return data, detected, keys, units, qc


def run_dataset(dataset: str, folds=FOLDS) -> pd.DataFrame:
    data, detected, keys, units, qc = _dataset(dataset)
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    has_halves = len(data.rep1) == len(data.shift)
    rows = []
    for fold in folds:
        train = {c for c in comp.index if comp.fold[c] != fold}
        held = sorted(c for c in comp.index if comp.fold[c] == fold)
        measured = {k: {c: r for c, r in data.index.get(k, {}).items() if qc[r]} for k in keys}
        train_rows = [r for k in keys for c, r in measured[k].items() if c in train]
        global_mean = data.shift[train_rows].astype(np.float64).mean(0)
        for c_key in keys:
            ref_names = sorted(n for n in measured[c_key] if n in train)
            R = data.shift[[measured[c_key][n] for n in ref_names]].astype(np.float64)
            u = M._unit(R.sum(0))
            Rp = R - np.outer(R @ u, u) if u is not None else R
            Rn = Rp / np.maximum(np.linalg.norm(Rp, axis=1, keepdims=True), 1e-12)
            for p_key in keys:
                if p_key == c_key:
                    continue
                names = [n for n in ref_names if n in measured[p_key]]
                X = data.shift[[measured[p_key][n] for n in names]]
                Y = data.shift[[measured[c_key][n] for n in names]]
                tr = TR.fit(p_key, c_key, names, X, Y, global_mean)
                items = [c for c in held if c in measured[p_key] and c in measured[c_key]]
                if not items:
                    continue
                x = data.shift[[measured[p_key][c] for c in items]].astype(np.float64)
                y = data.shift[[measured[c_key][c] for c in items]].astype(np.float64)
                truth_nn = _nearest(Rn, u, y)
                base = {"dataset": dataset, "fold": fold, "prompt": "|".join(map(str, p_key)),
                        "target": "|".join(map(str, c_key)), "references": tr.references, "k": tr.k}
                ceiling = []
                for i, c in enumerate(items):
                    row_c = measured[c_key][c]
                    if has_halves:
                        a = data.rep1[row_c].astype(np.float64)
                        b = data.rep2[row_c].astype(np.float64)
                        ceiling.append((M.pearson_delta(a, b), M.centred_cosine(a, b, tr.mean_target)))
                    else:
                        ceiling.append((np.nan, np.nan))
                for arm in TR.ARMS:
                    pred = np.stack([tr.predict(xi, arm) for xi in x])
                    disc = M.discrimination(pred, y)
                    pred_nn = _nearest(Rn, u, pred)
                    for i, c in enumerate(items):
                        rows.append({**base, "compound": c, "unit": units.get(c, c), "arm": arm,
                                     "prompt_detected": bool(detected[measured[p_key][c]]),
                                     "target_detected": bool(detected[measured[c_key][c]]),
                                     "pearson_delta": M.pearson_delta(pred[i], y[i]),
                                     "centred_cosine": M.centred_cosine(pred[i], y[i], tr.mean_target),
                                     "mse": M.mse(pred[i], y[i]), "discrimination": float(disc[i]),
                                     "norm": float(np.linalg.norm(pred[i])),
                                     "phenocopy5": len(pred_nn[i] & truth_nn[i]) / 5 if len(Rn) >= 5 else np.nan,
                                     "ceiling_pearson": ceiling[i][0], "ceiling_centred_cosine": ceiling[i][1]})
    return pd.DataFrame(rows)


def _nearest(Rn: np.ndarray, u, V: np.ndarray, k: int = 5) -> list[set]:
    """Indices of the k nearest references (projected cosine) of each row of V."""
    if len(Rn) < k:
        return [set() for _ in range(len(V))]
    Vp = V - np.outer(V @ u, u) if u is not None else V
    Vn = Vp / np.maximum(np.linalg.norm(Vp, axis=1, keepdims=True), 1e-12)
    order = np.argsort(-(Vn @ Rn.T), axis=1, kind="stable")[:, :k]
    return [set(o.tolist()) for o in order]


# ------------------------------------------------------------------------------------ analysis
def _unit_means(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    return frame.groupby(["unit", "arm"])[metric].mean().unstack("arm").sort_index()


def _boot(values: np.ndarray, index: np.ndarray) -> list[float]:
    return np.quantile(values[index].mean(axis=1), [0.025, 0.975]).tolist()


def summarise(frame: pd.DataFrame, metric: str, candidate: str = "ridge_st") -> dict:
    table = _unit_means(frame, metric).dropna()
    index = np.random.default_rng(SEED).integers(len(table), size=(DRAWS, len(table)))
    arms = {a: {"unit_mean": float(table[a].mean()), "ci": _boot(table[a].to_numpy(), index)} for a in table.columns}
    paired = {}
    for other in table.columns:
        if other == candidate:
            continue
        diff = (table[candidate] - table[other]).to_numpy()
        paired[other] = {"difference": float(diff.mean()), "ci": _boot(diff, index)}
    return {"metric": metric, "units": int(len(table)), "items": int(len(frame) // max(frame.arm.nunique(), 1)),
            "arms": arms, f"{candidate}_minus": paired}


def weighted_auroc(frame: pd.DataFrame, arm: str, index: np.ndarray, units: list) -> dict:
    sub = frame[frame.arm == arm]
    order = np.argsort(sub.norm.to_numpy(), kind="stable")
    score = sub.norm.to_numpy()[order]
    label = sub.target_detected.to_numpy(bool)[order]
    code = pd.Categorical(sub.unit.astype(str).to_numpy()[order], categories=units).codes
    point = M.effect_auroc(score, label)
    # tie groups share the average rank; weights come from each bootstrap draw's unit multiplicities
    _, start = np.unique(score, return_index=True)
    group = np.searchsorted(start, np.arange(len(score)), side="right") - 1
    boot = []
    for draw in index:
        w = np.bincount(draw, minlength=len(units))[code].astype(float)
        wn, wp = w * ~label, w * label
        neg_by_group = np.bincount(group, weights=wn)
        below = np.concatenate([[0.0], np.cumsum(neg_by_group)[:-1]])[group]
        tie = neg_by_group[group]
        total = wp.sum() * wn.sum()
        boot.append(float((wp * (below + 0.5 * tie)).sum() / total) if total > 0 else np.nan)
    return {"auroc": point, "ci": np.nanquantile(boot, [0.025, 0.975]).tolist(), "draws": int(len(index))}


def analyse(out: Path = OUT) -> dict:
    result = {"spec": "research/incontext_world/spec.json#E-WM1", "datasets": {}}
    for dataset in ("sciplex3", "l1000"):
        paths = sorted(out.glob(f"{dataset}_items*.csv.gz"))
        if not paths:
            continue
        # the arm is literally called "null"; pandas would read it as missing by default
        frame = pd.concat([pd.read_csv(p, keep_default_na=False, na_values=[""]) for p in paths], ignore_index=True)
        if frame.duplicated(["fold", "compound", "prompt", "target", "arm"]).any():
            raise ValueError(f"{dataset}: an item appears in two record files")
        detected = frame[frame.target_detected]
        entry = {"primary": summarise(detected, "centred_cosine")}
        entry["secondary"] = {
            "pearson_delta_detected": summarise(detected, "pearson_delta"),
            "discrimination_detected": summarise(detected, "discrimination"),
            "phenocopy5_detected": summarise(detected, "phenocopy5"),
            "mse_all": summarise(frame, "mse"),
            "centred_cosine_prompt_detected": summarise(detected[detected.prompt_detected], "centred_cosine"),
            "centred_cosine_prompt_undetected": summarise(detected[~detected.prompt_detected], "centred_cosine"),
        }
        units = sorted(frame.unit.astype(str).unique())
        index = np.random.default_rng(SEED).integers(len(units), size=(DRAWS, len(units)))
        entry["effect_auroc"] = {arm: weighted_auroc(frame, arm, index, units) for arm in TR.ARMS}
        ceiling = detected[detected.arm == "ridge_st"]
        if ceiling.ceiling_pearson.notna().any():
            per_unit = ceiling.groupby("unit")[["ceiling_pearson", "ceiling_centred_cosine"]].mean()
            entry["noise_ceiling_detected"] = {m: float(per_unit[m].mean()) for m in per_unit.columns}
        else:
            entry["noise_ceiling_detected"] = "unknown: no split-half replicates"
        prim = entry["primary"]["ridge_st_minus"]
        entry["gate"] = {"pass": all(prim[b]["ci"][0] > 0 for b in TR.BASELINES),
                         "rule": "ridge_st above each baseline with the 95% unit-bootstrap interval above 0"}
        entry["transition_k"] = frame[frame.arm == "ridge_st"].groupby("target").k.median().to_dict()
        result["datasets"][dataset] = entry
    (out / "analysis.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def posthoc_ceiling(out: Path = OUT) -> dict:
    """POST HOC: Tahoe-x1's split-half ceiling compares two half-samples, so a prediction scored against the full
    measurement can exceed it. The Spearman-Brown correction sqrt(2r / (1 + r)) bounds the Pearson delta of a
    perfect predictor against the full measurement (SciPlex3, detected targets, ridge_st rows)."""
    frame = pd.concat([pd.read_csv(p, keep_default_na=False, na_values=[""])
                       for p in sorted(out.glob("sciplex3_items*.csv.gz"))], ignore_index=True)
    d = frame[(frame.arm == "ridge_st") & frame.target_detected].copy()
    r = d.ceiling_pearson.clip(lower=0)
    d["spearman_brown"] = np.sqrt(2 * r / (1 + r))
    u = d.groupby("unit")[["ceiling_pearson", "spearman_brown", "pearson_delta"]].mean()
    result = {"status": "post hoc", "units": int(len(u)), "split_half_pearson": float(u.ceiling_pearson.mean()),
              "spearman_brown_ceiling": float(u.spearman_brown.mean()),
              "ridge_st_pearson_delta": float(u.pearson_delta.mean()),
              "ridge_st_fraction_of_corrected_ceiling": float((u.pearson_delta / u.spearman_brown).mean())}
    (out / "ceiling_posthoc.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "analyse", "ceiling"))
    parser.add_argument("--folds", type=int, nargs="*", default=list(FOLDS))
    parser.add_argument("--suffix", default="")
    args = parser.parse_args()
    if args.command == "ceiling":
        print(json.dumps(posthoc_ceiling(), indent=1))
        return
    if args.command == "run":
        OUT.mkdir(parents=True, exist_ok=True)
        for dataset in ("sciplex3", "l1000"):
            path = OUT / f"{dataset}_items{args.suffix}.csv.gz"
            if path.exists():
                raise SystemExit(f"{path} exists; records are write-once")
            started = time.time()
            frame = run_dataset(dataset, tuple(args.folds))
            frame.to_csv(path, index=False)
            print(dataset, len(frame), f"{time.time() - started:.0f}s", flush=True)
    print(json.dumps(analyse(), indent=1)[:4000])


if __name__ == "__main__":
    main()
