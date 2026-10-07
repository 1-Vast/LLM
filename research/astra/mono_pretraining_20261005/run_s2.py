"""Stage S2: combination development on HD (outer folds) and the single frozen E read.

File summary
- Path: research/astra/mono_pretraining_20261005/run_s2.py
- Purpose: compare mono-pretrained, scratch, permuted-pretraining, potency-only, own-mono-ceiling and strong
  simple screen rankings for the registered two-round P2 contract (fp 30, cap ceil(menu/5), one verification
  round, verification order from the same development-selected simple ranking in every arm).
- Core points:
  - Units are target cell lines; roles and history draws are averaged inside a line (not units).
  - HD targets: five tissue-stratified, line-grouped outer folds; histories (4 lines) are drawn from HD
    lines outside the target's fold; mono pretraining excludes the fold's Jaaks lines. E targets: histories from
    HD lines; mono pretraining excludes E lines. E is opened once, after the dev stage froze the base ranking,
    the per-family configuration and the gates, and only if the gates passed.
  - Fine-tuning configuration is chosen per arm family on HD by mean within-line Spearman of score vs the
    two-orientation mean label (4 frozen configurations), never by yield and never on E.
- Interfaces: `main` (stages: dev, eval).
- Depends on: `common`, `combo`, `bilinear`, the frozen campaign engine and builder.
"""
from __future__ import annotations

import argparse
import json
import pickle
import time

import numpy as np
from scipy.stats import spearmanr

from research.astra.confirmation_campaign_20261004.design import campaign as c
from research.astra.feedback_validation_20261003.jaaks import build_panels

from . import common as cm
from .bilinear import ComboConfig, init_params
from .combo import Fitter, additive_scores

# v1.1 repair: v1 grid was {1, 30} x {10, 300}; strong shrinkage added (1e6 ~ exact fall-back to the base ranking)
CFG_GRID = [(t, i) for t in (30.0, 1000.0, 30000.0, 1e6) for i in (10.0, 300.0)]     # (l2_theta, l2_init)
FP = 30
SIMPLE = c.SIMPLE


def arm_specs(n_drugs: int):
    """name -> dict(family, features, init(fold) -> params)."""
    specs = {}
    pdir = cm.RESULTS / "mono_params"
    cache = {}

    def load(tag):
        if tag not in cache:
            cache[tag] = {k: v for k, v in np.load(pdir / f"{tag}.npz").items()}
        return cache[tag]

    fl = lambda f: "E" if f == "E" else f"F{f}"
    specs["pre_h6"] = dict(family="pre_h6", features="h6", init=lambda f: load(f"{fl(f)}_pre"))
    specs["pre_h3"] = dict(family="pre_h3", features="h3", init=lambda f: load(f"{fl(f)}_pre"))
    specs["pot_p3"] = dict(family="pot_p3", features="p3", init=lambda f: load(f"{fl(f)}_pre"))
    specs["preX_h6"] = dict(family="preX_h6", features="h6", init=lambda f: load("X_pre"))
    specs["own_h6"] = dict(family="own_h6", features="h6", init=lambda f: load(f"{fl(f)}_pre"), own=True)
    for i in range(cm.N_PERM):
        specs[f"scr{i}_h6"] = dict(family="scr_h6", features="h6",
                                   init=lambda f, i=i: init_params(14, n_drugs, 4, seed=300 + i))
        specs[f"dperm{i}_h6"] = dict(family="dperm_h6", features="h6", init=lambda f, i=i: load(f"{fl(f)}_dperm{i}"))
        specs[f"cperm{i}_h6"] = dict(family="cperm_h6", features="h6", init=lambda f, i=i: load(f"{fl(f)}_cperm{i}"))
    return specs


def setup():
    ticket = cm.guard("Jaaks combination outcomes: development (HD) and, if gates pass, E transport", cm.JAAKS)
    panels, report, candidates = build_panels(ticket, path=cm.JAAKS)
    tissues = c.build_tissues(panels, candidates)
    sidms, z, row = cm.load_context()
    drugs = cm.drug_table()
    drow = dict(zip(drugs.jaaks_id, drugs.row))
    mapped = drugs.mapped.to_numpy()
    mono = cm.load_mono()
    own_rec = mono[(~mono.sibling_id_record) & mono.jaaks_drug_id.notna() & mono.NOT_ELIGIBLE_target_line_own_mono_diagnostic_only]
    own = {(r.sidm, int(drow[r.jaaks_drug_id])): float(r.y_rel) for r in own_rec.itertuples()}
    return dict(tissues=tissues, z=z, row=row, drow=drow, mapped=mapped, own=own, n_drugs=len(drugs),
                split=cm.load_split(), fold=cm.fold_of(cm.load_split()), report=report)


