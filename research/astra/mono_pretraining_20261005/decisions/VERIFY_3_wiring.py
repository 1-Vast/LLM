"""Check 3 (a, b, c, d): wiring of own-mono, mono-leakage re-derivation, independent mono retrain, poisoning.

Run: PYTHONPATH='src;.' D:/anaconda/envs/maestro/python.exe research/astra/mono_pretraining_20261005/decisions/VERIFY_3_wiring.py
Writes decisions/VERIFY_3_wiring.json (refuses to overwrite). E outcomes are masked at load (VERIFY_lib).
"""
from __future__ import annotations

import json
import re
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

OUT = L.HERE / "VERIFY_3_wiring.json"
S0 = L.STUDY / "data_s0"
MONO = L.STUDY / "results/mono_labels.csv.gz"
PROGENY = L.ROOT / "research/astra/knowledge_transfer_20261004/context/raw/GDSC_progeny_activities.csv"
VALID = L.ROOT / "data/external/gdsc_combinations/jaaks2022_figshare/validation_screen_all_tissues_fitted.csv"


def norm(s):
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


def spearman(a, b):
    if len(a) < 4 or np.ptp(b) == 0:
        return np.nan
    if np.ptp(a) == 0:
        return 0.0
    return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])


def within_cell(cell, pred, y, min_drugs=8):
    out = {}
    for ce in np.unique(cell):
        m = cell == ce
        if m.sum() >= min_drugs:
            r = spearman(pred[m], y[m])
            if np.isfinite(r):
                out[int(ce)] = r
    return out


