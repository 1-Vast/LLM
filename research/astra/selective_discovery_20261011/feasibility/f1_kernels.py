"""Feasibility F1 (exploratory; exposed block-N compounds only): which transcriptional kernel should the
virtual cell use for phase-2 compounds?

Queries: the 542 block-N compounds that also have GSE70138 signatures (outcomes exposed).
References for each query (leave-one-out):
* native: the other 541 compounds via GSE70138 signatures (variants below);
* cross: the other 1,402 block-N compounds via GSE92742 signatures, on the 5 shared 24 h, 10 uM options;
* L18: block N's own kernel (GSE92742, 18 options); not available for new compounds, shown as context.

Scores per query: selective r (block N) over all lines, and, over (query, lineage) pairs, the AUROC and
top-1% precision of predicted lineage selectivity s_T for the exploratory hit definition.
Also: the cross-dataset identity check (rank of a compound's own GSE92742 signature among all
GSE92742 references, by its GSE70138 signature).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BLOCK = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(BLOCK))
sys.path.insert(0, str(ROOT / "research/astra/mechanism_routing_20261011"))
import extract as EX  # noqa: E402
import predictors as PR  # noqa: E402

SHARED = ["A375", "HA1E", "HT29", "MCF7", "PC3"]
K = 5


def mean_cos(Q, R, same=False):
    """Mean cosine over shared options. Q (nq, o, g), R (nr, o, g), NaN rows = absent."""
    hq = np.isfinite(Q[..., 0])
    hr = np.isfinite(R[..., 0])
    Qn = np.nan_to_num(Q) / np.maximum(np.linalg.norm(np.nan_to_num(Q), axis=2), 1e-12)[..., None]
    Rn = np.nan_to_num(R) / np.maximum(np.linalg.norm(np.nan_to_num(R), axis=2), 1e-12)[..., None]
    s = np.zeros((len(Q), len(R)), np.float32)
    c = np.zeros((len(Q), len(R)), np.float32)
    for o in range(Q.shape[1]):
        m = np.outer(hq[:, o], hr[:, o])
        s += np.where(m, Qn[:, o] @ Rn[:, o].T, 0)
        c += m
    out = np.where(c > 0, s / np.maximum(c, 1), np.nan)
    if same:
        np.fill_diagonal(out, np.nan)
    return out


def concat_cos(Q, R, same=False):
    """Cosine of concatenated options, over options both have (strong options weigh more)."""
    hq = np.isfinite(Q[..., 0]).astype(np.float32)
    hr = np.isfinite(R[..., 0]).astype(np.float32)
    Qz, Rz = np.nan_to_num(Q), np.nan_to_num(R)
    dot = np.einsum("aog,bog->ab", Qz, Rz)
    nq2 = (Qz ** 2).sum(2)  # (nq, o)
    nr2 = (Rz ** 2).sum(2)
    den = np.sqrt((nq2 @ hr.T) * (hq @ nr2.T))
    out = np.where(den > 0, dot / np.maximum(den, 1e-12), np.nan)
    if same:
        np.fill_diagonal(out, np.nan)
    return out


def knn_pred(S, Y, k=K):
    """Rows of S: queries x references; Y: references x lines. Similarity-weighted mean of top k."""
    out = np.full((S.shape[0], Y.shape[1]), np.nan)
    for i in range(S.shape[0]):
        s = S[i]
        ok = np.isfinite(s)
        if not ok.any():
            continue
        idx = np.argsort(-np.where(ok, s, -np.inf))[:k]
        w = np.clip(s[idx], 0, None)
        if w.sum() <= 0:
            w = np.ones_like(w)
        out[i] = np.nansum(Y[idx] * w[:, None], 0) / w.sum()
    return out


def main():
    t0 = time.time()
    W = PR.load_world("sealed")
    name_idx = {d: i for i, d in enumerate(W.drug)}
    L = EX.load_l1000()
    dev = L["role"] == "blockn"
    q_names = L["blockn_name"][dev]
    qi = np.array([name_idx[n] for n in q_names])            # positions in W
    X2 = L["x"][dev].astype(np.float32)                       # (542, 7, 6, g)
    lines2 = list(L["line"])
    doses = list(L["dose"])
    P = W.P.astype(float)
    G = np.nanmean(P, 0)
    info = pd.read_csv(ROOT / "data/external/prism_19q4/raw/primary-screen-cell-line-info.csv").set_index("row_name")
    tissue = np.array([info.at[l, "primary_tissue"] if l in info.index else "na" for l in W.lines])
    lineages = [t for t, n in pd.Series(tissue).value_counts().items() if n >= 20 and t != "na"]

    def opt(lines, ds):
        return X2[:, [lines2.index(l) for l in lines]][:, :, [doses.index(d) for d in ds]].reshape(len(X2), -1, X2.shape[-1])

    variants = {
        "P2_d10": mean_cos(opt(lines2, ["10.0 um"]), opt(lines2, ["10.0 um"]), True),
        "P2_d3": mean_cos(opt(lines2, ["3.33 um"]), opt(lines2, ["3.33 um"]), True),
        "P2_d1-10": mean_cos(opt(lines2, ["1.11 um", "3.33 um", "10.0 um"]), opt(lines2, ["1.11 um", "3.33 um", "10.0 um"]), True),
        "P2_all": mean_cos(opt(lines2, doses), opt(lines2, doses), True),
        "P2_cat_d1-10": concat_cos(opt(lines2, ["1.11 um", "3.33 um", "10.0 um"]), opt(lines2, ["1.11 um", "3.33 um", "10.0 um"]), True),
        "P2_cat_all": concat_cos(opt(lines2, doses), opt(lines2, doses), True),
        "P2_shared5_d10": mean_cos(opt(SHARED, ["10.0 um"]), opt(SHARED, ["10.0 um"]), True),
    }
    print("native kernels", round(time.time() - t0, 1), flush=True)
    # cross-dataset: query phase-2 shared5@10uM vs block-N GSE92742 24 h options of the same lines
    p1_opts = [list(W.options).index(f"{l}|24 h") for l in SHARED]
    Xq = opt(SHARED, ["10.0 um"])
    Xr = np.where(W.l1000_have[:, p1_opts][..., None], W.Xf[:, p1_opts], np.nan).astype(np.float32)
    cross = mean_cos(Xq, Xr)
    cross[np.arange(len(qi)), qi] = np.nan                    # leave the query itself out
    # identity check: rank of own GSE92742 signature
    cross_id = mean_cos(Xq, Xr)
    own = cross_id[np.arange(len(qi)), qi]
    rank = np.array([np.sum(cross_id[r] > own[r]) for r in range(len(qi))])
    ident = {"median_rank_of_self": float(np.median(rank)), "top1": float(np.mean(rank == 0)),
             "top10": float(np.mean(rank < 10)), "n": int(np.isfinite(own).sum()), "median_self_cos": float(np.nanmedian(own))}
    print("identity", ident, flush=True)
    # L18 block N kernel (query vs all other block-N compounds)
    X18 = np.where(W.l1000_have[..., None], W.Xf, np.nan).astype(np.float32)
    l18 = mean_cos(X18[qi], X18)
    l18[np.arange(len(qi)), qi] = np.nan
    # predictions
    preds = {}
    Pq = P[qi]
    for k, S in variants.items():
        preds[k] = knn_pred(S, Pq)
    preds["cross5"] = knn_pred(cross, P)
    preds["L18_blockN"] = knn_pred(l18, P)
    # combined: native P2_cat_all + cross5, z-averaged selective profiles
    preds["G_only"] = np.tile(G, (len(qi), 1))
    res = {"identity": ident, "variants": {}}
    sT_true = {T: np.nanmean(Pq[:, tissue == T], 1) - np.nanmean(Pq[:, tissue != T], 1) for T in lineages}
    mT_true = {T: np.nanmean(Pq[:, tissue == T], 1) for T in lineages}
    hit = np.stack([(sT_true[T] <= -0.5) & (mT_true[T] <= -0.5) for T in lineages], 1)
    killers = np.nanmean(Pq < -1, 1) >= 0.05
    for k, pr in preds.items():
        r = np.array([PR.selective_r(pr[i], Pq[i], G) for i in range(len(qi))])
        sp = np.stack([np.nanmean(pr[:, tissue == T], 1) - np.nanmean(pr[:, tissue != T], 1) for T in lineages], 1)
        y = hit.ravel()
        s = -sp.ravel()
        ok = np.isfinite(s)
        from scipy.stats import rankdata
        rk = rankdata(s[ok])
        pos = y[ok]
        auc = (rk[pos].sum() - pos.sum() * (pos.sum() + 1) / 2) / (pos.sum() * (~pos).sum())
        top = np.argsort(-np.where(ok, s, -np.inf))[: max(1, int(0.01 * len(s)))]
        res["variants"][k] = {"selective_r_all": float(np.nanmean(r)), "selective_r_killers": float(np.nanmean(r[killers])),
                              "hit_auroc": float(auc), "hit_prec_top1pct": float(y[top].mean()), "n_hits": int(y.sum())}
        print(k, res["variants"][k], flush=True)
    res["seconds"] = round(time.time() - t0, 1)
    (HERE / "f1_kernels.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
