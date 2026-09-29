"""The baseline-safe research arm: follow the fixed expert order unless a departure is supported.

File summary
- Path: research/protocol_v2/safe.py
- Purpose: a conservative planner in the spirit of safe policy improvement with baseline
  bootstrapping (SPIBB; Laroche, Trichelair & Tachet des Combes, ICML 2019). Where the reference
  data do not support an estimate, the arm takes the baseline's action. It departs only to an
  action whose value estimate is supported, clearly better than the baseline's, and no riskier.
- Core points:
  - The value estimates are the belief planner's (`research.belief_planning.planner.plan_measurement` with the
    `research/belief_planning` world model), computed from the same state (`arms.belief_state`).
    The arm changes which action is taken, never the estimates or the evidence rules.
  - Effective support of an action, per hypothesis (`effective_support`):
    - independent reference units at that condition (distinct components or skeletons, not
      rows), at least `MIN_REFERENCE_UNITS` = 6, the registered pool rule's minimum identities;
    - the history-weighted support after the real readings so far, at least the same 6;
    - detected templates the validator can match, at least `MIN_TEMPLATES` = 2, the pool rule's
      minimum detected identities;
    - the compound inside the structural applicability domain: nearest training reference at
      Tanimoto >= `SIM_FLOOR` = 0.40, the world model's own floor (dropped in `safe_class`);
    - a validator that can eliminate in this fold;
    - no uncalibrated study shift between references and compound (`extra["study_shift"]`).
    All thresholds are existing registered constants, not tuned here.
  - A departure also needs:
    - a value gain over the baseline action above `DEVIATION_Z` = 1.645 standard errors;
    - no increase in the forecast wrong risk: point estimate within the registered
      non-inferiority margin (0.005), and the conservative bound not above the baseline's.
    Among supported, no-riskier actions the arm takes the one with the highest value, so an
    unsupported favourite does not block a supported alternative (the SPIBB constraint, not a
    single comparison).
  - Stopping. A refused or unknown forecast never becomes a stop: the arm takes the baseline
    action. A model-driven early stop is allowed only when `allow_model_stop` is true, which
    protocol v2 ties to the wrong-risk calibration gate (`calibration.py`). When the baseline has
    no action left, an extra measurement needs a supported, confidently positive value.
  - Approximation, disclosed: the value of a first action assumes the planner's unconstrained
    continuation; the gate is re-applied at every real step.
- Interfaces: `safe_arm`, `effective_support`, `SUPPORT_RULE`
- Depends on: research/belief_planning (arms, world, planner), maestro.acquisition
"""
from __future__ import annotations

import math

import numpy as np

from maestro.acquisition import outcome_consequences
from research.belief_planning import arms as BA
from research.belief_planning import world as W
from research.belief_planning.planner import plan_measurement

from . import contracts as K

P, C, V = BA.P, BA.C, BA.V
LP = K.T.LP

MIN_REFERENCE_UNITS = LP.POOL_MIN_IDENTITIES
MIN_TEMPLATES = LP.POOL_MIN_DETECTED_IDENTITIES
SIM_FLOOR = W.SIM_FLOOR
DEVIATION_Z = BA.DEVIATION_Z
WRONG_MARGIN = 0.005
SUPPORT_RULE = {"min_reference_units": MIN_REFERENCE_UNITS, "min_weighted_support": MIN_REFERENCE_UNITS,
                "min_templates": MIN_TEMPLATES, "sim_floor": SIM_FLOOR, "deviation_z": DEVIATION_Z,
                "wrong_margin": WRONG_MARGIN,
                "sources": {"min_reference_units": "sequence_audit.lincs_prepare.POOL_MIN_IDENTITIES",
                            "min_templates": "sequence_audit.lincs_prepare.POOL_MIN_DETECTED_IDENTITIES",
                            "sim_floor": "belief_planning.world.SIM_FLOOR",
                            "deviation_z": "belief_planning.arms.DEVIATION_Z",
                            "wrong_margin": "belief_planning protocol wrong_noninferiority_margin"}}