def my_pretrain(z, cell, drug, y, n_drugs, w, steps, l2, seed, lr=0.02, rank=4):
    g = torch.Generator().manual_seed(seed)
    W = torch.nn.Parameter(torch.randn(z.shape[1], rank, generator=g, dtype=torch.float64) * 0.3 / np.sqrt(z.shape[1]) * np.sqrt(rank))
    E = torch.nn.Parameter(torch.randn(n_drugs, rank, generator=g, dtype=torch.float64) * 0.3)
    beta = torch.nn.Parameter(torch.zeros(n_drugs, dtype=torch.float64))
    zt, ct, dt = torch.as_tensor(z), torch.as_tensor(cell), torch.as_tensor(drug)
    yt, wt = torch.as_tensor(y), torch.as_tensor(w)[dt]
    opt = torch.optim.Adam([W, E, beta], lr=lr)
    for _ in range(steps):
        opt.zero_grad()
        r = zt @ W
        pred = beta[dt] + (r[ct] * E[dt]).sum(1)
        loss = (((pred - yt) ** 2) * wt).mean() + l2 * (W ** 2).mean() + l2 * (E ** 2).mean()
        loss.backward()
        opt.step()
    return W.detach().numpy(), E.detach().numpy(), beta.detach().numpy()


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"REFUSED: {OUT} exists")
    res = {}
    sp = L.split()
    fold = L.my_fold_of(sp)
    ticket = open_vault(L.FREEZE, L.LOG, purpose="VERIFY phase 2: GDSC2 mono labels (results/mono_labels.csv.gz) for wiring, leakage and retrain checks",
                        source=MONO, root=L.ROOT)
    mono = pd.read_csv(MONO, dtype={"jaaks_drug_id": str, "drug_id": str})
    # ---------------------------------------------------------------- Jaaks identity sets from DESIGN columns only
    cols = ["SIDM", "CELL_LINE_NAME", "COSMIC_ID"]
    jo = pd.read_csv(L.jk.RELEASE, usecols=cols, dtype=str).drop_duplicates()
    jv = pd.read_csv(VALID, usecols=cols, dtype=str).drop_duplicates()
    jall = pd.concat([jo, jv]).drop_duplicates()
    J_sidm = set(jall.SIDM.str.strip())
    J_cos = set(jall.COSMIC_ID.dropna().str.strip().str.replace(r"\.0$", "", regex=True))
    J_name = {norm(x) for x in jall.CELL_LINE_NAME}
    J125 = set(fold)
    res["jaaks_identity_sets"] = dict(original_sidms=int(jo.SIDM.nunique()), validation_sidms=int(jv.SIDM.nunique()),
                                      union_sidms=len(J_sidm), partition_125=len(J125), partition_subset_of_union=J125 <= J_sidm,
                                      HPAF_II_in_union="SIDM00669" in J_sidm, HPAF_II_in_partition="SIDM00669" in J125)
    # ---------------------------------------------------------------- re-derive mono records and pools
    prog_sidms = set(pd.read_csv(PROGENY, index_col=0).columns)
    d = pd.read_csv(S0 / "drug_identity_map.csv", dtype={"jaaks_id": str})
    mapped = set(d.loc[d.status == "mapped", "jaaks_id"])
    m = mono[(~mono.sibling_id_record) & mono.jaaks_drug_id.notna()].copy()
    m = m[m.jaaks_drug_id.isin(mapped)]
    m["has_ctx"] = m.sidm.isin(prog_sidms)
    assert (m.has_ctx == m.has_context14).all(), "context flag differs from PROGENy columns"
    m = m[m.has_ctx].copy()
    m["fold"] = m.sidm.map(lambda s: fold[s][1] if s in fold else None)
    m["is_j125"] = m.sidm.isin(J125)
    mine_elig = (~m.sidm.isin(J_sidm)) & (~m.cosmic_id.astype(str).str.replace(r"\.0$", "", regex=True).isin(J_cos)) \
        & (~m.cell_line_name.map(norm).isin(J_name))
    flag = m.eligible_primary_pretrain.astype(bool)
    res["eligibility_rederivation"] = dict(
        n_records=len(m), flag_true=int(flag.sum()), mine_true=int(mine_elig.sum()),
        disagreements=int((flag != mine_elig).sum()),
        eligible_rows_with_Jaaks_sidm=int(m[flag].sidm.isin(J_sidm).sum()),
        eligible_rows_with_Jaaks_cosmic=int(m[flag].cosmic_id.astype(str).str.replace(r"\.0$", "", regex=True).isin(J_cos).sum()),
        eligible_rows_with_Jaaks_name=int(m[flag].cell_line_name.map(norm).isin(J_name).sum()),
        HPAF_II_rows=int((m.sidm == "SIDM00669").sum()), HPAF_II_rows_flagged_eligible=int(flag[m.sidm == "SIDM00669"].sum()))
    pools = {}
    for k in list(range(5)) + ["E"]:
        theirs_rule = m[flag | (m.is_j125 & (m.fold != k))]             # run_s1.train_pool logic
        mine_rule = m[mine_elig | (m.is_j125 & (m.fold != k))]
        held = set(s for s, (t, f) in fold.items() if f == k)
        tr_s = set(theirs_rule.sidm)
        pools[k] = dict(n_records=len(theirs_rule), n_cells=len(tr_s), same_as_mine=bool(set(zip(theirs_rule.sidm, theirs_rule.drug_id)) == set(zip(mine_rule.sidm, mine_rule.drug_id))),
                        held_out_lines=len(held), held_out_in_training=len(held & tr_s),
                        HPAF_II_in_training="SIDM00669" in tr_s,
                        jaaks_lines_in_training=len(tr_s & J125), E_lines_in_training=len({s for s in tr_s if s in fold and fold[s][1] == "E"}),
                        aliases_by_cosmic_or_name_in_training=int(theirs_rule[~theirs_rule.sidm.isin(J125)].cosmic_id.astype(str).str.replace(r"\.0$", "", regex=True).isin(J_cos).sum()
                                                                  + theirs_rule[~theirs_rule.sidm.isin(J125)].cell_line_name.map(norm).isin(J_name).sum()))
    res["pools_by_config"] = pools
    # ---------------------------------------------------------------- (c) independent retrain of F0 'pre'
    z_df = pd.read_csv(PROGENY, index_col=0).T.sort_index()
    zx = z_df.to_numpy(float)
    zs = (zx - zx.mean(0)) / zx.std(0)
    row = {s: i for i, s in enumerate(z_df.index)}
    drugs_sorted = sorted(mapped)
    di = {x: i for i, x in enumerate(drugs_sorted)}
    cfg = json.loads((L.STUDY / "results/s1_mono_config.json").read_text())["chosen"]
    out_c = {}
    for k in (0,):
        tr = m[flag | (m.is_j125 & (m.fold != k))].copy()
        cells = sorted(tr.sidm.map(row).unique()); ci = {x: i for i, x in enumerate(cells)}
        cell = tr.sidm.map(row).map(ci).to_numpy(); drug = tr.jaaks_drug_id.map(di).to_numpy()
        y = tr.y_rel.to_numpy().copy()
        w = np.ones(len(di))
        for dd in range(len(di)):
            mk = drug == dd
            if mk.sum() > 20:
                lo, hi = np.quantile(y[mk], [0.01, 0.99]); y[mk] = np.clip(y[mk], lo, hi); w[dd] = 1.0 / max(np.var(y[mk]), 1e-6)
        w = w / w.mean()
        held = m[m.is_j125 & (m.fold == k)]
        hc = held.sidm.map(row).to_numpy(); hd_ = held.jaaks_drug_id.map(di).to_numpy(); hy = held.y_rel.to_numpy()
        theirs = {kk: v for kk, v in np.load(L.STUDY / "results/mono_params/F0_pre.npz").items()}
        # their drug rows follow cm.drug_table order = mapped sorted by id string (identical to drugs_sorted)
        tp = theirs["beta"][hd_] + ((zs[hc] @ theirs["W"]) * theirs["E"][hd_]).sum(1)
        wc_theirs = within_cell(hc, tp, hy)
        trd = tr.groupby("jaaks_drug_id").y_rel.mean()
        dm = hd_.copy().astype(float); dm = np.array([trd.get(drugs_sorted[i], 0.0) for i in hd_])
        wc_dm = within_cell(hc, dm, hy)
        mine_runs = []
        for seed in (1, 2, 3):
            W, E, b = my_pretrain(zs[cells], cell, drug, y, len(di), w, int(cfg["steps"]), cfg["l2"], seed)
            pr = b[hd_] + ((zs[hc] @ W) * E[hd_]).sum(1)
            wc = within_cell(hc, pr, hy)
            mine_runs.append(dict(seed=seed, within_cell_spearman=float(np.mean(list(wc.values()))), n_cells=len(wc),
                                  corr_with_their_predictions=float(np.corrcoef(pr, tp)[0, 1])))
        out_c[f"fold{k}"] = dict(n_train_records=len(tr), n_train_cells=len(cells), n_heldout_records=len(held),
                                 theirs_within_cell=float(np.mean(list(wc_theirs.values()))), n_cells=len(wc_theirs),
                                 drug_mean_baseline=float(np.mean(list(wc_dm.values()))), mine=mine_runs,
                                 s1_g1_pooled_pre=json.loads((L.STUDY / "results/s1_g1.json").read_text())["arms"]["pre"]["within_cell"])
    res["retrain_check"] = out_c
    # ---------------------------------------------------------------- (a) own-mono wiring on their actual training/target rows
    tissues, report, sp2, e_sidms = L.load_hd("VERIFY phase 2: HD outcomes for own-mono wiring and poisoning checks (E masked at load)")
    L.assert_e_masked(tissues, e_sidms)
    from research.astra.mono_pretraining_20261005 import common as cm, combo, run_s2
    own_rec = mono[(~mono.sibling_id_record) & mono.jaaks_drug_id.notna() & mono.NOT_ELIGIBLE_target_line_own_mono_diagnostic_only]
    dup = int(own_rec.duplicated(["sidm", "jaaks_drug_id"]).sum())
    y_re = (own_rec.ln_ic50 - np.log(own_rec.max_conc)) / np.log(2.0)
    res["own_table"] = dict(records=len(own_rec), lines=int(own_rec.sidm.nunique()), duplicates_sidm_drug=dup,
                            max_abs_yrel_recompute=float(np.abs(y_re - own_rec.y_rel).max()),
                            lines_in_partition=int(own_rec.sidm.isin(J125).sum()), E_lines_records=int(own_rec.sidm.isin(
                                {s for s, (t, f) in fold.items() if f == "E"}).sum()))
    drugs = cm.drug_table()
    drow = dict(zip(drugs.jaaks_id, drugs.row))
    mapped_arr = drugs.mapped.to_numpy()
    zc, rowc = cm.load_context()[1], cm.load_context()[2]
    own = {(r.sidm, int(drow[r.jaaks_drug_id])): float(r.y_rel) for r in own_rec.itertuples() if r.jaaks_drug_id in drow}
    fit_own = combo.Fitter(zc, drow, rowc, mapped_arr, own=own)
    fracs_train, fracs_target, mism = [], [], 0.0
    my_own = {(r.sidm, di[r.jaaks_drug_id]): float(y_re[i]) for i, r in zip(own_rec.index, own_rec.itertuples()) if r.jaaks_drug_id in di}
    units = L.units(sp, fold, cm.history_draw)
    for u in units[::7]:                                   # a sample of 22 units
        T = tissues[u["tissue"]]
        H = c.restrict(T, u["hist"])
        pf = {kk: v for kk, v in np.load(L.STUDY / f"results/mono_params/F{u['fold']}_pre.npz").items()}
        rows = combo.training_rows(H, drow, rowc, mapped_arr)
        uo_a, uo_b = fit_own._uo(pf, rows)
        # independent recomputation: u = clip(y_rel - beta_d, +-4); line of a row from its cell row
        sid_of = {v: kk for kk, v in rowc.items()}
        mine_a = np.array([np.clip(my_own.get((sid_of[int(cc)], int(a)), np.nan) - pf["beta"][int(a)], -4, 4) for cc, a in zip(rows["cell"], rows["anchor"])])
        mine_b = np.array([np.clip(my_own.get((sid_of[int(cc)], int(b)), np.nan) - pf["beta"][int(b)], -4, 4) for cc, b in zip(rows["cell"], rows["library"])])
        for x, yv in ((uo_a, mine_a), (uo_b, mine_b)):
            ok = np.isfinite(x) & np.isfinite(yv)
            mism = max(mism, float(np.abs(x[ok] - yv[ok]).max()) if ok.any() else 0.0)
            assert (np.isfinite(x) == np.isfinite(yv)).all()
        fracs_train.append(float(np.mean(np.isfinite(uo_a) & np.isfinite(uo_b))))
        for sidm in u["targets"][:3]:
            tg = c.make_target(T, H, sidm, "SV", allowed_history=u["allowed"], forbidden=u["forbidden"])
            pairs = [T.pairs[i] for i in tg.rows]
            s = np.array([drow[p[0]] for p in pairs]); v = np.array([drow[p[1]] for p in pairs])
            ua = combo.own_shift(own, pf["beta"], sidm, s); ub = combo.own_shift(own, pf["beta"], sidm, v)
            fracs_target.append(float(np.mean(np.isfinite(ua) & np.isfinite(ub))))
    res["own_wiring"] = dict(units_checked=len(units[::7]), frac_training_rows_with_observed_shift_both_drugs=float(np.mean(fracs_train)),
                             frac_target_menu_with_observed_shift_both_drugs=float(np.mean(fracs_target)),
                             max_abs_diff_shift_vs_independent=mism,
                             note="shift u = clip(y_rel - beta_drug, +-4); y_rel raw (unwinsorised); combination labels never enter the shift")
    # ---------------------------------------------------------------- (d) poisoning on pre_h6 scores through run_s2.score_unit
    S = dict(tissues=tissues, z=zc, row=rowc, drow=drow, mapped=mapped_arr, own=own, n_drugs=len(drugs))
    specs_all = run_s2.arm_specs(len(drugs))
    specs = {"pre_h6": specs_all["pre_h6"], "scr0_h6": specs_all["scr0_h6"]}
    selected = {"pre_h6": 3, "scr_h6": 3}
    pois = []
    for u in [units[i] for i in (3, 47, 101)]:
        a = run_s2.build_targets(S, u)
        _, sc_a = run_s2.score_unit(S, specs, u, selected, a)
        # poisoned copy: flip every outcome of the unit's targets and of all HD lines that are not history
        T0 = tissues[u["tissue"]]
        T1 = c.restrict(T0, sorted(set(T0.present_lines)))     # fresh view (copies arrays)
        bad = [T0.lines.index(s_) for s_ in sorted(set(u["targets"]) | (set(T0.present_lines) - set(u["hist"])))]
        mk = np.isin(T1.c, bad)
        rng = np.random.default_rng(0)
        for role in ("SV", "VS"):
            A_ = T1.arrays[role]
            for kk in ("y_s", "y_v"):
                A_[kk][mk] = rng.normal(0, 50, mk.sum())
            for kk in ("h_s", "h_v"):
                A_[kk][mk] = ~A_[kk][mk]
        S2 = dict(S, tissues=dict(tissues, **{u["tissue"]: T1}))
        b = run_s2.build_targets(S2, u)
        _, sc_b = run_s2.score_unit(S2, specs, u, selected, b)
        diffs = [float(np.abs(sc_a[k] - sc_b[k]).max()) for k in sc_a]
        pois.append(dict(unit=f"{u['tissue']}/fold{u['fold']}/draw{u['draw']}", n_score_vectors=len(sc_a), max_abs_score_diff=max(diffs),
                         rows_poisoned=int(mk.sum())))
    res["poisoning"] = pois
    OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