def units(S, phase: str):
    """(tissue, fold, draw, hist, targets, allowed, forbidden) for the phase's outer folds."""
    split, fold = S["split"], S["fold"]
    folds = list(range(cm.N_FOLDS)) if phase == "dev" else ["E"]
    out = []
    for tissue in split:
        hd = sorted(split[tissue]["HD"]); ev = sorted(split[tissue]["E"])
        for k in folds:
            targets = [s for s in (hd if phase == "dev" else ev) if fold[s][1] == k]
            allowed = [s for s in hd if fold[s][1] != k] if phase == "dev" else hd
            forbidden = sorted(set(targets) | set(ev) if phase == "dev" else set(ev))
            for d in range(cm.N_DRAWS):
                hist = cm.history_draw(cm.TISSUE_CODE[tissue], k, d, allowed, cm.N_HIST)
                out.append(dict(tissue=tissue, fold=k, draw=d, hist=hist, targets=targets, allowed=allowed,
                                forbidden=forbidden))
    return out


def conc(score, truth):
    tv = (truth["y_s"] + truth["y_v"]) / 2.0
    if np.ptp(score) == 0 or np.ptp(tv) == 0:
        return np.nan
    return float(spearmanr(score, tv).correlation)


def build_targets(S, u):
    T = S["tissues"][u["tissue"]]
    H = c.restrict(T, u["hist"])
    out = {}
    for sidm in u["targets"]:
        for role in c.ROLES:
            tg = c.make_target(T, H, sidm, role, allowed_history=u["allowed"], forbidden=u["forbidden"])
            tg.scores["D_add"] = (lambda s: (s, s))(additive_scores(H, [T.pairs[i] for i in tg.rows], tg.pid))
            out[(u["tissue"], sidm, role, u["draw"], u["fold"])] = (T, tg)
    return out


def score_unit(S, specs, u, selected, targets):
    """Fit every arm (and configuration) on the unit's history and score its targets; returns (conc, scores)."""
    fit = Fitter(S["z"], S["drow"], S["row"], S["mapped"])
    fit_own = Fitter(S["z"], S["drow"], S["row"], S["mapped"], own=S["own"])
    T = S["tissues"][u["tissue"]]
    H = c.restrict(T, u["hist"])
    conc_rec, scores = [], {}
    for sidm in u["targets"]:
        _, tg = targets[(u["tissue"], sidm, "SV", u["draw"], u["fold"])]
        truth = c.truth_of(T, tg)
        joint = truth["h_s"] & truth["h_v"]
        for b in SIMPLE + ("D_add",):
            s = tg.scores[b][0]
            conc_rec.append(dict(tissue=u["tissue"], line=sidm, draw=u["draw"], fold=u["fold"], arm=b, cfg=-1,
                                 rho=conc(s, truth), auc=c.auc(s, joint)))
        for name, sp in specs.items():
            cfgs = range(len(CFG_GRID)) if selected is None else [selected[sp["family"]]]
            for ci in cfgs:
                l2t, l2i = CFG_GRID[ci]
                cfg = ComboConfig(features=sp["features"], l2_theta=l2t, l2_init=l2i)
                f = fit_own if sp.get("own") else fit
                p = f.fit(name, sp["init"](u["fold"]), H, cfg)
                s = f.target_score(p, T, tg)
                scores[(name, ci, u["tissue"], sidm, u["draw"], u["fold"])] = s
                conc_rec.append(dict(tissue=u["tissue"], line=sidm, draw=u["draw"], fold=u["fold"], arm=name, cfg=ci,
                                     rho=conc(s, truth), auc=c.auc(s, joint)))
    return conc_rec, scores


_W = {}


def _init_worker(S):
    _W["S"], _W["specs"] = S, arm_specs(S["n_drugs"])


def _job(args):
    u, selected = args
    S = _W["S"]
    return u, score_unit(S, _W["specs"], u, selected, build_targets(S, u))


def compute(S, phase, specs, selected=None, workers=1, log=print):
    """Pass over all units; selected=None evaluates every (arm, config) (dev), else only the selected one."""
    targets, scores, conc_rec = {}, {}, []
    t0 = time.time()
    us = units(S, phase)

    def take(u, res):
        conc_rec.extend(res[0]); scores.update(res[1])
        log(f"  {phase} {u['tissue']} fold {u['fold']} draw {u['draw']}: {len(conc_rec)} records, {time.time() - t0:.0f}s")

    for u in us:
        targets.update(build_targets(S, u))
    if workers <= 1:
        for u in us:
            take(u, score_unit(S, specs, u, selected, {k: v for k, v in targets.items() if k[3] == u["draw"] and
                                                       k[4] == u["fold"] and k[0] == u["tissue"]}))
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(workers, initializer=_init_worker, initargs=(S,)) as ex:
            for u, res in ex.map(_job, [(u, selected) for u in us]):
                take(u, res)
    return targets, scores, conc_rec


def line_mean(recs, key):
    by = {}
    for r in recs:
        if r[key] is not None and np.isfinite(r[key]):
            by.setdefault((r["tissue"], r["line"]), []).append(r[key])
    return {k: float(np.mean(v)) for k, v in by.items()}


