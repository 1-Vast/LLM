"""Development: DepMap-scale basal priors versus observed early readouts.

MIX-Seq dev lines (24): references = external PRISM lines + the other dev lines.
Tahoe dev lines (15): references = external PRISM lines + the other dev lines (within-line
selectivity view, as in dev_horizon.py, and across-line view on the dev top-29 drugs).
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import ccle as C  # noqa: E402
import horizon_data as H  # noqa: E402
import mixseq_panel as MP  # noqa: E402


def r(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() >= 6 and np.std(a[ok]) > 0 and np.std(b[ok]) > 0 else np.nan


out = {}
# ---- MIX-Seq dev
sp = MP.split(); dev = sp["pool_A_development"]
DR = ["Trametinib", "Afatinib", "Everolimus", "Gemcitabine", "Taselisib", "JQ1"]
ext = H.load_late("external_mix"); mixd = H.load_late("mix_development")
ed, md = list(ext["drugs"]), list(mixd["drugs"])
mp = MP.pool_a_panel(dev, ["A_treated_dev"], "v1", DR)
grid = [("kernel", tau, m) for tau in (0.05, 0.1) for m in (10, 20, 50)] + [("ridge", k, a) for k in (20, 50) for a in (10.0, 100.0, 1000.0)]
for yk in ("secondary_mean", "primary_2p5"):
    res = {}
    for g in grid:
        rs = []
        for j, drug in enumerate(DR):
            y_ext = ext[yk][:, ed.index(drug)]
            y_dev = mixd[yk][:, md.index(drug)]
            pred = np.full(len(dev), np.nan)
            for i, d in enumerate(dev):
                refs = list(ext["depmap"]) + [x for x in dev if x != d]
                y = np.r_[y_ext, np.delete(y_dev, i)]
                if g[0] == "kernel":
                    pred[i] = C.kernel(d, refs, y, g[1], g[2])
                else:
                    pred[i] = C.ridge([d], refs, y, g[1], g[2])[0]
            rs.append(r(pred, y_dev))
        res["_".join(map(str, g))] = {"mean": round(float(np.nanmean(rs)), 3), "per_drug": [round(x, 3) for x in rs]}
    # early observed readout for reference
    rm = []
    for j, drug in enumerate(DR):
        y_dev = mixd[yk][:, md.index(drug)]
        mag = np.array([-np.linalg.norm(mp.obs[i, j]) if np.isfinite(mp.obs[i, j]).all() else np.nan for i in range(len(dev))])
        rm.append(r(mag, y_dev))
    res["R_mag_observed_24h"] = {"mean": round(float(np.nanmean(rm)), 3), "per_drug": [round(x, 3) for x in rm]}
    out["mix_" + yk] = res
out["mix_ccle_coverage"] = len(C.available(dev))
# ---- Tahoe dev, within-line late selectivity (217 drugs) with external refs
split = H.split(); tdev = split["development"]
ext_t = H.load_late("external_tahoe"); tl = H.load_late("development")
Yd = tl["primary_2p5"]; Ye = ext_t["primary_2p5"]
assert list(ext_t["drugs"]) == list(tl["drugs"])
dep = [split["lines"][f]["depmap_id"] for f in tdev]
tres = {}
for g in [("kernel", 0.1, 20), ("kernel", 0.05, 50), ("ridge", 50, 100.0)]:
    rs = []
    P = np.full_like(Yd, np.nan)
    for j in range(Yd.shape[1]):
        for i, d in enumerate(dep):
            refs = list(ext_t["depmap"]) + [x for x in dep if x != d]
            y = np.r_[Ye[:, j], np.delete(Yd[:, j], i)]
            if np.isfinite(y).sum() < 20:
                continue
            P[i, j] = C.kernel(d, refs, y, g[1], g[2]) if g[0] == "kernel" else C.ridge([d], refs, y, g[1], g[2])[0]
    # selectivity: subtract drug mean over external refs
    mu = np.nanmean(Ye, 0)
    within = [r(P[i] - mu, Yd[i] - mu) for i in range(len(dep))]
    tres["_".join(map(str, g))] = {"within_line_sel_r": round(float(np.nanmean(within)), 3)}
out["tahoe_dev"] = tres
print(json.dumps(out, indent=1))
(HERE / "dev_ccle.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
