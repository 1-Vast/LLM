"""POST HOC: line-bootstrap uncertainty of the development gate's MIX-Seq ceiling and forecast
increment (24 development lines; development data only; same predictions as gate.py).
Question: would a gate that requires the lower 95% bound to clear MUB have abstained?
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import ccle as C  # noqa: E402
import gate as G  # noqa: E402
import horizon_data as H  # noqa: E402
import mixseq_panel as MP  # noqa: E402

sp = MP.split(); dev = sp["pool_A_development"]
ext = H.load_late("external_mix"); mixd = H.load_late("mix_development")
ed, md = list(ext["drugs"]), list(mixd["drugs"])
mp = MP.pool_a_panel(dev, ["A_treated_dev"], "v1", G.MIX_DRUGS_LATE)
st = MP.state_forecast("A", "v1", dev, G.STATE_DRUGS)
yk = G.CONFIG["mix_late_endpoint"]
n, D = len(dev), len(G.MIX_DRUGS_LATE)
Y, B, R, S = (np.full((n, D), np.nan) for _ in range(4))
for j, drug in enumerate(G.MIX_DRUGS_LATE):
    Y[:, j] = mixd[yk][:, md.index(drug)]
    y_ext = ext[yk][:, ed.index(drug)]
    B[:, j] = [G.mix_prior(d, list(ext["depmap"]) + [x for x in dev if x != d], np.r_[y_ext, np.delete(Y[:, j], i)]) for i, d in enumerate(dev)]
    R[:, j] = [-np.linalg.norm(mp.obs[i, j]) if np.isfinite(mp.obs[i, j]).all() else np.nan for i in range(n)]
    if drug in G.STATE_DRUGS:
        S[:, j] = -np.linalg.norm(st["paired"][:, G.STATE_DRUGS.index(drug)], axis=1)


def inc(b, E, js):
    return float(np.nanmean([G.r(G.z(B[b, j]) + G.z(E[b, j]), Y[b, j]) - G.r(B[b, j], Y[b, j]) for j in js]))


rng = np.random.default_rng(20261010)
allj, sj = range(D), range(len(G.STATE_DRUGS))
bc = [inc(rng.integers(0, n, n), R, allj) for _ in range(2000)]
rng = np.random.default_rng(20261010)
bf = [inc(rng.integers(0, n, n), S, sj) for _ in range(2000)]
out = {"ceiling_point": inc(np.arange(n), R, allj), "ceiling_ci95": [float(np.nanpercentile(bc, 2.5)), float(np.nanpercentile(bc, 97.5))],
       "ceiling_ci90_lower": float(np.nanpercentile(bc, 5)),
       "forecast_point": inc(np.arange(n), S, sj), "forecast_ci95": [float(np.nanpercentile(bf, 2.5)), float(np.nanpercentile(bf, 97.5))],
       "mub": G.MUB}
out["lower_bound_rule_decision"] = "MEASURE_EARLY" if out["ceiling_ci95"][0] >= G.MUB else "ABSTAIN_COLLECT_REFERENCE_UNITS"
(HERE / "gate_uncertainty.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
