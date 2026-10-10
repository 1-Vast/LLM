"""Development analysis on the 15 development lines only (confirmation and held-out PRISM sealed).

D1 late-endpoint reliability (PRISM primary vs secondary at 2.5 uM, independent screens);
D2 univariate early -> late association; D3 leave-one-dev-line-out bridges; D4 basal transfer of
the late endpoint; D5 routing through a basal forecast of the early state; D6 combinations.
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import horizon_data as H  # noqa: E402

A = H.A
sp = H.split()
dev = sp["development"]
keep, info = A.qualified_reference()
E = H.early_panel(keep)
ref_idx = np.arange(len(keep))
sel = lambda X: X - np.nanmean(X[ref_idx], 0, keepdims=True)  # noqa: E731
s_sel, k_sel, g_sel = sel(E.s24), sel(E.k24), sel(E.g24)
L = H.load_late("development")
late_drugs = list(L["drugs"])
common = [d for d in late_drugs if d in E.drugs]
ej = np.array([E.drugs.index(d) for d in common])
lj = np.array([late_drugs.index(d) for d in common])
erow = np.array([keep.index(f) for f in dev])


def loo_center(Y):
    out = np.full_like(Y, np.nan)
    for i in range(len(Y)):
        others = np.delete(np.arange(len(Y)), i)
        out[i] = Y[i] - np.nanmean(Y[others], 0)
    return out


late = {k: loo_center(L[k][:, lj]) for k in ("primary_2p5", "secondary_2p5", "secondary_mean")}
Y = late["primary_2p5"]
S, K, G = s_sel[erow][:, ej], k_sel[erow][:, ej], g_sel[erow][:, ej]
out = {"n_dev_lines": len(dev), "n_common_drugs": len(common),
       "finite_primary": int(np.isfinite(Y).sum())}
mr = lambda P, O: float(np.nanmean([A.within_r(P[i], O[i]) for i in range(len(O))]))  # noqa: E731
lines_r = lambda P, O: [round(A.within_r(P[i], O[i]), 3) for i in range(len(O))]  # noqa: E731
# D1 reliability
out["D1_primary_vs_secondary2p5"] = mr(late["secondary_2p5"], Y)
out["D1_primary_vs_secondary_mean"] = mr(late["secondary_mean"], Y)
out["D1_secondary2p5_vs_mean"] = mr(late["secondary_mean"], late["secondary_2p5"])
# D2 univariate
for name, X in (("s24", S), ("k24", K), ("g24", G), ("abs_g24", np.abs(G))):
    out[f"D2_r_{name}"] = mr(X, Y)
    out[f"D2_r_{name}_secondary_mean"] = mr(X, late["secondary_mean"])
# D3 bridges, leave-one-dev-line-out OLS without intercept on centred features
feats = {"s": [S], "k": [K], "g": [G], "sk": [S, K], "skg": [S, K, G]}
out["D3"] = {}
for name, Xs in feats.items():
    pred = np.full_like(Y, np.nan)
    coefs = []
    for i in range(len(dev)):
        tr = [t for t in range(len(dev)) if t != i]
        Xtr = np.column_stack([X[tr].ravel() for X in Xs])
        ytr = Y[tr].ravel()
        ok = np.isfinite(Xtr).all(1) & np.isfinite(ytr)
        w = np.linalg.lstsq(Xtr[ok], ytr[ok], rcond=None)[0]
        coefs.append(w.tolist())
        Xi = np.column_stack([X[i] for X in Xs])
        pred[i] = Xi @ w
    out["D3"][name] = {"mean_r": mr(pred, Y), "lines": lines_r(pred, Y), "coef_mean": np.mean(coefs, 0).round(4).tolist()}
    if name == "sk":
        R_dyn = pred
# D4 basal transfer of the late endpoint (other dev lines only)
panel = A.phenotype_panel(keep, keep, info["table"], info["names"])
panel = A.attach_expression(panel)
basal = panel.basal[erow]
out["D4"] = {}
best = None
for tau in (0.02, 0.05, 0.1):
    for m in (3, 5, 10, 14):
        pred = np.full_like(Y, np.nan)
        for i in range(len(dev)):
            tr = np.array([t for t in range(len(dev)) if t != i])
            pred[i] = A.kernel_prior(basal[i], basal[tr], Y[tr], tau, m)
        r = mr(pred, Y)
        out["D4"][f"tau{tau}_m{m}"] = round(r, 4)
        if best is None or r > best[0]:
            best = (r, tau, m, pred)
B_late = best[3]
out["D4_best"] = {"r": best[0], "tau": best[1], "top_m": best[2], "lines": lines_r(B_late, Y)}
# D5 forecast the early state from basal (all other 39 reference lines' Tahoe), then bridge
basal_all = panel.basal
coef = np.array(out["D3"]["sk"]["coef_mean"])
pred = np.full_like(Y, np.nan)
for ii, i in enumerate(erow):
    tr = np.array([t for t in range(len(keep)) if t != i])
    Sf = A.kernel_prior(basal_all[i], basal_all[tr], s_sel[tr], 0.1, 10)[ej]
    Kf = A.kernel_prior(basal_all[i], basal_all[tr], k_sel[tr], 0.1, 10)[ej]
    pred[ii] = coef[0] * Sf + coef[1] * Kf
B_dyn = pred
out["D5_B_dyn_r"] = mr(B_dyn, Y)
# D6 combinations (z-score within line, equal weights)
z = lambda X: (X - np.nanmean(X, 1, keepdims=True)) / np.nanstd(X, 1, keepdims=True)  # noqa: E731
out["D6_Rdyn_plus_Blate"] = mr(z(R_dyn) + z(B_late), Y)
out["D6_Bdyn_plus_Blate"] = mr(z(B_dyn) + z(B_late), Y)
out["D6_Rdyn_r"] = mr(R_dyn, Y)
out["D6_lines_Rdyn_plus_Blate"] = lines_r(z(R_dyn) + z(B_late), Y)
print(json.dumps(out, indent=1))
(HERE / "dev_horizon.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
