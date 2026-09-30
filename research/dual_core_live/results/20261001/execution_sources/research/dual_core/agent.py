"""Dual-core agent: a belief planner reading purchased prompts, and a switchable risk-abstention policy.

File summary
- Path: research/dual_core/agent.py
- Purpose: the opt-in research agent of the dual-core iteration. It plugs into the protocol-v2.1
  runner (`research/protocol_v2/runner.run_episode`) through two things:
  - an executor that also records every purchase in the episode's `PurchaseLedger`;
  - arms.
- Core points:
  - One executor. `LedgerExecutor` wraps the registered executor (`episodes.execute`) and records each
    result in the ledger of (compound, h1, h2). Arms never touch the real context. They see the
    runner's public steps and, through the ledger, only prompts for steps already executed.
  - `incontext_arm` is the belief-expectimax planner of block 2 (same planner, legality, price and
    notes) with `world2.StrictInContextWorld`. Real steps condition on their purchased prompts. In the
    lookahead, hypothetical steps have labels only: a predicted future profile is never treated as
    acquired, and the horizon is the runner's remaining measurements.
  - Predictions stay predictions. Forecasts carry `EvidenceKind.MODEL_PREDICTION`. Only the runner's
    `evidence_update`, on a real executor result, can eliminate a hypothesis.
  - The risk forecast of a chosen action is recorded for both arms:
        r = sum over h of belief(h) x P(reading matches the other hypothesis | h)
    It is the agent's own probability that this purchase will eliminate the true hypothesis.
  - `abstaining(arm, threshold)` is the independently switchable decision-policy change. When the
    chosen action's risk exceeds the threshold, the agent stops and abstains (`risk_abstain`)
    instead of buying. Because abstention only truncates a trajectory, a threshold's effect can be
    evaluated exactly from one unconstrained run (`truncate`). A test checks this equality against
    live runs.
- Interfaces: `LedgerExecutor`, `incontext_arm`, `abstaining`, `risk_of`, `truncate`
- Depends on: ledger.py, world2.py, research/belief_planning (planner, arms, world), research/protocol_v2
"""
from __future__ import annotations

import numpy as np

from maestro.acquisition import outcome_consequences
from research.belief_planning import arms as BA
from research.belief_planning import world as W
from research.belief_planning.planner import plan_measurement, update_belief

from . import world2 as W2
from .ledger import PurchaseLedger

P, C, E, V = BA.P, BA.C, BA.E, BA.V


class LedgerExecutor:
    """The registered executor plus a ledger per episode; the only place a real result is produced."""

    def __init__(self, real_ctx, *, dataset: str, assay: str, quality, batch, detected, cost_days, execute=None):
        self.real_ctx = real_ctx
        self.execute_fn = execute or E.execute
        self.args = dict(dataset=dataset, assay=assay, conditions=real_ctx.data.conditions, shift=real_ctx.data.shift,
                         quality=quality, detected=detected, batch=batch, cost_days=cost_days)
        self.ledgers: dict = {}

    def open(self, compound, h1, h2) -> PurchaseLedger:
        ledger = PurchaseLedger(compound, **self.args)
        self.ledgers[(compound, h1, h2)] = ledger
        return ledger

    def __call__(self, ctx, compound, key, h1, h2):
        result = self.execute_fn(ctx, compound, key, h1, h2)
        self.ledgers[(compound, h1, h2)].record(key, result)
        return result


def risk_of(belief: dict, forecast) -> float:
    """The agent's probability that the chosen purchase eliminates the true hypothesis."""
    h1, h2 = forecast.branches[0].hypothesis, forecast.branches[1].hypothesis
    wrong = {h1: forecast.branch_for(h1).probabilities.get(W.MATCH_H2, 0.0),
             h2: forecast.branch_for(h2).probabilities.get(W.MATCH_H1, 0.0)}
    return float(sum(belief[h] * wrong[h] for h in belief))


