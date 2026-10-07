"""Development-only check of a profile-shape decision (run before freezing; exploratory, disclosed).

Decision: for a target coordinate (gene), flag the m menu conditions with the strongest decrease of that
gene in the new line, scored in the independent replicate well B. Targets: the 40 named coordinates with
the largest panel response variance on the menu wells (training contexts only, chosen before looking at
held-out values). Forecasts of the well-B effect: panel mean (M0), M0 + gamma_S devS (STATE), gene-gated (M1).
Room for acquisition = gap between the forecast ranking and perfect information, and how much a
first-well profile of the forecast's top candidates closes it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agent_data as ad  # noqa: E402
import world_models as wm  # noqa: E402
from world_dev import panel_keys  # noqa: E402

M, K_SCREENS = 5, 8


def main():
    dev = json.loads((HERE / "world_dev" / "DEV_RESULTS.json").read_text(encoding="utf-8"))
    v, gs, gk = dev["M0"]["selected"], dev["M2"]["selected_gamma_S"], dev["M1"]["selected_gamma_K"]
    panel = wm.Panel(panel_keys())
    wells = ad.menu_labels()
    names = json.loads((HERE.parents[2] / "data/virtual_cell/tahoe_c39_x_hvg_feature_names.json").read_text(encoding="utf-8"))["names"]
    index = {k: i for i, k in enumerate(panel.keys)}
    colsB = np.array([index[(l, p[1])] for l, p in wells.items()])
    colsA = np.array([index[(l, p[0])] for l, p in wells.items()])
    W0 = panel.w_m0(v)
    var = np.var(panel.delta[:, colsB].astype(np.float64), axis=0).mean(0)  # panel response variance per coordinate
    named = np.array([n is not None for n in names])
    targets = [int(j) for j in np.argsort(-np.where(named, var, -1))[:40]]
    out = {"status": "development only", "targets": [names[j] for j in targets], "m": M, "screens": K_SCREENS, "lines": {}}
    for name in wm.SPLIT["development"]:
        t = wm.target(name, panel)
        kidx = {k: i for i, k in enumerate(t["keys"])}
        iB = np.array([kidx[(l, p[1])] for l, p in wells.items()])
        iA = np.array([kidx[(l, p[0])] for l, p in wells.items()])
        m0B, m0A = panel.apply(W0, colsB), panel.apply(W0, colsA)
        gate, _, _ = panel.gate(t["basal"], W0, colsB, 0.0)
        fc = {"M0": m0B, "M1_gate": m0B + gk * gate, "M2_state": m0B + gs * t["devS"][iB]}
        obsB, obsA = t["delta"][iB], t["delta"][iA]
        rows = {f: {"hits": [], "value": [], "value_after_screens": []} for f in fc}
        perfect, reliab = [], []
        for j in targets:
            yB, yA = obsB[:, j], obsA[:, j]
            truth = set(np.argsort(yB)[:M].tolist())
            perfect.append(float(-yB[list(truth)].sum()))
            reliab.append(float(np.corrcoef(yA, yB)[0, 1]))
            for f, pred in fc.items():
                p = pred[:, j]
                top = list(np.argsort(p)[:M])
                rows[f]["hits"].append(len(truth & set(top)))
                rows[f]["value"].append(float(-yB[top].sum()))
                # Screen the forecast's top-k first wells; replace forecast by the screened value; flag m.
                screened = list(np.argsort(p)[:K_SCREENS])
                q = p.copy()
                q[screened] = yA[screened]
                f2 = list(np.argsort(q)[:M])
                rows[f]["value_after_screens"].append(float(-yB[f2].sum()))
        out["lines"][name] = {"perfect_value_mean": float(np.mean(perfect)), "replicate_well_corr_median": float(np.median(reliab)),
                              **{f: {"hits_mean": float(np.mean(r["hits"])), "value_mean": float(np.mean(r["value"])),
                                     "value_after_screens_mean": float(np.mean(r["value_after_screens"]))} for f, r in rows.items()}}
    (HERE / "agent_dev" / "PROFILE_DECISION_CHECK.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out["lines"], indent=1))


if __name__ == "__main__":
    main()
