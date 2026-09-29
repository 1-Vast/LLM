"""E1 re-evaluation with honest transfer errors: A2 aggregation weights and the rank-grid boundary.

File summary
- Path: research/dual_core_v2/e1_honest.py
- Purpose: recompute what block 7's in-sample gamma error affected, on block 7's own E1 items.
- Core points:
  - Per registered outer fold, the A1 pair models are refitted exactly as in `research/dual_core/e1`
    on outer-training compounds, and `transfer_honest.honest_errors` adds the error of the complete
    procedure. Nothing uses the outer fold's outcomes except scoring.
  - A2 items are block 7's (same seeded prompt pairs per held-out compound and target). Aggregations
    of the two prompts' `rrt_q` predictions:
    - `rrt_mean`: equal weights;
    - `rrt_precision_v1`: inverse of block 7's in-sample error (reproduces block 7's `rrt_precision`);
    - `inverse_error_honest`: inverse of the honest error;
    - `best_single_v1` and `best_single_honest`: the prompt whose error is smaller;
    - `additive_mean` and `prompt_mean`, block 7's simple baselines.
  - Rank grid (training only). For L1000 pairs, the honest error of the complete procedure under the
    registered grid (k <= 32) and an extended grid (k <= 128). No outer-fold outcome is used.
- Interfaces: `run_fold`, `analyse`; CLI `python -m research.dual_core_v2.e1_honest run|analyse`
- Depends on: transfer_honest.py, research/dual_core/e1.py, research/dual_core/transfer.py
"""
from __future__ import annotations

import argparse
import gzip
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from research.dual_core import e1 as E1
from research.dual_core import splits as SP
from research.dual_core import transfer as TF

from . import transfer_honest as TH

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/dual_core_v2_20260928/e1_honest"
EXTENDED_K = (1, 2, 4, 8, 16, 32, 48, 64, 96, 128)
A2_ARMS = ("rrt_mean", "rrt_precision_v1", "inverse_error_honest", "best_single_v1", "best_single_honest",
           "additive_mean", "prompt_mean")


def _weights(errors, kind):
    e = np.asarray(errors, dtype=np.float64)
    if kind == "equal":
        return np.full(len(e), 1.0 / len(e))
    if kind == "inverse":
        w = 1.0 / np.maximum(e, 1e-12)
        return w / w.sum()
    w = np.zeros(len(e))
    w[int(np.argmin(e))] = 1.0
    return w


