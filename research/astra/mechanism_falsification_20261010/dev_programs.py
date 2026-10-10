"""Discriminative test of the agent's gene programs on reference drugs (development, open tier).

For every reference drug d and every option o it was measured at, the cosine between its landmark
signature and each class's EMH unit program at o's time is computed (classes whose program is empty
are skipped). The drug's own-class program is ranked among all programs: the score is the fraction
of other classes' programs with a lower cosine (0.5 = chance), averaged over the drug's options.
Programs are the agent's specific gene claims (proximal and late lists), not its generic effects.

Controls: EMHs permuted across classes (seeded; keeps the agent's habits, removes specificity).
Strata: drug activity = mean over its options of the signature norm's percentile in the reference
norm distribution of that option (top quartile = "active").
Writes development/programs.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import knowledge as KN
import study as S

HERE = Path(__file__).resolve().parent


def activity(Xq: np.ndarray, Xref: np.ndarray) -> np.ndarray:
    """Mean over measured options of each query's norm percentile among reference norms at that option."""
    nq, nr = np.linalg.norm(Xq, axis=2), np.linalg.norm(Xref, axis=2)  # NaN where absent
    pct = np.full(nq.shape, np.nan)
    for j in range(nq.shape[1]):
        r = np.sort(nr[:, j][np.isfinite(nr[:, j])])
        ok = np.isfinite(nq[:, j])
        pct[ok, j] = np.searchsorted(r, nq[ok, j]) / max(len(r), 1)
    with np.errstate(invalid="ignore"):
        return np.nanmean(pct, axis=1)


def drug_activity(X: np.ndarray, ref: np.ndarray) -> np.ndarray:
    return activity(X, X[ref])


def own_rank(X, moa, idx, programs, classes, options):
    """Per drug: mean over options of the own program's rank fraction among all programs."""
    pos = {c: i for i, c in enumerate(classes)}
    P = {t: np.stack([programs[c][t] for c in classes]) for t in KN.TIMES}  # (C, G)
    out = np.full(len(idx), np.nan)
    for n, i in enumerate(idx):
        c = moa[i]
        if c not in pos:
            continue
        vals = []
        for j, o in enumerate(options):
            x = X[i, j]
            if np.isnan(x[0]):
                continue
            t = o.split("|")[1]
            cos = P[t] @ x / (np.linalg.norm(x) + 1e-12)
            own = cos[pos[c]]
            other = np.delete(cos, pos[c])
            vals.append(np.mean(other < own) + 0.5 * np.mean(other == own))
        if vals:
            out[n] = float(np.mean(vals))
    return out


def main() -> dict:
    data = S.load_tier("open")
    X, moa, role, options, genes = data["x"], data["moa"], data["role"], data["options"], data["genes"]
    ref = role == "reference"
    act = drug_activity(X, ref)
    idx = np.where(ref)[0]
    res = {"n_reference": int(len(idx))}
    rng = np.random.default_rng(20261010)
    for v in ("nolit", "lit", "lit_critic"):
        emhs = KN.load_emhs(HERE, v, S.all_classes(data["split"]))
        progs = {c: KN.programs(e, genes) for c, e in emhs.items()}
        classes = sorted(c for c, p in progs.items() if np.linalg.norm(p["24 h"]) > 0)
        r = own_rank(X, moa, idx, progs, classes, options)
        keys = list(classes)
        perm = rng.permutation(len(keys))
        progs_p = {keys[i]: progs[keys[perm[i]]] for i in range(len(keys))}
        rp = own_rank(X, moa, idx, progs_p, classes, options)
        ok = np.isfinite(r)
        a = act[idx]
        res[v] = {"n_classes_with_program": len(classes), "n_drugs": int(ok.sum()),
                  "own_rank_mean": float(np.nanmean(r)), "permuted_rank_mean": float(np.nanmean(rp)),
                  "own_rank_active_q4": float(np.nanmean(r[a >= 0.75])), "permuted_active_q4": float(np.nanmean(rp[a >= 0.75])),
                  "own_rank_inactive": float(np.nanmean(r[a < 0.5])), "n_active_q4": int(np.sum(ok & (a >= 0.75))),
                  "share_top10pct": float(np.nanmean(r >= 0.9)), "share_top10pct_permuted": float(np.nanmean(rp >= 0.9))}
        # per-class mean rank for the 20 most frequent classes among active drugs
        per = {}
        for c in sorted(set(moa[idx])):
            m = (moa[idx] == c) & ok
            if m.sum() >= 3:
                per[c] = (float(np.nanmean(r[m])), int(m.sum()), float(np.nanmean(a[m])))
        res[v]["per_class"] = dict(sorted(per.items(), key=lambda kv: -kv[1][2])[:30])
    (HERE / "development" / "programs.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main()
    for v in ("nolit", "lit", "lit_critic"):
        print(v, {k: (round(x, 3) if isinstance(x, float) else x) for k, x in r[v].items() if k != "per_class"})
    for c, x in r["lit"]["per_class"].items():
        print(f"  {c:45s} rank={x[0]:.2f} n={x[1]} act={x[2]:.2f}")
