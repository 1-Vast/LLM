"""Phase E: the registered comparison on estimation folds 2, 3 and 4 (exposed data; see PROTOCOL.md section 2).

File summary
- Path: research/feedback_propagation_20261018/compare.py
- Purpose: for each estimation fold build the fold (leave-one-fold-out training on the other four folds, chemical
  purge at Tanimoto 0.5), then run, with the programs and hyper-parameters fixed by Phase D and PROTOCOL.md:
  - A. identical histories (the first B pools of the design order for every compound): every update rule on the same
    observations, graded on the unmeasured-pair nominations (primary) and on all pairs (secondary);
  - B. cost-matched closed loops (B pools per compound on average) for total decision utility;
  - C. sensitivities: B = 2 and 4, the logical 16-line grain, a second synthetic-noise seed, the deranged-history
    control, and the budget curve on a common target set;
  - D. hindsight diagnostics (gate identification, best-of-rules ceiling, oracle ceiling); these read the hidden side
    and are never policies.
- Outputs: records/E_fold{f}.json (write-once, compact per-compound arrays; analyse.py turns them into RESULTS.json).
- Usage: ``python -B compare.py`` (requires FREEZE.json to match; records the first access in ACCESS.json).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

import bench
import loop as L
import metrics as M
import repair as RP
import rules as R
import seal
from bench import tc

HERE = Path(__file__).resolve().parent
REC = HERE / "records"
EST_FOLDS = (2, 3, 4)
B_PRIMARY = 3
REGISTERED_R1 = {"K": 10, "lam": 1.0}                               # PROTOCOL.md section 5
REGISTERED_GATE = {"K": 10, "lam": 1.0, "loss": "kill", "gate": "lopo"}
C_STAR = {"K": 10}
SECONDARY_CONVENTIONAL = (("mixture_mean", "mixture_mean", {}), ("empcov_0.1", "empcov", {"alpha": 0.1}), ("knn20", "knn", {"K": 20}),
                          ("knn40", "knn", {"K": 40}), ("forest", "forest", {}))
ARMS_A = (("ridge", "ridge", {}), ("C_star_knn10", "knn", C_STAR), ("R1", "anchored", REGISTERED_R1), ("gated", "repair", REGISTERED_GATE),
          *SECONDARY_CONVENTIONAL)


def ev_(fold, rule, hist, q, target=None, **params):
    return M.compact(L.evaluate_scores(fold, L.score_matrix(fold, rule, hist, **params), q, target))


def identical(fold, B, rules_=ARMS_A, derange=False):
    oracle = fold.oracle()
    hist = L.pool_history(fold, oracle, B)
    q = L.queried_from(fold, hist)
    if derange:
        hist = L.derange(fold, hist)
    out = {"prior": ev_(fold, "prior", hist, q)}
    for nm, rule, prm in rules_:
        if rule == "repair" and B < RP.MIN_POOLS:
            continue
        out[nm] = ev_(fold, rule, hist, q, **prm)
    out["_cost"] = {"units_lines": int(oracle.units), "pools_per_compound": B, "lines_per_compound": float(q.sum(1).mean())}
    return out, hist, q


def one_fold(T, ev: int) -> dict:
    t0 = time.time()
    fold = bench.make_fold(T, ev)
    n = len(fold.cores)
    res: dict = {"fold": ev, "compounds": int(n), "campaign_sizes": [int(len(ix)) for ix in fold.campaigns], "n_train": fold.n_train,
                 "n_purged": fold.n_purged, "admissible_lines": int(fold.avail.sum()),
                 "family": [str(x) for x in fold.hidden.family], "campaign_index": [[int(i) for i in ix] for ix in fold.campaigns]}
    log = lambda s: print(f"fold {ev} {s} {time.time() - t0:.0f}s", flush=True)

    # A. identical histories ------------------------------------------------------------------
    A3, hist3, q3 = identical(fold, B_PRIMARY)
    res["A_B3"] = A3
    res["A_B3"]["prior_no_measurement"] = ev_(fold, "prior", hist3, np.zeros_like(q3))
    res["A_B3"]["oracle"] = M.compact({"unmeasured": L.grade_lists(fold, L.oracle_lists(fold, q3, True), q3),
                                                  "any": L.grade_lists(fold, L.oracle_lists(fold, q3, False), q3)})
    log("A B=3")
    for B in (2, 4):
        res[f"A_B{B}"] = identical(fold, B, (("ridge", "ridge", {}), ("C_star_knn10", "knn", C_STAR), ("R1", "anchored", REGISTERED_R1)))[0]
    log("A B=2,4")

    # C1. logical 16-line grain (the unmeasured-pair propagation headroom at the logical cost) ------
    oracle = fold.oracle()
    h16 = L.fixed_histories(fold, oracle, 16)
    q16 = L.queried_from(fold, h16)
    res["C_logical16"] = {"prior": ev_(fold, "prior", h16, q16), "ridge": ev_(fold, "ridge", h16, q16),
                          "C_star_knn10": ev_(fold, "knn", h16, q16, **C_STAR), "R1": ev_(fold, "anchored", h16, q16, **REGISTERED_R1)}
    log("C logical16")

    # C1b. second synthetic-noise draw (same cells, different frozen z): is the contrast an artefact of one noise realisation?
    fold2 = bench.make_fold(T, ev, noise_salt="probe2")
    oracle2 = fold2.oracle()
    hist_s = L.pool_history(fold2, oracle2, B_PRIMARY)
    q_s = L.queried_from(fold2, hist_s)
    res["C_noise_seed2"] = {"prior": ev_(fold2, "prior", hist_s, q_s), "ridge": ev_(fold2, "ridge", hist_s, q_s),
                            "C_star_knn10": ev_(fold2, "knn", hist_s, q_s, **C_STAR), "R1": ev_(fold2, "anchored", hist_s, q_s, **REGISTERED_R1)}
    log("C noise seed 2")

    # C2. deranged-history negative control ----------------------------------------------------
    D3, _, _ = identical(fold, B_PRIMARY, (("ridge", "ridge", {}), ("C_star_knn10", "knn", C_STAR), ("R1", "anchored", REGISTERED_R1)), derange=True)
    res["C_deranged"] = D3
    log("C deranged")

    # C3. budget curve on a common target set ----------------------------------------------------
    order = bench.pool_order(fold)
    target = ~np.isin(fold.pid, order[:4])
    curve = {}
    for b in (1, 2, 3, 4):
        hb = L.pool_history(fold, fold.oracle(), b)
        qb = L.queried_from(fold, hb)
        curve[str(b)] = {nm: ev_(fold, rule, hb, qb, target=target, **prm)
                         for nm, rule, prm in (("ridge", "ridge", {}), ("C_star_knn10", "knn", C_STAR), ("R1", "anchored", REGISTERED_R1))}
    res["C_budget_curve"] = curve
    log("C curve")

    # D. hindsight diagnostics (read the hidden side; never policies) ----------------------------
    hid = fold.hidden
    q = q3
    ridge_prof = lambda i, P, y: R.conditional_mean(fold, fold.prior[i], P, y)
    profs = {"ridge": ridge_prof, "mixture_mean": lambda i, P, y: R.mixture_profile(fold, i, P, y),
             "C_star_knn10": lambda i, P, y: R.knn_profile(fold, i, P, y, 10),
             "R1": lambda i, P, y: RP.anchored_profile(fold, i, P, y, **REGISTERED_R1)}
    mses = {}
    for nm, fn in profs.items():
        v = np.zeros(n)
        for i in range(n):
            m = ~q[i] & fold.avail & np.isfinite(hid.Y[i])
            v[i] = float(((fn(i, *hist3[i]) - hid.Y[i])[m] ** 2).mean())
        mses[nm] = v
    S = {"ridge": L.score_matrix(fold, "ridge", hist3), "mixture_mean": L.score_matrix(fold, "mixture_mean", hist3),
         "C_star_knn10": L.score_matrix(fold, "knn", hist3, **C_STAR), "R1": L.score_matrix(fold, "anchored", hist3, **REGISTERED_R1)}
    names = list(profs)
    stack = np.stack([mses[k] for k in names])
    best = np.argmin(stack, axis=0)
    S_best = np.stack([S[k] for k in names])[best, np.arange(n)]
    better = mses["R1"] < mses["ridge"]
    eb, ea = [], []
    for i in range(n):
        b_, a_, _ = RP.lopo_pool_errors(fold, i, *hist3[i], REGISTERED_R1["K"], REGISTERED_R1["lam"], REGISTERED_GATE["loss"])
        eb.append(b_)
        ea.append(a_)
    eb, ea = np.array(eb), np.array(ea)
    diff = (eb - ea) / np.maximum(eb + ea, 1e-9)
    ranks = np.empty(n)
    ranks[np.argsort(diff)] = np.arange(n)
    pos, neg = ranks[better], ranks[~better]
    auc = float((pos[:, None] > neg[None, :]).mean()) if len(pos) and len(neg) else None
    res["D_hindsight"] = {
        "true_mse_mean": {k: float(v.mean()) for k, v in mses.items()},
        "share_R1_truly_better_than_ridge": float(better.mean()),
        "gate_auc_loss_difference_vs_truly_better": auc,
        "hindsight_gate_R1_or_ridge": M.compact(L.evaluate_scores(fold, np.where(better[:, None], S["R1"], S["ridge"]), q)),
        "hindsight_best_of_rules": M.compact(L.evaluate_scores(fold, S_best, q)),
        "best_of_rule_share": {k: float((best == j).mean()) for j, k in enumerate(names)},
        "reading": "hindsight arms read the hidden side to choose per compound; they are ceilings, not attainable policies"}
    log("D hindsight")

    # B. cost-matched closed loops ---------------------------------------------------------------
    loops = {}
    specs = {"loop_ridge": ("uniform", "ridge", {}), "loop_C_star_knn10": ("uniform", "knn", C_STAR),
             "loop_R1": ("uniform", "anchored", REGISTERED_R1), "loop_gated": ("uniform", "repair", REGISTERED_GATE),
             "two_stage_ridge": ("two_stage", "ridge", {})}
    for nm, (alloc, rule, prm) in specs.items():
        hist, qq, oracle = L.closed_loop(fold, rule, B=B_PRIMARY, params=prm, allocation=alloc)
        rec = ev_(fold, rule, hist, qq, **prm)
        rec["_cost"] = {"units_lines": int(oracle.units), "lines_per_compound": float(qq.sum(1).mean()),
                        "pools_per_compound": float(np.mean([len(set(fold.pid[hist[i][0]].tolist())) for i in range(n)]))}
        loops[nm] = rec
        log(f"B {nm}")
    res["B_closed_loops"] = loops
    res["seconds"] = round(time.time() - t0, 1)
    return res


def main() -> None:
    seal.check()
    REC.mkdir(exist_ok=True)
    seal.record_access()
    T = bench.load_tables()
    for ev in EST_FOLDS:
        path = REC / f"E_fold{ev}.json"
        if path.exists():
            print("exists, skipped", path.name)
            continue
        res = one_fold(T, ev)
        res["tables_sha256"] = tc.sha256(bench.CACHE / "tables.npz")
        tc.write_json(path, res)
        print("wrote", path.name, flush=True)


if __name__ == "__main__":
    main()
