"""Frozen evaluation script.  `python final_eval.py final` is run ONCE after FREEZE.json exists (it claims the final stage); `python final_eval.py sel` is the
exposed dry run of the same code on the selection stage (development evidence, never confirmatory).
Outputs: RUN/<stage>_eval/RESULTS.json and CSVs.  All inference uses cluster bootstrap over background LINEAGES with multiplicity (B=10000, seed 20261021)."""
from __future__ import annotations
import json, sys, time, warnings
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, torch
import ptv_data as D, ptv_tasks as T, ptv_direct as X, ptv_eval as E, eval_R as R, eval_Q as Q, agent_data as AD, agent_search as AS, ptv_env as ENV

EPOCH = {"full": 30, "no_traj": 30, "no_fp": 45}
NAME = R.NAMES
DELTA_T = 0.09      # precision@5 margin (about 0.45 confirmed hits per 5 nominations)
DELTA_E = 0.40      # confirmed hits per background under the 5.0-unit contract
B = 10000
SEED = 20261021


def ci(vals, lins):
    return R.boot_lineage(pd.Series(np.asarray(vals, float)), pd.Series(np.asarray(lins)), B=B, seed=SEED)


def label(lo, hi, delta, higher_better=True):
    """SUPPORTED_USEFUL_GAIN: lower bound above +delta.  NO_USEFUL_GAIN_WITHIN_RESOLUTION: upper bound below +delta.  Otherwise INCONCLUSIVE."""
    if lo > delta: return "SUPPORTED_USEFUL_GAIN"
    if hi < delta: return "NO_USEFUL_GAIN_WITHIN_RESOLUTION"
    return "INCONCLUSIVE"


def contrast(df, a, b, metric, delta):
    """Paired per-background difference a-b of a metric column; returns estimate, 95% interval, n independent lineages and decision label."""
    pa = df[df.score == a].set_index("cell")[metric]; pb = df[df.score == b].set_index("cell")[metric]
    idx = pa.dropna().index.intersection(pb.dropna().index)
    d = (pa[idx] - pb[idx]).values
    lin = np.array([D.lineage_of(c) for c in idx])
    lo, hi = ci(d, lin)
    return {"a": a, "b": b, "metric": metric, "diff": float(d.mean()), "ci95": [lo, hi], "n_backgrounds": int(len(idx)), "n_lineages": int(len(set(lin))),
            "margin": delta, "label": label(lo, hi, delta), "significantly_negative": bool(hi < 0)}


def load_scores(P, dr, stage, rundir):
    sc = R.direct_scores(P, dr, stage, None)
    ex, hold, train = R.stage_inputs(P, stage)
    sc = sc.copy()
    for v, nm in NAME.items():
        cols = []
        for seed in (0, 1):
            parts = []
            for f in sorted(Path(rundir).glob(f"{stage}_*_{v}_s{seed}.npz")):
                z = np.load(f, allow_pickle=True)
                parts.append(pd.DataFrame({"cell": z["cell"], "perts": z["perts"], f"{nm}_s{seed}": z[f"p_e{EPOCH[v]}"]}).loc[lambda d: z["single"]])
            if parts:
                sc = sc.merge(pd.concat(parts), on=["cell", "perts"], how="left"); cols.append(f"{nm}_s{seed}")
        sc[nm + "_mean"] = sc[cols].mean(axis=1)
    return sc, train


