"""Secondary analysis to PLAN_P1 (written before REPRO.json was read): cross-half variance decomposition of Delta.

Components per (side, drug pair), estimated in each half and covaried across halves:
  pair     - mean Delta of the pair (what an annotated-equivalence or pair-effect model can know)
  partner  - partner-specific deviation a(pair, B)
  context  - line-specific deviation b(pair, c)
  cond     - partner x context residual
Reproducible variance of a component = covariance of its half-1 and half-2 estimates across units. Composite anchors
(pre-combined 'X|Y' drugs) are excluded. Writes DECOMP.json (write-once).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import cas_data as D
import repro as R

HERE = Path(__file__).resolve().parent
OUT = HERE / "DECOMP.json"


def components(g, col):
    y = g[col].to_numpy()
    m = y.mean()
    pi = pd.factorize(g.partner)[0]
    li = pd.factorize(g.line)[0]
    a = np.zeros(pi.max() + 1)
    b = np.zeros(li.max() + 1)
    for _ in range(50):
        a = np.bincount(pi, y - m - b[li]) / np.bincount(pi)
        b = np.bincount(li, y - m - a[pi]) / np.bincount(li)
    return np.full(len(y), m), a[pi], b[li], y - m - a[pi] - b[li]


def decompose(t):
    parts = {k: ([], []) for k in ("pair", "partner", "context", "cond")}
    for _, g in t.groupby(["side", "A", "A2"]):
        if g.partner.nunique() < 2 or g.line.nunique() < 2:
            continue
        c1, c2 = components(g, "d1"), components(g, "d2")
        for k, x, y in zip(parts, c1, c2):
            parts[k][0].append(x)
            parts[k][1].append(y)
    out = {}
    for k, (x, y) in parts.items():
        x, y = np.concatenate(x), np.concatenate(y)
        # pair component: covariance around the grand mean (raw second moment of signed pair effects)
        out[k] = float(np.mean(x * y)) if k == "pair" else float(np.cov(x, y)[0, 1])
    out["total"] = sum(out[k] for k in ("pair", "partner", "context", "cond"))
    out["n"] = int(len(x))
    return out


def main():
    if OUT.exists():
        raise SystemExit("DECOMP.json exists (write-once)")
    R.N_BOOT = 500
    df = R.halves(D.full("original"))
    df = df[~df.ANCHOR_NAME.str.contains(r"\|") & ~df.LIBRARY_NAME.str.contains(r"\|")]
    census = json.loads((HERE / "CENSUS.json").read_text(encoding="utf-8"))
    cls = R.families(census["drugs"])
    res = {}
    for ep in ("SYNERGY_DELTA_AUC", "SYNERGY_OBS_AUC"):
        t = R.unit_table(df, cls, ep)
        res[ep] = {}
        for k in ("target", "pathway", "unrelated"):
            for side in ("library", "anchor", "both"):
                sub = t[(t.cls == k) & ((t.side == side) | (side == "both"))].reset_index(drop=True)
                if len(sub) < 50:
                    continue
                d = decompose(sub)
                d["reliability"] = R.stats(sub)
                d["noise_var_half"] = float(np.var(sub.d1 - sub.d2) / 2)
                if k == "target" and side == "both":
                    d["cond_ci_line"] = R.boot(sub, lambda x: decompose(x), "cond", "line")
                    d["pair_ci_line"] = R.boot(sub, lambda x: decompose(x), "pair", "line")
                res[ep][f"{k}/{side}"] = d
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8", newline="\n")
    for ep, r in res.items():
        print("==", ep)
        for k, d in r.items():
            print(f"  {k:20s} n={d['n']:6d} r={d['reliability']['r']:.3f} pair={d['pair']:.5f} partner={d['partner']:.5f} "
                  f"context={d['context']:.5f} cond={d['cond']:.5f} noise/half={d['noise_var_half']:.5f}",
                  {x: d[x] for x in d if x.endswith("_ci_line")})


if __name__ == "__main__":
    main()
