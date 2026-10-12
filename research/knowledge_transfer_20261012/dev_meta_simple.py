"""Development check: NumPy-only meta-models (ridge on support features + isotonic) vs gradient boosting."""
import json
import numpy as np
from scipy.stats import spearmanr
import rkt
from dev_common import CACHE, load_phase1, vehicle_thresholds
from pool import SPECIFIC_ROUTES, perp, route_features
from dev_pool import own_activity

def pava(x, y):
    o = np.argsort(x); xs, ys = x[o], y[o].astype(float)
    w = np.ones(len(ys)); vals = list(ys); wts = list(w); idx = [[i] for i in range(len(ys))]
    i = 0
    v, ww, blocks = [], [], []
    for k in range(len(ys)):
        v.append(ys[k]); ww.append(1.0); blocks.append(1)
        while len(v) > 1 and v[-2] > v[-1]:
            nv = (v[-2]*ww[-2] + v[-1]*ww[-1])/(ww[-2]+ww[-1]); nw = ww[-2]+ww[-1]; nb = blocks[-2]+blocks[-1]
            v = v[:-2]+[nv]; ww = ww[:-2]+[nw]; blocks = blocks[:-2]+[nb]
    fit = np.repeat(v, blocks)
    return xs, fit

class Iso:
    def fit(self, x, y):
        self.x, self.y = pava(x, y); return self
    def predict(self, x):
        return np.interp(x, self.x, self.y)

def ridge(X, y, lam=1.0):
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Xs = (X - mu) / sd
    A = Xs.T @ Xs + lam * len(X) * 1e-3 * np.eye(X.shape[1])
    b = np.linalg.solve(A, Xs.T @ (y - y.mean()))
    return lambda Z: ((Z - mu) / sd) @ b + y.mean()

zz = load_phase1(); Y = zz["cp"].astype(np.float64); thr = vehicle_thresholds(zz)
z = dict(np.load(CACHE / "dev_routes.npz"))
G = rkt.unit_rows(np.load(CACHE / "dev_generic.npy").astype(np.float64))
truth = z["truth"].astype(np.float64); tperp = perp(truth, G); act = z["active"]
oa = own_activity(z, Y, thr)
av = {r: z[f"av_{r}"] for r in SPECIFIC_ROUTES}; sup = {r: z[f"sup_{r}"] for r in SPECIFIC_ROUTES}
preds = {r: z[f"pred_{r}"].astype(np.float64) for r in SPECIFIC_ROUTES}
spec = {r: np.where(av[r], rkt.centred_cosine(perp(preds[r], G), tperp), np.nan) for r in SPECIFIC_ROUTES}
folds = z["fold"]
hgb = np.load(CACHE / "dev_pool.npz")
res = {}
rho_simple = {r: np.zeros(len(truth)) for r in SPECIFIC_ROUTES}
for r in SPECIFIC_ROUTES:
    feats = np.concatenate([sup[r], oa], 1)
    for f in range(5):
        tr = (folds != f) & av[r] & act; te = (folds == f) & av[r]
        lin = ridge(feats[tr], spec[r][tr])
        iso = Iso().fit(lin(feats[tr]), spec[r][tr])
        rho_simple[r][te] = iso.predict(lin(feats[te]))
    m = av[r] & act
    res[r] = {"spearman_simple": round(float(spearmanr(rho_simple[r][m], spec[r][m]).statistic), 4),
              "spearman_hgb": round(float(spearmanr(hgb[f"rho_{r}"][m], spec[r][m]).statistic), 4)}
print(json.dumps(res, indent=1))
