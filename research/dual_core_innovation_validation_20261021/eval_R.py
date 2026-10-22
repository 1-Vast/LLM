"""Experiment R: held-out functional prediction / nomination and molecular intervention-response skill for the world-model variants and comparators."""
from __future__ import annotations
import json, sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import ptv_data as D, ptv_tasks as T, ptv_direct as X, ptv_eval as E

VARIANTS = ["full", "no_traj", "no_fp"]
NAMES = {"full": "M1", "no_traj": "M2", "no_fp": "M3"}
STAGE_PARTS = {"dev": ["dev"], "sel": ["dev", "sel"], "final": ["dev", "sel"]}


def boot_lineage(vals: pd.Series, lineages: pd.Series, B=2000, seed=0):
    """Cluster bootstrap over lineages WITH multiplicity."""
    rng = np.random.default_rng(seed)
    us = lineages.unique(); groups = {u: vals[lineages == u].values for u in us}
    est = [np.mean(np.concatenate([groups[u] for u in rng.choice(us, len(us))])) for _ in range(B)]
    return [float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))]


def stage_inputs(prep, stage):
    ex = prep.R.experiments(1)
    hold = ex[ex.part == "final"] if stage == "final" else ex[ex.part == stage]
    train = ex[ex.part.isin(STAGE_PARTS[stage])]
    return ex, hold, train


def direct_scores(prep, dr, stage, helds):
    """M0 (lr, hgb) and priors for each held-out background; returns DataFrame cell, perts, y, scores."""
    ex, hold, train = stage_inputs(prep, stage)
    out = []
    for c in sorted(hold.cell.unique()):
        te = hold[hold.cell == c].copy(); lin = D.lineage_of(c)
        tr = train[~train.lineage.isin([lin])]
        tr = tr[tr.y.notna()]
        te["single"] = True
        for kind in ("lr", "hgb"):
            te["m0_" + kind] = dr.fit_predict(tr, te, kind)
        pri = [dr.priors(tr, c, d) for d in te.perts]
        gm = float(tr.y.mean())
        te["b0"] = [gm if p[0] != p[0] else p[0] for p in pri]; te["b1"] = [b if b == b else a for (a, _), b in zip(pri, [p[1] for p in pri])]
        te["b1"] = te["b1"].fillna(te["b0"])
        out.append(te)
    return pd.concat(out, ignore_index=True)


def decision_table(scores: pd.DataFrame, train: pd.DataFrame, cols):
    rows = []
    for c in sorted(scores.cell.unique()):
        te = scores[scores.cell == c]
        tr = train[~train.lineage.isin([D.lineage_of(c)])]
        for col in cols:
            m = E.background_metrics(te, tr, score=col); m.update(cell=c, lineage=D.lineage_of(c), score=col); rows.append(m)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- molecular
def molecular_skill(prep, stage, rundir, seed=0, variant="full"):
    """Intervention-response skill of stored trajectory predictions (variants with an ODE) against authentic held-out treated proteomes.
    All metrics use quantified proteins only.  Comparators: C1 baseline persistence (y_hat = x); C2 baseline + mean training shift over all
    drugs at that time; C3 baseline + drug-specific mean shift over training stocks (strong comparator)."""
    ex = prep.R.experiments()
    parts = STAGE_PARTS[stage]
    train = ex[ex.part.isin(parts)]
    # training shifts (change from stock baseline) per (perts, t)
    shifts: dict = {}
    for _, r in train.iterrows():
        for ti, t in enumerate(D.TIMES):
            raw = prep.R.treated(r.cell, r.perts, t)
            if raw is None: continue
            y = T.minmax(raw); ob = raw > 0
            d = np.where(ob, y - prep.baseline(r.cell), np.nan)
            shifts.setdefault((r.perts, ti, r.lineage), []).append(d)
    shifts = {k: np.nanmean(np.stack(v), axis=0) for k, v in shifts.items()}
    out = []
    for f in sorted(Path(rundir).glob(f"{stage}_*_{variant}_s{seed}.npz")):
        z = np.load(f, allow_pickle=True)
        if z["ypred"].ndim < 3: continue
        held_lin = {D.lineage_of(c) for c in z["cell"]}
        for i in range(len(z["perts"])):
            cell, perts = str(z["cell"][i]), str(z["perts"][i])
            x = z["x"][i].astype("float64")
            for ti in range(3):
                yt = z["ytrue"][i, ti].astype("float64"); ob = z["yobs"][i, ti].astype(bool)
                yp = z["ypred"][i, ti].astype("float64")
                keys = [k for k in shifts if k[1] == ti and k[2] not in held_lin]
                allm = np.nanmean(np.stack([shifts[k] for k in keys]), axis=0)
                dk = [shifts[k] for k in keys if k[0] == perts]
                c1 = x; c2 = x + np.nan_to_num(allm)
                c3 = x + (np.nan_to_num(np.nanmean(np.stack(dk), axis=0)) if dk else np.nan_to_num(allm))
                m = ob & (x > 0)
                if m.sum() < 100: continue
                tgt = (prep.pert(perts) > 0) & ob
                rec = {"cell": cell, "perts": perts, "t": D.TIMES[ti], "single": bool(z["single"][i]), "n": int(m.sum()), "n_target_obs": int(tgt.sum())}
                for name, yh in (("model", yp), ("C1", c1), ("C2", c2), ("C3", c3)):
                    rec["mse_" + name] = float(np.mean((yh[m] - yt[m]) ** 2))
                    dtrue, dhat = (yt - x)[m], (yh - x)[m]
                    rec["corr_" + name] = float(np.corrcoef(dtrue, dhat)[0, 1]) if np.std(dhat) > 1e-9 else 0.0
                    if tgt.sum() >= 1:
                        rec["tgt_mse_" + name] = float(np.mean((yh[tgt] - yt[tgt]) ** 2))
                out.append(rec)
    return pd.DataFrame(out)
