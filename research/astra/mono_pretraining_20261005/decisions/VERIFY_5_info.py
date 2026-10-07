"""Check 5: is the own-mono ceiling failure an information fact or a wiring/fit artefact? (independent code)

Part A (information, full HD history, ridge/univariate tests with own GDSC2 mono) and part B (regularisation sweep of the
study's own pre_h6 / dperm / scratch pipeline on a subset of units). HD outcomes only (E masked at load), GDSC2 mono
labels from results/mono_labels.csv.gz. Run:
PYTHONPATH='src;.' D:/anaconda/envs/maestro/python.exe research/astra/mono_pretraining_20261005/decisions/VERIFY_5_info.py
Writes decisions/VERIFY_5_info.json (refuses to overwrite).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import VERIFY_lib as L  # noqa: E402
from tools.datasets.combination_screens import open_vault  # noqa: E402
from research.astra.confirmation_campaign_20261004.design import campaign as c  # noqa: E402

OUT = L.HERE / "VERIFY_5_info.json"
MONO = L.STUDY / "results/mono_labels.csv.gz"


def sp(a, b):
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return np.nan
    return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])


def part_a(tissues, mono, hd_lines, synthetic=False, rng=None):
    """Return dict of information tests over the 64 HD lines (tissue-wise full-HD leave-one-line-out)."""
    # per-drug standardisation of own y_rel from NON-Jaaks eligible cells only
    elig = mono[mono.eligible_primary_pretrain & ~mono.sibling_id_record & mono.jaaks_drug_id.notna()]
    st = elig.groupby("jaaks_drug_id").y_rel.agg(["mean", "std"])
    own = mono[mono.NOT_ELIGIBLE_target_line_own_mono_diagnostic_only & ~mono.sibling_id_record & mono.jaaks_drug_id.notna()]
    mval = {}
    for r in own.itertuples():
        if r.jaaks_drug_id in st.index:
            mval[(r.sidm, r.jaaks_drug_id)] = (r.y_rel - st.loc[r.jaaks_drug_id, "mean"]) / st.loc[r.jaaks_drug_id, "std"]
    res = {"per_tissue": {}}
    drug_r, perm_r = [], []
    line_gain = {}
    for tissue, T in tissues.items():
        lines = [s for s in hd_lines[tissue]]
        li = {s: T.lines.index(s) for s in lines}
        A = T.arrays["SV"]
        y = (A["y_s"] + A["y_v"]) / 2.0
        pairs = T.pairs
        S_id = np.array([p[0] for p in pairs]); V_id = np.array([p[1] for p in pairs])
        ms = np.array([mval.get((T.lines[int(ci)], a), np.nan) for ci, a in zip(T.c, S_id)])
        mv = np.array([mval.get((T.lines[int(ci)], b), np.nan) for ci, b in zip(T.c, V_id)])
        hd_mask = np.isin(T.c, list(li.values()))
        pid = T.pid
        # leave-own-line-out shrunk pair mean over HD lines of the tissue
        mu_all = y[hd_mask].mean()
        size = int(pid.max()) + 1
        ssum = np.bincount(pid[hd_mask], weights=y[hd_mask], minlength=size)
        scnt = np.bincount(pid[hd_mask], minlength=size).astype(float)
        mu_lo = (y[hd_mask].sum() - y) / (hd_mask.sum() - 1)
        prior = (ssum[pid] - y + 2.0 * mu_lo) / (scnt[pid] - 1 + 2.0)       # exact LOO of the row's own observation
        resid = y - prior
        for s in lines:                                                      # centre within line
            m = T.c == li[s]
            resid[m] -= resid[m].mean()
        if synthetic:                                                        # positive control: inject a drug-in-line effect
            drugs = sorted(set(S_id) | set(V_id))
            beta = {d: rng.normal(0, 1.0) for d in drugs}
            eff = np.array([beta[a] * (0 if np.isnan(x) else x) + beta[b] * (0 if np.isnan(z) else z)
                            for a, b, x, z in zip(S_id, V_id, ms, mv)])
            eff[~hd_mask] = 0.0
            resid = resid + 0.5 * resid[hd_mask].std() * eff / eff[hd_mask].std()
            y = prior + resid + 0.0
        # ---- test 1: drug-in-line association, within tissue
        for d in sorted(set(S_id) | set(V_id)):
            xs, zs = [], []
            for s in lines:
                m = (T.c == li[s]) & ((S_id == d) | (V_id == d))
                x = mval.get((s, d), np.nan)
                if m.sum() >= 3 and np.isfinite(x):
                    xs.append(x); zs.append(resid[m].mean())
            if len(xs) >= 10:
                r = sp(np.array(xs), np.array(zs))
                if np.isfinite(r):
                    drug_r.append(r)
                    perm_r.append([sp(rng.permutation(xs), np.array(zs)) for _ in range(200)] if rng is not None else [])
        # ---- test 2: LOLO ridge with drug-specific slopes on own sensitivity
        drugs = sorted(set(S_id) | set(V_id)); dix = {d: i for i, d in enumerate(drugs)}
        X = np.zeros((len(y), len(drugs)))
        for r_i in np.flatnonzero(hd_mask):
            if np.isfinite(ms[r_i]):
                X[r_i, dix[S_id[r_i]]] += ms[r_i]
            if np.isfinite(mv[r_i]):
                X[r_i, dix[V_id[r_i]]] += mv[r_i]
        Xp = np.column_stack([np.nan_to_num(ms), np.nan_to_num(mv), np.nan_to_num(ms) * np.nan_to_num(mv),
                              np.abs(np.nan_to_num(ms) - np.nan_to_num(mv))])
        for variant, F, alpha in (("drug_slopes", X, 300.0), ("pair_features", Xp, 300.0)):
            for s in lines:
                tr = hd_mask & (T.c != li[s]); te = T.c == li[s]
                Ft = F[tr]
                beta = np.linalg.solve(Ft.T @ Ft + alpha * np.eye(F.shape[1]), Ft.T @ resid[tr])
                g = F[te] @ beta
                tv = y[te]
                base = prior[te]
                # the prior of the target line is the LOO prior (history = the other HD lines)
                c0 = sp(base, tv)
                c1 = sp(base + g, tv)
                # residual R^2 within line
                r2 = 1.0 - ((resid[te] - g) ** 2).sum() / (resid[te] ** 2).sum()
                line_gain.setdefault(variant, {})[(tissue, s)] = (c1 - c0, r2, c0)
    out = {"drug_in_line": dict(n_groups=len(drug_r), mean_spearman=float(np.mean(drug_r)),
                                null_mean=float(np.mean([np.mean(p) for p in zip(*perm_r)])) if perm_r and perm_r[0] else None,
                                null_p95_of_mean=float(np.percentile([np.mean(p) for p in zip(*perm_r)], 95)) if perm_r and perm_r[0] else None,
                                frac_positive=float(np.mean(np.array(drug_r) > 0)))}
    for variant, d in line_gain.items():
        keys = sorted(d)
        gains = {k: d[k][0] for k in keys if np.isfinite(d[k][0])}
        b = L.line_bootstrap(gains, {k: k[0] for k in gains})
        out[variant] = dict(concordance_gain_over_pair_prior=b, mean_residual_r2=float(np.mean([d[k][1] for k in keys])),
                            base_concordance=float(np.nanmean([d[k][2] for k in keys])))
    return out


def part_b(S, units, sub):
    from research.astra.mono_pretraining_20261005 import run_s2
    from research.astra.mono_pretraining_20261005.bilinear import ComboConfig
    from research.astra.mono_pretraining_20261005.combo import Fitter
    specs_all = run_s2.arm_specs(S["n_drugs"])
    use = {"pre_h6": specs_all["pre_h6"], "dperm0_h6": specs_all["dperm0_h6"], "scr0_h6": specs_all["scr0_h6"],
           "pot_p3": specs_all["pot_p3"]}
    cfgs = [(30.0, 300.0), (300.0, 300.0), (3000.0, 300.0), (30000.0, 300.0)]
    gains = {(a, ct): {} for a in use for ct in cfgs}
    ratio = {a: [] for a in use}
    fit = Fitter(S["z"], S["drow"], S["row"], S["mapped"])
    for u in units[::sub]:
        T = S["tissues"][u["tissue"]]
        H = c.restrict(T, u["hist"])
        for sidm in u["targets"][:4]:
            tg = c.make_target(T, H, sidm, "SV", allowed_history=u["allowed"], forbidden=u["forbidden"])
            truth = c.truth_of(T, tg)
            tv = (truth["y_s"] + truth["y_v"]) / 2.0
            base = tg.q["S_both"]
            r0 = sp(base, tv)
            for a, spc in use.items():
                for ct in cfgs:
                    cfg = ComboConfig(features=spc["features"], l2_theta=ct[0], l2_init=ct[1])
                    p = fit.fit(a, spc["init"](u["fold"]), H, cfg)
                    sc = fit.target_score(p, T, tg)
                    gains[(a, ct)].setdefault((u["tissue"], sidm), []).append(sp(sc, tv) - r0)
                    if ct == cfgs[0]:
                        ratio[a].append(float(np.std(sc - base) / np.std(base)))
    out = {}
    for (a, ct), d in gains.items():
        out[f"{a}|theta{ct[0]:g}|init{ct[1]:g}"] = float(np.mean([np.mean(v) for v in d.values()]))
    return dict(mean_concordance_gain_over_S_both=out, std_g_over_std_prior_at_theta30={a: float(np.mean(v)) for a, v in ratio.items()},
                n_units=len(units[::sub]), n_lines=len(next(iter(gains.values()))))


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"REFUSED: {OUT} exists")
    open_vault(L.FREEZE, L.LOG, purpose="VERIFY phase 2: GDSC2 mono labels for the independent own-mono information test", source=MONO, root=L.ROOT)
    mono = pd.read_csv(MONO, dtype={"jaaks_drug_id": str, "drug_id": str})
    tissues, report, sp_, e_sidms = L.load_hd("VERIFY phase 2: HD outcomes for the independent own-mono information test and regularisation sweep (E masked at load)")
    L.assert_e_masked(tissues, e_sidms)
    hd_lines = {t: sorted(v["HD"]) for t, v in sp_.items()}
    rng = np.random.default_rng(7)
    real = part_a(tissues, mono, hd_lines, synthetic=False, rng=rng)
    synth = part_a(tissues, mono, hd_lines, synthetic=True, rng=np.random.default_rng(11))
    from research.astra.mono_pretraining_20261005 import common as cm
    drugs = cm.drug_table()
    zc, rowc = cm.load_context()[1], cm.load_context()[2]
    S = dict(tissues=tissues, z=zc, row=rowc, drow=dict(zip(drugs.jaaks_id, drugs.row)), mapped=drugs.mapped.to_numpy(), own=None,
             n_drugs=len(drugs))
    fold = L.my_fold_of(sp_)
    units = L.units(sp_, fold, cm.history_draw)
    b = part_b(S, units, sub=5)
    res = dict(part_a_real=real, part_a_synthetic_positive_control=synth, part_b_regularisation_sweep=b)
    OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