def part_R(P, dr, stage, rundir, out):
    sc, train = load_scores(P, dr, stage, rundir)
    cols = ["b0", "b1", "m0_lr", "m0_hgb"] + [c for c in sc.columns if c[:2] in ("M1", "M2", "M3") and c[2:3] == "_"]
    sc = sc[sc.y.notna()]
    dt = R.decision_table(sc, train, cols)
    dt.to_csv(out / "R_decision_table.csv", index=False)
    pool = dt[dt.prec_at_k_pool.notna()]
    res = {"n_backgrounds_in_table": int(dt.cell.nunique()), "n_backgrounds_with_pool": int(pool.cell.nunique()), "means": dt.groupby("score")[["auroc_all", "auroc_pool", "prec_at_k_pool", "brier_pool"]].mean().round(4).to_dict("index")}
    Cstar = "b1"
    cons = []
    for a, b in (("M1_s0", Cstar), ("M1_s0", "m0_lr"), ("M1_s0", "M2_s0"), ("M1_s0", "M3_s0"), ("M2_s0", Cstar), ("M1_mean", Cstar), ("m0_lr", Cstar), ("M1_s1", Cstar)):
        for metric, delta in (("prec_at_k_pool", DELTA_T), ("auroc_pool", 0.0), ("brier_pool", 0.0)):
            if a in dt.score.values and b in dt.score.values:
                c = contrast(pool, a, b, metric, delta)
                if metric == "brier_pool":   # lower is better: report the improvement as b - a
                    c = contrast(pool.assign(brier_pool=-pool.brier_pool), a, b, metric, 0.0); c["note"] = "sign reversed: positive = lower Brier for a"
                cons.append(c)
    res["contrasts"] = cons
    # calibration of pooled contested-pool predictions
    cal = {}
    for col in ("b1", "m0_lr", "M1_s0", "M2_s0", "M3_s0"):
        if col not in sc.columns: continue
        ys, ps = [], []
        for c in sc.cell.unique():
            te = sc[sc.cell == c].set_index("perts"); pl = T.contested_pool(train[~train.lineage.isin([D.lineage_of(c)])].dropna(subset=["y"]), list(te.index))
            ys += list(te.loc[pl].y); ps += list(te.loc[pl][col])
        ys, ps = np.array(ys), np.array(ps)
        cal[col] = {"n": int(len(ys)), "brier": E.brier(ps, ys), "calib_slope": E.calib_slope(ps, ys), "mean_pred": float(ps.mean()), "prevalence": float(ys.mean())}
    res["calibration_pooled_pool"] = cal
    # molecular intervention-response skill
    mol = {}
    for v in ("full", "no_traj", "no_fp"):
        ms = R.molecular_skill(P, stage, rundir, seed=0, variant=v)
        if len(ms):
            ms.to_csv(out / f"R_molecular_{NAME[v]}.csv", index=False)
            m = ms.groupby("t")[["mse_model", "mse_C1", "mse_C2", "mse_C3", "corr_model", "corr_C1", "corr_C2", "corr_C3", "tgt_mse_model", "tgt_mse_C1", "tgt_mse_C3"]].mean().round(5)
            mol[NAME[v]] = {"by_time": m.to_dict("index"), "n_rows": int(len(ms)), "n_rows_singles": int(ms.single.sum())}
    res["molecular_skill"] = mol
    return res, sc


def part_Q(P, dr, stage, rundir_m1, out):
    grid = [("func", 10, 1e-4), ("mol", 10, 1e-4), ("both", 10, 1e-4)]
    df = Q.run(stage, rundir_m1, "full", 0, grid, dev="cuda" if torch.cuda.is_available() else "cpu")
    df.to_csv(out / "Q_per_background.csv", index=False)
    res = {"means": df.groupby("arm")[["auroc", "prec5", "brier"]].mean().round(4).to_dict("index"), "n_backgrounds": int(df.cell.nunique()),
           "support_size": int(df.n_support.max()), "support_cost": {"func": "3 F", "mol": "3 M", "both": "3 F + 3 M"}}
    d2 = df.assign(score=df.arm, cell=df.cell)
    cons = []
    for a, b in (("M1:func:10:0.0001", "M1:none:0:0"), ("M1:mol:10:0.0001", "M1:none:0:0"), ("M1:both:10:0.0001", "M1:none:0:0"),
                 ("M1:func:10:0.0001", "W:kernel0.25"), ("M1:func:10:0.0001", "B1:kernel0.25"), ("M1:both:10:0.0001", "Cmol"),
                 ("M1:mol:10:0.0001", "Cmol"), ("W:kernel0.25", "W:none"), ("B1:kernel0.25", "B1:none"), ("B1:none", "M1:none:0:0")):
        for metric, delta in (("prec5", DELTA_T), ("auroc", 0.0)):
            if a in set(df.arm) and b in set(df.arm):
                cons.append(contrast(d2, a, b, metric, delta))
        if a in set(df.arm) and b in set(df.arm):
            c = contrast(d2.assign(brier=-d2.brier), a, b, "brier", 0.0); c["note"] = "sign reversed: positive = lower Brier for a"; cons.append(c)
    res["contrasts"] = cons
    return res


