"""Development-only diagnostics run after world_dev.py and before the freeze (exploratory, disclosed).

(a) Leakage check on the deviation itself: STATE's leave-one-out deviation skill on TRAINING contexts
    (in-sample for STATE) versus the held-out development lines. Genuine holdout predicts a clearly
    larger in-sample gain; a held-out gain as large as in-sample would be uninformative or worrying.
(b) Dose breakdown of the selected M2 gain.
(c) Why the unpaired STATE output looks better than the paired one: the plate-common component.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import world_models as wm  # noqa: E402
from world_dev import components, panel_keys, se_model  # noqa: E402


def main():
    dev_results = json.loads((HERE / "world_dev" / "DEV_RESULTS.json").read_text(encoding="utf-8"))
    v, gs, lam = dev_results["M0"]["selected"], dev_results["M2"]["selected_gamma_S"], dev_results["krr_lambda"]["selected"]
    panel = wm.Panel(panel_keys())
    out = {"status": "development-only exploratory diagnostics, after world_dev selection, before freeze"}
    # (a) in-sample deviation skill.
    state = panel.state.astype(np.float32)
    ok = np.zeros(panel.state.shape[:2], bool)
    for li, f in enumerate(panel.files):
        s = wm.load_state(f)
        idx = {k: i for i, k in enumerate(panel.keys)}
        for k in zip(s["label"].tolist(), s["plate"].tolist()):
            if k in idx:
                ok[li, idx[k]] = True
    gains = []
    for li in range(len(panel.files)):
        W = panel.avail.copy(); W[li] = False
        W = W / np.maximum(W.sum(0), 1)
        cols = np.flatnonzero(panel.avail[li] & ok[li] & (panel.coverage >= wm.MIN_PANEL_LINES))
        others = ok.copy(); others[li] = False
        loo_state_mean = (state * others[..., None]).sum(0) / np.maximum(others.sum(0), 1)[:, None]
        total0, total2 = 0.0, 0.0
        for a in range(0, len(cols), 150):
            c = cols[a:a + 150]
            obs = panel.delta[li, c].astype(np.float64)
            m0 = np.einsum("lk,lkd->kd", W[:, c], panel.delta[:, c], optimize=True)
            nm = (W[:, c] ** 2 * panel.noise0[:, c]).sum(0)
            dev = state[li, c] - loo_state_mean[c]
            total0 += (np.mean((m0 - obs) ** 2, 1) - nm - panel.noise0[li, c]).sum()
            total2 += (np.mean((m0 + gs * dev - obs) ** 2, 1) - nm - panel.noise0[li, c]).sum()
        gains.append({"file": panel.files[li], "M2_minus_M0_in_sample": (total2 - total0) / len(cols),
                      "M0_loo": total0 / len(cols), "relative_gain": (total2 - total0) / total0})
    rel = np.array([g["relative_gain"] for g in gains])
    out["a_in_sample_deviation_skill"] = {"per_context": gains, "median_relative_gain": float(np.median(rel)),
                                          "quantiles_relative_gain": np.percentile(rel, [10, 25, 50, 75, 90]).tolist()}
    raw = {n: wm.target(n, panel) for n in wm.SPLIT["development"]}
    dev = {n: components(panel, t, lam) for n, t in raw.items()}
    held_rel = {}
    for n, c in dev.items():
        m0 = se_model(c, v).mean()
        held_rel[n] = float((se_model(c, v, gs=gs).mean() - m0) / m0)
    out["a_heldout_relative_gain"] = held_rel
    # (b) dose breakdown.
    by = {}
    for n, c in dev.items():
        dose = np.array([wm.dose_of(k) for k in c["keys"]])
        d = se_model(c, v, gs=gs) - se_model(c, v)
        m0 = se_model(c, v)
        by[n] = {x: {"groups": int((dose == x).sum()), "M2_minus_M0": float(d[dose == x].mean()), "M0": float(m0[dose == x].mean())}
                 for x in sorted(set(dose))}
    out["b_dose_breakdown"] = by
    # (c) plate-common component of the observed responses and of the unpaired STATE offset.
    pc = {}
    for n, c in dev.items():
        t = raw[n]
        e = t["eligible"]
        plates = np.array([k[1] for k in c["keys"]])
        obs = c["obs"]
        common = np.zeros_like(obs)
        offset = c["S_raw"] - c["S"]  # f(basal, DMSO) - basal: drug-independent per plate
        for p in set(plates):
            m = plates == p
            common[m] = obs[m].mean(0)
        resid = obs - common
        m0 = c[f"P0_{v}"]
        m0common = np.zeros_like(m0)
        for p in set(plates):
            m = plates == p
            m0common[m] = m0[m].mean(0)
        pc[n] = {"plate_common_energy_fraction_of_observed": float(np.mean(common ** 2) / np.mean(obs ** 2)),
                 "corr_offset_vs_plate_common": float(np.corrcoef(offset.ravel(), common.ravel())[0, 1]),
                 "corr_M0common_vs_plate_common": float(np.corrcoef(m0common.ravel(), common.ravel())[0, 1]),
                 "se_obs_common_part_M0": float(np.mean(np.mean((m0common - common) ** 2, 1))),
                 "se_obs_common_part_offset_plus_M0common": float(np.mean(np.mean((m0common + offset - common) ** 2, 1))),
                 "energy_resid_after_plate_common": float(np.mean(resid ** 2))}
    out["c_plate_common"] = pc
    (HERE / "world_dev" / "DEV_DIAGNOSTICS.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: (v if k != "a_in_sample_deviation_skill" else {kk: vv for kk, vv in v.items() if kk != "per_context"}) for k, v in out.items()}, indent=1))


if __name__ == "__main__":
    main()
