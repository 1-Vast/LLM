"""Experiment Q: does revealing REAL support measurements of a held-out background improve predictions for its unrevealed (target) drugs?

Updates (declared): none | func (head fine-tune on support labels) | mol (trajectory fine-tune on support 24 h proteomes) | both.
Comparators on the SAME support information: ordinary kernel updating of a conventional score (B1, M0-lr) and of M1's output with the support labels,
and a conditional predictor g_mol (trained on training backgrounds) fed a kernel-imputed measured state.  Targets are the contested-pool drugs that are not
in the support; their outcomes are never used for updating.  Metrics per background; units for inference are lineages.
usage (GPU interpreter):  python eval_Q.py STAGE RUNDIR VARIANT SEED [steps lr ...]
"""
from __future__ import annotations
import json, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, torch
from sklearn.metrics import roc_auc_score
import ptv_data as D, ptv_tasks as T, ptv_direct as X, ptv_models as M, ptv_feedback as FB, ptv_episodes as EP, eval_R as R

KAPPAS = (0.25, 0.5, 1.0, 2.0)
KAPPA = 2.0     # kernel-update gain, fixed by the development rule (A0 table)


def kernel_update(w: dict, sim, support: dict, targets, kappa=KAPPA):
    out = {}
    for d in targets:
        a = 0.0
        for s, y in support.items():
            k = max(sim[d][s], 0.0)
            a += kappa * k * k * (y - w[s])
        out[d] = float(np.clip(w[d] + a, 0.0, 1.0)) if a != 0 else w[d]
    return out


def metrics(score: dict, labels: dict, k=T.K_NOM):
    ds = [d for d in score if d in labels]
    y = np.array([labels[d] for d in ds]); s = np.array([score[d] for d in ds])
    r = {"n": len(ds), "prev": float(y.mean())}
    if len(set(y)) > 1:
        r["auroc"] = float(roc_auc_score(y, s))
    r["brier"] = float(np.mean((np.clip(s, 0, 1) - y) ** 2))
    if len(ds) >= k + 1:
        top = np.argsort(-s, kind="stable")[:k]
        r["prec5"] = float(y[top].mean())
    return r


def run(stage, rundir, variant, seed, grid, helds=None, models=None, dev="cuda"):
    P = T.Prep(); dr = X.Direct(P)
    ex, hold, train_all = R.stage_inputs(P, stage)
    sc = R.direct_scores(P, dr, stage, None)
    rows = []
    for c in sorted(hold.cell.unique()):
        if helds and c not in helds: continue
        lin = D.lineage_of(c)
        tr = train_all[~train_all.lineage.isin([lin])]; tr = tr[tr.y.notna()]
        te = hold[hold.cell == c]
        pool = T.contested_pool(tr, [d for d, y in zip(te.perts, te.y) if (y == y) or stage == "final"])
        labels = te.set_index("perts").y.to_dict()
        pool = [d for d in pool if labels.get(d) == labels.get(d)]
        sup, tgt = FB.support_split(tr, pool)
        if len(tgt) < 6: continue
        sim = EP.fp_similarity(dr, pool)
        fn = None
        for f in Path(rundir).glob(f"{stage}_*_{variant}_s{seed}.pt"):
            h = f.name[len(stage) + 1:].rsplit(f"_{variant}_s{seed}", 1)[0]
            if stage == "final" or D.lineage_of(h) == lin: fn = f

        m = M.PPODE(5585, 935, hidden=16, variant=variant).to(dev); m.load_state_dict(torch.load(fn, map_location=dev)); m.eval()
        sc_c = sc[sc.cell == c].set_index("perts")
        sup_ex = te[te.perts.isin(sup)]
        sup_items, _ = P.items(sup_ex, with_outcome=True)
        tgt_ex = te[te.perts.isin(pool)]
        titems, tdf = P.items(tgt_ex, with_outcome=False)
        tt = M.make_tensors(titems)
        base = {}
        for arm, steps, lr in [("none", 0, 0.0)] + grid:
            mm = FB.fine_tune(m, sup_items, arm, steps, lr) if arm != "none" else m
            _, p = M.predict(mm, tt)
            base[(arm, steps, lr)] = dict(zip(tdf.perts, map(float, p)))
        W = base[("none", 0, 0.0)]
        lab = {d: float(labels[d]) for d in pool}
        supl = {d: lab[d] for d in sup}
        res = {}
        for key, sdict in base.items():
            res["M1:%s:%d:%g" % key if variant == "full" else "%s:%s:%d:%g" % ((variant,) + key)] = metrics({d: sdict[d] for d in tgt}, lab)
        b1 = {d: float(sc_c.b1[d]) for d in pool}; m0 = {d: float(sc_c.m0_lr[d]) for d in pool}
        for nm, w in (("B1", b1), ("M0", m0), ("W", W)):
            res[nm + ":none"] = metrics({d: w[d] for d in tgt}, lab)
            for kp in KAPPAS:
                res[nm + ":kernel%g" % kp] = metrics(kernel_update(w, sim, supl, tgt, kp), lab)
        # conditional predictor with the same molecular information (kernel-imputed measured state)
        tool = EP.MolTool(P, dr, tr)
        zs = {d: tool.space.z(c, d) for d in sup}
        if all(v is not None for v in zs.values()):
            cond = {}
            for d in tgt:
                wts = np.array([max(sim[d][s], 0) ** 2 + 1e-6 for s in sup]); wts /= wts.sum()
                z = sum(w_ * zs[s] for w_, s in zip(wts, sup))
                cond[d] = float(tool.m.predict_proba(tool.sc.transform(tool.row(tr, c, d, z)[None]))[0, 1])
            res["Cmol"] = metrics(cond, lab)
        for k_, v in res.items():
            rows.append(dict(cell=c, lineage=lin, arm=k_, n_support=len(sup), **v))
        print(c, "done", len(tgt), flush=True)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    stage, rundir, variant, seed = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    out = sys.argv[5]
    grid = []
    for arm in ("func", "mol", "both"):
        for steps, lr in ((10, 1e-4), (30, 1e-4), (30, 5e-4)):
            grid.append((arm, steps, lr))
    df = run(stage, rundir, variant, seed, grid, dev="cuda" if torch.cuda.is_available() else "cpu")
    df.to_csv(out, index=False)
    g = df.groupby("arm")[["auroc", "prec5", "brier"]].mean().round(3)
    print(g.to_string())
