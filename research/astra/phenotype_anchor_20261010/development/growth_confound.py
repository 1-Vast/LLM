"""Development (reference-only): is survival selectivity a rank-1 growth-rate x drug-potency interaction?"""
import sys, json, numpy as np
sys.path.insert(0, ".")
import analysis as A, phenotypes as P
keep, info = A.qualified_reference()
panel = A.phenotype_panel(keep, keep, info["table"], info["names"])
doses = np.array([A.dose_of(l) for l in panel.labels]); c5 = np.flatnonzero(doses == 5.0)
S = panel.survival[:, c5]
ok = ~np.isnan(S).any(0); S = S[:, ok]
I = S - S.mean(0, keepdims=True) - S.mean(1, keepdims=True) + S.mean()
u, s, vt = np.linalg.svd(I, full_matrices=False)
print("5uM drugs", S.shape[1], "interaction variance share of top components:", (s[:5]**2 / (s**2).sum()).round(3))
line_f = u[:, 0] * s[0]; drug_f = vt[0]
# DMSO cycling fraction per line (pooled over plates)
cyc = []
for f in keep:
    rows = [v for (ff, lab, pl), v in info["table"].items() if ff == f and lab == P.DMSO]
    n = sum(r["n"] for r in rows); cyc.append(sum(r["S"] + r["G2M"] for r in rows) / n)
cyc = np.array(cyc)
generic = S.mean(0)
print("corr(line factor, DMSO S+G2M fraction) =", np.corrcoef(line_f, cyc)[0, 1].round(3))
print("corr(drug factor, generic panel survival) =", np.corrcoef(drug_f, generic)[0, 1].round(3))
# replicate reliability of the residual after removing rank-1 (using 2-plate labels via phenotype_frame)
frame = P.phenotype_frame(info["table"], keep, keep)
from collections import defaultdict
byl = defaultdict(set)
for (f, lab, pl) in frame: byl[lab].add(pl)
lab5 = [panel.labels[c] for c in c5[ok]]
reps = [l for l in lab5 if len(byl[l]) == 2 and all((f, l, pl) in frame for f in keep for pl in byl[l])]
X = np.array([[frame[(f, l, sorted(byl[l])[0])]["survival"] for f in keep] for l in reps])
Y = np.array([[frame[(f, l, sorted(byl[l])[1])]["survival"] for f in keep] for l in reps])
def inter(M): return M - M.mean(1, keepdims=True) - M.mean(0, keepdims=True) + M.mean()
def strip(M):
    Mi = inter(M); idx = [lab5.index(l) for l in reps]; d = drug_f[idx]
    beta = (Mi * d[:, None]).sum(0) / (d ** 2).sum()  # per-line loading on the reference drug factor
    return Mi - d[:, None] * beta[None, :]
print("replicate r interaction:", np.corrcoef(inter(X).ravel(), inter(Y).ravel())[0, 1].round(3),
      " residual after rank-1:", np.corrcoef(strip(X).ravel(), strip(Y).ravel())[0, 1].round(3), " n labels", len(reps))
json.dump({"rank_shares": (s[:5]**2/(s**2).sum()).tolist(), "corr_line_factor_cycling": float(np.corrcoef(line_f, cyc)[0, 1]),
           "corr_drug_factor_generic": float(np.corrcoef(drug_f, generic)[0, 1])}, open("development/growth_confound.json", "w"), indent=1)
