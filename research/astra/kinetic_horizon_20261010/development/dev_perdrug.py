"""Development (15 dev lines): per-drug across-line concordance and active-drug restriction."""
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
sel = lambda X: X - np.nanmean(X, 0, keepdims=True)  # noqa: E731
L = H.load_late("development")
late_drugs = list(L["drugs"])
common = [d for d in late_drugs if d in E.drugs]
ej = np.array([E.drugs.index(d) for d in common]); lj = np.array([late_drugs.index(d) for d in common])
erow = np.array([keep.index(f) for f in dev])
S, K, G = sel(E.s24)[erow][:, ej], sel(E.k24)[erow][:, ej], sel(E.g24)[erow][:, ej]
Sraw = E.s24[erow][:, ej]
Y = L["primary_2p5"][:, lj]; Y2 = L["secondary_mean"][:, lj]
Yc = Y - np.nanmean(Y, 0, keepdims=True)


def r(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return np.corrcoef(a[ok], b[ok])[0, 1] if ok.sum() >= 5 and np.std(a[ok]) > 0 and np.std(b[ok]) > 0 else np.nan


out = {}
sd_late = np.nanstd(Y, 0)
sd_early = np.nanstd(Sraw, 0)
mean_late = np.nanmean(Y, 0)
order = np.argsort(-sd_late)
for name, X in (("s24", S), ("k24", K), ("g24", G)):
    rr = np.array([r(X[:, j], Y[:, j]) for j in range(len(common))])
    rr2 = np.array([r(X[:, j], Y2[:, j]) for j in range(len(common))])
    out[name] = {"mean_across_line_r_all": float(np.nanmean(rr)),
                 "mean_r_top30_late_sd": float(np.nanmean(rr[order[:30]])),
                 "mean_r_top30_late_sd_secondary": float(np.nanmean(rr2[order[:30]])),
                 "mean_r_top30_early_sd": float(np.nanmean(rr[np.argsort(-sd_early)[:30]]))}
# reliability of across-line pattern between screens, top-30 by late SD
rel = np.array([r(Y[:, j], L["secondary_2p5"][:, lj][:, j]) for j in range(len(common))])
out["primary_vs_secondary2p5_across_line_r_top30"] = float(np.nanmean(rel[order[:30]]))
out["primary_vs_secondary2p5_across_line_r_all"] = float(np.nanmean(rel))
# drug potency concordance (generic, across drugs): panel-mean early survival vs panel-mean late
out["generic_potency_r_s24_vs_late"] = r(np.nanmean(E.s24[:, ej], 0), mean_late)
out["generic_potency_r_k24_vs_late"] = r(np.nanmean(E.k24[:, ej], 0), mean_late)
out["generic_potency_r_g24_vs_late"] = r(np.nanmean(E.g24[:, ej], 0), mean_late)
out["top15_late_sd_drugs"] = [(common[j], round(float(sd_late[j]), 2), round(float(mean_late[j]), 2),
                               round(float(r(S[:, j], Y[:, j])), 2), round(float(r(K[:, j], Y[:, j])), 2)) for j in order[:15]]
print(json.dumps(out, indent=1, default=float))
(HERE / "dev_perdrug.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
