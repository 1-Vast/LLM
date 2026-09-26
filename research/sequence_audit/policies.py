"""Behaviour-matched sequence episodes, and the arms compared in them.

File summary
- Path: research/sequence_audit/policies.py
- Purpose: one episode runner that every arm goes through. Candidate actions, exposure-time order,
  the measurement and assay-day budgets, the QC-failure rule, stopping and terminal utility are the
  runner's, so they are identical across arms; an arm only chooses among the legal actions it is
  offered, or stops with a named reason.
- Core points:
  - `Setting` holds what differs between datasets (menu, assay days, budget, fixed sequence), so the
    same runner and arms serve SciPlex3 and L1000.
  - `plan_contingent` is `acquisition_followup/two_step.plan_two_step` with the assay-day function
    passed in instead of read from the SciPlex3 module. `test_sequence_audit.py` checks that it
    returns the original plans on every SciPlex3 contrast.
  - A QC failure charges its assay days, updates no evidence, and (under the primary rule) every
    arm is asked again. The two-step arms then value one remaining measurement from unconditioned
    forecasts, because a failed assay says nothing about the compound.
  - `two_step_fallback` is the pre-registered revision (`protocol.json`): when the contingent
    planner would stop or defer only because it has no paired references or only thin ones, it
    takes the fixed sequence's next legal action. It still stops when the references it has
    forecast no gain or a wrong-elimination risk above break-even.
    The current implementation re-evaluates supported continuations after the actual fallback
    first measurement; `arms(..., frozen_replay=True)` retains the historical early-stop defect.
  - Forecasts only choose actions. Evidence changes only through `common.evidence_update` on a
    real, executed result.
- Depends on: research/acquisition_followup/two_step.py, research/acquisition_link/evaluate.py,
  research/dynamic_world_model (common, episodes), maestro.acquisition, maestro.selection
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "acquisition_followup"))

import two_step as S  # noqa: E402

C, E, V = S.C, S.E, S.V

from maestro.acquisition import (  # noqa: E402
    outcome_consequences,
    select_discriminating_action,
    select_expected_coverage,
)
from maestro.models import BiologicalQuantity, EvidenceAction, EvidenceActionKind  # noqa: E402
from maestro.outcome import EvidenceState  # noqa: E402
from maestro.selection import BudgetedEvidenceSelector  # noqa: E402

LABELS = S.LABELS
NEUTRAL = {"ambiguous": V.UNRESOLVED, "undetected": V.ABSENT}
UNINFORMED = ("no_paired_references", "no_references", "inadequate_support_or_uncertainty")


@dataclass(frozen=True)
class Setting:
    """What differs between datasets; everything else is the runner's."""

    name: str
    keys: tuple
    fixed_order: tuple
    days: Callable[[tuple], float]
    budget_days: float
    max_measurements: int = 2

    @property
    def step_budget(self) -> float:
        """A one-action budget for the single-step selectors: the costliest menu action."""
        return max(self.days(key) for key in self.keys)


# The sequences `episodes.choose("fixed")` follows; the follow-up's two-measurement, 16-day budget.
SCIPLEX3_FIXED = {"B": (("A549", 24.0, 10000.0), ("MCF7", 24.0, 10000.0)),
                  "A": (("A549", 24.0, 10000.0), ("A549", 72.0, 10000.0))}


def sciplex3_setting(tier) -> Setting:
    return Setting("sciplex3", tuple(tier.keys), SCIPLEX3_FIXED[tier.name], E.days, 16.0)


# ------------------------------------------------------------------------------ runner
def legal_menu(setting: Setting, executed: list, remaining: float) -> list:
    """Distinct, not earlier than anything executed (failed assays included), and affordable."""
    done = {tuple(step["key"]) for step in executed}
    latest = max((step["key"][1] for step in executed), default=-math.inf)
    return [key for key in setting.keys
            if key not in done and key[1] >= latest and setting.days(key) <= remaining + 1e-9]


def make_action(key, h1, h2, setting: Setting) -> EvidenceAction:
    line, t, dose = key
    return EvidenceAction(
        identifier=C.action_id(key), description=f"transcriptome, {line}, {dose:g} nM, {t:g} h",
        cost=setting.days(key), distinguishes=(h1, h2), kind=EvidenceActionKind.RNA_ABUNDANCE_MEASUREMENT,
        readout="transcriptome_shift", time_hours=t, expected_conditions={"dose_nM": f"{dose:g}"},
        execution_context=line, quantity=BiologicalQuantity.RNA_ABUNDANCE)