def incontext_arm(executor: LedgerExecutor, worlds: dict, *, price: float = BA.PRICE):
    """Belief planner with the strict in-context world; `worlds[id(view)]` is the fold's world model."""

    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        if not ctx.params.get("eliminates"):
            return BA._stop("registered_validator_cannot_eliminate")
        world = worlds[id(ctx)]
        ledger = executor.ledgers[(compound, h1, h2)]
        real = tuple((tuple(s["key"]), W.label_of(s["outcome"])) for s in executed)
        belief = {h1: 0.5, h2: 0.5}
        for i, (key, label) in enumerate(real):
            prompts = ledger.prompts(target=key, executed=executed[:i])
            belief = update_belief(belief, world.forecast(key, h1, h2, compound, real[:i], profiles=prompts), label)
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
            # only purchased prompts: hypothetical lookahead steps condition through labels alone
            return world.forecast(target, h1, h2, compound, real + tuple((by_id[a], lab) for a, lab in hyp),
                                  profiles=ledger.prompts(target=target, executed=executed))

        consequences = outcome_consequences(V.registered_rules(h1, h2))
        plan = plan_measurement((h1, h2), belief, legal, forecast, consequences,
                                horizon=setting.max_measurements - len(executed), price=price)
        note = {"evidence_kind": "model_prediction", "planner": "belief_expectimax", "world": world.incontext.get("source"),
                "belief": {h: round(p, 6) for h, p in belief.items()}, "history_labels": [lab for _, lab in real],
                "prompts": [p.provenance() for p in ledger.prompts(target=("", -1.0, -1.0), executed=executed).values()]}
        if plan.chosen is None:
            return BA._stop(f"belief_{plan.reason}", **note, refusals=dict(plan.refusals))
        key = by_id[plan.chosen]
        chosen = forecast(P.make_action(key, h1, h2, setting), ())
        note.update({"expected_utility": plan.value.utility, "p_correct_plan": plan.value.p_correct,
                     "p_wrong_plan": plan.value.p_wrong, "basis": chosen.basis, "model_version": chosen.model_version,
                     "risk_forecast": risk_of(belief, chosen),
                     "prediction_by_hypothesis": {
                         b.hypothesis: {"probabilities": dict(b.probabilities), "support": b.support,
                                        "p_correct": b.probabilities.get(W.MATCH_H1 if b.hypothesis == h1 else W.MATCH_H2, 0.0),
                                        "p_wrong": b.probabilities.get(W.MATCH_H2 if b.hypothesis == h1 else W.MATCH_H1, 0.0)}
                         for b in chosen.branches}})
        return key, note

    return arm


def note_risk(note: dict) -> float | None:
    """The risk forecast of a step's chosen action, from either arm's notes."""
    if note is None:
        return None
    if "risk_forecast" in note:
        return float(note["risk_forecast"])
    belief, pred = note.get("belief"), note.get("prediction_by_hypothesis")
    if not belief or not pred:
        return None
    return float(sum(belief[h] * pred[h]["p_wrong"] for h in belief if h in pred))


def abstaining(arm, threshold: float):
    """Wrap an arm: abstain (stop) when the chosen action's risk forecast exceeds `threshold`."""

    def wrapped(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        key, note = arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state)
        if key is None:
            return key, note
        risk = note_risk(note)
        if risk is not None and risk > threshold:
            return None, {**note, "reason": "risk_abstain", "risk_threshold": threshold}
        return key, {**note, "risk_threshold": threshold}

    return wrapped


def truncate(trace: dict, truth: str, threshold: float, calibrate=lambda r: r) -> dict:
    """Outcome of `abstaining(arm, threshold)` computed from the unconstrained trace of `arm`.

    Steps run while the (optionally calibrated) risk of each chosen action is at most the threshold.
    The first step above it is not bought, and the episode ends there, abstained.
    """
    steps = trace["steps"]
    kept = []
    abstained = False
    for step in steps:
        risk = note_risk(step.get("note"))
        if risk is not None and calibrate(risk) > threshold:
            abstained = True
            break
        kept.append(step)
    eliminated = set(kept[-1]["eliminated"]) if kept else set()
    decided = bool(eliminated)
    wrong = truth in eliminated
    return {"decided": decided, "wrong": wrong, "correct": decided and not wrong, "abstained": abstained,
            "measurements": len(kept), "keys": [tuple(s["key"]) for s in kept]}