def _unit_map(view) -> dict:
    cache = view.extra.get("v2_unit_of")
    if cache is None:
        comp = view.data.compounds.drop_duplicates("compound").set_index("compound")
        column = "component" if "component" in comp.columns else "skeleton"
        cache = {c: (g if isinstance(g, str) else c) for c, g in comp[column].items()}
        view.extra["v2_unit_of"] = cache
    return cache


def max_train_similarity(view, world, compound) -> float:
    """Nearest training reference's Tanimoto similarity; NaN without a parsable structure."""
    cache = view.extra.setdefault("v2_similarity", {})
    if compound not in cache:
        row = world.pos.get(compound, -1)
        if world.fp is None or row < 0 or not world.fp[row].any():
            cache[compound] = float("nan")
        else:
            train = [world.pos[c] for c in view.extra["training_compounds"] if world.pos.get(c, -1) >= 0]
            if not train:
                cache[compound] = float("nan")
            else:
                x = world.fp[row]
                fp = world.fp[np.asarray(train)]
                inter = fp @ x
                union = fp.sum(1) + x.sum() - inter
                sim = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
                cache[compound] = float(sim.max())
    return cache[compound]


def effective_support(view, world, compound, key, h1, h2, forecast, *, gate_novelty=True) -> dict:
    """Per-hypothesis support of one action's forecast, and whether it clears every gate."""
    entry = world.keys.get(tuple(key))
    table = view.ft.tables.get(tuple(key))
    out = {"action": C.action_id(key), "reasons": []}
    if entry is None or table is None or forecast is None or forecast.refusal:
        out["reasons"].append("condition_not_in_reference_library")
        out["supported"] = False
        return out
    unit_of = _unit_map(view)
    for own, other in ((h1, h2), (h2, h1)):
        rows = np.flatnonzero(entry["klass"] == own)
        if own in world.cidx and other in world.cidx:
            rows = rows[entry["cat"][rows, world.cidx[other]] >= 0]
        units = len({unit_of.get(entry["names"][r], entry["names"][r]) for r in rows})
        branch = forecast.branch_for(own)
        weighted = int(branch.support) if branch is not None else 0
        templates = int(((np.asarray(table.klass) == own) & np.asarray(table.detected, dtype=bool)).sum())
        out[own] = {"reference_units": units, "weighted_support": weighted, "templates": templates}
        if units < MIN_REFERENCE_UNITS:
            out["reasons"].append(f"few_reference_units:{own}")
        if weighted < MIN_REFERENCE_UNITS:
            out["reasons"].append(f"thin_history_weighted_support:{own}")
        if templates < MIN_TEMPLATES:
            out["reasons"].append(f"few_validator_templates:{own}")
    similarity = max_train_similarity(view, world, compound)
    out["max_train_tanimoto"] = similarity
    if gate_novelty and not (similarity >= SIM_FLOOR):
        out["reasons"].append("outside_structural_applicability_domain")
    if not view.params.get("eliminates"):
        out["reasons"].append("validator_cannot_eliminate")
    if view.extra.get("study_shift") and not view.extra.get("study_calibrated"):
        out["reasons"].append("uncalibrated_study_shift")
    out["supported"] = not out["reasons"]
    return out


def _plan(view, compound, h1, h2, executed, menu, setting, world_args, price):
    cache = view.extra.setdefault("v2_plans", {})
    history = tuple((tuple(s["key"]), s["outcome"]) for s in executed)
    key = (compound, h1, h2, history, world_args, price)
    if key not in cache:
        world, real, belief, legal, forecast, by_id = BA.belief_state(view, compound, h1, h2, executed, menu, setting,
                                                                      **dict(world_args))
        depth = setting.max_measurements - len(executed)
        plan = plan_measurement((h1, h2), belief, legal, forecast, outcome_consequences(V.registered_rules(h1, h2)),
                                horizon=depth, price=price)
        cache[key] = (world, real, belief, plan, by_id)
    return cache[key]