def run_matched(arm_name: str, arm, ctx, compound, truth, h1, h2, setting: Setting, *, qc_rule: str = "continue",
                execute=None) -> dict:
    """One episode under the shared rules; `arm` only picks from the legal menu or stops."""
    if qc_rule not in ("continue", "stop"):
        raise ValueError(qc_rule)
    execute = execute or E.execute
    actions = {key: make_action(key, h1, h2, setting) for key in setting.keys}
    contrast = E.contrast_for(h1, h2, list(actions.values()))
    state = EvidenceState.open(contrast.hypotheses)
    executed, stop = [], None
    while True:
        if state.eliminated:
            stop = "eliminated"
            break
        if len(executed) >= setting.max_measurements:
            stop = "measurement_budget_spent"
            break
        if executed and not executed[-1]["qc"] and qc_rule == "stop":
            stop = "qc_failure_stop_rule"
            break
        remaining = setting.budget_days - sum(setting.days(tuple(step["key"])) for step in executed)
        menu = legal_menu(setting, executed, remaining)
        if not menu:
            stop = "no_legal_action"
            break
        key, note = arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state)
        if key is None:
            stop = note.get("reason") or "arm_stopped"
            break
        if key not in menu:
            raise ValueError(f"{arm_name} chose {key}, which is not in the legal menu")
        result = execute(ctx, compound, key, h1, h2)
        state, interpretation, outcome = C.evidence_update(
            state, contrast, actions[key], key, result, h1, h2, qc=result["qc"], agreement=result["agreement"],
            source=f"{setting.name}:{compound}")
        executed.append({"key": list(key), "action": C.action_id(key), "outcome": outcome, "qc": result["qc"],
                         "outcome_class": interpretation.outcome_class.value, "eliminated": sorted(state.eliminated),
                         "note": note})
    return finish(arm_name, compound, truth, h1, h2, state, executed, stop, setting, qc_rule)


def finish(arm_name, compound, truth, h1, h2, state, executed, stop, setting: Setting, qc_rule: str) -> dict:
    other = h2 if truth == h1 else h1
    remaining = state.candidates
    if not executed:
        final = "deferred"
    elif remaining == frozenset({truth}):
        final = "correct"
    elif remaining == frozenset({other}):
        final = "wrong"
    elif not remaining:
        final = "exhausted"
    else:
        final = "undetermined"
    utility = {"correct": 1, "wrong": -2, "exhausted": -2}.get(final, 0)
    return {"policy": arm_name, "qc_rule": qc_rule, "compound": compound, "truth": truth, "h1": h1, "h2": h2,
            "final": final, "utility": utility, "stop": stop, "measurements": len(executed),
            "days": sum(setting.days(tuple(step["key"])) for step in executed), "steps": executed}


def audit_record(record: dict, setting: Setting) -> list[str]:
    """Violations of the shared rules in one recorded episode; empty when it is behaviour-matched."""
    problems = []
    steps = record["steps"]
    if len(steps) > setting.max_measurements:
        problems.append("too_many_measurements")
    if sum(setting.days(tuple(s["key"])) for s in steps) > setting.budget_days + 1e-9:
        problems.append("over_budget")
    times = [s["key"][1] for s in steps]
    if times != sorted(times):
        problems.append("time_order")
    if len({s["action"] for s in steps}) != len(steps):
        problems.append("repeated_action")
    for i, s in enumerate(steps[:-1]):
        if s["eliminated"]:
            problems.append("continued_after_elimination")
        if not s["qc"] and record["qc_rule"] == "stop":
            problems.append("continued_after_qc_failure_under_stop_rule")
    if any(not s["qc"] and s["eliminated"] != (steps[i - 1]["eliminated"] if i else []) for i, s in enumerate(steps)):
        problems.append("qc_failure_changed_evidence")
    if record["qc_rule"] == "continue" and steps and not steps[-1]["qc"] and record["stop"] == "qc_failure_stop_rule":
        problems.append("stopped_by_harness_after_qc_failure_under_continue_rule")
    return problems


# ------------------------------------------------------------------------------ planning
def raw_probabilities(forecast, hypothesis):
    """Reference frequencies without the planner's Jeffreys shrinkage (diagnosis only)."""
    branch = forecast.branch_for(hypothesis)
    return {label: branch.probabilities.get(label, 0.0) for label in LABELS}


