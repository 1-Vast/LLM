"""Check 5c: sweep the regularisation of the study's own_h6 ceiling arm and compare with a closed-form ridge on its features.

Uses the study's Fitter (as the test subject) on a subset of dev units; HD outcomes only (E masked at load). Run:
PYTHONPATH='src;.' D:/anaconda/envs/maestro/python.exe research/astra/mono_pretraining_20261005/decisions/VERIFY_7_own_sweep.py
Writes decisions/VERIFY_7_own_sweep.json (refuses to overwrite).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import rankdata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import VERIFY_lib as L  # noqa: E402
from tools.datasets.combination_screens import open_vault  # noqa: E402
from research.astra.confirmation_campaign_20261004.design import campaign as c  # noqa: E402

OUT = L.HERE / "VERIFY_7_own_sweep.json"
MONO = L.STUDY / "results/mono_labels.csv.gz"


def sp(a, b):
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return np.nan
    return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"REFUSED: {OUT} exists")
    open_vault(L.FREEZE, L.LOG, purpose="VERIFY phase 2: GDSC2 mono labels for the own_h6 regularisation sweep", source=MONO, root=L.ROOT)
    mono = pd.read_csv(MONO, dtype={"jaaks_drug_id": str, "drug_id": str})
    tissues, report, sp_, e_sidms = L.load_hd("VERIFY phase 2: HD outcomes for the own_h6 regularisation sweep (E masked at load)")
    L.assert_e_masked(tissues, e_sidms)
    from research.astra.mono_pretraining_20261005 import common as cm, combo, run_s2, bilinear
    from research.astra.mono_pretraining_20261005.bilinear import ComboConfig
    drugs = cm.drug_table()
    drow = dict(zip(drugs.jaaks_id, drugs.row)); mapped = drugs.mapped.to_numpy()
    zc, rowc = cm.load_context()[1], cm.load_context()[2]
    own_rec = mono[(~mono.sibling_id_record) & mono.jaaks_drug_id.notna() & mono.NOT_ELIGIBLE_target_line_own_mono_diagnostic_only]
    own = {(r.sidm, int(drow[r.jaaks_drug_id])): float(r.y_rel) for r in own_rec.itertuples() if r.jaaks_drug_id in drow}
    fit = combo.Fitter(zc, drow, rowc, mapped, own=own)
    fold = L.my_fold_of(sp_)
    units = L.units(sp_, fold, cm.history_draw)
    cfgs = [(1.0, 10.0), (30.0, 10.0), (300.0, 10.0), (3000.0, 10.0), (30000.0, 10.0)]
    gains = {cf: {} for cf in cfgs}
    conv = []
    for u in units[::5]:
        T = tissues[u["tissue"]]
        H = c.restrict(T, u["hist"])
        pf = {kk: v for kk, v in np.load(L.STUDY / f"results/mono_params/F{u['fold']}_pre.npz").items()}
        for sidm in u["targets"][:4]:
            tg = c.make_target(T, H, sidm, "SV", allowed_history=u["allowed"], forbidden=u["forbidden"])
            truth = c.truth_of(T, tg)
            tv = (truth["y_s"] + truth["y_v"]) / 2.0
            r0 = sp(tg.q["S_both"], tv)
            for cf in cfgs:
                cfg = ComboConfig(features="h6", l2_theta=cf[0], l2_init=cf[1])
                p = fit.fit("own", pf, H, cfg)
                sc = fit.target_score(p, T, tg)
                gains[cf].setdefault((u["tissue"], sidm), []).append(sp(sc, tv) - r0)
        # convergence check of the Adam solution against the closed-form ridge on the same features (W,E frozen limit)
        rows = combo.training_rows(H, drow, rowc, mapped)
        uo = fit._uo(pf, rows)
        r = (torch.as_tensor(zc) @ torch.as_tensor(pf["W"]))[torch.as_tensor(rows["cell"])]
        Ea, Eb = torch.as_tensor(pf["E"])[torch.as_tensor(rows["anchor"])], torch.as_tensor(pf["E"])[torch.as_tensor(rows["library"])]
        Phi = bilinear._feats(r, Ea, Eb, "h6", torch.as_tensor(pf["beta"])[torch.as_tensor(rows["anchor"])],
                              torch.as_tensor(pf["beta"])[torch.as_tensor(rows["library"])], torch, (torch.as_tensor(uo[0]), torch.as_tensor(uo[1]))).numpy()
        yv = rows["y"]
        n = len(yv)
        th_closed = np.linalg.solve(Phi.T @ Phi + 30.0 * np.eye(6), Phi.T @ yv)
        p30 = fit.fit("own", pf, H, ComboConfig(features="h6", l2_theta=30.0, l2_init=1e9))
        conv.append(float(np.abs(p30["theta"] - th_closed).max()))
    out = dict(mean_concordance_gain_own_h6={f"theta{cf[0]:g}|init{cf[1]:g}": float(np.mean([np.mean(v) for v in d.values()])) for cf, d in gains.items()},
               n_lines=len(next(iter(gains.values()))), adam_vs_closed_form_theta_max_abs_diff_mean=float(np.mean(conv)),
               adam_vs_closed_form_theta_max_abs_diff_max=float(np.max(conv)))
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
