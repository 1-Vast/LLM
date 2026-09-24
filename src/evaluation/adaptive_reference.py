"""An exact outcome-adaptive policy reference for small evidence-acquisition problems.

File summary
- Path: src/evaluation/adaptive_reference.py
- Purpose: give repair policies something exact to be compared against. A problem declares hypotheses, a prior, actions with costs, premise prerequisites, suppliers, and probabilistic outcomes that include failure and inconclusive results; the reference computes the optimal contingent policy by exhaustive dynamic programming over observation histories.
- Core points:
  - A policy is a function of the public declarations and the observed history only, so it is non-anticipative by construction; the evaluator alone holds the true generative model.
  - Expected loss is computed exactly by enumerating outcome histories under the true model, never by sampling.
  - Completeness is reported: a search that hits its state cap returns bounds instead of a certificate, with the clairvoyant loss as the lower bound.
  - Competent controls keep ordinary prerequisite handling: a blocked readout buys the cheapest supplier of its missing premise. Removing that would manufacture a win.
  - An action may declare an *interpretation gate*: a premise field without which
    the action still executes and still returns a qualified observation, but the
    observation carries no information about the hypotheses. This is the
    "uninterpretable success" the current grammar could not express, and it is
    what makes a composed plan worth buying rather than merely cheaper.
  - A composed action is a new registered object, not a sequence: it exists to
    carry shared-control economics that no sequence of the original actions can
    reach inside the same budget.
  - Every result here is a statement about a declared finite model. Synthetic problems establish algorithm behaviour, not biology.
- Interfaces: `AdaptiveAction`, `DecisionProblem`, `History`, `outcome_model_for`, `solve_optimal_policy`, `evaluate_policy`, `optimal_policy`, `reactive_prerequisite_policy`, `information_gain_policy`, `lookahead_policy`, `fixed_order_policy`, `to_evidence_action`, `PolicyEvaluation`
- Depends on: maestro.models (for the execution-semantics bridge)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence

from maestro.models import EvidenceAction

DEFER = "defer"


@dataclass(frozen=True)
class AdaptiveAction:
    """A registered action with a declared outcome model.

    ``outcome_model[h][o]`` is the declared probability of outcome ``o`` when
    hypothesis ``h`` is true; failed and inconclusive outcomes are ordinary
    outcomes with their own probabilities. ``supplies[o]`` names the premise
    fields that outcome ``o`` discharges, so a failed supplier supplies nothing.

    ``interpretation_gate`` names the premise field that makes this action's
    outcome interpretable. When the gate is not supplied, the action is still
    legal and its declared ``uninterpretable_model`` applies instead: the assay
    runs, passes its own quality check, and moves no belief. Both declarations
    are the case author's; neither is confirmed until a real result arrives.

    ``composed_from`` names the registered actions this object was composed
    from. A composed action is a new object in the action space rather than a
    sequence of the originals, because only a new object can carry a
    shared-control cost that the originals cannot reach.
    """

    identifier: str
    cost: float
    outcome_model: Mapping[str, Mapping[str, float]]
    prerequisites: tuple[str, ...] = ()
    supplies: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    role: str = "readout"
    source: str = "menu"
    interpretation_gate: str | None = None
    uninterpretable_model: Mapping[str, Mapping[str, float]] | None = None
    composed_from: tuple[str, ...] = ()

    @property
    def is_composed(self) -> bool:
        return bool(self.composed_from)

    def outcomes(self) -> tuple[str, ...]:
        seen: list[str] = []
        for distribution in self.outcome_model.values():
            for outcome in distribution:
                if outcome not in seen:
                    seen.append(outcome)
        for distribution in (self.uninterpretable_model or {}).values():
            for outcome in distribution:
                if outcome not in seen:
                    seen.append(outcome)
        return tuple(seen)

    def uninterpretable_outcomes(self) -> tuple[str, ...]:
        """Outcomes this action can return while its interpretation gate is unmeasured."""

        if self.interpretation_gate is None or not self.uninterpretable_model:
            return ()
        seen: list[str] = []
        for distribution in self.uninterpretable_model.values():
            for outcome in distribution:
                if outcome not in seen:
                    seen.append(outcome)
        return tuple(seen)


@dataclass(frozen=True)
class DecisionProblem:
    """A finite evidence-acquisition problem with a terminal decision and a loss."""

    identifier: str
    hypotheses: tuple[str, ...]
    prior: Mapping[str, float]
    actions: tuple[AdaptiveAction, ...]
    budget: float
    decisions: tuple[str, ...]
    loss: Mapping[str, Mapping[str, float]]
    family: str = ""
    note: str = ""
    attributions: tuple[str, ...] = ()
    enforce_licensing: bool = False

    def action(self, identifier: str) -> AdaptiveAction:
        return next(item for item in self.actions if item.identifier == identifier)

    def validate(self) -> tuple[str, ...]:
        problems: list[str] = []
        if abs(sum(self.prior.values()) - 1.0) > 1e-9:
            problems.append("prior_does_not_sum_to_one")
        if set(self.prior) != set(self.hypotheses):
            problems.append("prior_hypotheses_mismatch")
        for action in self.actions:
            if set(action.outcome_model) != set(self.hypotheses):
                problems.append(f"{action.identifier}:outcome_model_hypotheses_mismatch")
            for hypothesis, distribution in action.outcome_model.items():
                if abs(sum(distribution.values()) - 1.0) > 1e-9:
                    problems.append(f"{action.identifier}:{hypothesis}:outcomes_do_not_sum_to_one")
            if action.interpretation_gate is not None and not action.uninterpretable_model:
                # A gate with no declared uninterpretable behaviour would be a
                # gate that silently keeps the informative model, which is the
                # defect this field exists to make impossible.
                problems.append(f"{action.identifier}:gate_without_uninterpretable_model")
            if action.uninterpretable_model:
                if set(action.uninterpretable_model) != set(self.hypotheses):
                    problems.append(f"{action.identifier}:uninterpretable_model_hypotheses_mismatch")
                for hypothesis, distribution in action.uninterpretable_model.items():
                    if abs(sum(distribution.values()) - 1.0) > 1e-9:
                        problems.append(
                            f"{action.identifier}:{hypothesis}:uninterpretable_outcomes_do_not_sum_to_one"
                        )
            if action.is_composed:
                if len(action.composed_from) < 2:
                    problems.append(f"{action.identifier}:composition_needs_two_components")
                known = {item.identifier for item in self.actions}
                for component in action.composed_from:
                    if component not in known:
                        problems.append(f"{action.identifier}:unknown_component:{component}")
        for decision in self.decisions:
            if set(self.loss.get(decision, {})) != set(self.hypotheses):
                problems.append(f"{decision}:loss_hypotheses_mismatch")
        if self.attributions:
            unknown = [name for name in self.attributions if name not in self.decisions]
            if unknown:
                problems.append("attributions_not_among_decisions:" + ",".join(unknown))
            if len(set(self.attributions)) == len(set(self.decisions)):
                # With every terminal act an attribution there is no admissible
                # terminal act at all, and the search would have to invent one.
                problems.append("no_non_attribution_decision")
        return tuple(problems)

    def restricted_to(self, sources: Sequence[str], *, identifier: str | None = None) -> "DecisionProblem":
        """The same problem with only actions from the named sources (for example no repair catalogue)."""

        allowed = set(sources)
        return DecisionProblem(
            identifier=identifier or f"{self.identifier}[{'+'.join(sorted(allowed))}]",
            hypotheses=self.hypotheses,
            prior=self.prior,
            actions=tuple(action for action in self.actions if action.source in allowed),
            budget=self.budget,
            decisions=self.decisions,
            loss=self.loss,
            family=self.family,
            note=self.note,
            attributions=self.attributions,
            enforce_licensing=self.enforce_licensing,
        )

    def licensed_variant(self, *, identifier: str | None = None) -> "DecisionProblem":
        """The same problem with terminal attribution made subject to the runtime's licence.

        Everything else — prior, actions, budget, loss, costs — is untouched, so a
        difference between the two variants is attributable to the licence alone.
        """

        return DecisionProblem(
            identifier=identifier or f"{self.identifier}+licensed",
            hypotheses=self.hypotheses,
            prior=self.prior,
            actions=self.actions,
            budget=self.budget,
            decisions=self.decisions,
            loss=self.loss,
            family=self.family,
            note=self.note,
            attributions=self.attributions,
            enforce_licensing=True,
        )


History = tuple[tuple[str, str], ...]
Step = tuple[str, str]  # ("act", action_id) or ("decide", decision)
Policy = Callable[[DecisionProblem, History], Step]


def spent(problem: DecisionProblem, history: History) -> float:
    return sum(problem.action(action).cost for action, _ in history)


def supplied(problem: DecisionProblem, history: History) -> frozenset[str]:
    fields: set[str] = set()
    for action, outcome in history:
        fields.update(problem.action(action).supplies.get(outcome, ()))
    return frozenset(fields)


def legal(problem: DecisionProblem, history: History) -> tuple[AdaptiveAction, ...]:
    """Unacquired actions that fit the remaining budget and whose premises are supplied."""

    taken = {action for action, _ in history}
    remaining = problem.budget - spent(problem, history)
    fields = supplied(problem, history)
    return tuple(
        action
        for action in problem.actions
        if action.identifier not in taken
        and action.cost <= remaining + 1e-9
        and set(action.prerequisites) <= fields
    )


def outcome_model_for(
    problem: DecisionProblem, history: History, action: AdaptiveAction
) -> Mapping[str, Mapping[str, float]]:
    """The outcome model that applies *now*, given what the history has measured.

    An action carrying an interpretation gate has two declared models: the
    informative one, available once the gate field has been supplied, and the
    degenerate one that applies while it has not. Both are public declarations;
    which one governs is a function of the history, not of the hypothesis, so
    the policy can anticipate this without any hidden information.
    """

    if action.interpretation_gate is None or not action.uninterpretable_model:
        return action.outcome_model
    if action.interpretation_gate in supplied(problem, history):
        return action.outcome_model
    return action.uninterpretable_model


def posterior(problem: DecisionProblem, history: History) -> dict[str, float]:
    """Marginal belief after a history, using the model that governed each step.

    Which model governed a past action depends on the premise fields supplied
    *before that action*, so the history is replayed in order rather than
    re-scored as a set. An action taken without its interpretation gate
    contributes the likelihood of the degenerate model it actually returned,
    which is how "the assay ran and moved no belief" enters the arithmetic.
    """

    weights = {}
    for hypothesis in problem.hypotheses:
        weight = problem.prior[hypothesis]
        prefix: History = ()
        for action, outcome in history:
            model = outcome_model_for(problem, prefix, problem.action(action))
            weight *= model[hypothesis].get(outcome, 0.0)
            prefix = prefix + ((action, outcome),)
        weights[hypothesis] = weight
    total = sum(weights.values())
    if total <= 0:
        return {hypothesis: 0.0 for hypothesis in problem.hypotheses}
    return {hypothesis: value / total for hypothesis, value in weights.items()}


def history_key(problem: DecisionProblem, history: History) -> tuple:
    """Canonical state identity: acquired model-governed observations plus spend.

    Sorting the raw (action, outcome) pairs is not enough once a gate exists:
    acquiring the gate before or after a gated readout gives the readout a
    different declared model, so two histories with the same pair set can have
    different likelihoods and different futures. Recording which model governed
    each step restores the equivalence the memo relies on.
    """

    scored: list[tuple[str, str, str]] = []
    prefix: History = ()
    for action, outcome in history:
        item = problem.action(action)
        model = outcome_model_for(problem, prefix, item)
        governed = "interpretable" if model is item.outcome_model else "uninterpretable"
        scored.append((action, outcome, governed))
        prefix = prefix + ((action, outcome),)
    return tuple(sorted(scored))


def outcome_probabilities(problem: DecisionProblem, history: History, action: AdaptiveAction) -> dict[str, float]:
    belief = posterior(problem, history)
    model = outcome_model_for(problem, history, action)
    return {
        outcome: sum(belief[h] * model[h].get(outcome, 0.0) for h in problem.hypotheses)
        for outcome in action.outcomes()
    }


def surviving_hypotheses(problem: DecisionProblem, history: History) -> tuple[str, ...]:
    """Hypotheses the observations so far have not excluded."""

    belief = posterior(problem, history)
    return tuple(name for name in problem.hypotheses if belief[name] > 1e-12)


def bayes_actions_for(problem: DecisionProblem, hypothesis: str) -> tuple[str, ...]:
    """The terminal acts that would be right if this hypothesis were the true one."""

    best = min(problem.loss[decision][hypothesis] for decision in problem.decisions)
    return tuple(
        decision for decision in problem.decisions
        if problem.loss[decision][hypothesis] <= best + 1e-12
    )


def licensed_decisions(problem: DecisionProblem, history: History) -> tuple[str, ...]:
    """Terminal acts the runtime would actually emit at this history.

    An act that *asserts a cause* is licensed only when every hypothesis still
    compatible with the observations would take that same act: either one
    explanation survives, or the survivors agree on the stage action. A
    non-attribution act — deferral, or any decision declared not to assert a
    cause — is always licensed, which is why the caller must register one.

    This is the constraint the runtime already enforces and the objective did
    not. Pricing an unlicensed attribution finitely is not the same rule: it
    makes attribution optimal whenever the penalty is cheaper than the
    measurement, which is the defect this function exists to remove.
    """

    if not problem.enforce_licensing or not problem.attributions:
        return problem.decisions
    permitted = tuple(d for d in problem.decisions if d not in problem.attributions)
    survivors = surviving_hypotheses(problem, history)
    if not survivors:
        # A contradictory history licenses no attribution at all. The
        # non-attribution acts stay available, so the state is not a dead end.
        return permitted
    joint = set(problem.decisions)
    for hypothesis in survivors:
        joint &= set(bayes_actions_for(problem, hypothesis))
    return tuple(
        decision for decision in problem.decisions
        if decision not in problem.attributions or decision in joint
    )


def is_licensed(problem: DecisionProblem, history: History, decision: str) -> bool:
    """Whether the runtime would emit this act at this history.

    Deliberately independent of ``enforce_licensing``: the licence is a property
    of the runtime's rule, not of the objective a policy was optimised against,
    so a policy that ignores the rule must still be scored as having ignored it.
    """

    if decision not in problem.attributions:
        return True
    survivors = surviving_hypotheses(problem, history)
    if not survivors:
        return False
    joint = set(problem.decisions)
    for hypothesis in survivors:
        joint &= set(bayes_actions_for(problem, hypothesis))
    return decision in joint


def terminal(problem: DecisionProblem, history: History) -> tuple[str, float]:
    """The best admissible terminal decision and its expected loss under the declared model.

    ``enforce_licensing`` restricts the choice to the acts the runtime would
    emit. The unconstrained variant is preserved as the default so that every
    number published before this field existed keeps its meaning, and so the two
    conventions can be reported side by side instead of one replacing the other.
    """

    belief = posterior(problem, history)
    admissible = licensed_decisions(problem, history)
    best = min(
        admissible,
        key=lambda decision: (sum(belief[h] * problem.loss[decision][h] for h in problem.hypotheses), decision),
    )
    return best, sum(belief[h] * problem.loss[best][h] for h in problem.hypotheses)


def entropy(belief: Mapping[str, float]) -> float:
    return -sum(value * math.log2(value) for value in belief.values() if value > 0)


@dataclass(frozen=True)
class OptimalSolution:
    """The optimal contingent policy of a declared problem, with its search status."""

    policy_table: Mapping[History, Step]
    expected_loss: float
    states: int
    complete: bool
    lower_bound: float
    stopping_reason: str


def clairvoyant_loss(problem: DecisionProblem) -> float:
    """Expected loss with the true hypothesis revealed for free: a valid lower bound."""

    return sum(problem.prior[h] * min(problem.loss[d][h] for d in problem.decisions) for h in problem.hypotheses)


def solve_optimal_policy(problem: DecisionProblem, *, state_cap: int = 500_000) -> OptimalSolution:
    """Exhaustive dynamic programming over observation histories.

    Histories are canonicalised as ordered sequences, not sets, because the
    order of acquisition is part of what a contingent policy chooses; the
    search is still finite because every action is acquired at most once and
    costs are positive or the budget bounds the depth.
    """

    problems = problem.validate()
    if problems:
        raise ValueError("Invalid decision problem: " + ", ".join(problems))
    table: dict[History, Step] = {}
    memo: dict[tuple, float] = {}
    counter = {"states": 0, "truncated": False}

    def key(history: History) -> tuple:
        # Two histories whose acquired observations were governed by the same
        # declared models reach identical futures; the policy table still
        # records the concrete history for the decision it takes.
        return history_key(problem, history)

    def value(history: History) -> float:
        canonical = key(history)
        if canonical in memo:
            cached = memo[canonical]
            if history not in table:
                table[history] = _replay_choice(problem, history, memo, key)
            return cached
        counter["states"] += 1
        if counter["states"] > state_cap:
            counter["truncated"] = True
            decision, loss = terminal(problem, history)
            memo[canonical] = loss
            table[history] = ("decide", decision)
            return loss
        decision, best = terminal(problem, history)
        choice: Step = ("decide", decision)
        for action in legal(problem, history):
            expected = action.cost
            for outcome, probability in outcome_probabilities(problem, history, action).items():
                if probability > 0:
                    expected += probability * value(history + ((action.identifier, outcome),))
            if expected < best - 1e-12:
                best, choice = expected, ("act", action.identifier)
        memo[canonical] = best
        table[history] = choice
        return best

    loss = value(())
    return OptimalSolution(
        policy_table=table,
        expected_loss=loss,
        states=counter["states"],
        complete=not counter["truncated"],
        lower_bound=loss if not counter["truncated"] else clairvoyant_loss(problem),
        stopping_reason="exhausted" if not counter["truncated"] else "state_cap_reached",
    )


def _replay_choice(problem: DecisionProblem, history: History, memo, key) -> Step:
    decision, best = terminal(problem, history)
    choice: Step = ("decide", decision)
    for action in legal(problem, history):
        expected = action.cost
        for outcome, probability in outcome_probabilities(problem, history, action).items():
            if probability > 0:
                expected += probability * memo.get(key(history + ((action.identifier, outcome),)), float("inf"))
        if expected < best - 1e-12:
            best, choice = expected, ("act", action.identifier)
    return choice


def optimal_policy(problem: DecisionProblem) -> Policy:
    """The optimal policy for the problem as declared, recomputed from public declarations only."""

    solution = solve_optimal_policy(problem)

    def act(public: DecisionProblem, history: History) -> Step:
        step = solution.policy_table.get(history)
        if step is None:
            return ("decide", terminal(public, history)[0])
        return step

    return act


def _separating(problem: DecisionProblem, history: History, action: AdaptiveAction) -> bool:
    """Whether some outcome of this action would change the Bayes decision."""

    current, _ = terminal(problem, history)
    for outcome, probability in outcome_probabilities(problem, history, action).items():
        if probability > 0 and terminal(problem, history + ((action.identifier, outcome),))[0] != current:
            return True
    return False


def _cheapest_supplier(problem: DecisionProblem, history: History, missing: set[str]) -> AdaptiveAction | None:
    candidates = [
        action for action in legal(problem, history)
        if any(missing & set(fields) for fields in action.supplies.values())
    ]
    return min(candidates, key=lambda item: (item.cost, item.identifier), default=None)


def reactive_prerequisite_policy(problem: DecisionProblem, history: History) -> Step:
    """Competent reactive control: the cheapest decision-changing readout, prerequisites bought as needed.

    It reads the same declarations as the reference, re-plans after every
    outcome, and handles a blocked readout exactly as the agent's executor does:
    by buying the cheapest registered supplier of the missing premise.
    """

    taken = {action for action, _ in history}
    remaining = problem.budget - spent(problem, history)
    fields = supplied(problem, history)
    readouts = sorted(
        (
            action for action in problem.actions
            if action.identifier not in taken and action.role != "premise_supplier"
            and _separating(problem, history, action)
        ),
        key=lambda item: (item.cost, item.identifier),
    )
    for readout in readouts:
        missing = set(readout.prerequisites) - fields
        if not missing and readout.cost <= remaining + 1e-9:
            return ("act", readout.identifier)
        if missing:
            supplier = _cheapest_supplier(problem, history, missing)
            if supplier is not None and supplier.cost + readout.cost <= remaining + 1e-9:
                return ("act", supplier.identifier)
    return ("decide", terminal(problem, history)[0])


def information_gain_policy(problem: DecisionProblem, history: History, *, minimum_gain_per_cost: float = 1e-6) -> Step:
    """Experimental-design control: expected entropy reduction per unit cost, bundles for blocked readouts."""

    belief = posterior(problem, history)
    before = entropy(belief)
    remaining = problem.budget - spent(problem, history)
    fields = supplied(problem, history)
    taken = {action for action, _ in history}
    best: tuple[float, str] | None = None
    for readout in problem.actions:
        if readout.identifier in taken or readout.role == "premise_supplier":
            continue
        expected_after = 0.0
        for outcome, probability in outcome_probabilities(problem, history, readout).items():
            if probability > 0:
                expected_after += probability * entropy(posterior(problem, history + ((readout.identifier, outcome),)))
        gain = before - expected_after
        missing = set(readout.prerequisites) - fields
        if not missing:
            if readout.cost <= remaining + 1e-9 and gain / readout.cost > (best[0] if best else minimum_gain_per_cost):
                best = (gain / readout.cost, readout.identifier)
            continue
        supplier = _cheapest_supplier(problem, history, missing)
        if supplier is None:
            continue
        success = sum(
            probability for outcome, probability in outcome_probabilities(problem, history, supplier).items()
            if missing <= set(supplier.supplies.get(outcome, ()))
        )
        bundle = supplier.cost + readout.cost
        if bundle <= remaining + 1e-9 and success * gain / bundle > (best[0] if best else minimum_gain_per_cost):
            best = (success * gain / bundle, supplier.identifier)
    if best is None:
        return ("decide", terminal(problem, history)[0])
    return ("act", best[1])


def lookahead_policy(depth: int) -> Policy:
    """Depth-limited expectimax on the declared model: optimisation without full contingency."""

    def value(problem: DecisionProblem, history: History, horizon: int) -> tuple[float, Step]:
        decision, best = terminal(problem, history)
        choice: Step = ("decide", decision)
        if horizon == 0:
            return best, choice
        for action in legal(problem, history):
            expected = action.cost
            for outcome, probability in outcome_probabilities(problem, history, action).items():
                if probability > 0:
                    expected += probability * value(problem, history + ((action.identifier, outcome),), horizon - 1)[0]
            if expected < best - 1e-12:
                best, choice = expected, ("act", action.identifier)
        return best, choice

    def act(problem: DecisionProblem, history: History) -> Step:
        return value(problem, history, depth)[1]

    return act


def fixed_order_policy(order: Sequence[str]) -> Policy:
    """Non-LLM template control: a reviewed order, executed while legal, then the Bayes decision."""

    def act(problem: DecisionProblem, history: History) -> Step:
        taken = {action for action, _ in history}
        available = {action.identifier for action in legal(problem, history)}
        for identifier in order:
            if identifier not in taken and identifier in available:
                return ("act", identifier)
        return ("decide", terminal(problem, history)[0])

    return act


@dataclass(frozen=True)
class PolicyEvaluation:
    """Exact expected performance of one policy under a (possibly different) true model."""

    expected_loss: float
    expected_cost: float
    probability_wrong_decision: float
    probability_defer: float
    histories: int
    unlicensed_attribution_rate: float = 0.0


def evaluate_policy(
    policy: Policy,
    planning: DecisionProblem,
    truth: DecisionProblem | None = None,
    *,
    wrong: Callable[[str, str], bool] | None = None,
) -> PolicyEvaluation:
    """Enumerate every outcome history the policy can reach and weight it by the true model.

    The policy sees ``planning`` and the history; ``truth`` supplies the prior
    and outcome probabilities used for weighting. Identity of the two is the
    usual case; they differ when a planner's outcome model came from a
    prediction.
    """

    truth = truth or planning
    wrong = wrong or (lambda decision, hypothesis: decision != DEFER and truth.loss[decision][hypothesis] > min(truth.loss[d][hypothesis] for d in truth.decisions))
    totals = {"loss": 0.0, "cost": 0.0, "wrong": 0.0, "defer": 0.0, "histories": 0, "unlicensed": 0.0}

    def walk(history: History, weights: Mapping[str, float]) -> None:
        mass = sum(weights.values())
        if mass <= 0:
            return
        kind, name = policy(planning, history)
        if kind == "decide":
            totals["histories"] += 1
            if not is_licensed(planning, history, name):
                # The act asserts a cause the observations have not isolated. It
                # is counted whether or not that cause turns out to be right: an
                # attribution that happens to be correct was still made without
                # the evidence that licenses it.
                totals["unlicensed"] += mass
            for hypothesis, weight in weights.items():
                totals["loss"] += weight * truth.loss[name][hypothesis]
                totals["wrong"] += weight if wrong(name, hypothesis) else 0.0
            totals["defer"] += mass if name == DEFER else 0.0
            return
        if name in {action for action, _ in history}:
            raise ValueError(f"Policy repeated action '{name}'.")
        if name not in {action.identifier for action in legal(planning, history)}:
            raise ValueError(f"Policy chose an illegal action '{name}'.")
        action = truth.action(name)
        totals["loss"] += action.cost * mass
        totals["cost"] += action.cost * mass
        model = outcome_model_for(truth, history, truth.action(name))
        for outcome in action.outcomes():
            next_weights = {h: weights[h] * model[h].get(outcome, 0.0) for h in truth.hypotheses}
            walk(history + ((name, outcome),), next_weights)

    walk((), dict(truth.prior))
    return PolicyEvaluation(
        expected_loss=totals["loss"],
        expected_cost=totals["cost"],
        probability_wrong_decision=totals["wrong"],
        probability_defer=totals["defer"],
        histories=int(totals["histories"]),
        unlicensed_attribution_rate=totals["unlicensed"],
    )


def policy_tree(policy: Policy, problem: DecisionProblem) -> tuple[tuple[History, Step], ...]:
    """Every (history, step) the policy visits, for non-anticipativity and equivalence checks."""

    visited: list[tuple[History, Step]] = []

    def walk(history: History) -> None:
        step = policy(problem, history)
        visited.append((history, step))
        if step[0] == "decide":
            return
        action = problem.action(step[1])
        model = outcome_model_for(problem, history, action)
        for outcome in action.outcomes():
            if any(model[h].get(outcome, 0.0) > 0 for h in problem.hypotheses):
                walk(history + ((step[1], outcome),))

    walk(())
    return tuple(visited)


def to_evidence_action(action: AdaptiveAction, hypotheses: Sequence[str]) -> EvidenceAction:
    """The execution-semantics view of an adaptive action.

    Prerequisites and supplied fields carry over unchanged, so the shared
    legality rule and this module agree on what may run. The declared expected
    outcome per hypothesis is the modal outcome; the full distribution stays
    here, because EvidenceAction has no place for probabilities.
    """

    supplies = tuple(dict.fromkeys(field for fields in action.supplies.values() for field in fields))
    expected = {
        hypothesis: max(action.outcome_model[hypothesis].items(), key=lambda item: (item[1], item[0]))[0]
        for hypothesis in hypotheses
    }
    return EvidenceAction(
        identifier=action.identifier,
        description=f"{action.role} from {action.source}",
        cost=action.cost,
        distinguishes=tuple(hypotheses),
        prerequisites=action.prerequisites,
        supplies=supplies,
        expected_outcomes=expected,
    )