def select_configs(conc_rec, specs, base):
    """Per family: the config with the highest HD mean concordance gain over the base ranking."""
    base_rho = line_mean([r for r in conc_rec if r["arm"] == base], "rho")
    sel, table = {}, {}
    for fam in sorted({sp["family"] for sp in specs.values()}):
        names = [n for n, sp in specs.items() if sp["family"] == fam]
        best = None
        for ci in range(len(CFG_GRID)):
            lm = line_mean([r for r in conc_rec if r["arm"] in names and r["cfg"] == ci], "rho")
            gain = float(np.mean([lm[k] - base_rho[k] for k in lm if k in base_rho]))
            table[f"{fam}|{ci}"] = gain
            if best is None or gain > best[0] + 1e-12:
                best = (gain, ci)
        sel[fam] = best[1]
    return sel, table


def campaigns(targets, scores, specs, selected, base, arms_extra=()):
    recs = []
    for key, (T, tg) in targets.items():
        tissue, sidm, role, draw, fold = key
        truth = c.truth_of(T, tg)
        verify = tg.scores[base][1]
        names = list(SIMPLE) + ["D_add"] + list(arms_extra)
        for b in names:
            recs.append(dict(c.run_p2(tg, truth, b, FP), draw=draw, fold=fold, arm=b))
        for name, sp in specs.items():
            tg.scores[name] = (scores[(name, selected[sp["family"]], tissue, sidm, draw, fold)], verify)
            r = c.run_p2(tg, truth, name, FP)
            recs.append(dict(r, draw=draw, fold=fold, arm=name))
    return recs


def line_yield(recs, names):
    """(tissue,line) -> mean confirmed over roles, draws and members."""
    by = {}
    for r in recs:
        if r["arm"] in names:
            by.setdefault((r["tissue"], r["line"]), []).append(r["confirmed"])
    return {k: float(np.mean(v)) for k, v in by.items()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["dev", "eval"])
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args(argv)
    cm.RESULTS.mkdir(exist_ok=True)
    logf = open(cm.RESULTS / f"s2_{a.stage}_{cm.RUN}_log.txt", "a", encoding="utf-8")

    def log(m):
        line = time.strftime("%H:%M:%S ") + m
        print(line, flush=True); logf.write(line + "\n"); logf.flush()

    S = setup()
    specs = arm_specs(S["n_drugs"])
    if a.stage == "dev":
        log("dev: computing scores for every arm and configuration on HD")
        targets, scores, conc_rec = compute(S, "dev", specs, workers=a.workers, log=log)
        # base ranking: best of the six simple rankings and D_add on HD confirmed yield (family-level choice)
        recs0 = []
        for key, (T, tg) in targets.items():
            truth = c.truth_of(T, tg)
            for b in SIMPLE + ("D_add",):
                recs0.append(dict(c.run_p2(tg, truth, b, FP), draw=key[3], fold=key[4], arm=b))
        tot = {b: sum(line_yield(recs0, [b]).values()) for b in SIMPLE + ("D_add",)}
        base = max(sorted(tot), key=lambda b: tot[b])
        log(f"base ranking chosen on HD: {base}; totals {tot}")
        selected, table = select_configs(conc_rec, specs, base)
        log(f"selected configs {selected}")
        recs = campaigns(targets, scores, specs, selected, base)
        cm.dump(cm.RESULTS / f"s2_dev_selection_{cm.RUN}.json", dict(base=base, simple_totals=tot, selected=selected,
                                                           concordance_gain_by_family_config=table,
                                                           cfg_grid=CFG_GRID))
        with open(cm.RESULTS / f"s2_dev_records_{cm.RUN}.pkl", "wb") as f:
            pickle.dump(dict(conc=conc_rec, campaigns=[{k: v for k, v in r.items() if k != "rounds"} for r in recs],
                             pids={(k[0], k[1], k[2]): tg.pid for k, (T, tg) in targets.items()}), f)
        log("dev written")
    else:
        sel = json.loads((cm.RESULTS / f"s2_dev_selection_{cm.RUN}.json").read_text())
        gates = json.loads((cm.RESULTS / f"s2_gates_{cm.RUN}.json").read_text())
        if not gates.get("open_E", False):
            raise PermissionError("E_SEALED: the registered gates did not pass; E is not read")
        log("eval: E transport with the frozen base, configurations and gates")
        base, selected = sel["base"], sel["selected"]
        targets, scores, conc_rec = compute(S, "eval", specs, selected=selected, workers=a.workers, log=log)
        recs = campaigns(targets, scores, specs, selected, base)
        with open(cm.RESULTS / f"s2_eval_records_{cm.RUN}.pkl", "wb") as f:
            pickle.dump(dict(conc=conc_rec, campaigns=[{k: v for k, v in r.items() if k != "rounds"} for r in recs],
                             pids={(k[0], k[1], k[2]): tg.pid for k, (T, tg) in targets.items()}), f)
        log("eval written")


if __name__ == "__main__":
    main()
