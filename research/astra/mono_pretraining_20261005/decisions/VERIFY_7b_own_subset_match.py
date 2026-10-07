"""Check 5c (b): is the own_h6 sweep subset consistent with the study's recorded own_h6 concordance (cfg 2)? Reads pkl + HD (E masked).
Writes decisions/VERIFY_7b_own_subset_match.json (refuses to overwrite)."""
import json, pickle, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import rankdata
sys.path.insert(0, str(Path(__file__).resolve().parent))
import VERIFY_lib as L
from tools.datasets.combination_screens import open_vault
from research.astra.confirmation_campaign_20261004.design import campaign as c
OUT = L.HERE / "VERIFY_7b_own_subset_match.json"
MONO = L.STUDY / "results/mono_labels.csv.gz"
def sp(a, b):
    if np.ptp(a) == 0 or np.ptp(b) == 0: return np.nan
    return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
if OUT.exists(): raise SystemExit("REFUSED")
open_vault(L.FREEZE, L.LOG, purpose="VERIFY phase 2: GDSC2 mono labels to match own_h6 records", source=MONO, root=L.ROOT)
mono = pd.read_csv(MONO, dtype={"jaaks_drug_id": str, "drug_id": str})
tissues, report, sp_, e_sidms = L.load_hd("VERIFY phase 2: HD outcomes to match recorded own_h6 concordance (E masked at load)")
L.assert_e_masked(tissues, e_sidms)
from research.astra.mono_pretraining_20261005 import common as cm, combo
from research.astra.mono_pretraining_20261005.bilinear import ComboConfig
drugs = cm.drug_table(); drow = dict(zip(drugs.jaaks_id, drugs.row)); mapped = drugs.mapped.to_numpy()
zc, rowc = cm.load_context()[1], cm.load_context()[2]
own_rec = mono[(~mono.sibling_id_record) & mono.jaaks_drug_id.notna() & mono.NOT_ELIGIBLE_target_line_own_mono_diagnostic_only]
own = {(r.sidm, int(drow[r.jaaks_drug_id])): float(r.y_rel) for r in own_rec.itertuples() if r.jaaks_drug_id in drow}
fit = combo.Fitter(zc, drow, rowc, mapped, own=own)
fold = L.my_fold_of(sp_); units = L.units(sp_, fold, cm.history_draw)
rec = pickle.load(open(L.STUDY / "results/s2_dev_records.pkl", "rb"))
pk = {(r["tissue"], r["line"], r["draw"]): r["rho"] for r in rec["conc"] if r["arm"] == "own_h6" and r["cfg"] == 2}
base = {(r["tissue"], r["line"], r["draw"]): r["rho"] for r in rec["conc"] if r["arm"] == "S_both"}
diffs, g_mine, g_pkl, g_pkl_all = [], [], [], []
for u in units[::5]:
    T = tissues[u["tissue"]]; H = c.restrict(T, u["hist"])
    pf = {k: v for k, v in np.load(L.STUDY / f"results/mono_params/F{u['fold']}_pre.npz").items()}
    for sidm in u["targets"][:4]:
        tg = c.make_target(T, H, sidm, "SV", allowed_history=u["allowed"], forbidden=u["forbidden"])
        truth = c.truth_of(T, tg); tv = (truth["y_s"] + truth["y_v"]) / 2.0
        p = fit.fit("own", pf, H, ComboConfig(features="h6", l2_theta=30.0, l2_init=10.0))
        rho = sp(fit.target_score(p, T, tg), tv)
        key = (u["tissue"], sidm, u["draw"])
        diffs.append(abs(rho - pk[key])); g_mine.append(rho - sp(tg.q["S_both"], tv)); g_pkl.append(pk[key] - base[key])
allg = [pk[k] - base[k] for k in pk if np.isfinite(pk[k])]
out = dict(n_records=len(diffs), max_abs_diff_vs_recorded_rho=float(max(diffs)), mean_gain_mine_subset=float(np.mean(g_mine)),
           mean_gain_recorded_same_subset=float(np.mean(g_pkl)), mean_gain_recorded_all_640=float(np.mean(allg)),
           sd_of_per_record_gain=float(np.std(allg)))
OUT.write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
