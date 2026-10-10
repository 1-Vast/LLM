"""Development check of the identifiability map (H5) on the open tier.

Predicted single-option cross-rejection R_pred[a, b, o] comes from reference drugs only
(identifiability.predicted_cross_rejection). Realised events are the development drugs of referenced
classes: for drug d of class a, option o and every other referenced hypothesis b, the event is
p_b(z_d at o alone) <= alpha. Scores:

* AUC of R_pred for the events, against a pair-blind predictor (the mean realised-in-reference rate
  of b at o, i.e. how often b is rejected by anything) computed from R_pred averaged over a;
* calibration by deciles of R_pred;
* pairs predicted non-identifiable (max over options and both directions of R_pred < floor) and
  how often a development drug of either class separated them anyway;
* the time (6 h or 24 h) of each pair's best predicted option.

Usage: python dev_identifiability.py <name> [config json] --floor 0.2
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

import identifiability as ID
import study as S

HERE = Path(__file__).resolve().parent


def auc(score: np.ndarray, y: np.ndarray) -> float:
    """Mann-Whitney AUC with average ranks for ties."""
    from scipy.stats import rankdata
    y = y.astype(bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(score)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def events(fz, Z, labels, queries, classes, R_pred):
    """Per (drug, option, b != a) rows: predicted rate, pair-blind rate, realised rejection."""
    pos = {n: i for i, n in enumerate(fz.names[classes])}
    blind = np.nanmean(R_pred, axis=0)  # (B, n_opt): how often b is rejected by a random referenced class
    pred, base, y, a_idx, b_idx, o_idx = [], [], [], [], [], []
    for qi in queries:
        a = pos.get(labels[qi])
        if a is None:
            continue
        for o in range(Z.shape[1]):
            if np.isnan(Z[qi, o, 0]) or np.isnan(R_pred[a, 0, o]):
                continue
            p = fz.pvalues(Z[qi], [o], classes)
            m = np.arange(len(classes)) != a
            m &= ~np.isnan(R_pred[a, :, o])
            pred.append(R_pred[a, m, o])
            base.append(blind[m, o])
            y.append(p[m] <= fz.alpha)
            a_idx.append(np.full(m.sum(), a))
            b_idx.append(np.where(m)[0])
            o_idx.append(np.full(m.sum(), o))
    cat = lambda v: np.concatenate(v) if v else np.array([])
    return cat(pred), cat(base), cat(y), cat(a_idx), cat(b_idx), cat(o_idx)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("config", nargs="?", default="{}")
    ap.add_argument("--floor", type=float, default=0.2)
    ap.add_argument("--n-sim", type=int, default=64)
    a = ap.parse_args()
    t0 = time.time()
    data = S.load_tier("open")
    cfg = S.Config(**json.loads(a.config))
    b = S.build(data, cfg)
    fz = S.falsifier(b)
    classes = np.array([i for i, m in enumerate(b.models) if m.kind != "knowledge"])
    R_pred = ID.predicted_cross_rejection(fz, classes, n_sim=a.n_sim, seed=cfg.seed, lam_pool=b.lam_pool)
    q = np.where(data["role"] == "development")[0]
    pred, base, y, ai, bi, oi = events(fz, b.Z_open, data["moa"], q, classes, R_pred)
    res = {"name": a.name, "config": asdict(cfg), "n_classes": int(len(classes)), "n_events": int(len(y)),
           "realised_rate": float(y.mean()), "predicted_rate": float(pred.mean()),
           "auc_pair": auc(pred, y), "auc_pair_blind": auc(base, y)}
    # pair information beyond the hypothesis's general rejectability: AUC within strata of the blind rate
    bins = np.quantile(base, np.linspace(0, 1, 11))
    strata = np.clip(np.searchsorted(bins, base, side="right") - 1, 0, 9)
    res["auc_pair_within_blind_deciles"] = float(np.nanmean([auc(pred[strata == s], y[strata == s]) for s in range(10)]))
    dec = np.quantile(pred, np.linspace(0, 1, 11))
    cal = []
    for lo, hi in zip(dec[:-1], dec[1:]):
        m = (pred >= lo) & (pred <= hi)
        if m.any():
            cal.append({"pred_lo": float(lo), "pred_hi": float(hi), "n": int(m.sum()), "pred_mean": float(pred[m].mean()),
                        "real_mean": float(y[m].mean())})
    res["calibration_deciles"] = cal
    # pairs: predicted separability (both directions, best option)
    sep = np.fmax(R_pred, np.transpose(R_pred, (1, 0, 2)))  # (A, A, n_opt)
    best = np.nanmax(sep, axis=2)
    iu = np.triu_indices(len(classes), 1)
    best_pairs = best[iu]
    non_id = best_pairs < a.floor
    # realised separation of a pair: any development event of either class rejecting the other
    real_sep = np.zeros((len(classes), len(classes)), bool)
    real_seen = np.zeros((len(classes), len(classes)), bool)
    for aa, bb, yy in zip(ai, bi, y):
        real_seen[aa, bb] = real_seen[bb, aa] = True
        if yy:
            real_sep[aa, bb] = real_sep[bb, aa] = True
    seen = real_seen[iu]
    rs = real_sep[iu]
    res["pairs"] = {"n": int(len(best_pairs)), "predicted_non_identifiable": int(non_id.sum()),
                    "share_non_identifiable": float(non_id.mean()),
                    "realised_separated_given_pred_non_id": float(rs[non_id & seen].mean()) if (non_id & seen).any() else None,
                    "realised_separated_given_pred_id": float(rs[~non_id & seen].mean()) if (~non_id & seen).any() else None,
                    "n_seen_non_id": int((non_id & seen).sum()), "n_seen_id": int((~non_id & seen).sum())}
    arg = np.nanargmax(np.where(np.isnan(sep), -1, sep), axis=2)[iu]
    times = np.array([data["options"][o].split("|")[1] for o in arg])
    res["best_option_time_share"] = {t: float((times[~non_id] == t).mean()) for t in ("6 h", "24 h")}
    lines = np.array([data["options"][o].split("|")[0] for o in arg])
    res["best_option_line_share"] = {l: float((lines[~non_id] == l).mean()) for l in sorted(set(lines))}
    res["seconds"] = round(time.time() - t0, 1)
    out = HERE / "development" / f"{a.name}.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("calibration_deciles", "config")}, indent=1))
    for c in cal:
        print(round(c["pred_mean"], 3), round(c["real_mean"], 3), c["n"])


if __name__ == "__main__":
    main()
