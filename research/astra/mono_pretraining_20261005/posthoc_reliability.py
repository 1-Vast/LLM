"""POST HOC (not registered): how much of the within-line residual is reproducible across the two orientations?

File summary
- Path: research/astra/mono_pretraining_20261005/posthoc_reliability.py
- Purpose: bound what any context model could explain. For each HD line and pair the two orientations are two
  physical experiments (anchor S titrating V; anchor V titrating S). After removing the leave-one-line-out pair
  prior and the line mean, the correlation between the two orientations' residuals measures the share of the
  line x pair residual that reproduces; a model cannot systematically explain more than that reproducible part.
- Core points: HD lines only; labelled POST HOC; orientation reproducibility includes any true line x pair
  interaction shared by both orientations and any shared noise (e.g. same line, same day effects are NOT shared
  across orientations because plates are disjoint).
- Interfaces: `main`.
"""
from __future__ import annotations

import numpy as np

from research.astra.confirmation_campaign_20261004.design import campaign as c

from . import common as cm
from .run_s2 import setup


def main():
    S = setup()
    out = {}
    allr = []
    for tissue, T in S["tissues"].items():
        hd = sorted(S["split"][tissue]["HD"])
        rs, rv, ys, yv = [], [], [], []
        for sidm in hd:
            Hh = c.restrict(T, [s for s in hd if s != sidm])
            r = np.flatnonzero(T.c == T.lines.index(sidm))
            prior = c.history_quantities(Hh, "SV", T.pid[r])["S_both"]
            a = T.arrays["SV"]
            x, y = a["y_s"][r] - prior, a["y_v"][r] - prior
            rs.append(x - x.mean()); rv.append(y - y.mean())
            ys.append(a["y_s"][r] - a["y_s"][r].mean()); yv.append(a["y_v"][r] - a["y_v"][r].mean())
        rs, rv, ys, yv = map(np.concatenate, (rs, rv, ys, yv))
        out[tissue] = dict(n=int(len(rs)), corr_residual_orientations=float(np.corrcoef(rs, rv)[0, 1]),
                           corr_raw_within_line_orientations=float(np.corrcoef(ys, yv)[0, 1]),
                           sd_residual=float(np.sqrt((rs.var() + rv.var()) / 2)),
                           sd_raw_within_line=float(np.sqrt((ys.var() + yv.var()) / 2)))
        allr.append((rs, rv))
    rs, rv = (np.concatenate([a[i] for a in allr]) for i in (0, 1))
    out["pooled"] = dict(corr_residual_orientations=float(np.corrcoef(rs, rv)[0, 1]), n=int(len(rs)))
    out["note"] = "POST HOC, HD only, full-HD LOLO pair prior; corr^2 ~ upper bound of residual variance share explainable"
    cm.dump(cm.RESULTS / "posthoc_reliability.json", out)
    print(out)


if __name__ == "__main__":
    main()
