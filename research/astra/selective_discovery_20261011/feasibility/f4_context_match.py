"""Feasibility F4 (exploratory; exposed block-N compounds with GSE70138 signatures).

F2 showed the virtual cell wins for skin, gastric and uterus and loses for esophagus and upper
aerodigestive. Hypothesis: transcriptional transfer reports a lineage's selective vulnerability
when the L1000 panel contains a context that shares it. A375 is a BRAF V600E melanoma line; no
panel line is a squamous EGFR-dependent line.

Test: for each lineage T and each single L1000 line (all six doses concatenated), the hit AUROC of
kNN transfer (k=5, leave-one-out over the 542 compounds), against the all-line kernel.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import extract as EX  # noqa: E402
import world as WM  # noqa: E402


def auroc(score, y):
    from scipy.stats import rankdata
    ok = np.isfinite(score)
    s, y = score[ok], y[ok]
    if y.sum() == 0 or (~y).sum() == 0:
        return np.nan
    r = rankdata(s)
    return float((r[y].sum() - y.sum() * (y.sum() + 1) / 2) / (y.sum() * (~y).sum()))


def main():
    U = WM.build(include_new=False)
    L = EX.load_l1000()
    idx = np.where(U.has_p2)[0]
    l_pos = {b: i for i, b in enumerate(L["brd"])}
    X = np.stack([L["x"][l_pos[b]].astype(np.float32) for b in U.brd[idx]])     # (n, 7, 6, g)
    H = U.hits()[idx]
    Y = U.P[idx]
    res = {}
    kernels = {"all": WM.concat_cos(X.reshape(len(idx), -1, X.shape[-1]), X.reshape(len(idx), -1, X.shape[-1]))}
    for j, line in enumerate(L["line"]):
        kernels[str(line)] = WM.concat_cos(X[:, j], X[:, j])
    for name, S in kernels.items():
        S = S.copy()
        np.fill_diagonal(S, np.nan)
        prof, _ = WM.knn_profiles(S, Y)
        s, m = U.selectivity(prof)
        res[name] = {T: auroc(-s[:, t], H[:, t]) for t, T in enumerate(U.lineages)}
    lin = [T for t, T in enumerate(U.lineages) if H[:, t].sum() >= 3]
    print("lineage".ljust(24), " ".join(k[:6].rjust(6) for k in kernels), " n_hits")
    for T in lin:
        t = U.lineages.index(T)
        print(T[:24].ljust(24), " ".join(f"{res[k][T]:.3f}".rjust(6) for k in kernels), int(H[:, t].sum()))
    (HERE / "f4_context_match.json").write_text(json.dumps({"auroc": res, "n_hits": {T: int(H[:, U.lineages.index(T)].sum())
                                                                                      for T in U.lineages}}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