def run_fold(task) -> str:
    from threadpoolctl import threadpool_limits
    dataset, fold = task
    path = OUT / f"{dataset}_fold{fold}"
    if Path(f"{path}.pairs.json.gz").exists():
        return f"{dataset} fold {fold}: exists, skipped (write-once)"
    started = time.time()
    with threadpool_limits(limits=1):
        frame, data, detected, keys, qc, fp, pos, quality, batch = E1._dataset(dataset)
        sets = E1.gene_sets(dataset, data)
        compounds = list(frame.index)
        train = [c for c in compounds if frame.fold[c] != fold]
        held = [c for c in compounds if frame.fold[c] == fold]
        measured = {k: {c: r for c, r in data.index.get(k, {}).items() if qc[r]} for k in keys}
        train_rows = [r for k in keys for c, r in measured[k].items() if c in set(train)]
        global_mean = data.shift[train_rows].astype(np.float64).mean(0)
        pairs, models = [], {}
        for c_key in keys:
            for p_key in keys:
                if p_key == c_key:
                    continue
                names = [n for n in train if n in measured[c_key] and n in measured[p_key]]
                X = data.shift[[measured[p_key][n] for n in names]]
                Y = data.shift[[measured[c_key][n] for n in names]]
                q = quality[[measured[p_key][n] for n in names]]
                units = [frame.unit[n] for n in names]
                pm = TF.fit_pair(p_key, c_key, X, Y, q, units)
                models[(p_key, c_key)] = pm
                rec = {"fold": fold, "prompt": E1._id(p_key), "target": E1._id(c_key), "references": len(names),
                       "k": pm.k, "gamma0": pm.gamma0}
                if len(names) >= 6:
                    h = TH.honest_errors(p_key, c_key, X, Y, q, units)
                    rec.update(honest=h["honest"], in_sample=h["in_sample"], k_inner=h["k_inner"])
                    if dataset == "l1000":
                        rec["honest_extended_k"] = TH.honest_errors(p_key, c_key, X, Y, q, units,
                                                                    k_grid=EXTENDED_K)["honest"]
                        rec["k_extended_full"] = TF.fit_pair(p_key, c_key, X, Y, q, units, k_grid=EXTENDED_K).k
                pairs.append(rec)
        honest = {(r["prompt"], r["target"]): r.get("honest", {}).get("rrt_q", np.inf) for r in pairs}
        rows = []
        for c_key in keys:
            names = [n for n in train if n in measured[c_key]]
            Y = data.shift[[measured[c_key][n] for n in names]].astype(np.float64)
            hnames = [h for h in held if h in measured[c_key]]
            if not hnames:
                continue
            scorer = E1._Scorer(data.shift[[measured[c_key][h] for h in hnames]].astype(np.float64), hnames,
                                Y.mean(0), Y, sets)
            for h in hnames:
                prompts = [p for p in keys if p != c_key and h in measured[p]]
                plist = [(a, b) for i, a in enumerate(prompts) for b in prompts[i + 1:]]
                if not plist:
                    continue
                pick = np.random.default_rng([E1.SEED, fold, E1._stable(h, E1._id(c_key))])
                chosen = [plist[i] for i in sorted(pick.choice(len(plist), size=min(E1.A2_PAIRS, len(plist)), replace=False))]
                for pa in chosen:
                    per = {p: models[(p, c_key)] for p in pa}
                    xs = {p: data.shift[measured[p][h]].astype(np.float64) for p in pa}
                    qs = {p: quality[measured[p][h]] for p in pa}
                    rrt = np.stack([per[p].predict(xs[p], qs[p], "rrt_q") for p in pa])
                    e_v1 = [per[p].inner_mse.get("rrt_q", np.inf) for p in pa]
                    e_h = [honest[(E1._id(p), E1._id(c_key))] for p in pa]
                    preds = {"rrt_mean": _weights(e_v1, "equal") @ rrt,
                             "rrt_precision_v1": _weights(e_v1, "inverse") @ rrt,
                             "inverse_error_honest": _weights(e_h, "inverse") @ rrt,
                             "best_single_v1": _weights(e_v1, "best") @ rrt,
                             "best_single_honest": _weights(e_h, "best") @ rrt,
                             "additive_mean": np.mean([per[p].predict(xs[p], qs[p], "additive") for p in pa], axis=0),
                             "prompt_mean": np.mean([xs[p] for p in pa], axis=0)}
                    scored = scorer.score([h] * len(A2_ARMS), np.stack([preds[a] for a in A2_ARMS]))
                    for arm, m in zip(A2_ARMS, scored):
                        rows.append({"fold": fold, "compound": h, "unit": frame.unit[h], "target": E1._id(c_key),
                                     "prompts": "+".join(E1._id(p) for p in pa), "arm": arm,
                                     "weight_max_v1": float(max(_weights(e_v1, "inverse"))),
                                     "weight_max_honest": float(max(_weights(e_h, "inverse"))),
                                     "target_detected": bool(detected[measured[c_key][h]]), **m})
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(f"{path}.pairs.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(pairs, fh, default=float)
    with gzip.open(f"{path}.a2.csv.gz", "wt", encoding="utf-8") as fh:
        pd.DataFrame(rows).to_csv(fh, index=False)
    return f"{dataset} fold {fold}: {len(pairs)} pairs, {len(rows)} A2 rows, {time.time() - started:.0f}s"


def analyse() -> dict:
    out = {}
    for dataset in ("sciplex3", "l1000"):
        pair_files = sorted(OUT.glob(f"{dataset}_fold*.pairs.json.gz"))
        if len(pair_files) != 5:
            continue
        pairs = []
        for p in pair_files:
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                pairs += json.load(fh)
        a2 = pd.concat([pd.read_csv(p) for p in sorted(OUT.glob(f"{dataset}_fold*.a2.csv.gz"))], ignore_index=True)
        SP.duplicated_records(a2, ["fold", "compound", "target", "prompts", "arm"])
        fitted = [p for p in pairs if "honest" in p]
        ratio = lambda arm, kind: np.array([p[kind][arm] / p[kind]["ridge_st"] for p in fitted])
        entry = {"pairs": len(fitted),
                 "in_sample_rrt_q_over_ridge_st": np.quantile(ratio("rrt_q", "in_sample"), [0.1, 0.5, 0.9]).tolist(),
                 "honest_rrt_q_over_ridge_st": np.quantile(ratio("rrt_q", "honest"), [0.1, 0.5, 0.9]).tolist(),
                 "share_rrt_q_better_in_sample": float((ratio("rrt_q", "in_sample") < 1).mean()),
                 "share_rrt_q_better_honest": float((ratio("rrt_q", "honest") < 1).mean()),
                 "optimism_rrt_q_median": float(np.median([p["honest"]["rrt_q"] / p["in_sample"]["rrt_q"] - 1 for p in fitted])),
                 "honest_mse_by_arm_median_ratio_to_ridge_st": {a: float(np.median(ratio(a, "honest")))
                                                                for a in TH.ARMS}}
        if dataset == "l1000":
            ext = [p for p in fitted if "honest_extended_k" in p]
            entry["rank_grid"] = {
                "k_histogram_registered": pd.Series([p["k"] for p in fitted]).value_counts().sort_index().to_dict(),
                "k_histogram_extended": pd.Series([p["k_extended_full"] for p in ext]).value_counts().sort_index().to_dict(),
                "honest_ridge_st_extended_over_registered": np.quantile(
                    [p["honest_extended_k"]["ridge_st"] / p["honest"]["ridge_st"] for p in ext], [0.1, 0.5, 0.9]).tolist(),
                "honest_rrt_q_extended_over_registered": np.quantile(
                    [p["honest_extended_k"]["rrt_q"] / p["honest"]["rrt_q"] for p in ext], [0.1, 0.5, 0.9]).tolist(),
                "share_extended_better_rrt_q": float(np.mean([p["honest_extended_k"]["rrt_q"] < p["honest"]["rrt_q"] for p in ext]))}
        d2 = a2[a2.target_detected]
        k2 = ["fold", "compound", "target", "prompts"]
        entry["A2_arm_means"] = {m: E1.arm_means(d2, m) for m in ("centred_cosine", "discrimination")}
        entry["A2_contrasts"] = {
            f"{a}-{b}|{m}": E1.paired(d2, a, b, m, k2)
            for a, b in (("inverse_error_honest", "rrt_mean"), ("rrt_precision_v1", "rrt_mean"),
                         ("inverse_error_honest", "rrt_precision_v1"), ("best_single_honest", "rrt_mean"),
                         ("rrt_mean", "additive_mean"))
            for m in ("centred_cosine", "discrimination")}
        entry["weights"] = {"max_weight_v1_median": float(a2.weight_max_v1.median()),
                            "max_weight_honest_median": float(a2.weight_max_honest.median())}
        out[dataset] = entry
    (OUT / "analysis.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "analyse"))
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.command == "run":
        OUT.mkdir(parents=True, exist_ok=True)
        tasks = [(d, f) for d in ("l1000", "sciplex3") for f in SP.FOLDS]
        if args.workers > 1:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(args.workers, maxtasksperchild=1) as pool:
                for line in pool.imap_unordered(run_fold, tasks):
                    print(line, flush=True)
        else:
            for t in tasks:
                print(run_fold(t), flush=True)
    print(json.dumps(analyse(), indent=1, default=float)[:6000])


if __name__ == "__main__":
    main()