def part_A(P, dr, stage, w1_table, out):
    eps = AD.build(stage, w1_table, "eval_" + stage)
    progs = {"A0": AS.A0_SRC}
    for nm in ("A1", "A2", "Aconv"):
        progs[nm] = (HERE / "RUN" / "programs" / f"{nm}.py").read_text()
    rows = []
    for world in ("W0", "W1", "B1"):
        for pn, src in progs.items():
            r = AS.evaluate(src, eps[world])
            bad = [x["error"] for x in r if str(x.get("error", "")).startswith("runner")]
            if bad: raise RuntimeError("runner fault " + bad[0])
            for e, x in zip(eps[world], r):
                k = e["kwargs"]; npos = sum(k["labels"].values())
                rows.append(dict(world=world, program=pn, cell=e["cell"], lineage=e["lineage"], hits=x["yield"], f_used=x["f_used"], m_used=x["m_used"], spent=x["spent"],
                                 pool=len(k["drugs"]), positives=int(npos), oracle=min(5, int(npos)), random=5 * npos / len(k["drugs"]), error=x.get("error")))
    df = pd.DataFrame(rows); df.to_csv(out / "A_yields.csv", index=False)
    piv = df.pivot_table(index=["world", "program"], values=["hits", "f_used", "m_used", "oracle", "random"], aggfunc="mean").round(3)
    res = {"means": {f"{a}|{b}": v for (a, b), v in piv.to_dict("index").items()}, "n_backgrounds": int(df.cell.nunique()),
           "identical_program_source": {nm: progs[nm] == progs["A0"] for nm in ("A1", "A2", "Aconv")}}

    def paired(w1, p1, w2, p2):
        a = df[(df.world == w1) & (df.program == p1)].set_index("cell").hits; b = df[(df.world == w2) & (df.program == p2)].set_index("cell").hits
        d = (a - b).dropna(); lin = [D.lineage_of(c) for c in d.index]; lo, hi = ci(d.values, lin)
        return {"a": f"{p1}@{w1}", "b": f"{p2}@{w2}", "diff_hits": float(d.mean()), "ci95": [lo, hi], "n_backgrounds": int(len(d)), "n_lineages": int(len(set(lin))),
                "margin": DELTA_E, "label": label(lo, hi, DELTA_E), "significantly_negative": bool(hi < 0)}
    res["contrasts"] = [paired("W1", "A0", "B1", "A0"), paired("W1", "A0", "W0", "A0"), paired("W1", "Aconv", "W1", "A0"), paired("W1", "A1", "W1", "A0"),
                        paired("W1", "A2", "W1", "A0"), paired("W1", "Aconv", "B1", "A0"), paired("W0", "Aconv", "W0", "A0"), paired("W1", "Aconv", "W1", "A1"),
                        paired("W0", "A1", "B1", "A0")]
    # 2x2 with interaction (A0/Aconv x W0/W1) on the conventional program edit; A1/A2 are identical to A0 when nothing was accepted
    pa = lambda w, p: df[(df.world == w) & (df.program == p)].set_index("cell").hits
    inter = ((pa("W1", "Aconv") - pa("W0", "Aconv")) - (pa("W1", "A0") - pa("W0", "A0"))).dropna()
    lo, hi = ci(inter.values, [D.lineage_of(c) for c in inter.index])
    res["interaction_conv_program_x_world"] = {"estimate": float(inter.mean()), "ci95": [lo, hi], "n_backgrounds": int(len(inter))}
    # molecular-query price sensitivity: mol-using menu candidates vs the best non-molecular candidate
    menu = AS.menu(); sens = []
    for lam in (0.1, 0.25, 0.5, 1.0):
        row = {"lam": lam}
        for nm, src in (("A0", AS.A0_SRC), ("Aconv", progs["Aconv"]), ("mol_menu_6", menu[6]), ("mol_menu_7", menu[7])):
            ys = []
            for e in eps["W1"]:
                kw = dict(e["kwargs"]); kw["lam"] = lam
                ys.append(ENV.run_program(src, kw)["yield"])
            row[nm] = float(np.mean(ys))
        sens.append(row)
    res["molecular_price_sensitivity_W1"] = sens
    return res


def main(stage):
    t0 = time.time()
    P = T.Prep(); dr = X.Direct(P)
    rundir = HERE / "RUN" / stage
    q_dir = HERE / "RUN" / ("sel30" if stage == "sel" else stage)
    out = HERE / "RUN" / f"{stage}_eval"; out.mkdir(parents=True, exist_ok=True)
    res = {"stage": stage, "exposure": "EXPOSED development dry run" if stage != "final" else "final stage, claimed once after FREEZE", "margins": {"delta_T_prec5": DELTA_T, "delta_E_hits": DELTA_E}}
    rR, sc = part_R(P, dr, stage, rundir, out); res["R"] = rR
    res["Q"] = part_Q(P, dr, stage, q_dir, out)
    w1 = AD.w_from_npz(rundir, stage, "full", EPOCH["full"], seed=0)
    res["A"] = part_A(P, dr, stage, w1, out)
    res["wall_seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(out / "RESULTS.json", "w"), indent=1, default=float)
    print("wrote", out / "RESULTS.json", res["wall_seconds"])


if __name__ == "__main__":
    main(sys.argv[1])