def plan_contingent(menu, h1, h2, forecasts, conditional, *, days, budget, horizon=2, probabilities=S.probabilities):
    """`two_step.plan_two_step` with `days` passed in; arithmetic kept in the same order."""
    choices = []
    for first in menu:
        forecast = forecasts[C.action_id(first)]
        if forecast.refusal or days(first) > budget:
            continue
        p = {h: probabilities(forecast, h) for h in (h1, h2)}
        correct = 0.5 * (p[h1][LABELS[0]] + p[h2][LABELS[1]])
        wrong = 0.5 * (p[h1][LABELS[1]] + p[h2][LABELS[0]])
        immediate_utility = correct - 2 * wrong
        expected_days = days(first)
        followups, refusals = {}, {}
        if horizon in (1, 2):
            for label in (V.UNRESOLVED, V.ABSENT):
                tails = []
                for second in menu:
                    if second == first or second[1] < first[1] or days(first) + days(second) > budget:
                        continue
                    next_forecast = conditional(first, label, second)
                    if next_forecast.refusal:
                        refusals[f"{label}:{C.action_id(second)}"] = next_forecast.refusal
                        continue
                    q = {h: probabilities(next_forecast, h) for h in (h1, h2)}
                    c = 0.5 * (p[h1][label] * q[h1][LABELS[0]] + p[h2][label] * q[h2][LABELS[1]])
                    w = 0.5 * (p[h1][label] * q[h1][LABELS[1]] + p[h2][label] * q[h2][LABELS[0]])
                    if c > 2 * w + 1e-12:
                        tails.append((c - 2 * w, days(second), C.action_id(second), second, c, w))
                if tails:
                    tail = min(tails, key=lambda x: (-x[0], x[1], x[2]))
                    followups[label] = tail[3]
                    correct += tail[4]
                    wrong += tail[5]
                    expected_days += 0.5 * (p[h1][label] + p[h2][label]) * tail[1]
        utility = correct - 2 * wrong
        selection_utility = utility if horizon == 2 else immediate_utility
        if selection_utility > 1e-12:
            choices.append({"first": first, "followups": followups, "p_correct": correct,
                            "p_wrong": wrong, "utility": utility, "expected_days": expected_days,
                            "selection_utility": selection_utility, "immediate_utility": immediate_utility,
                            "conditional_refusals": refusals})
    return min(choices, key=lambda x: (-x["selection_utility"], x["expected_days"], C.action_id(x["first"]))) if choices else None


def continuation_audit(menu, first, h1, h2, forecasts, conditional, *, days, budget):
    """Every candidate second measurement after each neutral first reading, as the planner valued it."""
    initial = forecasts[C.action_id(first)]
    # A first measurement bought without a forecast (the fallback) cannot weight any branch.
    p = None if initial.refusal else {h: S.probabilities(initial, h) for h in (h1, h2)}
    pr = None if initial.refusal else {h: raw_probabilities(initial, h) for h in (h1, h2)}
    good = {h1: LABELS[0], h2: LABELS[1]}
    bad = {h1: LABELS[1], h2: LABELS[0]}
    audit = {}
    for label in (V.UNRESOLVED, V.ABSENT):
        rows = []
        for second in menu:
            if second == first:
                continue
            row = {"action": C.action_id(second), "time": second[1]}
            if second[1] < first[1]:
                rows.append({**row, "status": "time_order"})
                continue
            if days(first) + days(second) > budget:
                rows.append({**row, "status": "budget"})
                continue
            if p is None:
                rows.append({**row, "status": "refused", "refusal": f"first_condition_not_forecast:{initial.refusal}"})
                continue
            forecast = conditional(first, label, second)
            if forecast.refusal:
                rows.append({**row, "status": "refused", "refusal": forecast.refusal})
                continue
            q = {h: S.probabilities(forecast, h) for h in (h1, h2)}
            qr = {h: raw_probabilities(forecast, h) for h in (h1, h2)}
            c = 0.5 * sum(p[h][label] * q[h][good[h]] for h in (h1, h2))
            w = 0.5 * sum(p[h][label] * q[h][bad[h]] for h in (h1, h2))
            c_raw = 0.5 * sum(pr[h][label] * qr[h][good[h]] for h in (h1, h2))
            w_raw = 0.5 * sum(pr[h][label] * qr[h][bad[h]] for h in (h1, h2))
            rows.append({**row, "status": "valued", "c": c, "w": w, "positive": c > 2 * w + 1e-12,
                         "c_raw": c_raw, "w_raw": w_raw,
                         "support": [forecast.branch_for(h).support for h in (h1, h2)]})
        audit[label] = rows
    return audit


