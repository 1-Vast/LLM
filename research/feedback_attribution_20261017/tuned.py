"""Independently tuned procedures and a calibrated selector on Beat AML (question Q3 of PROTOCOL.md).

File summary
- Path: research/feedback_attribution_20261017/tuned.py
- Purpose: does a corrected, fully tuned exploit-first design still capture nearly all of the
  procedure gain? Each procedure gets its own rank, chosen by its own inner replay on the fold's
  source patients. The confirmation instead reused the rank chosen for ``vc0``.
- Core points:
  - Inner replay: `agent.procedure_selection.source_replay` with inner folds by patient and the
    confirmation's inner salt (``procedure:<fold>``), ranks 5, 10, 20, 40, and the corrected
    lookahead. The ``vc0`` and ``b_exploit`` inner means must equal the confirmation's (parity).
  - Outer replay: every procedure at every rank on the fold's held-out patients.
  - Tuned arms: ``vc0_t``, ``exploit_t`` and ``look_t``, each at its own best inner rank (ties to
    the smaller rank). ``hybrid_c`` is the promoted selector (rule ``hybrid``) with the corrected
    lookahead, which has not been run before.
  - Calibrated selector ``cs_l05`` (and ``cs_l0``): source patients are split by a hash into a
    generation half and a calibration half. The generation half fixes each procedure's rank. The
    calibration half gives, for each bridge procedure, the patient-level mean net gain over
    ``vc0`` (hits minus 0.05 or 0 per extra round) and a simultaneous one-sided 95% lower bound
    (Bonferroni over the two candidates, z = 1.96). The candidate with the highest lower bound is
    adopted only if that bound is positive; otherwise ``vc0``. This follows the generate-then-
    calibrate pattern of CSPI-MT (Cho et al. 2024). Unlike CSPI-MT, the units are patients and the
    guarantee assumes independent patients; it is asymptotic.
- Interfaces: ``python -B tuned.py`` writes ``tmp/feedback_attribution_20261017/records_tuned.json``.
"""
from __future__ import annotations

import json
import time

import numpy as np

from common import CACHE, SOURCE_STUDY, hash_unit, load_domain, outer_folds, write_json

from agent.procedure_selection import _replay, choose, source_replay  # noqa: E402

RANKS = (5, 10, 20, 40)
BUDGET, K = 16, 4
MIN_MEASURED, IMPUTE = 100, 15
PROCS = ("vc0", "b_exploit", "b_lookahead")
Z_SIM = 1.959963984540054  # one-sided 2.5% per candidate, two candidates
ROUND_COSTS = {"cs_l05": 0.05, "cs_l0": 0.0}


def best_rank(recs_by_rank, proc, keep=None):
    def mean(r):
        rows = [x[proc] for x in recs_by_rank[r] if keep is None or x["context"] in keep]
        return float(np.mean(rows)) if rows else -np.inf
    return max(RANKS, key=lambda r: (mean(r), -r))


def calibrated(inner, patient_of, lam):
    contexts = [x["context"] for x in inner[RANKS[0]]]
    u = hash_unit(sorted({patient_of[c] for c in contexts}), "calibration")
    gen_pat = {p for p, v in zip(sorted({patient_of[c] for c in contexts}), u) if v < 0.5}
    gen = {c for c in contexts if patient_of[c] in gen_pat}
    cal = [c for c in contexts if c not in gen]
    ranks = {p: best_rank(inner, p, gen) for p in PROCS}
    look = {p: {x["context"]: x[p] for x in inner[ranks[p]]} for p in PROCS}
    out = {"ranks": ranks, "generation_contexts": len(gen), "calibration_contexts": len(cal), "candidates": {}}
    best, best_lcb = "vc0", 0.0
    for p in ("b_exploit", "b_lookahead"):
        by_pat: dict[str, list[float]] = {}
        for c in cal:
            by_pat.setdefault(patient_of[c], []).append(look[p][c] - look["vc0"][c] - lam)
        pm = np.array([np.mean(v) for v in by_pat.values()])
        m, se = float(pm.mean()), float(pm.std(ddof=1) / np.sqrt(len(pm)))
        lcb = m - Z_SIM * se
        out["candidates"][p] = {"net_gain": m, "se": se, "lcb": lcb, "patients": len(pm)}
        if lcb > best_lcb:
            best, best_lcb = p, lcb
    out["procedure"], out["rank"] = best, ranks[best]
    return out


def main():
    t0 = time.time()
    d = load_domain()
    Y, X, items = d["Y"], d["X"], d["items"]
    fid = outer_folds(d["groups"])
    patient_of = dict(zip(d["contexts"].tolist(), d["groups"].tolist()))
    conf = json.loads((SOURCE_STUDY / "RESULTS.json").read_text(encoding="utf-8"))["choices"]
    events = d["events"]
    outer = {r: _replay(Y, X, events, fid, np.ones(len(fid), bool), items, BUDGET, K, r, None, MIN_MEASURED,
                        IMPUTE, d["contexts"], "lookahead") for r in RANKS}
    print(f"outer replay done, {time.time() - t0:.0f} s", flush=True)
    outer_by = {r: {x["context"]: x for x in outer[r]} for r in RANKS}
    choices, parity, recs = {}, {}, []
    for k in range(5):
        src = np.flatnonzero(fid != k)
        inner = source_replay(Y[src], X[src], d["contexts"][src], d["groups"][src], items, BUDGET, K,
                              abs_gate=None, min_measured=MIN_MEASURED, impute_iters=IMPUTE, ranks=RANKS,
                              by_group=True, salt=f"procedure:{k}", lookahead_rule="lookahead")
        im = {r: {p: float(np.mean([x[p] for x in inner[r]])) for p in PROCS} for r in RANKS}
        cm = conf[str(k)]["inner_means"]
        parity[k] = all(abs(im[r][p] - cm[str(r)][p]) < 1e-12 for r in RANKS for p in ("vc0", "b_exploit"))
        ch = {"tuned_ranks": {p: best_rank(inner, p) for p in PROCS}, "inner_means": im,
              "hybrid_c": choose(inner, "hybrid").as_dict(),
              **{name: calibrated(inner, patient_of, lam) for name, lam in ROUND_COSTS.items()}}
        choices[k] = ch
        tr = ch["tuned_ranks"]
        for c in d["contexts"][fid == k]:
            c = str(c)
            o = {r: outer_by[r][c] for r in RANKS}
            rec = {"context": c, "group": patient_of[c], "fold": k,
                   "vc0_t": o[tr["vc0"]]["vc0"], "exploit_t": o[tr["b_exploit"]]["b_exploit"],
                   "look_t": o[tr["b_lookahead"]]["b_lookahead"],
                   "hybrid_c": o[ch["hybrid_c"]["rank"]][ch["hybrid_c"]["procedure"]]}
            for name in ROUND_COSTS:
                rec[name] = o[ch[name]["rank"]][ch[name]["procedure"]]
            for r in RANKS:
                for p in PROCS:
                    rec[f"{p}@{r}"] = o[r][p]
            recs.append(rec)
        print(f"fold {k}: tuned {tr}, hybrid {ch['hybrid_c']['procedure']}@{ch['hybrid_c']['rank']}, "
              f"cs_l05 {ch['cs_l05']['procedure']}@{ch['cs_l05']['rank']}, parity {parity[k]}, "
              f"{time.time() - t0:.0f} s", flush=True)
    write_json(CACHE / "records_tuned.json", {"choices": choices, "inner_parity_with_confirmation": parity,
                                              "records": recs})


if __name__ == "__main__":
    main()
