"""Check 5d: full own_h6 regularisation sweep on all 150 dev units + an independent ridge on the SAME histories/targets.
HD outcomes (E masked at load) + GDSC2 mono labels. Writes decisions/VERIFY_8_own_full.json (refuses to overwrite)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import rankdata
sys.path.insert(0, str(Path(__file__).resolve().parent))
import VERIFY_lib as L
from tools.datasets.combination_screens import open_vault
from research.astra.confirmation_campaign_20261004.design import campaign as c
OUT = L.HERE / "VERIFY_8_own_full.json"
MONO = L.STUDY / "results/mono_labels.csv.gz"
def sp(a, b):
    if np.ptp(a) == 0 or np.ptp(b) == 0: return np.nan
    return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
if OUT.exists(): raise SystemExit("REFUSED")
open_vault(L.FREEZE, L.LOG, purpose="VERIFY phase 2: GDSC2 mono labels for the full own_h6 sweep and same-history ridge", source=MONO, root=L.ROOT)
mono = pd.read_csv(MONO, dtype={"jaaks_drug_id": str, "drug_id": str})
tissues, report, sp_, e_sidms = L.load_hd("VERIFY phase 2: HD outcomes for the full own_h6 sweep and same-history ridge (E masked at load)")
L.assert_e_masked(tissues, e_sidms)
from research.astra.mono_pretraining_20261005 import common as cm, combo
from research.astra.mono_pretraining_20261005.bilinear import ComboConfig
drugs = cm.drug_table(); drow = dict(zip(drugs.jaaks_id, drugs.row)); mapped = drugs.mapped.to_numpy()
zc, rowc = cm.load_context()[1], cm.load_context()[2]
own_rec = mono[(~mono.sibling_id_record) & mono.jaaks_drug_id.notna() & mono.NOT_ELIGIBLE_target_line_own_mono_diagnostic_only]
own = {(r.sidm, int(drow[r.jaaks_drug_id])): float(r.y_rel) for r in own_rec.itertuples() if r.jaaks_drug_id in drow}
fit = combo.Fitter(zc, drow, rowc, mapped, own=own)
elig = mono[mono.eligible_primary_pretrain & ~mono.sibling_id_record & mono.jaaks_drug_id.notna()]
st = elig.groupby("jaaks_drug_id").y_rel.agg(["mean", "std"])
mval = {(r.sidm, r.jaaks_drug_id): (r.y_rel - st.loc[r.jaaks_drug_id, "mean"]) / st.loc[r.jaaks_drug_id, "std"]
        for r in mono[mono.NOT_ELIGIBLE_target_line_own_mono_diagnostic_only & ~mono.sibling_id_record & mono.jaaks_drug_id.notna()].itertuples() if r.jaaks_drug_id in st.index}
fold = L.my_fold_of(sp_); units = L.units(sp_, fold, cm.history_draw)
cfgs = [(30.0, 10.0), (300.0, 10.0), (3000.0, 10.0), (30000.0, 10.0)]
gains = {k: {} for k in [f"own_h6|theta{a:g}" for a, _ in cfgs] + ["ridge_pair_features_a100", "ridge_pair_features_a300", "ridge_pair_features_a1000"]}
for u in units:
    T = tissues[u["tissue"]]; H = c.restrict(T, u["hist"])
    pf = {k: v for k, v in np.load(L.STUDY / f"results/mono_params/F{u['fold']}_pre.npz").items()}
    fits = {cf: fit.fit("own", pf, H, ComboConfig(features="h6", l2_theta=cf[0], l2_init=cf[1])) for cf in cfgs}
    # my ridge on the same 4 history lines
    A = T.arrays["SV"]; y = (A["y_s"] + A["y_v"]) / 2.0
    S_id = np.array([p[0] for p in T.pairs]); V_id = np.array([p[1] for p in T.pairs])
    ms = np.array([mval.get((T.lines[int(ci)], a), np.nan) for ci, a in zip(T.c, S_id)])
    mv = np.array([mval.get((T.lines[int(ci)], b), np.nan) for ci, b in zip(T.c, V_id)])
    a0, b0 = np.nan_to_num(ms), np.nan_to_num(mv)
    F = np.column_stack([a0, b0, a0 * b0, np.abs(a0 - b0)])
    hl = [T.lines.index(s) for s in u["hist"]]
    trm = np.isin(T.c, hl); pid = T.pid; size = int(pid.max()) + 1
    ssum = np.bincount(pid[trm], weights=y[trm], minlength=size); scnt = np.bincount(pid[trm], minlength=size).astype(float)
    mu_lo = (y[trm].sum() - y) / (trm.sum() - 1)
    prior = (ssum[pid] - y + 2.0 * mu_lo) / (scnt[pid] - 1 + 2.0)
    resid = y - prior
    for li in hl:
        m = T.c == li; resid[m] -= resid[m].mean()
    betas = {al: np.linalg.solve(F[trm].T @ F[trm] + al * np.eye(4), F[trm].T @ resid[trm]) for al in (100.0, 300.0, 1000.0)}
    for sidm in u["targets"]:
        tg = c.make_target(T, H, sidm, "SV", allowed_history=u["allowed"], forbidden=u["forbidden"])
        truth = c.truth_of(T, tg); tv = (truth["y_s"] + truth["y_v"]) / 2.0
        r0 = sp(tg.q["S_both"], tv)
        key = (u["tissue"], sidm)
        for cf in cfgs:
            gains[f"own_h6|theta{cf[0]:g}"].setdefault(key, []).append(sp(fit.target_score(fits[cf], T, tg), tv) - r0)
        for al, b in betas.items():
            g = F[tg.rows] @ b
            gains[f"ridge_pair_features_a{al:g}"].setdefault(key, []).append(sp(tg.q["S_both"] + g, tv) - r0)
out = {}
for k, d in gains.items():
    lines = {kk: float(np.nanmean(v)) for kk, v in d.items()}
    out[k] = L.line_bootstrap(lines, {kk: kk[0] for kk in lines})
OUT.write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