def stop_reason(rows) -> str:
    """One reason per missed continuation; first match in the documented hierarchy."""
    legal = [r for r in rows if r["status"] != "time_order"]
    if not legal:
        return "time_order_or_action_legality"
    affordable = [r for r in legal if r["status"] != "budget"]
    if not affordable:
        return "insufficient_budget"
    valued = [r for r in affordable if r["status"] == "valued"]
    if not valued:
        return "no_paired_references"
    if any(r["positive"] for r in valued):
        return "implementation_defect"
    if any(r["c_raw"] > 2 * r["w_raw"] + 1e-12 for r in valued):
        return "inadequate_support_or_uncertainty"
    if any(r["c_raw"] > 0 for r in valued):
        return "wrong_elimination_risk"
    return "predicted_non_positive_continuation_utility"


def no_plan_reason(menu, h1, h2, forecasts, conditional, *, days, budget, horizon) -> str:
    """Why the planner found no action worth buying: absent references, thin ones, or an informed no."""
    served = [k for k in menu if not forecasts[C.action_id(k)].refusal and days(k) <= budget]
    if not served:
        return "no_references"
    if plan_contingent(menu, h1, h2, forecasts, conditional, days=days, budget=budget, horizon=horizon,
                       probabilities=raw_probabilities) is not None:
        return "inadequate_support_or_uncertainty"
    for k in served:
        p = {h: raw_probabilities(forecasts[C.action_id(k)], h) for h in (h1, h2)}
        if p[h1][LABELS[0]] + p[h2][LABELS[1]] > 0:
            return "wrong_elimination_risk"
    return "predicted_non_positive_utility"


# ------------------------------------------------------------------------------ arms
def _forecasts(ctx, h1, h2, keys, *, permuted=False):
    forecaster = V.ReferenceCardForecaster(ctx.ft_perm if permuted else ctx.ft, ctx.params)
    return {C.action_id(k): forecaster.forecast_key(k, h1, h2) for k in keys}


def _conditional(ctx, h1, h2, *, permuted=False):
    ft = ctx.ft_perm if permuted else ctx.ft
    return lambda a, y, b: S.conditional_forecast(ft, ctx.params, a, y, b, h1, h2)


