"""Typed ResearchEdit, decision-weighted discrimination, robust objective and failure routing.

File summary
- Path: research/observable_state_20261018/research_edit.py
- Purpose: the minimum representation of a scientific edit r = (Delta M, A, P, Omega) for the Observable-State
  Discovery Campaign. It is a small typed record plus pure functions; it never rewrites code and never fits
  numbers by language model (parameters come from ordinary statistics, e.g. `fit_interaction`).
- Interfaces: `ResearchEdit`, `validate`, `crossed_contrast`, `fit_interaction`, `hellinger2_gaussian`, `d_dec`,
  `robust_objective`, `sufficiency_verdict`, `e90`, `saving90`, `break_even_projects`, `route`.
- Nothing here reads outcomes. Thresholds passed to `route` and `robust_objective` are protocol parameters that must be
  fixed (and frozen) before any evaluation; this module ships no hidden defaults for them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

PRIMITIVES = ("split", "merge", "interaction", "local_exception", "observation_request")
DIRECTIONS = ("up", "down", "none")
COST_KINDS = ("assay_wells", "compute", "curation", "rounds", "logical_queries")
# required parameters per primitive (typed edit language; values are names/sets, never numbers to be invented)
PRIMITIVE_PARAMS = {
    "split": ("rule", "state_variable"),
    "merge": ("rules",),
    "interaction": ("drug_family", "state_variable"),
    "local_exception": ("subfamily_or_context", "rule"),
    "observation_request": ("missing_readout", "distinguishes"),
}


@dataclass
class ResearchEdit:
    edit_id: str
    primitive: str
    observed_failure: str
    competing_explanations: list  # [{"name", "description", "is_strong_simple_baseline": bool}]
    virtual_cell_edit: dict  # primitive parameters
    applicability_scope: dict  # drugs / contexts / dose / time / assay
    discriminating_assay: dict  # {"bundle", "cost": {kind: units}}
    predicted_outcomes: dict  # explanation name -> {"quantity", "direction", "min_magnitude"}
    expected_decision_change: dict  # {"nomination_change", "direction_of_qualified_hits"}
    rejection_condition: dict  # {"quantity", "op", "threshold"}
    registered_before_outcome: str = ""  # digest/timestamp written before any outcome is revealed
    dependence_group: str = ""  # edits from the same campaign/family are not independent
    provenance: dict = field(default_factory=dict)
    # filled only after evaluation
    observed_result: dict | None = None
    downstream_decision_effect: dict | None = None
    transfer_result: dict | None = None


def validate(e: ResearchEdit) -> list:
    """Return the list of problems; an empty list means the proposal is admissible to run (not that it is correct)."""

    bad = []
    if e.primitive not in PRIMITIVES:
        bad.append(f"unknown primitive {e.primitive!r}")
    else:
        for p in PRIMITIVE_PARAMS[e.primitive]:
            if p not in e.virtual_cell_edit:
                bad.append(f"primitive {e.primitive} needs virtual_cell_edit[{p!r}]")
    if not e.observed_failure.strip():
        bad.append("observed_failure empty")
    names = [x.get("name") for x in e.competing_explanations]
    if len(names) < 2 or len(set(names)) < 2:
        bad.append("need at least two distinct competing explanations")
    if not any(x.get("is_strong_simple_baseline") for x in e.competing_explanations):
        bad.append("one explanation must be the strong simple baseline")
    for n in names:
        p = e.predicted_outcomes.get(n)
        if not p:
            bad.append(f"no prediction for explanation {n!r}")
            continue
        if p.get("direction") not in DIRECTIONS:
            bad.append(f"prediction for {n!r} needs direction in {DIRECTIONS}")
        if not p.get("quantity"):
            bad.append(f"prediction for {n!r} names no observable quantity")
        if p.get("direction") in ("up", "down") and not isinstance(p.get("min_magnitude"), (int, float)):
            bad.append(f"directional prediction for {n!r} needs a numeric min_magnitude")
    dirs = {e.predicted_outcomes[n]["direction"] for n in names if n in e.predicted_outcomes and "direction" in e.predicted_outcomes[n]}
    if len(names) >= 2 and len(dirs) < 2 and all(n in e.predicted_outcomes for n in names):
        mags = {(e.predicted_outcomes[n].get("direction"), e.predicted_outcomes[n].get("min_magnitude")) for n in names}
        if len(mags) < 2:
            bad.append("explanations make identical predictions; the assay cannot discriminate them")
    rc = e.rejection_condition
    if not (rc.get("quantity") and rc.get("op") in ("<", "<=", ">", ">=") and isinstance(rc.get("threshold"), (int, float))):
        bad.append("rejection_condition needs quantity, op and numeric threshold")
    dc = e.expected_decision_change
    if not dc.get("nomination_change") or dc.get("direction_of_qualified_hits") not in DIRECTIONS:
        bad.append("expected_decision_change must state the nomination change and a direction (not only that utility rises)")
    if dc.get("nomination_change", "").strip().lower() in ("utility up", "total utility up", "up"):
        bad.append("expected_decision_change may not be only 'utility goes up'")
    if not any(e.applicability_scope.get(k) for k in ("drugs", "contexts", "assay")):
        bad.append("applicability_scope empty")
    cost = e.discriminating_assay.get("cost", {})
    if not cost or any(k not in COST_KINDS for k in cost):
        bad.append(f"assay cost must be itemised over {COST_KINDS}")
    if not e.registered_before_outcome:
        bad.append("predictions not registered before outcomes (registered_before_outcome empty)")
    if not e.dependence_group:
        bad.append("dependence_group empty (repeated masked episodes are not independent tasks)")
    return bad


# ---------------------------------------------------------------- crossed contrast and interaction
def crossed_contrast(Y, d, d2, c, c2) -> float:
    """Delta = [Y(d,c) - Y(d2,c)] - [Y(d,c2) - Y(d2,c2)] on a dict-like or 2-D array indexed Y[drug][context]."""

    return float((Y[d][c] - Y[d2][c]) - (Y[d][c2] - Y[d2][c2]))


def fit_interaction(y, drug, ctx_state, family) -> dict:
    """Ordinary least squares: main effects (drug, context) versus + gamma*I(drug in family)*I(state=1).

    `y`, `drug`, `ctx_state` are aligned 1-D observations (drug id, binary state of the context); `family` is the set of
    drug ids. Returns gamma, partial-F against the main-effect model and both residual sums of squares. A functional
    response pattern only; it is not evidence of a molecular mechanism.
    """

    y = np.asarray(y, float)
    drug = np.asarray(drug)
    st = np.asarray(ctx_state, int)
    ud = sorted(set(drug.tolist()))
    X = [np.ones_like(y)]
    X += [(drug == u).astype(float) for u in ud[1:]]
    X += [st.astype(float)]
    X0 = np.column_stack(X)
    inter = np.isin(drug, list(family)).astype(float) * st
    X1 = np.column_stack([X0, inter])
    b0, *_ = np.linalg.lstsq(X0, y, rcond=None)
    b1, *_ = np.linalg.lstsq(X1, y, rcond=None)
    r0, r1 = float(((y - X0 @ b0) ** 2).sum()), float(((y - X1 @ b1) ** 2).sum())
    df = len(y) - X1.shape[1]
    F = ((r0 - r1) / 1.0) / (r1 / df) if df > 0 and r1 > 0 else float("inf")
    return {"gamma": float(b1[-1]), "F": float(F), "rss_main": r0, "rss_interaction": r1, "df_resid": int(df)}


# ---------------------------------------------------------------- decision-weighted discrimination
def hellinger2_gaussian(m1, s1, m2, s2) -> float:
    """Squared Hellinger distance between two univariate Gaussians (bounded in [0, 1])."""

    v = s1 * s1 + s2 * s2
    if v <= 0:
        return 0.0 if m1 == m2 else 1.0
    return float(1.0 - np.sqrt(2.0 * s1 * s2 / v) * np.exp(-((m1 - m2) ** 2) / (4.0 * v)))


def d_dec(pi, delta_u, predictive) -> float:
    """D_dec(a) = sum_{h<h'} pi_h pi_h' DeltaU(h,h') d(p_h(o|a), p_h'(o|a)).

    `pi[h]` prior weights; `delta_u[h][h']` the downstream decision loss if h and h' are confused (symmetric, >= 0, in
    utility units); `predictive[h] = (mean, sd)` the Gaussian predictive of the observation under h for assay a.
    """

    tot = 0.0
    for h, k in combinations(range(len(pi)), 2):
        tot += pi[h] * pi[k] * delta_u[h][k] * hellinger2_gaussian(*predictive[h], *predictive[k])
    return float(tot)


def robust_objective(lcb_delta_u, assay_cost_u, complexity_u, misspec_u, *, lam=1.0, eta=1.0, rho=1.0) -> float:
    """J = LCB[Delta U_future] - lam*assay_cost - eta*complexity - rho*misspec_risk.

    All four inputs must already be in the SAME utility unit (qualified nominations per 64 compounds); `lam`, `eta`, `rho`
    are conversion/weight factors fixed in the protocol. assay_cost_u must be the whole assay cost once: callers may not
    also subtract it inside Delta U (the evaluator reports Delta U at equal budget or gross, never both).
    """

    return float(lcb_delta_u - lam * assay_cost_u - eta * complexity_u - rho * misspec_u)


# ---------------------------------------------------------------- decision sufficiency and amortisation
def sufficiency_verdict(per_cluster_loss, eps, *, n_boot=4000, seed=20261018) -> dict:
    """Decision sufficiency U(d*(z)) >= U(d*(H)) - eps.

    `per_cluster_loss[g] = U(d*(H)) - U(d*(z))` per cluster (family/lineage). SUFFICIENT only if the one-sided 95% upper
    bound of the mean loss is below eps; INSUFFICIENT if the lower bound exceeds eps; otherwise UNRESOLVED.
    """

    x = np.asarray(per_cluster_loss, float)
    rng = np.random.default_rng(seed)
    b = np.array([x[rng.integers(0, len(x), len(x))].mean() for _ in range(n_boot)])
    lo, hi = np.quantile(b, [0.05, 0.95])
    verdict = "SUFFICIENT" if hi < eps else ("INSUFFICIENT" if lo > eps else "UNRESOLVED")
    return {"mean_loss": float(x.mean()), "upper95_one_sided": float(hi), "lower95_one_sided": float(lo), "eps": eps, "verdict": verdict}


def e90(budgets, utilities, full_information_utility) -> float | None:
    """Smallest budget whose utility reaches 90% of the full-information decision utility (linear interpolation)."""

    b, u = np.asarray(budgets, float), np.asarray(utilities, float)
    target = 0.9 * full_information_utility
    if u.max() < target:
        return None
    k = int(np.argmax(u >= target))
    if k == 0:
        return float(b[0])
    return float(b[k - 1] + (target - u[k - 1]) * (b[k] - b[k - 1]) / (u[k] - u[k - 1]))


def saving90(e90_method, e90_baseline) -> float | None:
    if e90_method is None or e90_baseline is None or e90_baseline <= 0:
        return None
    return 1.0 - e90_method / e90_baseline


def break_even_projects(research_cost, per_project_savings) -> float:
    """N_BE = research cost / average per-project assay savings (same cost unit). Infinite if savings <= 0."""

    return float("inf") if per_project_savings <= 0 else float(research_cost / per_project_savings)


# ---------------------------------------------------------------- failure routing
def route(headroom, identifiability, transport, *, h_min, i_min, t_min, policy_ok=None, all_strong_independent_ready=False) -> str:
    """H/I/T routing table. Thresholds are required keyword arguments (no defaults) so they must be registered.

    Low H -> expand the research/action abstraction. High H, low I -> new discriminating measurement. High H and I, low T
    -> revise the state or applicability scope. High H, I, T with a poor policy -> algorithm search. All strong and the
    policy passes -> freeze a candidate for independent evaluation. A failed edit rejects the edit, never the project.
    """

    if headroom < h_min:
        return "EXPAND_ACTION_ABSTRACTION"
    if identifiability < i_min:
        return "NEW_DISCRIMINATING_MEASUREMENT"
    if transport < t_min:
        return "REVISE_STATE_OR_SCOPE"
    if policy_ok is False:
        return "CONSIDER_ALGORITHM_SEARCH"
    return "FREEZE_FOR_INDEPENDENT_EVALUATION" if all_strong_independent_ready else "CANDIDATE_NOT_YET_INDEPENDENT"
