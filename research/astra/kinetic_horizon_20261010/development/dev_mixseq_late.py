"""Development (24 pool-A dev lines): within-platform leading indicators of 5-day PRISM viability
and the oracle-vs-basal gate, plus the dose sweep of generic Tahoe/STATE -> MIX-Seq transport.

Across-line view per drug (which lines are most sensitive), leave-one-dev-line-out.
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import horizon_data as H  # noqa: E402
import mixseq_panel as MP  # noqa: E402

sp = MP.split()
dev = sp["pool_A_development"]
DRUGS = ["Trametinib", "Afatinib", "Everolimus", "Gemcitabine", "Taselisib", "JQ1"]
mp = MP.pool_a_panel(dev, ["A_treated_dev"], "v1", DRUGS)
st = MP.state_forecast("A", "v1", dev, ["Trametinib", "Afatinib", "Everolimus", "Gemcitabine"])
late = H.load_late("mix_development")
ld = list(late["drugs"]); lrow = {d: i for i, d in enumerate(late["files"])}
Y = {k: np.array([[late[k][lrow[d], ld.index(dr)] for dr in DRUGS] for d in dev]) for k in ("secondary_mean", "primary_2p5")}


def r(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() >= 6 and np.std(a[ok]) > 0 and np.std(b[ok]) > 0 else np.nan


def kernel_vec(sim, y, tau=0.1, m=8):
    o = np.argsort(-sim)[:m]; o = o[np.isfinite(y[o])]
    if len(o) == 0:
        return np.nan
    w = np.exp((sim[o] - sim[o].max()) / tau)
    return float((w * y[o]).sum() / w.sum())


def cos_sim(M, i, others):
    c = M[others].mean(0); a = M[i] - c; B = M[others] - c
    return (B @ a) / (np.linalg.norm(B, axis=1) * np.linalg.norm(a) + 1e-12)


out = {"n_dev": len(dev), "drugs": DRUGS}
n = len(dev)
for yk, YY in Y.items():
    res = {}
    for j, drug in enumerate(DRUGS):
        y = YY[:, j]
        O = mp.obs[:, j]
        okO = np.isfinite(O).all(1)
        arms = {k: np.full(n, np.nan) for k in ("B_late", "abundance", "R_mag", "R_kernel", "g1_shift", "S_mag", "S_kernel")}
        for i in range(n):
            others = np.array([t for t in range(n) if t != i])
            arms["B_late"][i] = kernel_vec(cos_sim(mp.basal, i, others), y[others])
            arms["abundance"][i] = mp.abundance[i, j]
            pt, pc = mp.phase_t[i, j] + 0.5, mp.phase_c[i] + 0.5
            arms["g1_shift"][i] = np.log(pt[0] / (pt.sum() - pt[0])) - np.log(pc[0] / (pc.sum() - pc[0]))
            if okO[i]:
                oo = np.array([t for t in others if okO[t]])
                dev_i = O[i] - O[oo].mean(0)
                arms["R_mag"][i] = -np.linalg.norm(O[i])  # larger response -> predicted more sensitive (lower viability)
                Dm = O - O[oo].mean(0)
                sim = np.array([np.corrcoef(dev_i, Dm[t])[0, 1] for t in oo])
                arms["R_kernel"][i] = kernel_vec(sim, y[oo])
            if j < 4:
                S = st["paired"][:, j][:, mp.present]
                arms["S_mag"][i] = -np.linalg.norm(S[i])
                Sd = S - S[others].mean(0)
                sim = np.array([np.corrcoef(Sd[i], Sd[t])[0, 1] for t in others])
                arms["S_kernel"][i] = kernel_vec(sim, y[others])
        res[drug] = {k: round(r(v, y), 3) for k, v in arms.items()} | {"n_late": int(np.isfinite(y).sum())}
    agg = {k: round(float(np.nanmean([res[d][k] for d in DRUGS])), 3) for k in res[DRUGS[0]] if k != "n_late"}
    out[yk] = {"per_drug": res, "mean_over_drugs": agg}
# dose sweep: generic response transport per drug (STATE and Tahoe observed vs MIX-Seq observed mean)
keep, info = H.A.qualified_reference()
tp = H.A.attach_expression(H.A.phenotype_panel(keep, keep, info["table"], info["names"]))
z = np.load(MP.DATA / "mixseq_state" / "A_v1.npz", allow_pickle=True)
zl = list(z["lines"]); rows = [zl.index(d) for d in dev]
sweep = {}
for j, drug in enumerate(["Trametinib", "Afatinib", "Everolimus", "Gemcitabine"]):
    O = mp.obs[:, j]; om = np.nanmean(O, 0)
    sweep[drug] = {}
    for dose in (0.05, 0.5, 5.0):
        lab = MP.MS.label(drug, dose)
        s_mean = z["paired_delta"][rows][:, list(z["labels"]).index(lab)].mean(0)[mp.present]
        k = tp.labels.index(lab)
        t_mean = np.nanmean(tp.delta[:, k], 0)[mp.present]
        sweep[drug][str(dose)] = {"state": round(r(s_mean, om), 3), "tahoe_observed": round(r(t_mean, om), 3)}
out["dose_sweep_generic"] = sweep
print(json.dumps(out, indent=1))
(HERE / "dev_mixseq_late.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
