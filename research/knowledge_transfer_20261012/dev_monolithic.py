"""Development comparator: one ridge model per line on concatenated knowledge features (PRESAGE-linear style).

Features: Morgan bits and knowledge tokens, each reduced by truncated SVD fitted on the reference
compounds of the fold. Scored on regime B (never-profiled) active queries against the routed pool.
"""
import json
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import RidgeCV
import rkt
from dev_common import CACHE, load_phase1, phase1_knowledge, fold_of
from pool import perp

zz = load_phase1(); Y = zz["cp"].astype(np.float64)
records, fps, know, vocab, targets = phase1_knowledge()
keys = list(zz["compound"]); folds = np.array([fold_of(k) for k in keys])
z = np.load(CACHE / "dev_routes.npz")
G = rkt.unit_rows(np.load(CACHE / "dev_generic.npy").astype(np.float64))
pool = np.load(CACHE / "dev_pool.npz")
truth = z["truth"].astype(np.float64); act = z["active"]
B = (z["regime"] == "B")
pred = np.zeros_like(truth)
for f in range(5):
    ref = folds != f
    svd_f = TruncatedSVD(128, random_state=0).fit(fps[ref].astype(np.float32))
    svd_k = TruncatedSVD(64, random_state=0).fit(know[ref].astype(np.float32))
    X = np.concatenate([svd_f.transform(fps.astype(np.float32)), svd_k.transform(know.astype(np.float32))], 1)
    mu = np.nanmean(np.where(ref[:, None, None], Y, np.nan), 0)
    for T in range(Y.shape[1]):
        tr = ref & np.isfinite(Y[:, T, 0])
        m = RidgeCV(alphas=np.logspace(-1, 4, 11)).fit(X[tr], Y[tr, T] - mu[T])
        sel = B & (z["fold"] == f) & (z["line"] == T)
        pred[sel] = m.predict(X[z["comp"][sel]])
m = B & act
spec_mono = rkt.centred_cosine(perp(pred[m], G[m]), perp(truth[m], G[m]))
gamma = 0.4302
s = pool["s"].astype(np.float64)
spec_pool = rkt.centred_cosine(s[m], perp(truth[m], G[m]))
# monolithic in the same decomposition: generic + its specific part at the pooled rho
cc_mono_raw = rkt.centred_cosine(pred[m], truth[m])
res = {"n_active_B": int(m.sum()), "mono_specific": round(float(spec_mono.mean()), 4), "pool_specific": round(float(spec_pool.mean()), 4),
       "mono_centred_raw": round(float(cc_mono_raw.mean()), 4)}
print(json.dumps(res, indent=1))