def fixed(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
    key = next((k for k in setting.fixed_order if k in menu), None)
    return key, ({} if key else {"reason": "fixed_sequence_exhausted"})


def production(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
    """The power-aware expected-coverage selector as production runs it: no world-model input."""
    actions = [make_action(k, h1, h2, setting) for k in menu]
    plan = select_expected_coverage(frozenset({h1, h2}), actions, E.PROFILE, min(remaining, setting.step_budget))
    if not plan.plan.actions:
        return None, {"reason": f"production_{plan.status}"}
    chosen = plan.plan.actions[0].identifier
    return next(k for k in menu if C.action_id(k) == chosen), {}


def magnitude(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
    """The non-default budgeted path with the served rung's magnitude priority (SciPlex3 only)."""
    actions = [make_action(k, h1, h2, setting) for k in menu]
    priorities = V.magnitude_priorities(ctx, compound, menu)
    plan = BudgetedEvidenceSelector().select(frozenset({h1, h2}), actions, E.PROFILE,
                                             min(remaining, setting.step_budget), action_priorities=priorities)
    if not plan.actions:
        return None, {"reason": "selector_returned_empty"}
    chosen = plan.actions[0].identifier
    return next(k for k in menu if C.action_id(k) == chosen), {}


def discrimination(ctx, compound, h1, h2, executed, menu, remaining, setting, state, *, conditioned=True):
    """`select_discriminating_action` fed the SciPlex3-style reference forecaster.

    With ``conditioned`` the forecaster reads the evidence state the way the runtime now does
    (the latest valid neutral result narrows the references); without it every step uses the
    unconditioned forecasts, as the follow-up's `da` arm did.
    """
    forecaster = V.ReferenceCardForecaster(ctx.ft, ctx.params, minimum_references=1)
    actions = [make_action(k, h1, h2, setting) for k in menu]
    if conditioned:
        contrast = E.contrast_for(h1, h2, actions)
        forecasts = forecaster.forecast(contrast, actions, state)
    else:
        forecasts = {C.action_id(k): forecaster.forecast_key(k, h1, h2) for k in menu}
    priorities = V.magnitude_priorities(ctx, compound, menu) if ctx.magnitude is not None else None
    plan = select_discriminating_action(frozenset({h1, h2}), actions, E.PROFILE, min(remaining, setting.step_budget),
                                        forecasts, outcome_consequences(V.registered_rules(h1, h2)),
                                        action_priorities=priorities)
    if plan.chosen is None:
        return None, {"reason": f"acquisition_{plan.status}"}
    return next(k for k in menu if C.action_id(k) == plan.chosen.action_identifier), {}


def _plan(ctx, h1, h2, setting, *, horizon, permuted):
    cache = ctx.extra.setdefault("sequence_audit_plans", {})
    key = (h1, h2, horizon, permuted)
    if key not in cache:
        forecasts = _forecasts(ctx, h1, h2, setting.keys, permuted=permuted)
        conditional = _conditional(ctx, h1, h2, permuted=permuted)
        plan = plan_contingent(setting.keys, h1, h2, forecasts, conditional, days=setting.days,
                               budget=setting.budget_days, horizon=horizon)
        cache[key] = (plan, forecasts, conditional)
    return cache[key]


def contingent(ctx, compound, h1, h2, executed, menu, remaining, setting, state, *, horizon=2, permuted=False,
               fallback=False, replan_after_fallback=True):
    """The follow-up's contingent planner under the shared rules, optionally with the revision.

    Step 1 follows the plan. After a neutral real result it takes the plan's continuation for that
    reading. After a QC failure it values one remaining measurement from unconditioned forecasts.
    With ``fallback`` an uninformed stop becomes the fixed sequence's next legal action.
    A first action supplied by that fallback has no cached continuation, so its real neutral
    result triggers a fresh continuation comparison. Disabling this repair is for frozen replay.
    """
    plan, forecasts, conditional = _plan(ctx, h1, h2, setting, horizon=horizon, permuted=permuted)
    if not executed:
        if plan is not None:
            return plan["first"], {"planned_followups": {y: C.action_id(k) for y, k in plan["followups"].items()}}
        reason = no_plan_reason(setting.keys, h1, h2, forecasts, conditional, days=setting.days,
                                budget=setting.budget_days, horizon=horizon)
        return _fallback_or_stop(fallback, reason, menu, setting, "no_positive_terminal_utility")
    last = executed[-1]
    if not last["qc"]:
        single = plan_contingent(menu, h1, h2, forecasts, conditional, days=setting.days, budget=remaining, horizon=1)
        if single is not None:
            return single["first"], {"after": "qc_failure"}
        reason = no_plan_reason(menu, h1, h2, forecasts, conditional, days=setting.days, budget=remaining, horizon=1)
        return _fallback_or_stop(fallback, reason, menu, setting, "no_positive_single_measurement_after_qc_failure")
    label = NEUTRAL.get(last["outcome"])
    first = tuple(executed[0]["key"])
    follows_plan = plan is not None and tuple(plan["first"]) == first
    chosen = (plan or {}).get("followups", {}).get(label) if follows_plan else None
    if chosen in menu:
        return chosen, {"after": label}
    if replan_after_fallback and not follows_plan:
        rows = continuation_audit(menu, first, h1, h2, forecasts, conditional, days=setting.days,
                                  budget=setting.days(first) + remaining)[label]
        positive = [row for row in rows if row["status"] == "valued" and row["positive"]]
        if positive:
            keys = {C.action_id(key): key for key in menu}
            best = min(positive, key=lambda row: (-(row["c"] - 2 * row["w"]),
                                                   setting.days(keys[row["action"]]), row["action"]))
            return keys[best["action"]], {"after": label, "replanned_from": C.action_id(first)}
        return _fallback_or_stop(fallback, stop_reason(rows), menu, setting,
                                 "no_supported_positive_utility_continuation")
    rows = continuation_audit(setting.keys, first, h1, h2, forecasts, conditional, days=setting.days,
                              budget=setting.budget_days)[label]
    return _fallback_or_stop(fallback, stop_reason(rows), menu, setting,
                             "no_supported_positive_utility_continuation")


def _fallback_or_stop(fallback, reason, menu, setting, stop_name):
    if fallback and reason in UNINFORMED:
        key = next((k for k in setting.fixed_order if k in menu), None)
        if key is not None:
            return key, {"fallback": "fixed_sequence", "planner_refusal": reason}
    return None, {"reason": f"{stop_name}:{reason}"}


def arms(setting_name: str, *, frozen_replay=False) -> dict:
    table = {
        "production": production,
        "da": discrimination,
        "da_unconditioned": lambda *a: discrimination(*a, conditioned=False),
        "fixed": fixed,
        "one_step_utility": lambda *a: contingent(*a, horizon=1),
        "two_step": contingent,
        "two_step_permuted": lambda *a: contingent(*a, permuted=True),
        "two_step_fallback": lambda *a: contingent(*a, fallback=True, replan_after_fallback=not frozen_replay),
    }
    if setting_name == "sciplex3":
        table["magnitude"] = magnitude
    return table
