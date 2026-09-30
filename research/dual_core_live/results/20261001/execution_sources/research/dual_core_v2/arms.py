"""Planner arms for the dual-core v2 comparison: one belief planner, three world models, three risk policies.

File summary
- Path: research/dual_core_v2/arms.py
- Purpose: arms for `research/protocol_v2/runner.run_episode`. Every arm uses the same planner
  (`research/belief_planning/planner.plan_measurement`), legality, price, executor and ledger;
  only the world model and the risk policy differ.
- Core points:
  - World models: `reference` (block 2's reference world, no prompts), `v1` (block 7's in-context
    world, reproduced as a restriction of `world3.WorldV2`) and `v2` (training-selected sources).
  - Three risks, kept apart and all recorded before a purchase:
    - `risk_step`: P(the next measurement eliminates the true hypothesis), block 7's risk;
    - `p_wrong_plan`: P(some wrong elimination during the rest of the episode under the chosen plan);
    - `p_wrong_upper_plan`: its conservative version (each wrong-eliminating reading raised to the
      Jeffreys 95% upper bound of its reference support).
    None of them is the evaluation target, P(wrong | decided); they are ranking devices that the
    policies threshold.
  - Policies:
    - P0: the planner as is;
    - stop-only: stop when the chosen action's risk exceeds a threshold. It is computed exactly by
      truncating P0 traces (`truncate_by`), for either risk;
    - risk-select: the planner's existing `wrong_risk_cap` (a Lagrangian scan that raises the wrong
      loss until the plan's conservative wrong probability is within the cap, otherwise stops).
      This compares safer alternative actions before stopping; nothing new is written for it.
      `cap_measure="point"` caps the point estimate instead by giving every branch a very large
      support, so the planner's upper bound collapses to the point value.
  - Predictions stay predictions. Notes carry `evidence_kind: model_prediction`; only the runner's
    `evidence_update` on a real executor result changes the evidence state.
- Interfaces: `ReferenceAdapter`, `LedgerExecutorV2`, `planner_arm`, `truncate_by`, `POINT_SUPPORT`
- Depends on: world3.py, research/dual_core (agent, ledger), research/belief_planning (planner, arms, world)
"""
from __future__ import annotations

from maestro.acquisition import OutcomeBranch, OutcomeForecast, outcome_consequences
from research.belief_planning import arms as BA
from research.belief_planning import world as W
from research.belief_planning.planner import plan_measurement, update_belief
from research.dual_core import agent as AG

from .world3 import LedgerV2

P, C, V = BA.P, BA.C, BA.V
POINT_SUPPORT = 10 ** 7


class ReferenceAdapter:
    """The reference world behind the v2 forecast signature; prompts are ignored by construction."""

    def __init__(self, world):
        self.world = world
        self.incontext = {"source": "reference", "kappa": 0.0, "tau": 0.0}

    def forecast(self, key, h1, h2, compound, history=(), prompts=None):
        return self.world.forecast(tuple(key), h1, h2, compound, history)


class LedgerExecutorV2(AG.LedgerExecutor):
    def open(self, compound, h1, h2) -> LedgerV2:
        ledger = LedgerV2(compound, **self.args)
        self.ledgers[(compound, h1, h2)] = ledger
        return ledger


def _point(forecast: OutcomeForecast) -> OutcomeForecast:
    if forecast.refusal:
        return forecast
    branches = tuple(OutcomeBranch(b.hypothesis, b.probabilities, POINT_SUPPORT) for b in forecast.branches)
    return OutcomeForecast(forecast.action_identifier, branches, basis=forecast.basis + "|point_support",
                           model_version=forecast.model_version)


