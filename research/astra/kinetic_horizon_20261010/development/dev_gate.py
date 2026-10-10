"""Development (15 dev lines): static baselines, basal transfer and oracle combination in the
across-line view (top-30 variable drugs), within-line restricted view, and drug-level potency."""
import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import horizon_data as H  # noqa: E402

A, P = H.A, H.P
sp = H.split(); dev = sp["development"]
keep, info = A.qualified_reference()
table = info["table"]
E = H.early_panel(keep)
H.DOSE = 0.5; E05 = H.early_panel(keep); H.DOSE = 5.0
L = H.load_late("development"); ld = list(L["drugs"])
erow = np.array([keep.index(f) for f in dev])
Y = L["primary_2p5"]
top = [ld[j] for j in np.argsort(-np.nanstd(Y, 0))[:30] if ld[j] in E.drugs]
cols_e = np.array([E.drugs.index(d) for d in top]); cols_l = np.array([ld.index(d) for d in top])
Yt = Y[:, cols_l]
g1b = []
for f in keep:
    rows = [v for (ff, lab, pl), v in table.items() if ff == f and lab == P.DMSO]
    n = sum(r["n"] for r in rows); g1b.append(sum(r["G1"] for r in rows) / n)
g1b = np.array(g1b); lg = np.log(g1b / (1 - g1b))
panel = A.attach_expression(A.phenotype_panel(keep, keep, table, info["names"]))
basal = panel.basal


def r(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return np.corrcoef(a[ok], b[ok])[0, 1] if ok.sum() >= 5 and np.std(a[ok]) > 0 and np.std(b[ok]) > 0 else np.nan


def across(Pm):  # mean over drugs of across-line r
    return float(np.nanmean([r(Pm[:, j], Yt[:, j]) for j in range(Yt.shape[1])]))


out = {"n_top": len(top)}
G = E.g24[erow][:, cols_e]
out["across_g24"] = across(G)
out["across_g24_0p5"] = across(E05.g24[erow][:, [E05.drugs.index(d) for d in top]])
# static: basal logit G1 (same value for all drugs, sign fit per drug -> use |r| fairly via LOO sign)
st = np.tile(lg[erow][:, None], (1, len(top)))
out["across_static_basal_logitG1"] = across(st)
# per-drug LOO-line regression of Y on [lg, lg^2] (static nonlinear) vs [lg, lg^2, g24]
def loo_pred(Xfun):
    Pm = np.full_like(Yt, np.nan)
    for j in range(len(top)):
        X = Xfun(j)
        for i in range(len(dev)):
            tr = np.array([t for t in range(len(dev)) if t != i and np.isfinite(Yt[t, j]) and np.isfinite(X[t]).all()])
            if len(tr) < 6 or not np.isfinite(X[i]).all():
                continue
            Xt = np.column_stack([np.ones(len(tr)), X[tr]])
            w = np.linalg.lstsq(Xt, Yt[tr, j], rcond=None)[0]
            Pm[i, j] = np.r_[1, X[i]] @ w
    return Pm
lgd = lg[erow]
out["across_loo_static_quad"] = across(loo_pred(lambda j: np.column_stack([lgd, lgd ** 2])))
out["across_loo_static_quad_plus_g24"] = across(loo_pred(lambda j: np.column_stack([lgd, lgd ** 2, G[:, j]])))
out["across_loo_g24_only"] = across(loo_pred(lambda j: G[:, j][:, None]))
# basal transfer of late across lines (within dev, LOO), several tau
for tau in (0.02, 0.1):
    Bp = np.full_like(Yt, np.nan)
    bd = basal[erow]
    for i in range(len(dev)):
        tr = np.array([t for t in range(len(dev)) if t != i])
        Bp[i] = A.kernel_prior(bd[i], bd[tr], Yt[tr], tau, 5)
    out[f"across_B_late_tau{tau}"] = across(Bp)
    z = lambda X: (X - np.nanmean(X, 0)) / np.nanstd(X, 0)  # noqa: E731  (standardize across lines per drug)
    out[f"across_B_late_tau{tau}_plus_g24"] = across(z(Bp) + z(G))
# within-line restricted to top drugs, selectivity form
Gs = (E.g24 - np.nanmean(E.g24, 0))[erow][:, cols_e]
Ys = Yt - np.nanmean(Yt, 0)
out["within_top_g24_sel"] = float(np.nanmean([r(Gs[i], Ys[i]) for i in range(len(dev))]))
Ks = (E.k24 - np.nanmean(E.k24, 0))[erow][:, cols_e]
out["within_top_k24_sel"] = float(np.nanmean([r(Ks[i], Ys[i]) for i in range(len(dev))]))
# drug-level potency: panel-mean early vs dev-mean late, all common drugs, both doses
common = [d for d in ld if d in E.drugs and d in E05.drugs]
lm = np.nanmean(Y[:, [ld.index(d) for d in common]], 0)
for name, M, drugs in (("k24_5", E.k24, E.drugs), ("s24_5", E.s24, E.drugs), ("g24_5", E.g24, E.drugs),
                       ("k24_0p5", E05.k24, E05.drugs), ("s24_0p5", E05.s24, E05.drugs)):
    out[f"potency_{name}"] = r(np.nanmean(M[:, [drugs.index(d) for d in common]], 0), lm)
# within-line raw (absolute late LFC), target's own early readouts vs generic early panel
Yr = Y[:, [ld.index(d) for d in common]]
ce = np.array([E.drugs.index(d) for d in common])
out["within_raw_own_k24"] = float(np.nanmean([r(E.k24[erow[i], ce], Yr[i]) for i in range(len(dev))]))
out["within_raw_panel_k24"] = float(np.nanmean([r(np.nanmean(E.k24[:, ce], 0), Yr[i]) for i in range(len(dev))]))
out["within_raw_own_s24"] = float(np.nanmean([r(E.s24[erow[i], ce], Yr[i]) for i in range(len(dev))]))
out["within_raw_generic_late_other_dev"] = float(np.nanmean([r(np.nanmean(np.delete(Yr, i, 0), 0), Yr[i]) for i in range(len(dev))]))
print(json.dumps(out, indent=1, default=float))
(HERE / "dev_gate.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
