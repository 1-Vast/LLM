"""Development probe (reference lines only, Tahoe 24 h obs codes; no held-out value is read).

Question: does a kinetic readout of the 24 h phase snapshot explain same-spheroid relative
survival, where the signed G1 log-odds shift explained ~0% (phenotype_anchor_20261010, dev.)?

Kinetic readout (age-structured, asynchronous exponential growth; Kafri 2013 / Steel):
phase fractions -> phase duration shares u_k = T_k / T_c.  Under lengthening-only drug action
(T'_k >= T_k), the minimal cycle slowdown is rho = min_k u'_k / u_k  (growth-rate ratio <= 1).
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "research/astra/phenotype_anchor_20261010"))
import analysis as A  # noqa: E402
import phenotypes as P  # noqa: E402

PS = 0.5


def shares(g1, s, g2m):
    n = g1 + s + g2m + 3 * PS
    f1, f2 = (g1 + PS) / n, (s + PS) / n
    u1 = -np.log2(1 - f1 / 2)
    u12 = -np.log2(1 - (f1 + f2) / 2)
    return np.stack([u1, u12 - u1, 1 - u12], -1)


keep, info = A.qualified_reference()
table = info["table"]
wells = {}
for (f, lab, pl), row in table.items():
    wells.setdefault((lab, pl), {})[f] = row
frame = P.phenotype_frame(table, keep, keep)
rec = []
for (f, lab, pl), r in frame.items():
    if A.dose_of(lab) != 5.0:
        continue
    t, b = table[(f, lab, pl)], table[(f, P.DMSO, pl)]
    ut = shares(t["G1"], t["S"], t["G2M"])
    ub = shares(b["G1"], b["S"], b["G2M"])
    ratio = ut / ub
    rec.append((f, lab, pl, r["survival"], r["G1"], np.log2(ratio.min()), np.log2(ratio[1]), np.log2(ratio[0]), np.log2(ratio[2]), t["n"]))
import pandas as pd  # noqa: E402

d = pd.DataFrame(rec, columns=["f", "lab", "pl", "surv", "g1", "log_rho", "log_uS", "log_uG1", "log_uG2M", "n"])
# selectivity within well: subtract the reference-panel mean for (label, plate)
for c in ["surv", "g1", "log_rho", "log_uS", "log_uG1", "log_uG2M"]:
    d[c + "_sel"] = d[c] - d.groupby(["lab", "pl"])[c].transform("mean")
out = {"n_rows": len(d), "n_lines": d.f.nunique(), "n_labels": d.lab.nunique()}
for c in ["g1", "log_rho", "log_uS", "log_uG1", "log_uG2M"]:
    pooled = np.corrcoef(d[c + "_sel"], d["surv_sel"])[0, 1]
    within = d.groupby("f").apply(lambda g: np.corrcoef(g[c + "_sel"], g["surv_sel"])[0, 1]).mean()
    raw = np.corrcoef(d[c], d["surv"])[0, 1]
    out[c] = {"pooled_r_sel": round(float(pooled), 3), "mean_within_line_r_sel": round(float(within), 3), "pooled_r_raw": round(float(raw), 3)}
# plate replicability of the kinetic readout (labels on two plates)
pl2 = d.groupby(["f", "lab"]).filter(lambda g: len(g) == 2).sort_values(["f", "lab", "pl"])
for c in ["g1_sel", "log_rho_sel", "surv_sel"]:
    a = pl2.groupby(["f", "lab"])[c].agg(["first", "last"])
    out["replicate_r_" + c] = round(float(np.corrcoef(a["first"], a["last"])[0, 1]), 3)
# well-count-weighted subset: wells with >= 500 cells
big = d[d.n >= 500]
out["n_rows_ge500"] = len(big)
out["pooled_r_sel_log_rho_ge500"] = round(float(np.corrcoef(big.log_rho_sel, big.surv_sel)[0, 1]), 3)
out["pooled_r_sel_g1_ge500"] = round(float(np.corrcoef(big.g1_sel, big.surv_sel)[0, 1]), 3)
print(json.dumps(out, indent=1))
(HERE / "kinetic_probe.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