def planner_arm(executor, worlds: dict, variant: str, *, cap: float | None = None, cap_measure: str = "upper",
                price: float = BA.PRICE):
    """`worlds[id(view)][variant]` is the world model; `cap` switches on risk-select."""
    if cap_measure not in ("upper", "point"):
        raise ValueError(cap_measure)

    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        if not ctx.params.get("eliminates"):
            return BA._stop("registered_validator_cannot_eliminate")
        world = worlds[id(ctx)][variant]
        ledger = executor.ledgers[(compound, h1, h2)]
        real = tuple((tuple(s["key"]), W.label_of(s["outcome"])) for s in executed)
        belief = {h1: 0.5, h2: 0.5}
        for i, (key, label) in enumerate(real):
            prompts = ledger.prompt_set(target=key, executed=executed[:i])
            belief = update_belief(belief, world.forecast(key, h1, h2, compound, real[:i], prompts=prompts), label)
        by_id = {C.action_id(k): k for k in setting.keys}
        done = [tuple(s["key"]) for s in executed]

        def legal(hyp):
            keys = done + [by_id[a] for a, _ in hyp]
            if len(keys) >= setting.max_measurements:
                return ()
            left = setting.budget_days - sum(setting.days(k) for k in keys)
            steps = [{"key": list(k)} for k in keys]
            return tuple(P.make_action(k, h1, h2, setting) for k in P.legal_menu(setting, steps, left))

        if [a.identifier for a in legal(())] != [C.action_id(k) for k in menu]:
            raise AssertionError("planner legality differs from the runner's menu")

        def forecast(action, hyp):
            target = by_id[action.identifier]
            out = world.forecast(target, h1, h2, compound, real + tuple((by_id[a], lab) for a, lab in hyp),
                                 prompts=ledger.prompt_set(target=target, executed=executed))
            return _point(out) if (cap is not None and cap_measure == "point") else out

        consequences = outcome_consequences(V.registered_rules(h1, h2))
        plan = plan_measurement((h1, h2), belief, legal, forecast, consequences,
                                horizon=setting.max_measurements - len(executed), price=price, wrong_risk_cap=cap)
        note = {"evidence_kind": "model_prediction", "planner": "belief_expectimax", "world": variant,
                "world_source": world.incontext.get("source"), "cap": cap, "cap_measure": cap_measure,
                "belief": {h: round(p, 6) for h, p in belief.items()}, "history_labels": [lab for _, lab in real],
                "prompts": len(ledger.prompts(target=("", -1.0, -1.0), executed=executed)),
                "wrong_loss_used": plan.wrong_loss_used}
        if plan.chosen is None:
            return BA._stop(f"belief_{plan.reason}", **note, refusals=dict(plan.refusals))
        key = by_id[plan.chosen]
        chosen = world.forecast(key, h1, h2, compound, real, prompts=ledger.prompt_set(target=key, executed=executed))
        note.update({"expected_utility": plan.value.utility, "p_correct_plan": plan.value.p_correct,
                     "p_wrong_plan": plan.value.p_wrong, "p_wrong_upper_plan": plan.value.p_wrong_upper,
                     "risk_forecast": AG.risk_of(belief, chosen), "basis": chosen.basis,
                     "prediction_by_hypothesis": {
                         b.hypothesis: {"probabilities": dict(b.probabilities), "support": b.support,
                                        "p_wrong": b.probabilities.get(W.MATCH_H2 if b.hypothesis == h1 else W.MATCH_H1, 0.0)}
                         for b in chosen.branches}})
        return key, note

    return arm


RISK_FIELDS = {"step": "risk_forecast", "plan": "p_wrong_plan", "plan_upper": "p_wrong_upper_plan"}


def truncate_by(trace: dict, truth: str, threshold: float, measure: str = "step") -> dict:
    """Stop-only outcome at `threshold` on the risk `measure`, computed exactly from an unconstrained trace."""
    field = RISK_FIELDS[measure]
    kept, abstained = [], False
    for step in trace["steps"]:
        risk = (step.get("note") or {}).get(field)
        if risk is not None and float(risk) > threshold:
            abstained = True
            break
        kept.append(step)
    eliminated = set(kept[-1]["eliminated"]) if kept else set()
    decided = bool(eliminated)
    wrong = truth in eliminated
    return {"decided": decided, "wrong": wrong, "correct": decided and not wrong, "abstained": abstained,
            "measurements": len(kept), "keys": [tuple(s["key"]) for s in kept]}
