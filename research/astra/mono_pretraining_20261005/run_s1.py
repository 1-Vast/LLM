"""Stage S1: mono pretraining per configuration and the held-out mono preflight (gate G1).

File summary
- Path: research/astra/mono_pretraining_20261005/run_s1.py
- Purpose: after FREEZE, (1) value-level checks of the mono labels, (2) choose the mono configuration on
  non-Jaaks validation cells only, (3) pretrain the rank-4 head for every outer configuration (five HD
  folds and E, tier Y: the fold's Jaaks lines are held out of mono training; tier X: no Jaaks line at all)
  together with K=10 drug-mapping and K=10 within-tissue cell-mapping permutations, (4) score the held-out
  Jaaks lines' own GDSC2 labels against baselines (G1). No combination label is touched.
- Core points: held-out Jaaks lines never enter that configuration's mono training; permutations use
  the same data, steps and initialisation scheme as the real arm; training labels are winsorised per drug
  at the training 1/99 percentiles and weighted by inverse drug variance; evaluation uses raw labels.
- Interfaces: `main` (CLI stage selector).
- Depends on: `common`, `bilinear`, `mono`.
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd

from . import common as cm
from .bilinear import MonoConfig, predict_mono, pretrain_mono
from .mono import Records, drug_mean, lineage_mean, lineage_ridge, ridge_per_drug, score

GRID = [(steps, l2) for steps in (300, 600, 1200) for l2 in (1e-3, 1e-2)]
PARAMS_DIR = cm.RESULTS / "mono_params"


def prepare():
    sidms, z, row = cm.load_context()
    split = cm.load_split()
    fold = cm.fold_of(split)
    mono = cm.load_mono()
    cells = pd.read_csv(cm.S0 / "cell_identity_map.csv").set_index("sidm")
    drugs = cm.drug_table()
    drow = dict(zip(drugs.jaaks_id, drugs.row))
    m = mono[(~mono.sibling_id_record) & mono.jaaks_drug_id.notna() & mono.has_context14].copy()
    m["drow"] = m.jaaks_drug_id.map(drow)
    assert m.drow.notna().all() and (m.drow < int(drugs.mapped.sum())).all()
    m["drow"] = m.drow.astype(int)
    m["crow"] = m.sidm.map(row)
    own = m.NOT_ELIGIBLE_target_line_own_mono_diagnostic_only
    m["jaaks_line"] = m.sidm.isin(fold)
    m["fold"] = m.sidm.map(lambda s: fold[s][1] if s in fold else None)
    m["tissue_j"] = m.sidm.map(lambda s: fold[s][0] if s in fold else None)
    lin = {t: i for i, t in enumerate(sorted(cells.cmp_tissue.dropna().unique()))}
    lineage = np.array([lin.get(cells.cmp_tissue.get(s), len(lin)) for s in sidms])
    return dict(sidms=sidms, z=z, row=row, split=split, fold=fold, m=m, own=own, cells=cells, drugs=drugs,
                lineage=lineage, n_drugs=len(drugs), n_mapped=int(drugs.mapped.sum()))


def train_pool(P, cfg_fold):
    """Training records of one configuration: tier X (cfg_fold None) or tier Y (cfg_fold = held-out fold)."""
    m = P["m"]
    base = m.eligible_primary_pretrain
    if cfg_fold is None:
        return m[base]
    inside = m.jaaks_line & (m.fold != cfg_fold)
    return m[base | inside]


def fit_arm(P, rec: pd.DataFrame, cfg: MonoConfig, seed: int, cell_perm_seed=None, drug_perm_seed=None) -> dict:
    cells = sorted(rec.crow.unique())
    ci = {c: i for i, c in enumerate(cells)}
    cell = rec.crow.map(ci).to_numpy()
    drug = rec.drow.to_numpy().copy()
    y = rec.y_rel.to_numpy().copy()
    zt = P["z"][cells].copy()
    if cell_perm_seed is not None:                      # permute the context map within tissue (labels stay with cells)
        g = np.random.default_rng([cm.SEED, 77, cell_perm_seed])
        tis = P["cells"].cmp_tissue.reindex([P["sidms"][c] for c in cells]).fillna("NA").to_numpy()
        src = np.arange(len(cells))
        for t in np.unique(tis):
            idx = np.flatnonzero(tis == t)
            src[idx] = g.permutation(idx)
        zt = zt[src]
    pi = None
    if drug_perm_seed is not None:                      # fixed random drug relabelling of the mono labels
        pi = np.random.default_rng([cm.SEED, 88, drug_perm_seed]).permutation(P["n_mapped"])
        drug = pi[drug]
    # per-drug winsorising and inverse-variance weights from the training records only
    w = np.ones(P["n_drugs"])
    for d in range(P["n_mapped"]):
        mk = rec.drow.to_numpy() == d
        if mk.sum() > 20:
            lo, hi = np.quantile(y[mk], [0.01, 0.99])
            y[mk] = np.clip(y[mk], lo, hi)
            w[d] = 1.0 / max(np.var(y[mk]), 1e-6)
    dw = np.ones(P["n_drugs"])                          # weight follows the embedding row the label is attached to
    for d in range(P["n_mapped"]):
        dw[pi[d] if drug_perm_seed is not None else d] = w[d]
    return pretrain_mono(zt, cell, drug, y, P["n_drugs"], cfg, seed, drug_weight=dw / dw[:P["n_mapped"]].mean())


def records_of(P, rec: pd.DataFrame, z_all) -> Records:
    return Records(rec.crow.to_numpy(), rec.drow.to_numpy(), rec.y_rel.to_numpy(), z_all, P["lineage"], P["n_mapped"])


def choose_mono_config(P, log):
    m = P["m"]
    tr = m[m.eligible_primary_pretrain & (m.proposed_mono_split == "train")]
    va = m[m.eligible_primary_pretrain & (m.proposed_mono_split == "val")]
    out = []
    for steps, l2 in GRID:
        t0 = time.time()
        cfg = MonoConfig(steps=steps, l2_w=l2, l2_e=l2)
        p = fit_arm(P, tr, cfg, seed=11)
        pred = predict_mono(p, P["z"], va.crow.to_numpy(), va.drow.to_numpy())
        te = records_of(P, va, P["z"])
        s = score(te, pred)
        base = score(te, drug_mean(records_of(P, tr, P["z"]), te))
        out.append(dict(steps=steps, l2=l2, within_cell=s["within_cell_spearman"], per_drug=s["per_drug_spearman"],
                        rmse=s["rmse"], base_within_cell=base["within_cell_spearman"], seconds=time.time() - t0))
        log(f"mono grid steps={steps} l2={l2}: within-cell {s['within_cell_spearman']:.4f} per-drug {s['per_drug_spearman']:.4f}")
    best = max(out, key=lambda r: (round(r["within_cell"] + r["per_drug"], 6), -r["steps"]))
    return best, out


def value_checks(P):
    m = P["m"]
    inr = ((m.ln_ic50 >= np.log(m.min_conc)) & (m.ln_ic50 <= np.log(m.max_conc)))
    return dict(n_records=len(m), frac_ln_ic50_inside_dose_range=float(inr.mean()),
                frac_above_max_conc=float((m.ln_ic50 > np.log(m.max_conc)).mean()),
                frac_below_min_conc=float((m.ln_ic50 < np.log(m.min_conc)).mean()),
                y_rel_quantiles={str(q): float(m.y_rel.quantile(q)) for q in (0.01, 0.1, 0.5, 0.9, 0.99)},
                rmse_max=float(m.rmse.max()), nonfinite=int((~np.isfinite(m.ln_ic50)).sum()))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["checks", "select", "pretrain", "g1"])
    a = ap.parse_args(argv)
    cm.RESULTS.mkdir(exist_ok=True)
    logf = open(cm.RESULTS / "s1_log.txt", "a", encoding="utf-8")

    def log(msg):
        line = time.strftime("%H:%M:%S ") + msg
        print(line, flush=True)
        logf.write(line + "\n"); logf.flush()

    P = prepare()
    if a.stage == "checks":
        cm.dump(cm.RESULTS / "s1_value_checks.json", value_checks(P))
        log("value checks written")
    elif a.stage == "select":
        best, grid = choose_mono_config(P, log)
        cm.dump(cm.RESULTS / "s1_mono_config.json", dict(chosen=best, grid=grid,
                rule="max within-cell + per-drug Spearman on non-Jaaks validation cells (proposed_mono_split == val)"))
        log(f"chosen {best}")
    elif a.stage == "pretrain":
        ch = json.loads((cm.RESULTS / "s1_mono_config.json").read_text())["chosen"]
        cfg = MonoConfig(steps=int(ch["steps"]), l2_w=ch["l2"], l2_e=ch["l2"])
        PARAMS_DIR.mkdir(parents=True, exist_ok=True)
        for k in [None] + list(cm.FOLDS):
            name = "X" if k is None else f"F{k}"
            rec = train_pool(P, k)
            log(f"config {name}: {len(rec)} records, {rec.crow.nunique()} cells")
            jobs = [("pre", dict(seed=11))]
            if k is not None:
                jobs += [(f"dperm{i}", dict(seed=100 + i, drug_perm_seed=i)) for i in range(cm.N_PERM)]
                jobs += [(f"cperm{i}", dict(seed=200 + i, cell_perm_seed=i)) for i in range(cm.N_PERM)]
            for arm, kw in jobs:
                f = PARAMS_DIR / f"{name}_{arm}.npz"
                if f.exists():
                    continue
                t0 = time.time()
                p = fit_arm(P, rec, cfg, **kw)
                np.savez(f, **p)
                log(f"  {name}/{arm} done in {time.time() - t0:.1f}s")
    elif a.stage == "g1":
        run_g1(P, log)


def _boot(vals_by_cell: dict, n=2000, seed=0):
    keys = sorted(vals_by_cell)
    arr = np.array([vals_by_cell[k] for k in keys])
    g = np.random.default_rng(seed)
    means = np.array([arr[g.integers(0, len(arr), len(arr))].mean() for _ in range(n)])
    return float(arr.mean()), float(np.quantile(means, .025)), float(np.quantile(means, .975))


def per_drug_within_tissue(te: Records, pred, tissue_of_cell):
    """Mean over (drug, tissue) groups of the Spearman between prediction and label across cells."""
    from .mono import _spearman
    tis = np.array([tissue_of_cell.get(int(c), "") for c in te.cell])
    out = []
    for d in np.unique(te.drug):
        for t in sorted(set(tis) - {""}):
            m = (te.drug == d) & (tis == t)
            if m.sum() >= 15:
                r = _spearman(pred[m], te.y[m])
                if np.isfinite(r):
                    out.append(r)
    return float(np.mean(out)) if out else float("nan"), len(out)


def run_g1(P, log):
    z = P["z"]
    tissue_of_cell = {int(P["row"][s]): P["fold"][s][0] for s in P["fold"]}
    methods = {}
    held_all = []
    for k in cm.FOLDS:
        held = P["m"][P["m"].jaaks_line & (P["m"].fold == k)]
        tr = train_pool(P, k)
        tr_r, te_r = records_of(P, tr, z), records_of(P, held, z)
        preds = {"drug_mean": drug_mean(tr_r, te_r), "lineage_mean": lineage_mean(tr_r, te_r),
                 "ridge": ridge_per_drug(tr_r, te_r), "lineage_ridge": lineage_ridge(tr_r, te_r)}
        for arm in ["pre"] + [f"dperm{i}" for i in range(cm.N_PERM)] + [f"cperm{i}" for i in range(cm.N_PERM)]:
            p = {kk: v for kk, v in np.load(cm.RESULTS / "mono_params" / f"F{k}_{arm}.npz").items()}
            preds[arm] = predict_mono(p, z, te_r.cell, te_r.drug)
        held_all.append((te_r, preds))
    te = Records(*(np.concatenate([getattr(h[0], f) for h in held_all]) for f in ("cell", "drug", "y")), z, P["lineage"], P["n_mapped"])
    names = list(held_all[0][1])
    pred = {n: np.concatenate([h[1][n] for h in held_all]) for n in names}
    res = {}
    for n in names:
        s = score(te, pred[n])
        pdwt, ngrp = per_drug_within_tissue(te, pred[n], tissue_of_cell)
        res[n] = dict(within_cell=s["within_cell_spearman"], n_cells=s["n_cells"], per_drug=s["per_drug_spearman"],
                      per_drug_within_tissue=pdwt, n_groups=ngrp, rmse=s["rmse"], per_cell=s["per_cell"])
        log(f"{n}: within-cell {res[n]['within_cell']:.4f} per-drug {res[n]['per_drug']:.4f} "
            f"per-drug-within-tissue {pdwt:.4f} rmse {res[n]['rmse']:.3f}")
    summary = dict(arms={n: {k: v for k, v in r.items() if k != "per_cell"} for n, r in res.items()})
    pc = {n: res[n]["per_cell"] for n in names}
    common = sorted(set(pc["pre"]) & set(pc["drug_mean"]))
    diff = {c: pc["pre"][c] - pc["drug_mean"][c] for c in common}
    summary["pre_minus_drug_mean_within_cell"] = dict(zip(("mean", "lo", "hi"), _boot(diff)))
    for base in ("lineage_mean", "ridge", "lineage_ridge"):
        d2 = {c: pc["pre"][c] - pc[base][c] for c in common if c in pc[base]}
        summary[f"pre_minus_{base}_within_cell"] = dict(zip(("mean", "lo", "hi"), _boot(d2)))
    null = {key: [res[f"{t}{i}"][key] for t in ("dperm", "cperm") for i in range(cm.N_PERM)]
            for key in ("within_cell", "per_drug_within_tissue")}
    summary["perm_null"] = {key: dict(drug=[res[f"dperm{i}"][key] for i in range(cm.N_PERM)],
                                      cell=[res[f"cperm{i}"][key] for i in range(cm.N_PERM)]) for key in null}
    # G1 per frozen rule: within-cell gain over drug mean with CI > 0 AND positive within-tissue per-drug skill
    g1_a = summary["pre_minus_drug_mean_within_cell"]["lo"] > 0
    g1_b = res["pre"]["per_drug_within_tissue"] > 0 and res["pre"]["per_drug_within_tissue"] > max(
        max(summary["perm_null"]["per_drug_within_tissue"]["drug"]), max(summary["perm_null"]["per_drug_within_tissue"]["cell"]))
    summary["G1"] = dict(within_cell_gain_ci_above_zero=bool(g1_a), within_tissue_per_drug_skill_above_all_permutations=bool(g1_b),
                         passed=bool(g1_a and g1_b))
    cm.dump(cm.RESULTS / "s1_g1.json", summary)
    log(f"G1: {summary['G1']}")


if __name__ == "__main__":
    main()
