"""Checks 1 and 2: reproduce the HD simple-ranking totals / concordance and challenge D_add (independent code).

Run: PYTHONPATH='src;.' D:/anaconda/envs/maestro/python.exe research/astra/mono_pretraining_20261005/decisions/VERIFY_1_reproduce.py
Writes decisions/VERIFY_1_reproduce.json (refuses to overwrite).
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import VERIFY_lib as L  # noqa: E402
from research.astra.confirmation_campaign_20261004.design import campaign as c  # noqa: E402
from research.astra.mono_pretraining_20261005 import common as cm  # noqa: E402

OUT = L.HERE / "VERIFY_1_reproduce.json"


def additive_backfit(Hpairs, y, target_pairs, k0=2.0, sweeps=5):
    s = np.array([p[0] for p in Hpairs]); v = np.array([p[1] for p in Hpairs])
    mu = y.mean()
    a, b = {}, {}
    for _ in range(sweeps):
        r = y - mu - np.array([b.get(x, 0.0) for x in v])
        a = {d: r[s == d].sum() / ((s == d).sum() + k0) for d in set(s)}
        r = y - mu - np.array([a.get(x, 0.0) for x in s])
        b = {d: r[v == d].sum() / ((v == d).sum() + k0) for d in set(v)}
    return np.array([mu + a.get(p[0], 0.0) + b.get(p[1], 0.0) for p in target_pairs])


def additive_ridge(Hpairs, y, target_pairs, k0=2.0):
    """Exact joint ridge (penalty k0 on every drug effect, intercept = mean) for the same additive model."""
    sd = sorted({p[0] for p in Hpairs}); vd = sorted({p[1] for p in Hpairs})
    si = {d: i for i, d in enumerate(sd)}; vi = {d: len(sd) + i for i, d in enumerate(vd)}
    X = np.zeros((len(Hpairs), len(sd) + len(vd)))
    for r, p in enumerate(Hpairs):
        X[r, si[p[0]]] = 1.0; X[r, vi[p[1]]] = 1.0
    mu = y.mean()
    beta = np.linalg.solve(X.T @ X + k0 * np.eye(X.shape[1]), X.T @ (y - mu))
    out = []
    for p in target_pairs:
        out.append(mu + (beta[si[p[0]]] if p[0] in si else 0.0) + (beta[vi[p[1]]] if p[1] in vi else 0.0))
    return np.array(out)


def conc(score, truth):
    tv = (truth["y_s"] + truth["y_v"]) / 2.0
    if np.ptp(score) == 0 or np.ptp(tv) == 0:
        return np.nan
    return float(spearmanr(score, tv).correlation)


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"REFUSED: {OUT} exists")
    tissues, report, sp, e_sidms = L.load_hd("VERIFY phase 2: independent reproduction of HD simple rankings and D_add (E masked at load)")
    masked = L.assert_e_masked(tissues, e_sidms)
    fold = L.my_fold_of(sp)
    assert fold == cm.fold_of(sp), "my fold assignment differs from common.fold_of"
    my_units = L.units(sp, fold, cm.history_draw)
    from research.astra.mono_pretraining_20261005 import run_s2
    theirs = run_s2.units({"split": sp, "fold": fold}, "dev")
    assert len(my_units) == len(theirs) == 150 and all(
        (a["tissue"], a["fold"], a["draw"], a["hist"], a["targets"]) == (b["tissue"], b["fold"], b["draw"], b["hist"], b["targets"])
        for a, b in zip(my_units, theirs)), "unit definitions differ"
    rec = pickle.load(open(L.STUDY / "results/s2_dev_records.pkl", "rb"))
    their_camp = {(r["arm"], r["tissue"], r["line"], r["role"], r["draw"]): r for r in rec["campaigns"]}
    their_conc = {(r["arm"], r["tissue"], r["line"], r["draw"]): r["rho"] for r in rec["conc"] if r["cfg"] == -1}

    mine = {}      # (arm, tissue, line, role, draw) -> record
    mine_rho = {}
    variants = {}  # extra D_add variants: name -> {(tissue,line,role,draw): confirmed}
    addvar_rho = {}
    purchases_equal = conf_equal = rho_close = n = 0
    max_rho_diff = 0.0
    full_hist_rows = []   # diagnostic: additive vs pair-mean with full allowed history (HD outer-training lines)
    for u in my_units:
        T = tissues[u["tissue"]]
        H = c.restrict(T, u["hist"])
        for sidm in u["targets"]:
            for role in c.ROLES:
                tg = c.make_target(T, H, sidm, role, allowed_history=u["allowed"], forbidden=u["forbidden"])
                truth = c.truth_of(T, tg)
                sc = L.my_simple(T, u["hist"], sidm, role, tg.pid)
                # independence check: my scores equal the engine's quantities
                for b in L.SIMPLE:
                    assert np.allclose(sc[b][0], tg.scores[b][0], atol=1e-12) and np.allclose(sc[b][1], tg.scores[b][1], atol=1e-12), b
                Hp = [T.pairs[i] for i in np.flatnonzero(np.isin(T.c, [T.lines.index(s) for s in u["hist"]]))]
                A = T.arrays[role]
                hm = np.isin(T.c, [T.lines.index(s) for s in u["hist"]])
                yH = ((A["y_s"] + A["y_v"]) / 2.0)[hm]
                tp = [T.pairs[i] for i in tg.rows]
                sc["D_add"] = (lambda x: (x, x))(additive_backfit(Hp, yH, tp))
                alt = {"D_add_ridge": (lambda x: (x, x))(additive_ridge(Hp, yH, tp))}
                alt["D_add_S_both_verify"] = (sc["D_add"][0], sc["S_both"][1])
                for name, scores in list(sc.items()) + list(alt.items()):
                    tg.scores[name] = scores
                    r = c.run_p2(tg, truth, name, 30)
                    key = (name, u["tissue"], sidm, role, u["draw"])
                    if name in alt:
                        variants.setdefault(name, {})[key] = r["confirmed"]
                    else:
                        mine[key] = r
                        theirs_r = their_camp[key]
                        n += 1
                        purchases_equal += int(theirs_r["screens"] == r["screens"] and theirs_r["verifies"] == r["verifies"])
                        conf_equal += int(theirs_r["confirmed"] == r["confirmed"])
                    if role == "SV":
                        rho = conc(scores[0], truth)
                        (addvar_rho if name in alt else mine_rho)[(name, u["tissue"], sidm, u["draw"])] = rho
                        if name not in alt:
                            tr = their_conc[(name, u["tissue"], sidm, u["draw"])]
                            if np.isfinite(rho) or tr is not None and np.isfinite(tr):
                                d = abs(rho - tr)
                                max_rho_diff = max(max_rho_diff, d)
                                rho_close += int(d < 1e-9)
                # diagnostic: additive with the full outer-training HD history, and in-sample oracle additive
                if role == "SV" and u["draw"] == 0:
                    hm2 = np.isin(T.c, [T.lines.index(s) for s in u["allowed"]])
                    Hp2 = [T.pairs[i] for i in np.flatnonzero(hm2)]
                    y2 = ((A["y_s"] + A["y_v"]) / 2.0)[hm2]
                    full_add = additive_backfit(Hp2, y2, tp)
                    pid2 = T.pid[hm2]
                    full_pair = L.shrunk(pid2, y2, tg.pid)
                    ytrue = (truth["y_s"] + truth["y_v"]) / 2.0
                    insample_add = additive_ridge(tp, ytrue, tp, k0=2.0)   # target's OWN labels, diagnostic only
                    full_hist_rows.append(dict(tissue=u["tissue"], line=sidm, add_full=conc(full_add, truth),
                                               pair_full=conc(full_pair, truth), add_n4=conc(sc["D_add"][0], truth),
                                               pair_n4=conc(sc["S_both"][0], truth), add_insample_ceiling=conc(insample_add, truth)))

    def totals(recs):
        by = {}
        for (arm, t, l, role, d), r in recs.items():
            by.setdefault(arm, {}).setdefault((t, l), []).append(r["confirmed"] if isinstance(r, dict) else r)
        return {a: float(sum(np.mean(v) for v in lines.values())) for a, lines in by.items()}

    tot = totals(mine)
    sel = json.loads((L.STUDY / "results/s2_dev_selection.json").read_text())["simple_totals"]
    tot_theirs = {a: sel[a] for a in sel}
    tissue_of = {(t, l): t for (_, t, l, _, _) in mine}
    conc_by_arm = {}
    for (a, t, l, d), v in mine_rho.items():
        conc_by_arm.setdefault(a, {}).setdefault((t, l), []).append(v)
    conc_mean = {a: {k: float(np.nanmean(v)) for k, v in lines.items()} for a, lines in conc_by_arm.items()}
    conc_tot = {a: float(np.mean(list(lines.values()))) for a, lines in conc_mean.items()}
    add_variants = {}
    for name, d in variants.items():
        by = {}
        for (a, t, l, role, dr), v in d.items():
            by.setdefault((t, l), []).append(v)
        add_variants[name] = float(sum(np.mean(v) for v in by.values()))
    add_conc = {}
    for (a, t, l, d), v in addvar_rho.items():
        add_conc.setdefault(a, {}).setdefault((t, l), []).append(v)
    add_conc = {a: float(np.mean([np.nanmean(v) for v in lines.values()])) for a, lines in add_conc.items()}
    fh = {k: float(np.nanmean([r[k] for r in full_hist_rows])) for k in
          ("add_full", "pair_full", "add_n4", "pair_n4", "add_insample_ceiling")}
    base_conc = conc_mean["S_both"]
    gain_ci = {a: L.line_bootstrap({k: conc_mean[a][k] - base_conc[k] for k in base_conc if np.isfinite(conc_mean[a][k])},
                                   {k: k[0] for k in base_conc}) for a in conc_mean if a != "S_both"}
    res = dict(
        e_masking=dict(e_rows_masked=report["e_rows_masked"], sentinel_rows_per_tissue=masked),
        units_equal_to_run_s2_units=True, fold_assignment_equal=True,
        campaigns_compared=n, purchase_lists_identical=purchases_equal, confirmed_identical=conf_equal,
        concordance_records_within_1e9=rho_close, max_abs_concordance_difference=max_rho_diff,
        simple_totals_mine=tot, simple_totals_theirs=tot_theirs,
        simple_totals_max_abs_diff=max(abs(tot[a] - tot_theirs[a]) for a in tot_theirs),
        concordance_mean_over_lines_mine=conc_tot,
        concordance_gain_vs_S_both_mine=gain_ci,
        base_choice_mine=max(sorted(tot), key=lambda a: tot[a]),
        D_add_variants_total_confirmed=add_variants, D_add_variants_concordance=add_conc,
        additive_diagnostic_full_history_and_insample=fh, n_diag_lines=len(full_hist_rows))
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