def safe_arm(*, gate_novelty: bool = True, allow_model_stop: bool = False, price: float = BA.PRICE,
             z: float = DEVIATION_Z):
    """The baseline-safe arm. `allow_model_stop` is set from the calibration gate, not by hand."""
    world_args = (("vc", "on"), ("feedback", "true"))

    def arm(view, compound, h1, h2, executed, menu, remaining, setting, state):
        fixed_key, _ = P.fixed(view, compound, h1, h2, executed, menu, remaining, setting, state)
        base_id = C.action_id(fixed_key) if fixed_key is not None else None
        note = {"evidence_kind": "model_prediction", "planner": "baseline_safe", "baseline": base_id,
                "gate_novelty": gate_novelty, "allow_model_stop": allow_model_stop}

        def follow(reason, **extra):
            note.update({"decision": "baseline", "why": reason, **extra})
            if fixed_key is None:
                return None, {**note, "reason": "fixed_sequence_exhausted"}
            return fixed_key, note

        if not view.params.get("eliminates"):
            return follow("validator_cannot_eliminate")
        world, real, belief, plan, by_id = _plan(view, compound, h1, h2, executed, menu, setting, world_args, price)
        note["belief"] = {h: round(p, 6) for h, p in belief.items()}
        note["planner_choice"] = plan.chosen
        note["planner_status"] = plan.reason or plan.status
        evaluations = plan.evaluations

        def support(action_id):
            key = by_id[action_id]
            return effective_support(view, world, compound, key, h1, h2, world.forecast(key, h1, h2, compound, real),
                                     gate_novelty=gate_novelty)

        if plan.chosen == base_id and base_id is not None:
            return follow("planner_agrees")
        if base_id is None:
            # The baseline has no action left. An extra measurement is a departure too.
            if plan.chosen is None:
                return None, {**note, "decision": "baseline", "why": "both_stop", "reason": "fixed_sequence_exhausted"}
            top = evaluations[plan.chosen]
            sup = support(plan.chosen)
            if sup["supported"] and top.utility - z * top.standard_error > 0:
                note.update({"decision": "departure", "why": "supported_extra_measurement", "support": sup})
                return by_id[plan.chosen], note
            return None, {**note, "decision": "baseline", "why": "extra_measurement_not_supported",
                          "support": sup, "reason": "fixed_sequence_exhausted"}
        if base_id not in evaluations:
            return follow("baseline_forecast_refused_or_unknown", refusals=dict(plan.refusals))
        kept = evaluations[base_id]
        base_support = support(base_id)
        if not base_support["supported"]:
            return follow("baseline_value_not_supported", support=base_support)
        if plan.chosen is None:
            if plan.reason in ("world_model_refused", "no_legal_action"):
                return follow("refusal_is_not_a_stop")
            if allow_model_stop and kept.utility + z * kept.standard_error < 0:
                note.update({"decision": "departure", "why": "supported_stop", "support": base_support})
                return None, {**note, "reason": "baseline_safe_supported_stop"}
            return follow("model_stop_not_allowed" if not allow_model_stop else "stop_not_supported")
        candidates, rejected = [], {}
        for action_id, value in evaluations.items():
            if action_id == base_id:
                continue
            sup = support(action_id)
            risk_ok = (value.p_wrong <= kept.p_wrong + WRONG_MARGIN
                       and value.p_wrong_upper <= kept.p_wrong_upper + 1e-12)
            margin = z * math.sqrt(value.standard_error ** 2 + kept.standard_error ** 2)
            gain = value.utility - kept.utility
            if sup["supported"] and risk_ok and gain > margin:
                candidates.append((value.utility, -value.cost, action_id, sup, gain, margin))
            else:
                rejected[action_id] = {"support": sup["reasons"], "risk_ok": risk_ok, "gain": gain, "margin": margin}
        if not candidates:
            return follow("no_supported_better_action",
                          top_rejected=rejected.get(plan.chosen) if plan.chosen else None)
        utility, _, action_id, sup, gain, margin = max(candidates, key=lambda x: (x[0], x[1], x[2]))
        note.update({"decision": "departure", "why": "supported_better_action", "support": sup,
                     "gain": gain, "margin": margin, "planner_top_taken": action_id == plan.chosen})
        return by_id[action_id], note

    return arm
