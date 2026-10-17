"""Equal-well replay of context-transfer arms on one domain.

File summary
- Path: research/context_transfer_20261017/replay.py
- Purpose: for every outer fold, fit the Virtual Cell on source contexts only, then run every arm
  on each held-out target context with the same total well budget, and grade the measured wells
  against the registered endpoint of the full matrix.
- Core points:
  - A well on an unmeasured pair consumes budget, reveals nothing and is never a hit.
  - Candidate items never depend on the target's outcome availability.
  - Arms without a bridge spend all wells on nominations; bridge arms spend `k_bridge` first.
  - Per-context records keep hits, misfit, repair flag and the no-bridge negative-transfer label,
    so every comparison is a paired difference over the same contexts.
- Interfaces: `run(domain, budget, k_bridge, arms, rank, repair_threshold, fold_salt)` -> records.
"""
from __future__ import annotations

import numpy as np

from agent import bma_expected_hit, choose_bridge, fixed_panel, nominate, repaired_prior
from common import folds, tie_order
from vc import ContextModel, State

NO_BRIDGE = ("random", "item", "knn", "vc0")
BRIDGE = ("b_random", "b_exploit", "b_panel", "b_info", "b_lookahead", "match_panel", "maestro")
CONTROLS = ("vc0_xshuffle", "maestro_yshuffle")


def knn_scores(model: ContextModel, Xs, src_events, x, k=10):
    if not model.has_prior or x is None or not np.isfinite(x).all():
        return None
    def proj(Z):
        Z = (Z[:, model.genes] - model.x_mu) / model.x_sd
        return Z @ model.W
    ok = np.isfinite(Xs).all(1)
    P = proj(Xs[ok])
    q = proj(x[None, :])[0]
    sim = (P @ q) / (np.linalg.norm(P, axis=1) * np.linalg.norm(q) + 1e-9)
    near = np.argsort(-sim)[:k]
    ev = src_events[ok][near]
    return (ev.sum(0) + 0.1) / (np.isfinite(ev).sum(0) + 1.0) if ev.dtype != bool else (ev.sum(0) + 0.1) / (k + 1.0)


def match_scores(Ys, src_events, bridge, yb, k=10):
    """Conventional pilot-screen matching without the Virtual Cell.

    Source contexts are ranked by Pearson correlation with the target over the measured bridge
    items (at least 3 shared finite values); the event rate over the k best matches is the score.
    Returns None when fewer than 3 bridge values are finite.
    """

    f = np.isfinite(yb)
    if f.sum() < 3:
        return None
    A = Ys[:, bridge[f]].astype(float)
    ok = np.isfinite(A).sum(1) >= 3
    sims = np.full(len(A), -np.inf)
    y = yb[f]
    for j in np.flatnonzero(ok):
        g = np.isfinite(A[j])
        a, b = A[j, g], y[g]
        if a.std() < 1e-9 or b.std() < 1e-9:
            continue
        sims[j] = np.corrcoef(a, b)[0, 1]
    near = np.argsort(-sims)[:k]
    near = near[np.isfinite(sims[near])]
    if len(near) == 0:
        return None
    return (src_events[near].sum(0) + 0.1) / (len(near) + 1.0)


