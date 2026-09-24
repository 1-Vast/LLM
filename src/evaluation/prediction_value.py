"""What a revocable virtual-cell prediction is worth inside the contingent grammar.

File summary
- Path: src/evaluation/prediction_value.py
- Purpose: price the secondary core honestly. A prediction is a planning input that changes which evidence plan looks affordable; this module measures the decision value of that change, the harm when the prediction is wrong, and what the framework's refusal and revocation rules recover.
- Core points:
  - The planner and the truth are separate problems, which is exactly the difference
    ``evaluate_policy(..., truth=...)`` exists to measure. A prediction never edits the
    evidence problem: only the declared branch parameter the planner reads.
  - Value is conditional on a plan change. Where the prediction does not move the chosen
    plan its value is exactly zero, and the module reports that instead of claiming credit.
  - Two contract rules are priced rather than asserted: refusing a prediction whose
    interval claims no coverage, and revoking a predictor whose intervals keep missing.
  - Every number is a statement about a declared finite model. The real checkpoint's
    measured limits live in the mechanism and real-path records, not here.
- Interfaces: `ContextPrediction`, `branch_family`, `with_predicted_qualification`,
  `prediction_influence`, `plan_signature`, `arm_rows`, `contract_effect`,
  `revocation_trace`, `main`
- Depends on: evaluation.adaptive_reference, maestro.reliability
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from maestro.reliability import PredictionReliabilityLedger

from .adaptive_reference import (
    DEFER,
    AdaptiveAction,
    DecisionProblem,
    evaluate_policy,
    optimal_policy,
    policy_tree,
    solve_optimal_policy,
)

HYPOTHESES = ("realised", "not_realised")
LOSS = {
    "continue": {"realised": 0.0, "not_realised": 10.0},
    "revise_intervention": {"realised": 10.0, "not_realised": 0.0},
    DEFER: {"realised": 4.0, "not_realised": 4.0},
}
DECISIONS = ("continue", "revise_intervention", DEFER)
CHEAP = "cheap_supplier"
RELIABLE = "reliable_supplier"
READOUT = "gated_readout"
PREMISE = "premise"


@dataclass(frozen=True)
class ContextPrediction:
    """A model's claim about one branch parameter of the current context.

    ``qualification`` is the claimed chance that the cheap supplier of the premise
    returns a qualified result here. ``interval`` is a coverage-claiming band when the
    model has one; a prediction without one may still inform a plan, but the contract
    is allowed to refuse it, and `contract_effect` measures what that refusal costs.
    """

    context_identifier: str
    qualification: float | None
    interval: tuple[float, float] | None = None
    basis: str = "declared"
    applicable: bool = True
    abstain_reason: str | None = None
    model_version: str = "unversioned_model"

    @property
    def claims_coverage(self) -> bool:
        return self.interval is not None

    def usable(self, *, require_coverage: bool) -> bool:
        """Whether this prediction may change the plan under the declared refusal rule."""

        if not self.applicable or self.qualification is None:
            return False
        if require_coverage and not self.claims_coverage:
            return False
        return True


def branch_family(
    *,
    identifier: str,
    qualification: float,
    cheap_cost: float = 1.0,
    reliable_cost: float = 2.0,
    readout_cost: float = 1.5,
    budget: float = 4.0,
    prior: Mapping[str, float] | None = None,
) -> DecisionProblem:
    """One premise, a fragile supplier and a reliable one, and a budget that binds.

    ``qualification`` is the context parameter: the chance the cheap supplier returns a
    qualified result. Both suppliers discharge the same premise; the readout cannot run
    without it. The reliable supplier is affordable together with the readout, but the
    cheap supplier's failure leaves too little budget to recover, so which supplier is
    right depends on this one number and on nothing else.
    """

    if not 0.0 <= qualification <= 1.0:
        raise ValueError("qualification must lie in [0, 1].")
    cheap = AdaptiveAction(
        identifier=CHEAP,
        cost=cheap_cost,
        role="premise_supplier",
        outcome_model={
            h: {"qualified": qualification, "failed": 1.0 - qualification} for h in HYPOTHESES
        },
        supplies={"qualified": (PREMISE,), "failed": ()},
    )
    reliable = AdaptiveAction(
        identifier=RELIABLE,
        cost=reliable_cost,
        role="premise_supplier",
        outcome_model={h: {"qualified": 1.0} for h in HYPOTHESES},
        supplies={"qualified": (PREMISE,), "failed": ()},
    )
    readout = AdaptiveAction(
        identifier=READOUT,
        cost=readout_cost,
        prerequisites=(PREMISE,),
        outcome_model={"realised": {"high": 1.0}, "not_realised": {"low": 1.0}},
        supplies={"high": ("phenotype:discordant",), "low": ("phenotype:concordant",)},
    )
    return DecisionProblem(
        identifier=identifier,
        hypotheses=HYPOTHESES,
        prior=dict(prior or {h: 0.5 for h in HYPOTHESES}),
        actions=(cheap, reliable, readout),
        budget=budget,
        decisions=DECISIONS,
        loss=LOSS,
        family="prediction prices the branch",
        note=(
            "Several suppliers of one premise; the budget binds only after the fragile "
            "supplier has been bought, so which supplier is optimal depends on the "
            "context parameter a prediction claims to know."
        ),
    )


def with_predicted_qualification(
    problem: DecisionProblem, qualification: float, *, supplier: str = CHEAP
) -> DecisionProblem:
    """The planner's view of the same problem with one rescaled branch parameter.

    Nothing else changes: the hypotheses, the actions, the costs, the prerequisites,
    the budget, the decisions and the loss stay identical, so a difference in the plan
    can only come from the declared branch probability the prediction supplied. The
    outcome labels are preserved, and the prediction never adds an action, removes one,
    or enters the evidence problem as an observation.
    """

    if not 0.0 <= qualification <= 1.0:
        raise ValueError("qualification must lie in [0, 1].")
    rescaled: list[AdaptiveAction] = []
    for action in problem.actions:
        if action.identifier != supplier:
            rescaled.append(action)
            continue
        labels = tuple(
            dict.fromkeys(outcome for distribution in action.outcome_model.values() for outcome in distribution)
        )
        qualified_label = next(
            (label for label in labels if action.supplies.get(label, ())), labels[0]
        )
        failed_label = next((label for label in labels if label != qualified_label), "failed")
        rescaled.append(
            AdaptiveAction(
                identifier=action.identifier,
                cost=action.cost,
                outcome_model={
                    h: {qualified_label: qualification, failed_label: 1.0 - qualification}
                    for h in problem.hypotheses
                },
                prerequisites=action.prerequisites,
                supplies=action.supplies,
                role=action.role,
                source=action.source,
                interpretation_gate=action.interpretation_gate,
                uninterpretable_model=action.uninterpretable_model,
                composed_from=action.composed_from,
            )
        )
    return DecisionProblem(
        identifier=f"{problem.identifier}@{qualification:.3f}",
        hypotheses=problem.hypotheses,
        prior=problem.prior,
        actions=tuple(rescaled),
        budget=problem.budget,
        decisions=problem.decisions,
        loss=problem.loss,
        family=problem.family,
        note=problem.note,
    )


def prediction_influence(
    prediction: ContextPrediction,
    *,
    fallback: float,
    weight: float = 1.0,
    require_coverage: bool = False,
) -> float:
    """The branch parameter the planner actually reads, after refusal and revocation.

    ``weight`` is the reliability weight the ledger currently allows this model and
    readout; zero means revoked. The blend is the influence semantics the ledger's
    weight is defined against: a weaker weight moves the planner back toward the value
    it would have used with no model at all, rather than leaving it fully informed.
    """

    if not 0.0 <= weight <= 1.0:
        raise ValueError("weight must lie in [0, 1].")
    if not prediction.usable(require_coverage=require_coverage):
        return fallback
    assert prediction.qualification is not None
    return weight * prediction.qualification + (1.0 - weight) * fallback


def no_model_prediction(context_identifier: str = "context") -> ContextPrediction:
    """The no-model control: nothing is claimed, so the planner reads the fallback value.

    It is the same object an out-of-scope or abstaining model returns, so the control arm
    and a refusal are measured on one code path rather than two that could drift apart.
    """

    return ContextPrediction(
        context_identifier=context_identifier,
        qualification=None,
        interval=None,
        basis="no prediction",
        applicable=False,
        abstain_reason="no_model",
    )


def plan_signature(problem: DecisionProblem) -> Mapping[str, object]:
    """The plan an exact planner would run, in a form two views can be compared by."""

    policy = optimal_policy(problem)
    tree = policy_tree(policy, problem)
    digest = hashlib.sha256(
        json.dumps([[list(map(list, history)), list(step)] for history, step in tree]).encode("utf-8")
    ).hexdigest()
    return {
        "first_step": list(policy(problem, ())),
        "tree_digest": digest,
        "tree_size": len(tree),
        "expected_loss": round(solve_optimal_policy(problem).expected_loss, 6),
    }


def arm_rows(
    truth: DecisionProblem,
    prediction: ContextPrediction,
    *,
    fallback: float,
    weight: float = 1.0,
    require_coverage: bool = False,
) -> Mapping[str, object]:
    """One prediction arm measured against the truth, with the plan it produced.

    The planner is exact on its own view of the problem; the loss is then evaluated
    under the truth. That is the only way a claim about a prediction can be honest: the
    planner is allowed to be wrong, and the evaluator is not allowed to share its error.
    """

    used = prediction_influence(
        prediction, fallback=fallback, weight=weight, require_coverage=require_coverage
    )
    planning = with_predicted_qualification(truth, used)
    policy = optimal_policy(planning)
    realised = evaluate_policy(policy, planning, truth)
    baseline = plan_signature(with_predicted_qualification(truth, fallback))
    current = plan_signature(planning)
    return {
        "prediction_used": used,
        "prediction_refused": used == fallback,
        "plan": current,
        "plan_changed": current["tree_digest"] != baseline["tree_digest"],
        "expected_loss_under_truth": round(realised.expected_loss, 6),
        "expected_cost_under_truth": round(realised.expected_cost, 6),
        "probability_wrong_decision": round(realised.probability_wrong_decision, 6),
        "probability_defer": round(realised.probability_defer, 6),
    }


def contract_effect(
    *,
    fallback: float = 0.5,
    true_contexts: Sequence[tuple[str, float]] = (("context_a", 0.9), ("context_b", 0.3)),
) -> Mapping[str, object]:
    """What the prediction is worth, and what the refusal rule is worth, across contexts.

    Two arms are compared on the same two contexts: a predictor that is right about the
    context, and a predictor whose claim comes from the other context. Expected losses
    are averaged uniformly over the contexts, because no frequency is claimed.
    """

    rows: dict[str, dict[str, object]] = {}
    totals = {"no_model": 0.0, "informed": 0.0, "shuffled": 0.0, "refused_uncalibrated": 0.0}
    plan_changes = 0
    for name, qualification in true_contexts:
        truth = branch_family(identifier=f"truth_{name}", qualification=qualification)
        other = next(value for other_name, value in true_contexts if other_name != name)
        informed = _context_prediction(name, qualification)
        shuffled = ContextPrediction(
            context_identifier=name,
            qualification=other,
            interval=(max(0.0, other - 0.1), 1.0),
            basis="declared calibration on another context",
        )
        uncalibrated = ContextPrediction(
            context_identifier=name,
            qualification=qualification,
            interval=None,
            basis="point estimate without a coverage claim",
        )
        absent = no_model_prediction(name)
        row = {
            "true_qualification": qualification,
            "no_model": arm_rows(truth, absent, fallback=fallback)["expected_loss_under_truth"],
            "informed": arm_rows(truth, informed, fallback=fallback)["expected_loss_under_truth"],
            "shuffled": arm_rows(truth, shuffled, fallback=fallback)["expected_loss_under_truth"],
            "refused_uncalibrated": arm_rows(
                truth, uncalibrated, fallback=fallback, require_coverage=True
            )["expected_loss_under_truth"],
            "informed_plan_changed": arm_rows(truth, informed, fallback=fallback)["plan_changed"],
            "shuffled_plan_changed": arm_rows(truth, shuffled, fallback=fallback)["plan_changed"],
        }
        plan_changes += 1 if row["informed_plan_changed"] else 0
        for key in totals:
            totals[key] += float(row[key])
        rows[name] = row
    count = len(true_contexts)
    means = {key: round(value / count, 6) for key, value in totals.items()}
    return {
        "fallback_qualification": fallback,
        "contexts": rows,
        "mean_expected_loss": means,
        "value_of_a_correct_prediction": round(means["no_model"] - means["informed"], 6),
        "harm_of_a_wrong_prediction": round(means["shuffled"] - means["no_model"], 6),
        "strictness_premium": round(means["refused_uncalibrated"] - means["informed"], 6),
        "informed_plan_change_rate": round(plan_changes / count, 6),
        "reading": (
            "A prediction is worth a plan change it gets right and costs about as much when it "
            "gets that same change wrong; where the plan does not change its value is exactly "
            "zero. Refusing an uncalibrated prediction gives up the gain and removes the harm."
        ),
    }


def value_map(
    *,
    contexts: Sequence[float] = (0.1, 0.3, 0.5, 0.7, 0.9),
    fallbacks: Sequence[float] = (0.2, 0.5, 0.8),
) -> Mapping[str, object]:
    """Where a correct prediction has value, and where it has exactly none.

    The grid runs over the context parameter and over the value the planner would use
    with no model. A cell's ``value`` is the loss the correct prediction saves against
    that no-model arm, and ``harm`` is what the *other* context's claim would cost, so a
    cell where both are zero is a context in which no prediction can change the plan at
    all. Reporting the grid rather than one instance is the difference between a
    characterisation and a demonstration picked after the numbers were seen.
    """

    cells: list[dict[str, object]] = []
    for true_value in contexts:
        truth = branch_family(identifier=f"truth_{true_value:.2f}", qualification=true_value)
        for fallback in fallbacks:
            others = [value for value in contexts if value != true_value]
            wrong_claim = max(others, key=lambda value: abs(value - true_value))
            informed = arm_rows(
                truth, _context_prediction(true_value, true_value), fallback=fallback
            )
            absent = arm_rows(truth, no_model_prediction(), fallback=fallback)
            shuffled = arm_rows(
                truth, _context_prediction(true_value, wrong_claim), fallback=fallback
            )
            cells.append(
                {
                    "context": true_value,
                    "fallback": fallback,
                    "plan_changed": informed["plan_changed"],
                    "wrong_claim_plan_changed": shuffled["plan_changed"],
                    "loss_no_model": absent["expected_loss_under_truth"],
                    "loss_informed": informed["expected_loss_under_truth"],
                    "loss_wrong_claim": shuffled["expected_loss_under_truth"],
                    "value": round(
                        float(absent["expected_loss_under_truth"])
                        - float(informed["expected_loss_under_truth"]),
                        6,
                    ),
                    "harm": round(
                        float(shuffled["expected_loss_under_truth"])
                        - float(absent["expected_loss_under_truth"]),
                        6,
                    ),
                }
            )
    informative = [cell for cell in cells if cell["plan_changed"]]
    return {
        "cells": cells,
        "plan_changing_cells": len(informative),
        "total_cells": len(cells),
        "reading": (
            "Value is positive exactly in the cells where the correct claim moves the plan, and "
            "zero everywhere else, including cells where the prediction is right. That is the "
            "secondary core's scope condition in one table. A claim that does not move the plan "
            "cannot move the loss in either direction, which is why the wrong-claim column is "
            "zero in every cell it leaves alone."
        ),
    }


def _context_prediction(context_identifier: str, qualification: float) -> ContextPrediction:
    return ContextPrediction(
        context_identifier=context_identifier,
        qualification=qualification,
        interval=(max(0.0, qualification - 0.1), 1.0),
        basis="declared calibration on this context",
    )


def revocation_trace(
    *,
    true_qualification: float = 0.3,
    claimed_qualification: float = 0.9,
    fallback: float = 0.5,
    cases: int = 5,
    minimum_records: int = 3,
    revoke_after_consecutive_misses: int = 3,
) -> Mapping[str, object]:
    """A miscalibrated predictor over a sequence of cases, with and without revocation.

    The ledger is the framework's own; the trace records the weight it allows before each
    case, the branch parameter that weight implies, and the loss the resulting plan incurs
    under the truth. The no-revocation arm keeps the weight at one, which is what a
    framework that scores a predictor once and then trusts it forever would do.
    """

    ledger = PredictionReliabilityLedger(
        minimum_records=minimum_records,
        revoke_after_consecutive_misses=revoke_after_consecutive_misses,
    )
    truth = branch_family(identifier="truth_miscalibrated", qualification=true_qualification)
    policy_row = ContextPrediction(
        context_identifier="context_miscalibrated",
        qualification=claimed_qualification,
        interval=(max(0.0, claimed_qualification - 0.1), 1.0),
        basis="claimed calibration that later misses",
        model_version="miscalibrated_model",
    )
    rows: list[dict[str, object]] = []
    with_revocation = 0.0
    without_revocation = 0.0
    for index in range(1, cases + 1):
        weight = ledger.weight(policy_row.model_version, READOUT, policy_row.context_identifier)
        current = ContextPrediction(
            context_identifier=policy_row.context_identifier,
            qualification=policy_row.qualification,
            interval=policy_row.interval,
            basis=policy_row.basis,
            model_version=policy_row.model_version,
        )
        informed = arm_rows(truth, current, fallback=fallback, weight=weight)
        trust = arm_rows(truth, current, fallback=fallback, weight=1.0)
        with_revocation += float(informed["expected_loss_under_truth"])
        without_revocation += float(trust["expected_loss_under_truth"])
        rows.append(
            {
                "case": index,
                "weight_before": round(weight, 6),
                "prediction_used": informed["prediction_used"],
                "expected_loss_under_truth": informed["expected_loss_under_truth"],
                "expected_loss_if_always_trusted": trust["expected_loss_under_truth"],
            }
        )
        ledger.record_pair(
            model_version=policy_row.model_version,
            readout=READOUT,
            predicted_value=policy_row.qualification,
            realized_value=true_qualification,
            interval=policy_row.interval,
            context_identifier=policy_row.context_identifier,
        )
    first_revoked = next(
        (row["case"] for row in rows if row["weight_before"] == 0.0), None
    )
    return {
        "true_qualification": true_qualification,
        "claimed_qualification": claimed_qualification,
        "cases": rows,
        "total_loss_with_revocation": round(with_revocation, 6),
        "total_loss_if_always_trusted": round(without_revocation, 6),
        "loss_recovered_by_revocation": round(without_revocation - with_revocation, 6),
        "revocation_latency_cases": first_revoked,
        "reading": (
            "Revocation does not make a bad predictor good; it stops paying for it. The "
            "recovered loss is bounded by how many cases pass before the ledger revokes, so "
            "the latency is the quantity to reduce, not the trust."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    out = Path(argv[0]) if argv else Path("prediction_value_results.json")
    payload = {
        "scope": (
            "Declared finite models pricing a revocable prediction inside the contingent "
            "grammar. The prediction changes one declared branch parameter of the planner's "
            "view and never edits the evidence problem. Not biological evidence."
        ),
        "loss_convention": "correct 0, wrong 10, deferral 4, plus the cost of every acquired action",
        "contract_effect": contract_effect(),
        "value_map": value_map(),
        "revocation": revocation_trace(),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    effect = payload["contract_effect"]
    print(
        "predictions: value=%s harm=%s strictness_premium=%s plan_change_rate=%s"
        % (
            effect["value_of_a_correct_prediction"],
            effect["harm_of_a_wrong_prediction"],
            effect["strictness_premium"],
            effect["informed_plan_change_rate"],
        )
    )
    print(
        "revocation: latency=%s recovered=%s"
        % (
            payload["revocation"]["revocation_latency_cases"],
            payload["revocation"]["loss_recovered_by_revocation"],
        )
    )
    print(
        "value map: plan-changing cells=%s of %s"
        % (payload["value_map"]["plan_changing_cells"], payload["value_map"]["total_cells"])
    )
    print(f"written: {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
