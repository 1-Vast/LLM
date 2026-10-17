"""Campaign arms: who measures which wells, and which pairs go to follow-up.

File summary
- Path: research/indication_triage_20261016/policy.py
- Purpose: every registered arm as a function of the same campaign context, so the grader sees
  only nominations, wells, cycles and receipts.
- Core points:
  - Two cost pools, equal for every arm:
    - probe wells: `w` single-dose primary wells per compound on average (the arm decides where);
    - follow-up list: 32 (compound, line) pairs per campaign, at most 3 per compound.
  - A probe returns the published value plus frozen probe noise (common random numbers per
    compound and line, scaled by the replicate spread at that effect size). A probe on a missing
    value is a failed well: spent, retained, no update.
  - Follow-up truth is the registered event of the published profile.
  - `two_stage` is the conventional adaptive screen (fixed first panel, more lines for the
    most-killed compounds, ridge completion); it isolates what adaptivity alone buys.
  - `maestro_loop` is the only adaptive arm: seed probes from the sparse design, a posterior per
    compound, compound triage by event uncertainty, one adaptive probe round, follow-up by
    posterior P(event), and a design-based yield certificate from a uniformly random audit of its
    own follow-up list (`maestro.certification`).
  - Named refusals: `POSTERIOR_INACTIVE` (no adaptive probes for a compound whose P(active) is
    below `P_MIN`), `FAILED_WELL` (probe on a missing value).
- Interfaces: `Context`, `ARMS`, `CYCLES`, `run_arm`, `grade`.
"""
from __future__ import annotations

import random
import sys
import warnings
from dataclasses import dataclass, field

import numpy as np

from common import CAP, FOLLOW_UP, ROOT, h, nominate, tie_break
from world import World, call_score

sys.path.insert(0, str(ROOT / "src"))
from maestro.certification import draw_audit, yield_lower_bound  # noqa: E402

ARMS = ("zero", "structure", "fixed_panel", "random_panel", "probe_knn", "fixed_calibrated", "two_stage",
        "maestro_loop", "full_panel", "oracle")
# Candidates for the H1 comparator: every arm that is not the loop, not a reference and not the zero arm.
COMPARATORS = ("structure", "fixed_panel", "random_panel", "probe_knn", "fixed_calibrated", "two_stage")
# Assay cycles before the follow-up list is complete (probe rounds plus the follow-up round).
CYCLES = {"zero": 1, "structure": 1, "fixed_panel": 2, "random_panel": 2, "probe_knn": 2,
          "fixed_calibrated": 2, "two_stage": 3, "maestro_loop": 3, "full_panel": 2, "oracle": 1}
P_MIN = 0.01           # P(active) below which the loop buys no adaptive probes
AUDIT = 8              # follow-up pairs measured first, uniformly at random, for the certificate
DELTA = 0.05           # one-sided error of the yield lower bound
TOP_UNCERTAIN = 10     # lines per compound entering the triage priority


@dataclass
class Context:
    world: World
    cores: np.ndarray          # evaluation cores
    Y: np.ndarray              # published profiles (truth and probe source), NaN = not measured
    truth: np.ndarray          # registered events
    prior: np.ndarray          # structure prior means
    noise: np.ndarray          # frozen probe noise per (compound, line)
    design: np.ndarray         # sparse-design line order
    lineage: np.ndarray
    cache: dict = field(default_factory=dict)

    def observe(self, i: int, lines) -> np.ndarray:
        lines = np.asarray(lines, dtype=int)
        return self.Y[i, lines] + self.noise[i, lines]


def _structure(ctx: Context, idx, w, params):
    rows = []
    for i in idx:
        key = ("structure", int(i))
        if key not in ctx.cache:
            post = ctx.world.posterior(ctx.prior[i], [], [])
            ctx.cache[key] = ctx.world.event_probability(post, str(ctx.cores[i]))[0]
        rows.append(ctx.cache[key])
    return {"score": np.stack(rows), "wells": 0, "failed": 0}


def _probe_lines(ctx: Context, i: int, w: int, kind: str) -> np.ndarray:
    if kind == "fixed":
        return ctx.design[:w]
    return np.random.default_rng(h(str(ctx.cores[i]), "random_panel") % (2 ** 32)).permutation(ctx.world.L)[:w]


def _point(ctx: Context, idx, w, kind: str):
    rows, failed = [], 0
    for i in idx:
        P = _probe_lines(ctx, i, w, kind)
        y = ctx.observe(i, P)
        failed += int((~np.isfinite(y)).sum())
        rows.append(call_score(ctx.world.point_mean(ctx.prior[i], P, y), ctx.world.G))
    return {"score": np.stack(rows), "wells": w * len(idx), "failed": failed}


