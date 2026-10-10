"""Component test of agent knowledge as a predictor of an unobserved class (development, open tier).

For every reference drug of a class, the class is treated as unobserved: its knowledge prototype is
compared with the drug's projected signature (cosine per measured option, averaged) and ranked
among the knowledge prototypes of all 424 classes (score = fraction of other classes with a lower
cosine; 0.5 = chance). Knowledge sources:

* emh: the agent's gene programs (knowledge compiler, slopes from reference drugs);
* analogy: the similarity-weighted mean of the agent-chosen analog classes' reference means (the
  class itself is never its own analog);
* analogy_permuted: analog lists shuffled across classes (control);
* own_data_loo: the class's other reference drugs (upper bound; needs >= 2 reference drugs).
Strata by drug activity (dev_programs.drug_activity). Writes development/analogy.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import dev_programs as DP
import study as S

HERE = Path(__file__).resolve().parent


def own_rank(Zd: np.ndarray, own: np.ndarray, protos: np.ndarray, own_idx: int) -> float:
    """Zd (n_opt, K) with NaN rows; own (n_opt, K) prototype for the drug's class; protos (C, n_opt, K)."""
    opts = [o for o in range(Zd.shape[0]) if not np.isnan(Zd[o, 0]) and not np.isnan(own[o, 0])]
    if not opts:
        return float("nan")
    vals = []
    for o in opts:
        x = Zd[o] / (np.linalg.norm(Zd[o]) + 1e-12)
        P = np.nan_to_num(protos[:, o])
        cos = P @ x / (np.linalg.norm(P, axis=1) + 1e-12)
        c_own = float(own[o] @ x / (np.linalg.norm(own[o]) + 1e-12))
        other = np.delete(cos, own_idx)
        vals.append(np.mean(other < c_own) + 0.5 * np.mean(other == c_own))
    return float(np.mean(vals))


def main() -> dict:
    data = S.load_tier("open")
    moa, role = data["moa"], data["role"]
    ref = role == "reference"
    act = DP.drug_activity(data["x"], ref)
    base = {"score": "relative", "kcal": "all", "kappa": 0.05, "tau2": 10.0, "n_bins": 3}
    res = {}
    idx = np.where(ref)[0]
    for source in ("emh", "analogy", "analogy_permuted", "generic"):
        b = S.build(data, S.Config(**base, knowledge=source))
        # knowledge prototype of every class: the falsifier stores data prototypes for referenced
        # classes, so read the knowledge compile through the K calibration rows' convention: rebuild
        # with knowledge used for every class (compile="knowledge")
        bk = S.build(data, S.Config(**base, knowledge=source, compile="knowledge"))
        names = [m.name for m in bk.models]
        P = np.stack([m.proto for m in bk.models])
        pos = {n: i for i, n in enumerate(names)}
        r = np.array([own_rank(bk.Z_open[i], P[pos[moa[i]]], P, pos[moa[i]]) for i in idx])
        a = act[idx]
        res[source] = {"own_rank_mean": float(np.nanmean(r)), "active_q4": float(np.nanmean(r[a >= 0.75])),
                       "weak": float(np.nanmean(r[a < 0.75])), "n": int(np.isfinite(r).sum()),
                       "share_top10pct": float(np.nanmean(r >= 0.9))}
        del b
    # upper bound: leave-one-out own-class data mean vs other classes' full data means
    b = S.build(data, S.Config(**base))
    P = np.stack([m.proto for m in b.models])
    names = [m.name for m in b.models]
    pos = {n: i for i, n in enumerate(names)}
    rr, aa = [], []
    for i in idx:
        mates = ref & (moa == moa[i])
        mates[i] = False
        if mates.sum() == 0:
            continue
        sub = b.Z_open[mates]
        cnt = (~np.isnan(sub[..., 0])).sum(axis=0)
        loo = np.where(cnt[:, None] > 0, np.nansum(sub, axis=0) / np.maximum(cnt, 1)[:, None], np.nan)
        rr.append(own_rank(b.Z_open[i], loo, P, pos[moa[i]]))
        aa.append(act[i])
    rr, aa = np.array(rr), np.array(aa)
    res["own_data_loo"] = {"own_rank_mean": float(np.nanmean(rr)), "active_q4": float(np.nanmean(rr[aa >= 0.75])),
                           "weak": float(np.nanmean(rr[aa < 0.75])), "n": int(np.isfinite(rr).sum()),
                           "share_top10pct": float(np.nanmean(rr >= 0.9))}
    (HERE / "development" / "analogy.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    for k, v in main().items():
        print(f"{k:18s}", {x: round(y, 3) if isinstance(y, float) else y for x, y in v.items()})
