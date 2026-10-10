"""Development (24 unseen pool-A dev lines): STATE zero-shot RNA skill on MIX-Seq vs baselines.

Context deviation = response minus the leave-one-line-out panel mean over the other dev lines.
Arms: Z (zero deviation), B_mix (basal kernel transfer of other dev lines' observed deviations),
B_tahoe (basal kernel transfer of Tahoe reference lines' observed deviations, same information as
STATE), S (STATE paired delta deviation), S_perm (STATE of another line, cyclic).
Metric: per-line Pearson r over the 1,905 axis genes, mean over lines; split-half noise ceiling.
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

A = H.A
sp = MP.split()
dev = sp["pool_A_development"]
keep, info = A.qualified_reference()
tpanel = A.attach_expression(A.phenotype_panel(keep, keep, info["table"], info["names"]))
tlabels = tpanel.labels
out = {}


def r(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() > 10 and np.std(a[ok]) > 0 and np.std(b[ok]) > 0 else np.nan


def kernel(target, train, Y, tau=0.1, m=10):
    c = train.mean(0); a = target - c; B = train - c
    sim = (B @ a) / (np.linalg.norm(B, axis=1) * np.linalg.norm(a) + 1e-12)
    o = np.argsort(-sim)[:m]; w = np.exp((sim[o] - sim[o].max()) / tau)
    Ym = Y[o]; ok = np.isfinite(Ym).all(-1)
    w = w * ok
    return np.tensordot(w, np.nan_to_num(Ym), 1) / max(w.sum(), 1e-12)


for variant in ("v0", "v1", "v2"):
    mp = MP.pool_a_panel(dev, ["A_treated_dev"], variant)
    st = MP.state_forecast("A", variant, dev)
    present = mp.present
    res = {}
    for j, drug in enumerate(mp.drugs):
        O = mp.obs[:, j]
        ok_lines = np.flatnonzero(np.isfinite(O).all(1))
        S = st["paired"][:, j][:, present]
        # Tahoe reference deviations for the matched label
        lab = MP.MS.label(drug, MP.MIX_DRUGS[drug])
        k = tlabels.index(lab)
        Td = tpanel.delta[:, k][:, present]
        Td_ok = np.isfinite(Td).all(1)
        Td_dev = Td[Td_ok] - Td[Td_ok].mean(0)
        tb = tpanel.basal[Td_ok]
        arms = {a: [] for a in ("Z", "B_mix", "B_tahoe", "S", "S_perm", "ceiling")}
        for ii, i in enumerate(ok_lines):
            others = np.array([x for x in ok_lines if x != i])
            panel = O[others].mean(0)
            obs_dev = O[i] - panel
            arms["B_mix"].append(r(kernel(mp.basal[i], mp.basal[others], O[others] - panel), obs_dev))
            arms["B_tahoe"].append(r(kernel(mp.basal[i], tb, Td_dev[:, None, :])[0] if False else kernel(mp.basal[i], tb, Td_dev), obs_dev))
            s_dev = S[i] - S[others].mean(0)
            arms["S"].append(r(s_dev, obs_dev))
            jperm = ok_lines[(ii + 1) % len(ok_lines)]
            arms["S_perm"].append(r(S[jperm] - S[others].mean(0), obs_dev))
            h = mp.halves[i, j]
            rh = r(h[0] - panel, h[1] - panel)
            arms["ceiling"].append(2 * rh / (1 + rh) if np.isfinite(rh) else np.nan)
        res[drug] = {a: round(float(np.nanmean(v)), 4) for a, v in arms.items() if a != "Z"} | {"n_lines": int(len(ok_lines))}
        # generic (panel-level) agreement: STATE mean delta vs observed mean delta
        res[drug]["generic_r_state_vs_obs"] = round(r(S[ok_lines].mean(0), O[ok_lines].mean(0)), 4)
        res[drug]["generic_r_tahoe_vs_obs"] = round(r(Td[Td_ok].mean(0), O[ok_lines].mean(0)), 4)
    out[variant] = res
print(json.dumps(out, indent=1))
(HERE / "dev_mixseq_rna.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
