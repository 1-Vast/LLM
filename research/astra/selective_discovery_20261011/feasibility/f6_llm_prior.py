"""Feasibility F6 (exploratory; exposed block-N compounds): is the LLM lineage prior informative?

Reads the cached ``agent_outputs/prior`` records (names + annotations, never outcomes) and scores, over
the 1,403 block-N compounds x 14 lineages:
* hit AUROC and average precision of the LLM probability, pooled and per lineage;
* the same for a leave-one-out class-mean selectivity lookup (an annotation baseline);
* on the 542 compounds with a masked record: named vs name-masked AUROC (memorisation check).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import world as WM  # noqa: E402
from llm_prior import slug  # noqa: E402


def auroc(score, y):
    from scipy.stats import rankdata
    ok = np.isfinite(score)
    s, y = score[ok], y[ok].astype(bool)
    if y.sum() == 0 or (~y).sum() == 0:
        return np.nan
    r = rankdata(s)
    return float((r[y].sum() - y.sum() * (y.sum() + 1) / 2) / (y.sum() * (~y).sum()))


def ap(score, y):
    ok = np.isfinite(score)
    s, y = score[ok], y[ok].astype(bool)
    o = np.argsort(-s)
    yy = y[o]
    prec = np.cumsum(yy) / (np.arange(len(yy)) + 1)
    return float((prec * yy).sum() / max(yy.sum(), 1))


def load(arm, brds, lineages):
    P = np.full((len(brds), len(lineages)), np.nan)
    for i, b in enumerate(brds):
        p = HERE.parent / "agent_outputs" / arm / f"{slug(b)}.json"
        if p.exists():
            r = json.loads(p.read_text(encoding="utf-8"))
            for t, T in enumerate(lineages):
                v = r["p"].get(T)
                if v is not None:
                    P[i, t] = v
    return P


def main():
    U = WM.build(include_new=False)
    H = U.hits()
    Pn = load("prior", U.brd, U.lineages)
    Pm = load("prior_masked", U.brd, U.lineages)
    # leave-one-out class-mean selectivity
    st = WM.Stack(U, ("klass",))
    allk = np.arange(len(U.brd))
    s_cls = st.source_preds(allk, allk, loo=True)["klass"][0]
    out = {"n_with_prior": int(np.isfinite(Pn[:, 0]).sum()), "n_hits": int(H.sum()),
           "pooled": {"llm_auroc": auroc(Pn.ravel(), H.ravel()), "llm_ap": ap(Pn.ravel(), H.ravel()),
                      "class_auroc": auroc(-s_cls.ravel(), H.ravel()), "class_ap": ap(-s_cls.ravel(), H.ravel()),
                      "base_rate": float(H.mean())},
           "per_lineage": {}}
    for t, T in enumerate(U.lineages):
        if H[:, t].sum() < 3:
            continue
        out["per_lineage"][T] = {"n_hits": int(H[:, t].sum()), "llm_auroc": auroc(Pn[:, t], H[:, t]),
                                 "class_auroc": auroc(-s_cls[:, t], H[:, t])}
    m = np.isfinite(Pm[:, 0])
    if m.any():
        out["masked_subset"] = {"n": int(m.sum()), "n_hits": int(H[m].sum()),
                                "named_auroc": auroc(Pn[m].ravel(), H[m].ravel()),
                                "masked_auroc": auroc(Pm[m].ravel(), H[m].ravel()),
                                "named_ap": ap(Pn[m].ravel(), H[m].ravel()), "masked_ap": ap(Pm[m].ravel(), H[m].ravel())}
    # calibration: mean predicted vs observed
    out["calibration"] = {"mean_p": float(np.nanmean(Pn)), "observed_rate": float(H.mean())}
    print(json.dumps(out, indent=1))
    (HERE / "f6_llm_prior.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
