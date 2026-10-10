"""Development (24 MIX-Seq dev lines): does the observed 24 h state add to the DepMap-scale prior?
Combination = equal-weight sum of across-line z-scores (no fitted weight). Also the STATE analogue.
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

sp = MP.split(); dev = sp["pool_A_development"]
DR = ["Trametinib", "Afatinib", "Everolimus", "Gemcitabine", "Taselisib", "JQ1"]
ext = H.load_late("external_mix"); mixd = H.load_late("mix_development")
ed, md = list(ext["drugs"]), list(mixd["drugs"])
mp = MP.pool_a_panel(dev, ["A_treated_dev"], "v1", DR)
st = MP.state_forecast("A", "v1", dev, DR[:4])


def r(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() >= 6 and np.std(a[ok]) > 0 and np.std(b[ok]) > 0 else np.nan


def z(x):
    return (x - np.nanmean(x)) / np.nanstd(x)


out = {}
for yk, prior in (("secondary_mean", ("ridge", 50, 100.0)), ("primary_2p5", ("kernel", 0.1, 50))):
    rows = {k: [] for k in ("B", "R_mag", "B+R_mag", "abund", "B+abund", "g1", "B-g1", "B+R_mag+abund", "S_mag", "B+S_mag")}
    for j, drug in enumerate(DR):
        y_ext = ext[yk][:, ed.index(drug)]
        y = mixd[yk][:, md.index(drug)]
        Bp = np.full(len(dev), np.nan)
        for i, d in enumerate(dev):
            refs = list(ext["depmap"]) + [x for x in dev if x != d]
            yy = np.r_[y_ext, np.delete(y, i)]
            Bp[i] = C.kernel(d, refs, yy, prior[1], prior[2]) if prior[0] == "kernel" else C.ridge([d], refs, yy, prior[1], prior[2])[0]
        mag = np.array([-np.linalg.norm(mp.obs[i, j]) if np.isfinite(mp.obs[i, j]).all() else np.nan for i in range(len(dev))])
        ab = mp.abundance[:, j]
        pt, pc = mp.phase_t[:, j] + 0.5, mp.phase_c + 0.5
        g1 = np.log(pt[:, 0] / pt[:, 1:].sum(1)) - np.log(pc[:, 0] / pc[:, 1:].sum(1))
        rows["B"].append(r(Bp, y)); rows["R_mag"].append(r(mag, y)); rows["B+R_mag"].append(r(z(Bp) + z(mag), y))
        rows["abund"].append(r(ab, y)); rows["B+abund"].append(r(z(Bp) + z(ab), y))
        rows["g1"].append(r(-g1, y)); rows["B-g1"].append(r(z(Bp) - z(g1), y))
        rows["B+R_mag+abund"].append(r(z(Bp) + z(mag) + z(ab), y))
        if j < 4:
            sm = -np.linalg.norm(st["paired"][:, j], axis=1)
            rows["S_mag"].append(r(sm, y)); rows["B+S_mag"].append(r(z(Bp) + z(sm), y))
    out[yk] = {k: {"mean": round(float(np.nanmean(v)), 3), "per_drug": [round(x, 3) for x in v]} for k, v in rows.items()}
print(json.dumps(out, indent=1))
(HERE / "dev_complement.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
