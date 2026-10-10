"""Development (15 dev lines): is early phase-redistribution direction a leading indicator of
late across-line selectivity beyond basal proliferation?  Drug set: top-30 by dev late SD."""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import horizon_data as H  # noqa: E402

A, P = H.A, H.P
sp = H.split()
dev = sp["development"]
keep, info = A.qualified_reference()
E5 = H.early_panel(keep)
H.DOSE = 0.5
E05 = H.early_panel(keep)
H.DOSE = 5.0
table = info["table"]


def phase_shift(files, dose, phase):
    frame = P.phenotype_frame(table, files, keep)
    labels = sorted({k[1] for k in frame if A.dose_of(k[1]) == dose})
    drugs = [A.drug_of(l) for l in labels]
    M = np.full((len(files), len(labels)), np.nan)
    acc = {}
    for (f, lab, pl), rec in frame.items():
        if lab in labels:
            acc.setdefault((f, lab), []).append(rec[phase])
    li = {l: i for i, l in enumerate(labels)}
    for (f, lab), v in acc.items():
        M[files.index(f), li[lab]] = np.mean(v)
    return drugs, M


cyc = []
for f in keep:
    rows = [v for (ff, lab, pl), v in table.items() if ff == f and lab == P.DMSO]
    n = sum(r["n"] for r in rows)
    cyc.append(sum(r["S"] + r["G2M"] for r in rows) / n)
cyc = np.array(cyc)
L = H.load_late("development")
late_drugs = list(L["drugs"])
erow = np.array([keep.index(f) for f in dev])
Y = L["primary_2p5"]
Y2 = L["secondary_mean"]
sd = np.nanstd(Y, 0)
top = [late_drugs[j] for j in np.argsort(-sd)[:30] if late_drugs[j] in E5.drugs and late_drugs[j] in E05.drugs]


def r(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return np.corrcoef(a[ok], b[ok])[0, 1] if ok.sum() >= 5 and np.std(a[ok]) > 0 and np.std(b[ok]) > 0 else np.nan


def partial(a, b, c):
    ok = np.isfinite(a) & np.isfinite(b) & np.isfinite(c)
    if ok.sum() < 6:
        return np.nan
    ra = a[ok] - np.polyval(np.polyfit(c[ok], a[ok], 1), c[ok])
    rb = b[ok] - np.polyval(np.polyfit(c[ok], b[ok], 1), c[ok])
    return np.corrcoef(ra, rb)[0, 1]


feats = {"g24_5uM": E5.g24, "g24_0p5uM": E05.g24, "k24_5uM": E5.k24, "s24_5uM": E5.s24}
_, S5 = phase_shift(keep, 5.0, "S")
_, M5 = phase_shift(keep, 5.0, "G2M")
d5 = sorted({A.drug_of(l) for (f, l, p) in P.phenotype_frame(table, keep[:1], keep) if A.dose_of(l) == 5.0})
feats["Sshift_5uM"], feats["G2Mshift_5uM"] = S5, M5
drug_lists = {"g24_5uM": E5.drugs, "g24_0p5uM": E05.drugs, "k24_5uM": E5.drugs, "s24_5uM": E5.drugs,
              "Sshift_5uM": E5.drugs, "G2Mshift_5uM": E5.drugs}
rng = np.random.default_rng(0)
res = {"n_top_drugs": len(top), "top_drugs": top}
per = {}
for name, X in feats.items():
    dl = drug_lists[name]
    R = np.array([[X[erow, dl.index(d)][i] for d in top] for i in range(len(dev))])  # dev x drugs
    Yt = np.array([[Y[i, late_drugs.index(d)] for d in top] for i in range(len(dev))])
    Y2t = np.array([[Y2[i, late_drugs.index(d)] for d in top] for i in range(len(dev))])
    rr = np.array([r(R[:, j], Yt[:, j]) for j in range(len(top))])
    rp = np.array([partial(R[:, j], Yt[:, j], cyc[erow]) for j in range(len(top))])
    boots = []
    for _ in range(2000):
        b = rng.integers(0, len(dev), len(dev))
        boots.append(np.nanmean([r(R[b, j], Yt[b, j]) for j in range(len(top))]))
    res[name] = {"mean_r": float(np.nanmean(rr)), "ci95_line_boot": np.nanpercentile(boots, [2.5, 97.5]).round(3).tolist(),
                 "mean_partial_r_given_dmso_cycling": float(np.nanmean(rp)),
                 "mean_r_secondary_mean": float(np.nanmean([r(R[:, j], Y2t[:, j]) for j in range(len(top))])),
                 "frac_drugs_positive": float(np.nanmean(rr > 0))}
    per[name] = rr
Yt = np.array([[Y[i, late_drugs.index(d)] for d in top] for i in range(len(dev))])
res["cyc_dmso_vs_late_mean_r"] = float(np.nanmean([r(cyc[erow], Yt[:, j]) for j in range(len(top))]))
res["cyc_dmso_vs_g24_mean_r"] = float(np.nanmean([r(cyc[erow], E5.g24[erow, E5.drugs.index(d)]) for d in top]))
moa = pd.read_parquet(H.ROOT / "data/external/tahoe_phenotype_20261010/metadata/tahoe_drugs.parquet").set_index("drug")["moa-fine"]
res["per_drug_g24_5uM"] = sorted([(d, str(moa.get(d)), round(float(per["g24_5uM"][j]), 2)) for j, d in enumerate(top)], key=lambda x: -x[2])
print(json.dumps(res, indent=1, default=float))
(HERE / "dev_direction.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