def run(domain: dict, budget: int, k_bridge: int, arms=NO_BRIDGE + BRIDGE + CONTROLS, rank: int = 20,
        repair_threshold: float = 2.0, fold_salt: str = "context-transfer", abs_gate=None,
        min_measured: int = 10, maestro_rule: str = "lookahead", fold_ids=None, context_filter=None,
        llm=None, context_text=None, item_names=None, source_fraction: float = 1.0, repair_grid=(),
        impute_iters: int = 0):
    Y, X, ev = domain["Y"], domain["X"], domain["events"]
    keys = domain["contexts"]
    items = domain["items"]
    fid = folds(keys, fold_salt) if fold_ids is None else fold_ids
    order = tie_order(items, "tie")
    records = []
    for k in sorted(set(fid.tolist())):
        src = np.flatnonzero(fid != k)
        if source_fraction < 1.0:
            gkeep = {g for g in set(domain["groups"][src].tolist())
                     if (tie_order([g], "source-subsample")[0]) < source_fraction}
            src = src[np.isin(domain["groups"][src], list(gkeep))]
        tgt = np.flatnonzero(fid == k)
        if context_filter is not None:
            tgt = tgt[context_filter[tgt]]
        if len(tgt) == 0:
            continue
        model = ContextModel(rank=rank, abs_gate=abs_gate, min_measured=min_measured,
                             impute_iters=impute_iters).fit(Y[src], X[src])
        src_events = _source_events(model, Y[src])
        panel = fixed_panel(model, k_bridge, order) if k_bridge > 0 else np.array([], int)
        # controls: each target borrows the basal profile / bridge readouts of a different target
        partner = _partners(tgt, keys, domain["groups"])
        for c in tgt:
            key = str(keys[c])
            rng_order = tie_order(items, f"random:{key}")
            x = X[c] if np.isfinite(X[c]).all() else None
            st0 = model.prior(x)
            p0 = model.expected_hit(st0)
            rec = {"context": key, "group": str(domain["groups"][c]), "fold": int(k),
                   "events": int(ev[c].sum()), "has_x": x is not None,
                   "oracle": int(min(budget, ev[c].sum()))}
            truth = ev[c]
            yc = Y[c]

            def grade(wells):
                wells = np.asarray(wells, dtype=int)
                return int(truth[wells].sum())

            def wasted(wells):
                return int((~np.isfinite(yc[np.asarray(wells, dtype=int)])).sum())

            for arm in arms:
                if arm == "random":
                    wells = nominate(rng_order, budget, [], order)
                    rec[arm] = grade(wells)
                    rec[arm + "_wasted"] = wasted(wells)
                elif arm == "item":
                    wells = nominate(model.measured_rate * model.source_event_rate, budget, [], order)
                    rec[arm] = grade(wells)
                    rec[arm + "_wasted"] = wasted(wells)
                elif arm == "knn":
                    s = knn_scores(model, X[src], src_events, x)
                    s = model.source_event_rate if s is None else s + 1e-6 * model.source_event_rate
                    wells = nominate(s, budget, [], order)
                    rec[arm] = grade(wells)
                    rec[arm + "_wasted"] = wasted(wells)
                elif arm == "vc0":
                    wells = nominate(p0, budget, [], order)
                    rec[arm] = grade(wells)
                    rec[arm + "_wasted"] = wasted(wells)
                elif arm == "vc0_xshuffle":
                    xp = X[partner[c]] if c in partner and np.isfinite(X[partner[c]]).all() else None
                    wells = nominate(model.expected_hit(model.prior(xp)), budget, [], order)
                    rec[arm] = grade(wells)
                    rec[arm + "_wasted"] = wasted(wells)
                elif arm == "llm":
                    from agent import info_gain
                    by_p = np.argsort(-(p0 + order * 1e-12))[:20]
                    g = info_gain(model, st0.S, np.arange(len(p0)))
                    g[by_p] = -np.inf
                    by_g = np.argsort(-(g + order * 1e-12))[:10]
                    short = np.concatenate([by_p, by_g])
                    mean0, var0 = model.predict(st0)
                    sl = [{"id": f"c{j:02d}", "item": str(item_names[i]),
                           "model_expected_hit_percent": round(float(100 * p0[i]), 1),
                           "model_sd": round(float(np.sqrt(var0[i])), 3)} for j, i in enumerate(short)]
                    ids, refusal = llm.choose(context_text(c), sl, k_bridge, budget)
                    if ids is None:
                        bridge = choose_bridge(maestro_rule, model, st0, k_bridge, budget, order,
                                               panel=panel, rng_order=rng_order)
                    else:
                        lookup = {d["id"]: int(i) for d, i in zip(sl, short)}
                        bridge = np.array([lookup[x] for x in ids])
                    rec["llm_refusal"] = refusal
                    yb = yc[bridge]
                    prior, _, _ = repaired_prior(model, st0, bridge, yb, repair_threshold)
                    st1 = model.posterior(prior, bridge, yb)
                    final = nominate(model.expected_hit(st1), budget - k_bridge, bridge, order)
                    wells = np.concatenate([bridge, final])
                    rec[arm] = grade(wells)
                    rec[arm + "_wasted"] = wasted(wells)
                    rec[arm + "_bridge_hits"] = grade(bridge)
                elif arm == "maestro_yshuffle":
                    bridge = choose_bridge(maestro_rule, model, st0, k_bridge, budget, order,
                                           panel=panel, rng_order=rng_order)
                    yb = Y[partner[c], bridge] if c in partner else np.full(len(bridge), np.nan)
                    prior, _, _ = repaired_prior(model, st0, bridge, yb, repair_threshold)
                    st1 = model.posterior(prior, bridge, yb)
                    final = nominate(model.expected_hit(st1), budget - k_bridge, bridge, order)
                    wells = np.concatenate([bridge, final])
                    rec[arm] = grade(wells)
                    rec[arm + "_wasted"] = wasted(wells)
                elif arm == "match_panel":
                    bridge = np.asarray(panel[:k_bridge], dtype=int)
                    yb = yc[bridge]
                    s = match_scores(Y[src], src_events, bridge, yb)
                    s = model.source_event_rate if s is None else s + 1e-6 * model.source_event_rate
                    final = nominate(s, budget - k_bridge, bridge, order)
                    wells = np.concatenate([bridge, final])
                    rec[arm] = grade(wells)
                    rec[arm + "_wasted"] = wasted(wells)
                    rec[arm + "_bridge_hits"] = grade(bridge)
                else:
                    rule = maestro_rule if arm == "maestro" else arm[2:]
                    bridge = choose_bridge(rule, model, st0, k_bridge, budget, order,
                                           panel=panel, rng_order=rng_order)
                    yb = yc[bridge]
                    prior = st0
                    if arm == "maestro":
                        prior, mis, repaired = repaired_prior(model, st0, bridge, yb, repair_threshold)
                        rec["misfit"] = mis
                        rec["repaired"] = bool(repaired)
                        rec["bridge_measured"] = int(np.isfinite(yb).sum())
                        if repair_grid:
                            pop = State(np.zeros(model.V.shape[1]), model.pop_cov.copy(), st0.observed.copy())
                            eh, w = bma_expected_hit(model, [st0, pop], bridge, yb)
                            fin = nominate(eh, budget - k_bridge, bridge, order)
                            rec["maestro_bma"] = grade(np.concatenate([bridge, fin]))
                            rec["bma_weight_transfer"] = float(w[0])
                        for thr in repair_grid:
                            pr, _, _ = repaired_prior(model, st0, bridge, yb, thr)
                            fin = nominate(model.expected_hit(model.posterior(pr, bridge, yb)),
                                           budget - k_bridge, bridge, order)
                            rec[f"maestro@{thr:g}"] = grade(np.concatenate([bridge, fin]))
                    st1 = model.posterior(prior, bridge, yb)
                    final = nominate(model.expected_hit(st1), budget - k_bridge, bridge, order)
                    wells = np.concatenate([bridge, final])
                    rec[arm] = grade(wells)
                    rec[arm + "_wasted"] = wasted(wells)
                    rec[arm + "_bridge_hits"] = grade(bridge)
            if "misfit" not in rec and k_bridge > 0:
                bridge = choose_bridge(maestro_rule, model, st0, k_bridge, budget, order,
                                       panel=panel, rng_order=rng_order)
                rec["misfit"] = model.misfit(st0, bridge, yc[bridge])
            records.append(rec)
    return records


def _partners(tgt, keys, groups):
    """A fixed derangement of targets (hash order), skipping partners from the same group."""

    seq = sorted((int(i) for i in tgt), key=lambda i: tie_order([keys[i]], "partner")[0])
    n = len(seq)
    out = {}
    for j, c in enumerate(seq):
        for step in range(1, n):
            q = seq[(j + step) % n]
            if groups[q] != groups[c] or step == n - 1:
                out[c] = q
                break
    return out


def _source_events(model: ContextModel, Ys):
    """Source-only registered events (no target outcome enters the threshold)."""

    from common import Z_EVENT, residualise, robust_z
    G = np.nanmedian(Ys, axis=1)
    S, _ = residualise(Ys.T, G, min_finite=model.min_measured)
    Z, _, _ = robust_z(S)
    with np.errstate(invalid="ignore"):
        e = Z <= Z_EVENT
        if model.abs_gate is not None:
            e &= Ys.T <= model.abs_gate
    return e.T
