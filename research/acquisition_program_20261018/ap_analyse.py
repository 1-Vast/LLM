"""Paired analysis, decision-level diagnostics and hindsight diagnostics for a set of acquisition arms.

File summary
- Path: research/acquisition_program_20261018/ap_analyse.py
- Purpose: given the cached cells of a kind (dev or held), a dict of acquisition programs (expression or None for the
  fixed design) and the predecessor comparators, compute per-compound events (mean over the 5 paired noise scenarios,
  summed over the 2 target groups, divided by the number of groups), paired contrasts with the registered
  uncertainty analysis (family-cluster bootstrap, 4,000 draws; one-sided family sign-flip), per-task and per-scenario
  totals, decision-level diagnostics (choice distribution, agreement with the fixed design, calibration of the
  lookahead probability) and the unavailable hindsight ceiling of the acquisition choice.
- Noise scenarios are paired draws on the same cells, not additional biological samples: they are averaged inside a
  compound, never counted as units.
"""
from __future__ import annotations

import numpy as np

import ap_task as A
import metrics as M


def arm_cells(data, arm):
    """arm = ('program', expr|None) or ('comparator', name) -> {task.name: [grade dict per scenario]}"""

    out = {}
    for task, scs in data:
        if arm[0] == "program":
            out[task.name] = A.eval_program(task, scs, arm[1])["per_scenario"]
        else:
            out[task.name] = [A.grade_scores(task, sc, sc["comparators"][arm[1]]) for sc in scs]
    return out


def per_compound(data, cells):
    """{fold: per-compound events} averaged over scenarios, summed over groups, / number of groups."""

    acc, ng = {}, {}
    for task, scs in data:
        f = task.fold.fold
        v = np.mean([g["hits_c"] for g in cells[task.name]], axis=0)
        acc[f] = acc.get(f, 0) + v
        ng[f] = ng.get(f, 0) + 1
    return {f: acc[f] / ng[f] for f in acc}


def stack(data, pc):
    folds = sorted(pc)
    fam = np.concatenate([np.asarray(next(t for t, _ in data if t.fold.fold == f).fold.hidden.family)[next(t for t, _ in data if t.fold.fold == f).rows] for f in folds])
    return np.concatenate([pc[f] for f in folds]), fam


def contrast(data, pc_a, pc_b):
    a, fam = stack(data, pc_a)
    b, _ = stack(data, pc_b)
    r = M.paired_family(a - b, fam, np.ones(len(a), dtype=bool))
    return {k: r[k] for k in ("mean", "ci95", "p_one_sided", "n_families", "n_compounds")}


def totals(data, cells):
    return {"per_task": {k: [int(g["hits"]) for g in v] for k, v in cells.items()},
            "total": int(sum(g["hits"] for v in cells.values() for g in v)),
            "unknown": int(sum(g["unknown"] for v in cells.values() for g in v))}


def decision_diagnostics(data, expr):
    """Choice distribution, agreement with the fixed design and calibration of the lookahead probability."""

    run = A.compile_program(expr)
    ranks, agree, n = np.zeros(20), 0, 0
    pred, real = [], []
    for task, scs in data:
        for sc in scs:
            ch = A.choose(sc["features"], run)
            for k in ch:
                ranks[int(k)] += 1
            agree += int((ch == 0).sum())
            n += len(ch)
            g = A.grade_choice(task, sc, ch)
            pred.append(sc["features"]["la"][np.arange(len(ch)), ch])
            real.append(g["hits_c"])
    pred, real = np.concatenate(pred), np.concatenate(real)
    q = np.quantile(pred, [0, 0.2, 0.4, 0.6, 0.8, 1.0])
    bins = []
    for lo, hi in zip(q[:-1], q[1:]):
        m = (pred >= lo) & (pred <= hi)
        bins.append({"la_mean": float(pred[m].mean()), "realised_events_per_compound": float(real[m].mean()), "n": int(m.sum())})
    return {"share_choosing_fixed_pool": agree / n, "choice_rank_histogram": [int(x) for x in ranks[:ranks.nonzero()[0].max() + 1]],
            "calibration_la_vs_realised_by_quintile": bins,
            "note": "la is an unvalidated model probability of the sum over 3 nominated lines; realised events are per compound after campaign-level nomination"}


def hindsight_choice(task, sc):
    """UNAVAILABLE: per compound the candidate whose own top-3 target nominations contain the most true events."""

    F, truth = sc["final"], sc["truth"]
    top = np.argsort(-F, axis=2)[:, :, :3]
    hits = np.take_along_axis(np.broadcast_to(truth[:, None, :], F.shape), top, axis=2).sum(2)
    return np.argmax(hits, axis=1)


def hindsight_total(data):
    tot = 0
    for task, scs in data:
        for sc in scs:
            tot += A.grade_choice(task, sc, hindsight_choice(task, sc))["hits"]
    return int(tot)
