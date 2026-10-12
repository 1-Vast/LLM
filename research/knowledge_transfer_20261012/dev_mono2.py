"""Development comparator on the 1,000-reference atlas: one ridge per line on knowledge features.

Regime B (never profiled) active queries of ``dev2_routes``. The monolithic prediction is scored raw
and inside the same decomposition as RKT (generic share gamma plus its specific part at the
out-of-fold mean specific cosine), so the comparison isolates the routing and certificates.
"""
import json

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import RidgeCV

import rkt
from dev_common import CACHE, N_FOLDS, fold_of, load_phase1, phase1_knowledge
from dev_routes2 import N_REF, h
from pool import perp


def monolithic(Y, fps, know, ref, query_rows, lines):
    """Per-line ridge on SVD(Morgan, 128) + SVD(knowledge, 64), fitted on references."""
    svd_f = TruncatedSVD(128, random_state=0).fit(fps[ref].astype(np.float32))
    svd_k = TruncatedSVD(64, random_state=0).fit(know[ref].astype(np.float32))
    X = np.concatenate([svd_f.transform(fps.astype(np.float32)), svd_k.transform(know.astype(np.float32))], 1)
    mu = np.nanmean(np.where(ref[:, None, None], Y, np.nan), 0)
    pred = np.zeros((len(query_rows), Y.shape[2]))
    for T in np.unique(lines):
        tr = ref & np.isfinite(Y[:, T, 0])
        m = RidgeCV(alphas=np.logspace(-1, 4, 11)).fit(X[tr], Y[tr, T] - mu[T])
        sel = lines == T
        pred[sel] = m.predict(X[query_rows[sel]])
    return pred


def main():
    zz = load_phase1(); Y = zz["cp"].astype(np.float64)
    records, fps, know, vocab, targets = phase1_knowledge()
    keys = list(zz["compound"]); folds = np.array([fold_of(k) for k in keys])
    nlines = np.isfinite(Y[..., 0]).sum(1)
    z = dict(np.load(CACHE / "dev2_routes.npz"))
    B = z["regime"] == "B"
    pred = np.zeros((int(B.sum()), Y.shape[2])); rows = np.flatnonzero(B)
    for f in range(N_FOLDS):
        pool = sorted(np.flatnonzero((folds != f) & (nlines >= 6)), key=lambda i: h(f"ref{f}:{keys[i]}"))
        ref = np.zeros(len(keys), bool); ref[pool[:N_REF]] = True
        sel = z["fold"][rows] == f
        pred[sel] = monolithic(Y, fps, know, ref, z["comp"][rows[sel]], z["line"][rows[sel]])
        print("fold", f, flush=True)
    truth = z["truth"][rows].astype(np.float64); act = z["active"][rows]
    G = z["G_table"][z["fold"][rows], z["line"][rows]].astype(np.float64)
    gam = z["gammas"][z["fold"][rows]]
    spec = rkt.centred_cosine(perp(pred, G), perp(truth, G))
    res = {"n_active": int(act.sum()), "mono_raw_centred": float(rkt.centred_cosine(pred[act], truth[act]).mean()),
           "mono_specific": float(spec[act].mean())}
    dec = np.zeros(len(rows))
    for f in range(N_FOLDS):
        te = z["fold"][rows] == f
        rho0 = float(np.clip(spec[act & ~te].mean(), 0, 0.95))
        d = rkt.unit_rows(gam[te, None] * G[te] + rho0 * np.sqrt(1 - gam[te, None] ** 2) * rkt.unit_rows(perp(pred[te], G[te])))
        dec[te] = rkt.centred_cosine(d, truth[te])
    res["mono_decomposed_centred"] = float(dec[act].mean())
    res["generic_centred"] = float(rkt.centred_cosine(G[act], truth[act]).mean())
    print(json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in res.items()}, indent=1))
    (CACHE / "dev_mono2_summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