def _probe_knn(ctx: Context, idx, w, params):
    K = int(params.get("knn", 20))
    P = ctx.design[:w]
    ref = ctx.world.Ytrain[:, P]
    rows, failed = [], 0
    for i in idx:
        y = ctx.observe(i, P)
        failed += int((~np.isfinite(y)).sum())
        diff = ref - y[None, :]
        both = np.isfinite(diff)
        dist = np.where(both, diff ** 2, 0.0).sum(1) / np.maximum(both.sum(1), 1)
        dist[both.sum(1) < max(1, len(P) // 2)] = np.inf
        nn = np.argsort(dist, kind="stable")[:K]
        with np.errstate(invalid="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            pred = np.nanmean(ctx.world.Ytrain[nn], axis=0)
        pred = np.where(np.isfinite(pred), pred, ctx.world.mu)
        ok = np.isfinite(y)
        pred[P[ok]] = y[ok]
        rows.append(call_score(pred, ctx.world.G))
    return {"score": np.stack(rows), "wells": w * len(idx), "failed": failed}


def _calibrated(ctx: Context, i: int, P: np.ndarray) -> tuple[np.ndarray, float, int]:
    y = ctx.observe(i, P)
    post = ctx.world.posterior(ctx.prior[i], P, y)
    pe, pa = ctx.world.event_probability(post, str(ctx.cores[i]))
    return pe, pa, int((~np.isfinite(y)).sum())


def _fixed_calibrated(ctx: Context, idx, w, params):
    rows, failed = [], 0
    for i in idx:
        key = ("fixed_calibrated", int(i), w)
        if key not in ctx.cache:
            ctx.cache[key] = _calibrated(ctx, i, ctx.design[:w])
        pe, _, f = ctx.cache[key]
        rows.append(pe)
        failed += f
    return {"score": np.stack(rows), "wells": w * len(idx), "failed": failed}


def _maestro_loop(ctx: Context, idx, w, params):
    k1, k2, rule = int(params["k1"]), int(params["k2"]), params["rule"]
    L = ctx.world.L
    seed = ctx.design[:k1]
    pe, pa, failed = [], [], 0
    for i in idx:
        key = ("seed", int(i), k1)
        if key not in ctx.cache:
            ctx.cache[key] = _calibrated(ctx, i, seed)
        e, a, f = ctx.cache[key]
        pe.append(e)
        pa.append(a)
        failed += f
    pe, pa = np.stack(pe), np.array(pa)
    top = -np.sort(-pe * (1 - pe), axis=1)[:, :TOP_UNCERTAIN].sum(1)
    ranked = list(np.argsort(-top, kind="stable"))
    eligible = [j for j in ranked if pa[j] >= P_MIN]
    refused = [j for j in ranked if pa[j] < P_MIN]
    extra = _allocate_extra(eligible, refused, w * len(idx) - k1 * len(idx), k2, k1, L)
    ties = tie_break(ctx.cores[idx], L)
    final, probed_counts = [], []
    for j, i in enumerate(idx):
        if extra[j] == 0:
            final.append(pe[j])
            probed_counts.append(k1)
            continue
        value = pe[j] if rule == "likely" else pe[j] * (1 - pe[j])
        value = value.copy()
        value[seed] = -np.inf
        order_lines = np.lexsort((ties[j], -value))
        add = order_lines[:extra[j]]
        P = np.concatenate([seed, add])
        e, _, f = _calibrated(ctx, i, P)
        failed += f - int((~np.isfinite(ctx.observe(i, seed))).sum())
        final.append(e)
        probed_counts.append(len(P))
    return {"score": np.stack(final), "wells": int(sum(probed_counts)), "failed": failed,
            "refusals": {"POSTERIOR_INACTIVE": len(refused)},
            "adaptive_compounds": int(sum(1 for v in extra.values() if v > 0))}


def _allocate_extra(first: list, then: list, remaining: int, per: int, k1: int, L: int) -> dict:
    """Second-round wells: `per` each in priority order (first, then), the remainder one at a time.

    If the first group cannot absorb the round at `per` wells each, each of its members gets an
    equal larger share, so every arm spends the same budget.
    """

    extra = {j: 0 for j in [*first, *then]}
    if first and len(first) * per < remaining:
        per = min(L - k1, remaining // len(first))
    order = [*first, *then]
    for j in order:
        if remaining <= 0:
            break
        give = int(min(per, remaining, L - k1))
        extra[j] = give
        remaining -= give
    while remaining > 0:
        progressed = False
        for j in order:
            if remaining <= 0:
                break
            if k1 + extra[j] < L:
                extra[j] += 1
                remaining -= 1
                progressed = True
        if not progressed:
            break
    return extra


def _two_stage(ctx: Context, idx, w, params):
    """Conventional adaptive screen: a fixed first panel, then more lines for the most-killed compounds.

    Stage-2 lines are the compound's top unprobed lines by its own ridge completion; the follow-up
    list is ranked by the conventional call score. No posterior, scale or event probability is used.
    """

    k1, k2 = int(params["k1"]), int(params["k2"])
    L = ctx.world.L
    seed = ctx.design[:k1]
    obs = [ctx.observe(i, seed) for i in idx]
    failed = sum(int((~np.isfinite(y)).sum()) for y in obs)
    potency = np.array([np.nanmin(y) if np.isfinite(y).any() else np.inf for y in obs])
    ranked = list(np.argsort(potency, kind="stable"))
    extra = _allocate_extra(ranked, [], w * len(idx) - k1 * len(idx), k2, k1, L)
    ties = tie_break(ctx.cores[idx], L)
    rows, wells = [], 0
    for j, i in enumerate(idx):
        score = call_score(ctx.world.point_mean(ctx.prior[i], seed, obs[j]), ctx.world.G)
        wells += k1 + extra[j]
        if extra[j]:
            value = score.copy()
            value[seed] = -np.inf
            add = np.lexsort((ties[j], -value))[:extra[j]]
            y_add = ctx.observe(i, add)
            failed += int((~np.isfinite(y_add)).sum())
            P = np.concatenate([seed, add])
            score = call_score(ctx.world.point_mean(ctx.prior[i], P, np.concatenate([obs[j], y_add])), ctx.world.G)
        rows.append(score)
    return {"score": np.stack(rows), "wells": wells, "failed": failed}


def _full_panel(ctx: Context, idx, w, params):
    L = ctx.world.L
    obs = np.stack([ctx.observe(i, np.arange(L)) for i in idx])
    return {"score": call_score(obs, ctx.world.G), "wells": L * len(idx), "failed": int((~np.isfinite(obs)).sum())}


def run_arm(arm: str, ctx: Context, idx: np.ndarray, w: int, params: dict | None = None) -> dict:
    params = params or {}
    if arm == "zero":
        out = {"score": np.tile(-ctx.world.G, (len(idx), 1)), "wells": 0, "failed": 0}
    elif arm == "structure":
        out = _structure(ctx, idx, w, params)
    elif arm == "fixed_panel":
        out = _point(ctx, idx, w, "fixed")
    elif arm == "random_panel":
        out = _point(ctx, idx, w, "random")
    elif arm == "probe_knn":
        out = _probe_knn(ctx, idx, w, params)
    elif arm == "fixed_calibrated":
        out = _fixed_calibrated(ctx, idx, w, params)
    elif arm == "two_stage":
        out = _two_stage(ctx, idx, w, params)
    elif arm == "maestro_loop":
        out = _maestro_loop(ctx, idx, w, params)
    elif arm == "full_panel":
        out = _full_panel(ctx, idx, w, params)
    elif arm == "oracle":
        out = {"score": ctx.truth[idx].astype(float), "wells": 0, "failed": 0}
    else:
        raise ValueError(f"unknown arm {arm}")
    out["picks"] = nominate(out.pop("score"), ctx.cores[idx], FOLLOW_UP, CAP)
    out["cycles"] = CYCLES[arm]
    return out


def grade(ctx: Context, idx: np.ndarray, result: dict, campaign_key: str) -> dict:
    picks = result["picks"]
    hits = [bool(ctx.truth[idx[i], l]) for i, l in picks]
    lineages = {(int(idx[i]), str(ctx.lineage[l])) for (i, l), hit in zip(picks, hits) if hit}
    rng = random.Random(h(campaign_key, "audit"))
    audit, remainder = draw_audit(list(range(len(picks))), AUDIT, rng)
    audit_hits = sum(hits[k] for k in audit)
    bound = yield_lower_bound(len(picks), len(audit), audit_hits, DELTA)
    remainder_hits = sum(hits[k] for k in remainder)
    return {"hits": int(sum(hits)), "listed": len(picks), "lineage_hits": len(lineages),
            "wells": int(result["wells"]), "failed_wells": int(result["failed"]), "cycles": result["cycles"],
            "certificate": {"audit": len(audit), "audit_hits": int(audit_hits), "yield_bound": int(bound),
                            "remainder": len(remainder), "remainder_hits": int(remainder_hits),
                            "covered": bool(remainder_hits >= bound)},
            **{k: result[k] for k in ("refusals", "adaptive_compounds") if k in result}}
