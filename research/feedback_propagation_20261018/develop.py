"""Phase D: strictly nested development on folds 0 and 1 (no estimation-fold outcome is read).

File summary
- Path: research/feedback_propagation_20261018/develop.py
- Purpose: qualify the regime, choose the registered repair program and the strongest conventional comparator,
  measure the headroom of a diagnosis gate, run the item-specificity control, derive the budget curve and the
  variances that fix the practical-effect threshold, and exercise the closed loop. Evaluation folds are 0 and 1;
  fold 0 is predicted from a world fitted on fold 1 only and vice versa (after the chemical purge), so the
  estimation folds 2-4 never enter any fit, selection or threshold.
- Selection rules (declared here, copied to PROTOCOL.md, applied to the pooled development hits of the two folds
  at B = 3 pools on identical fixed-design histories, unmeasured-pair utility):
  - repair program R1 = analogue-anchored update with (K, lam) in {10, 20} x {0.5, 1.0}; the most hits wins, ties
    go to the smaller K and then the larger lam;
  - strongest conventional comparator C* among {ridge, mixture_mean, empcov alpha in {0, 0.1, 0.3}, knn K in
    {10, 20, 40}, forest}; the most hits wins, ties go to the earlier name in that list;
  - gated variant: loss in {mse, kill, spearman} at the chosen (K, lam), the most hits wins, ties to mse.
- Outputs: DEVELOPMENT.json (write-once; `--force` for exploratory reruns before the freeze).
- Usage: ``python -B develop.py [--force]``.
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np

import bench
import loop as L
import metrics as M
import repair as RP
import rules as R
from bench import tc

HERE = Path(__file__).resolve().parent
OUT = HERE / "DEVELOPMENT.json"
DEV_FOLDS = ((0, (1,)), (1, (0,)))
PRIMARY_B = 3
CONVENTIONAL = (("ridge", "ridge", {}), ("mixture_mean", "mixture_mean", {}), ("empcov_0", "empcov", {"alpha": 0.0}),
                ("empcov_0.1", "empcov", {"alpha": 0.1}), ("empcov_0.3", "empcov", {"alpha": 0.3}),
                ("knn10", "knn", {"K": 10}), ("knn20", "knn", {"K": 20}), ("knn40", "knn", {"K": 40}), ("forest", "forest", {}))
GRID = tuple(itertools.product((10, 20), (0.5, 1.0)))
LOSSES = ("mse", "kill", "spearman")


def total(c: dict, kind="unmeasured", key="hits") -> int:
    return int(sum(v[kind][key] for v in c.values()))


def per_campaign(c: dict, kind="unmeasured", key="campaign_hits") -> list:
    out = []
    for v in c.values():
        sizes = v[kind]["campaign_compounds"]
        out += [h for h, s in zip(v[kind][key], sizes) if s == M.CAMPAIGN]
    return out


def evaluate(fold, rule, hist, q, target=None, **params):
    return M.compact(L.evaluate_scores(fold, L.score_matrix(fold, rule, hist, **params), q, target))


def true_mse(fold, prof_fn, hist, q):
    """HINDSIGHT: mean squared error of a profile on the unmeasured admissible finite cells (reads the hidden side)."""

    hid = fold.hidden
    out = np.zeros(len(fold.cores))
    for i in range(len(fold.cores)):
        m = ~q[i] & fold.avail & np.isfinite(hid.Y[i])
        out[i] = float(((prof_fn(i, *hist[i]) - hid.Y[i])[m] ** 2).mean())
    return out


def main() -> None:
    force = "--force" in sys.argv
    if OUT.exists() and not force:
        raise SystemExit("DEVELOPMENT.json exists; write-once (use --force only for exploratory reruns before the freeze)")
    t0 = time.time()
    T = bench.load_tables()
    res: dict = {"folds": [list(f) for f in DEV_FOLDS], "reads": "PRISM 19Q4 folds 0 and 1 only; no estimation-fold outcome, no 24Q2 value"}
    regime, grid, gate_diag, deranged, curve, closed = {}, {}, {}, {}, {}, {}
    folds = {}
    for ev, tr in DEV_FOLDS:
        fold = bench.make_fold(T, ev, tr)
        folds[ev] = fold
        print("fold", ev, "train", fold.n_train, "purged", fold.n_purged, "admissible lines", int(fold.avail.sum()),
              "pool order", bench.pool_order(fold)[:5], f"{time.time() - t0:.0f}s", flush=True)

    def collect(store, name, ev, value):
        store.setdefault(name, {})[str(ev)] = value

    # ---- D1 regime scan: how much does propagation add as the history grows? ------------------
    scan_rules = (("prior", "prior", {}), ("ridge", "ridge", {}), ("mixture_mean", "mixture_mean", {}), ("empcov_0.1", "empcov", {"alpha": 0.1}),
                  ("knn10", "knn", {"K": 10}), ("anchored_K10_lam1", "anchored", {"K": 10, "lam": 1.0}))
    for ev, fold in folds.items():
        for gname, lines in (("logical16", fold.design[:16]), ("logical64", fold.design[:64]), ("logical128", fold.world.sparse_design(128)),
                             *[(f"pool{b}", L.pool_lines_for(fold, b)) for b in (1, 2, 3, 4)]):
            oracle = fold.oracle()
            hist = L.fixed_histories(fold, oracle, len(lines), lines)
            q = L.queried_from(fold, hist)
            for nm, rule, prm in scan_rules:
                collect(regime.setdefault(gname, {}), nm, ev, evaluate(fold, rule, hist, q, **prm))
        print("D1 done fold", ev, f"{time.time() - t0:.0f}s", flush=True)
    res["regime"] = regime

    # ---- D2 selection at B = 3 -----------------------------------------------------------------
    hists = {}
    for ev, fold in folds.items():
        oracle = fold.oracle()
        hist = L.pool_history(fold, oracle, PRIMARY_B)
        hists[ev] = (hist, L.queried_from(fold, hist))
    cfgs = {}
    for nm, rule, prm in CONVENTIONAL:
        cfgs[nm] = (rule, prm)
    for K, lam in GRID:
        cfgs[f"anchored_K{K}_lam{lam}"] = ("anchored", {"K": K, "lam": lam})
        for loss in LOSSES:
            cfgs[f"repair_K{K}_lam{lam}_{loss}"] = ("repair", {"K": K, "lam": lam, "loss": loss, "gate": "lopo"})
    for nm, (rule, prm) in cfgs.items():
        for ev, fold in folds.items():
            hist, q = hists[ev]
            collect(grid, nm, ev, evaluate(fold, rule, hist, q, **prm))
        print("D2", nm, total(grid[nm]), f"{time.time() - t0:.0f}s", flush=True)
    hits = {nm: total(v) for nm, v in grid.items()}
    anchored_names = [f"anchored_K{K}_lam{lam}" for K, lam in GRID]
    best_anch = max(anchored_names, key=lambda n: (hits[n], -int(n.split("_K")[1].split("_")[0]), float(n.split("lam")[1])))
    K_star, lam_star = int(best_anch.split("_K")[1].split("_")[0]), float(best_anch.split("lam")[1])
    names = [c[0] for c in CONVENTIONAL]
    c_star = max(names, key=lambda n: (hits[n], -names.index(n)))
    gate_names = [f"repair_K{K_star}_lam{lam_star}_{loss}" for loss in LOSSES]
    gate_star = max(gate_names, key=lambda n: (hits[n], -gate_names.index(n)))
    res["grid"] = grid
    res["selection"] = {"B": PRIMARY_B, "R1": best_anch, "K": K_star, "lam": lam_star, "C_star": c_star, "gated": gate_star,
                        "hits_at_selection": {n: hits[n] for n in [best_anch, c_star, gate_star, "ridge"]},
                        "rule": "most pooled development unmeasured hits; ties: smaller K then larger lam (R1), earlier name (C*), mse (gate)"}
    print("selected", res["selection"], flush=True)

    # ---- D3 headroom and identification of a diagnosis gate -----------------------------------
    for ev, fold in folds.items():
        hist, q = hists[ev]
        ridge_prof = lambda i, P, y: R.conditional_mean(fold, fold.prior[i], P, y)
        anch_prof = lambda i, P, y: RP.anchored_profile(fold, i, P, y, K_star, lam_star)
        mb = true_mse(fold, ridge_prof, hist, q)
        ma = true_mse(fold, anch_prof, hist, q)
        Sb = L.score_matrix(fold, "ridge", hist)
        Sa = L.score_matrix(fold, "anchored", hist, K=K_star, lam=lam_star)
        better = ma < mb
        eb, ea = [], []
        for i in range(len(fold.cores)):
            b, a, _ = RP.lopo_pool_errors(fold, i, *hist[i], K_star, lam_star, "mse")
            eb.append(b)
            ea.append(a)
        eb, ea = np.array(eb), np.array(ea)
        chosen = ea < eb
        diff = (eb - ea) / np.maximum(eb + ea, 1e-9)
        order = np.argsort(diff)
        ranks = np.empty(len(diff))
        ranks[order] = np.arange(len(diff))
        pos, neg = ranks[better], ranks[~better]
        auc = float((pos[:, None] > neg[None, :]).mean()) if len(pos) and len(neg) else None
        S_hind = np.where(better[:, None], Sa, Sb)
        hind = M.compact(L.evaluate_scores(fold, S_hind, q))
        S_gate = np.where(chosen[:, None], Sa, Sb)
        gate = M.compact(L.evaluate_scores(fold, S_gate, q))
        gate_diag[str(ev)] = {"share_anchored_truly_better": float(better.mean()), "share_gate_chooses_anchored": float(chosen.mean()),
                              "agreement": float((chosen == better).mean()), "auc_loss_difference_vs_truly_better": auc,
                              "true_mse": {"ridge": float(mb.mean()), "anchored": float(ma.mean()), "gate": float(np.where(chosen, ma, mb).mean()),
                                           "hindsight": float(np.minimum(ma, mb).mean())},
                              "hindsight_gate": hind, "gate_mse_recomputed": gate}
    res["gate_diagnostics"] = gate_diag
    print("D3 done", f"{time.time() - t0:.0f}s", flush=True)

    # ---- D4 item-specificity control -------------------------------------------------------------
    for ev, fold in folds.items():
        hist, q = hists[ev]
        dh = L.derange(fold, hist)
        for nm, rule, prm in (("ridge", "ridge", {}), ("knn", "knn", {"K": K_star}), ("anchored", "anchored", {"K": K_star, "lam": lam_star})):
            collect(deranged, nm, ev, evaluate(fold, rule, dh, q, **prm))
    res["deranged"] = deranged
    print("D4 done", f"{time.time() - t0:.0f}s", flush=True)

    # ---- D5 budget curve on a common target set (pairs outside the first four pools) -----------
    curve_rules = (("ridge", "ridge", {}), ("R1", "anchored", {"K": K_star, "lam": lam_star}),
                   ("C_star", dict((n, (r, p)) for n, r, p in CONVENTIONAL)[c_star][0], dict((n, (r, p)) for n, r, p in CONVENTIONAL)[c_star][1]))
    for ev, fold in folds.items():
        order = bench.pool_order(fold)
        target = ~np.isin(fold.pid, order[:4])
        for b in (1, 2, 3, 4):
            oracle = fold.oracle()
            hist = L.pool_history(fold, oracle, b)
            q = L.queried_from(fold, hist)
            for nm, rule, prm in curve_rules:
                if b == 1 and nm == "R1":
                    pass
                collect(curve.setdefault(str(b), {}), nm, ev, evaluate(fold, rule, hist, q, target=target, **prm))
    res["budget_curve_common_target"] = curve
    print("D5 done", f"{time.time() - t0:.0f}s", flush=True)

    # ---- D6 closed loops at B = 3 -----------------------------------------------------------------
    arms = {"prior": None, "fixed_ridge": None, "two_stage_ridge": ("two_stage", "ridge", {}), "loop_ridge": ("uniform", "ridge", {}),
            "loop_knn": ("uniform", "knn", {"K": K_star}), "loop_R1": ("uniform", "anchored", {"K": K_star, "lam": lam_star}),
            "loop_gated": ("uniform", "repair", {"K": K_star, "lam": lam_star, "loss": gate_star.split("_")[-1], "gate": "lopo"})}
    for nm, spec in arms.items():
        for ev, fold in folds.items():
            if nm == "prior":
                q = np.zeros((len(fold.cores), len(fold.lines)), dtype=bool)
                S = np.stack([R.score("prior", fold, i, [], []) for i in range(len(fold.cores))])
                c = M.compact(L.evaluate_scores(fold, S, q))
                wells = 0
            elif nm == "fixed_ridge":
                oracle = fold.oracle()
                hist = L.pool_history(fold, oracle, PRIMARY_B)
                q = L.queried_from(fold, hist)
                c = evaluate(fold, "ridge", hist, q)
                wells = oracle.units
            else:
                alloc, rule, prm = spec
                hist, q, oracle = L.closed_loop(fold, rule, B=PRIMARY_B, params=prm, allocation=alloc)
                c = evaluate(fold, rule, hist, q, **prm)
                wells = oracle.units
            c["lines_queried_per_compound"] = float(q.sum(1).mean())
            collect(closed, nm, ev, c)
        print("D6", nm, "unm", total(closed[nm]), "any", total(closed[nm], "any"), f"{time.time() - t0:.0f}s", flush=True)
    res["closed_loop"] = closed
    res["seconds"] = round(time.time() - t0, 1)
    res["tables_sha256"] = tc.sha256(bench.CACHE / "tables.npz")
    tc.write_json(OUT, res)
    print("done", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
