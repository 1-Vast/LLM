"""Ambiguity-aware contingent repair over a typed premise-supply grammar.

File summary
- Path: src/evaluation/contingent.py
- Purpose: Make the core contribution of the framework testable. It adds the two
  things the frozen action grammar lacked -- several suppliers of one premise at
  different cost and interpretive strength, and repairs whose content depends on
  which failure the previous observation isolated -- and it decides admissibility
  with the same typed premise admission the rest of the framework uses.
- Core points:
  - A premise failure is treated as a fault. The observations available before
    purchase identify which premise is binding only up to an **ambiguity group**:
    the hypotheses still compatible with everything observed. That is the
    fault-isolation concept, transferred to evidence acquisition.
  - `ambiguity_aware_repair_policy` buys the cheapest **jointly decisive** bundle
    -- the minimal discriminating test set of the diagnosis literature -- rather
    than the cheapest single action that is separating now, and it re-plans after
    every outcome. It is bounded, deterministic, and reports when its bundle
    search was truncated.
  - `ambiguity_report` names the candidates, the single actions that would split
    them, and the cheapest separating bundles. `unsupported_attribution` measures
    the probability mass on which a policy reports a cause it has not isolated:
    a metric that did not exist while every action carried a declared separating
    outcome.
  - Nothing here is biological evidence. Every number is a statement about a
    declared finite model, and the exact contingent reference in
    `evaluation.adaptive_reference` remains the yardstick.
- Interfaces: `FaultMode`, `TypedCapability`, `RepairGrammar`, `AmbiguityReport`,
  `ambiguity_group`, `decisive`, `executable_bundles`, `ambiguity_report`,
  `ambiguity_aware_repair_policy`, `unsupported_attribution`, `required_depth`,
  `evaluate_with_attribution`
- Depends on: maestro.models (typed admission), evaluation.adaptive_reference
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from maestro.models import BiologicalQuantity, PremiseGrant, PremiseRequirement

from .adaptive_reference import (
    DEFER,
    AdaptiveAction,
    DecisionProblem,
    History,
    Policy,
    PolicyEvaluation,
    Step,
    evaluate_policy,
    legal,
    outcome_probabilities,
    posterior,
    solve_optimal_policy,
    spent,
    supplied,
    terminal,
)

TOLERANCE = 1e-9


@dataclass(frozen=True)
class FaultMode:
    """One reason a premise can fail, as a candidate diagnosis, not a label.

    The diagnosis is what the repair acts on, so it must be named before it can
    be repaired. Two modes of the same premise are the ambiguity group a policy
    has to split before it can claim to know why the premise failed.
    """

    identifier: str
    premise: str
    description: str = ""


@dataclass(frozen=True)
class TypedCapability:
    """A registered measurement capability with an explicit declared type.

    The declared quantity, entity, site, units, time and context are what decide
    admissibility, so a capability that measures RNA abundance can never discharge
    an occupancy premise however its identifier is spelled. ``exposes`` names the
    fault modes whose presence this capability's outcome can reveal, which is what
    makes a *jointly* decisive bundle constructible from individually weak actions.
    """

    identifier: str
    cost: float
    quantity: str
    supplies: tuple[str, ...] = ()
    entity: str | None = None
    site: str | None = None
    units: str | None = None
    time_hours: float | None = None
    context_identifier: str | None = None
    quantity_is_estimated: bool = False
    exposes: tuple[str, ...] = ()
    description: str = ""
    role: str = "readout"
    source: str = "menu"

    def grant(self, field_name: str) -> PremiseGrant:
        """The typed grant this capability's declaration would deliver.

        Quality is ``declared`` and passing, because a plan is a bet that the
        assay returns a qualified result. What the declaration is *not* allowed
        to be optimistic about is meaning, and that is exactly what the typed
        admission compares.
        """

        return PremiseGrant(
            field=field_name,
            source_action=self.identifier,
            quantity=BiologicalQuantity(self.quantity),
            is_estimate=self.quantity_is_estimated,
            entity=self.entity,
            site=self.site,
            units=self.units,
            context_identifier=self.context_identifier,
            time_hours=self.time_hours,
            quality="declared",
            quality_passed=True,
            provenance="declaration",
        )

    def unmet(self, requirement: PremiseRequirement) -> tuple[str, ...]:
        """Why this capability cannot discharge ``requirement``; empty means it can.

        The check is the framework's own typed admission, called rather than
        re-derived, so a repair admitted here is admitted by the executor too.
        """

        if not requirement.is_typed:
            return ()
        return requirement.unmet_reasons(self.grant(requirement.field))


@dataclass(frozen=True)
class RepairGrammar:
    """A decision problem plus the typed declarations and fault modes it needs.

    The decision problem is the object the exact reference solves. The premises,
    capabilities and fault modes are the layer above it: they are what an agent
    reads when it has to decide *which* repair is available and *why* the premise
    it is repairing actually failed.
    """

    problem: DecisionProblem
    premises: Mapping[str, PremiseRequirement] = field(default_factory=dict)
    capabilities: Mapping[str, TypedCapability] = field(default_factory=dict)
    fault_modes: tuple[FaultMode, ...] = ()

    def modes_of(self, premise: str) -> tuple[FaultMode, ...]:
        return tuple(mode for mode in self.fault_modes if mode.premise == premise)

    def resolving_capabilities(self, premise: str) -> tuple[TypedCapability, ...]:
        """Capabilities whose declared type actually discharges this premise."""

        requirement = self.premises.get(premise)
        if requirement is None:
            return ()
        return tuple(
            capability
            for capability in self.capabilities.values()
            if not capability.unmet(requirement)
        )

    def exposing_capabilities(self, mode: FaultMode) -> tuple[TypedCapability, ...]:
        """Capabilities whose outcome can reveal whether this fault mode holds."""

        return tuple(
            capability
            for capability in self.capabilities.values()
            if mode.identifier in capability.exposes
        )


def ambiguity_group(
    problem: DecisionProblem, history: History, *, tolerance: float = 1e-9
) -> tuple[str, ...]:
    """The supported hypotheses that still licence a different action.

    This is the ambiguity group in the fault-isolation sense, read on the decision
    rather than on the posterior: a hypothesis stays in the group when it is still
    compatible with every observation *and* the action now chosen would be the
    wrong one if that hypothesis were true. A hypothesis nobody can act on -- one
    whose loss is identical for every decision, or one the observations have ruled
    out -- is not part of the group, because buying evidence about it cannot change
    what is done.

    It is computed from the public prior, the declared outcome models and the
    observed history, so a policy can evaluate it without any hidden truth.
    """

    belief = posterior(problem, history)
    chosen = terminal(problem, history)[0]
    group: list[str] = []
    for hypothesis in problem.hypotheses:
        if belief.get(hypothesis, 0.0) <= tolerance:
            continue
        best = min(problem.loss[d][hypothesis] for d in problem.decisions)
        if problem.loss[chosen][hypothesis] > best + tolerance:
            group.append(hypothesis)
    return tuple(group)


def licensed(problem: DecisionProblem, history: History, decision: str, *, tolerance: float = 1e-9) -> bool:
    """Whether every supported hypothesis accepts this decision as optimal.

    This is the framework's own admission rule expressed on the decision: a
    decision is licensed when no supported explanation would have called for a
    different one. Anything else is a prior dressed as an attribution.
    """

    if decision == DEFER:
        return True
    belief = posterior(problem, history)
    for hypothesis in problem.hypotheses:
        if belief.get(hypothesis, 0.0) <= tolerance:
            continue
        best = min(problem.loss[d][hypothesis] for d in problem.decisions)
        if problem.loss[decision][hypothesis] > best + tolerance:
            return False
    return True


def _bundle_patterns(
    problem: DecisionProblem, history: History, bundle: Sequence[AdaptiveAction]
) -> tuple[tuple[tuple[tuple[str, str], ...], float, float], ...]:
    """Every outcome history a bundle can actually reach, with its probability and its spend.

    A bundle is a sequence, not a set. If a supplier returns its failure outcome,
    the readout it was meant to unlock is not executable, so the joint pattern in
    which the failure is followed by that readout is not a reachable world. Leaving
    such patterns in makes a bundle look more informative than it is and prices the
    cheap-but-fragile supplier as if its failure still bought the readout.

    A branch that stops early is kept, at the cost of the prefix it did execute.
    Dropping it instead would silently delete the failure mass from the bundle's
    expected cost, which is the one number the comparison turns on.
    """

    belief = posterior(problem, history)
    base_fields = supplied(problem, history)
    patterns: list[tuple[tuple[tuple[str, str], ...], float, float]] = []

    def walk(
        index: int,
        steps: tuple[tuple[str, str], ...],
        weights: Mapping[str, float],
        fields: frozenset[str],
        spend: float,
    ) -> None:
        if index == len(bundle):
            patterns.append((steps, sum(weights.values()), spend))
            return
        action = bundle[index]
        model = _model_now(action, fields)
        for outcome in action.outcomes():
            granted = frozenset(action.supplies.get(outcome, ()))
            if index + 1 < len(bundle):
                following = bundle[index + 1]
                if not set(following.prerequisites) <= (fields | granted):
                    # The bundle stops here on this branch; the branch is still a
                    # reachable world and it still cost the prefix that ran.
                    patterns.append(
                        (
                            steps + ((action.identifier, outcome),),
                            weights_total(weights, model, outcome),
                            spend + action.cost,
                        )
                    )
                    continue
            next_weights = {
                hypothesis: weights[hypothesis] * model.get(hypothesis, {}).get(outcome, 0.0)
                for hypothesis in problem.hypotheses
            }
            if sum(next_weights.values()) <= 0:
                continue
            walk(
                index + 1,
                steps + ((action.identifier, outcome),),
                next_weights,
                fields | granted,
                spend + action.cost,
            )

    walk(0, (), dict(belief), base_fields, 0.0)
    return tuple(entry for entry in patterns if entry[1] > 0)


def weights_total(
    weights: Mapping[str, float],
    model: Mapping[str, Mapping[str, float]],
    outcome: str,
) -> float:
    """Probability mass of one outcome of one action under the current weights."""

    return sum(
        weights[hypothesis] * model.get(hypothesis, {}).get(outcome, 0.0)
        for hypothesis in weights
    )


def bundle_outcome_patterns(
    problem: DecisionProblem, history: History, bundle: Sequence[AdaptiveAction]
) -> tuple[tuple[tuple[tuple[str, str], ...], float, float], ...]:
    """Public view of `_bundle_patterns`, for policies that price bundles themselves.

    A repair policy that optimizes a different objective than this module still has
    to enumerate the same reachable joint outcomes, including the branches where a
    failed supplier leaves its readout unexecutable. Exposing the enumeration keeps
    that arithmetic in one place instead of re-deriving it per objective.
    """

    return _bundle_patterns(problem, history, bundle)


def _model_now(
    action: AdaptiveAction, fields: frozenset[str]
) -> Mapping[str, Mapping[str, float]]:
    """The declared model that governs this action once ``fields`` have been measured.

    An action carrying an interpretation gate runs and returns a qualified result
    even while the gate is unmeasured; that result just carries no information.
    A bundle can supply the gate earlier in the same bundle, so which declaration
    governs is decided per step and not once at the root.
    """

    gate = getattr(action, "interpretation_gate", None)
    degenerate = getattr(action, "uninterpretable_model", None)
    if gate is None or not degenerate:
        return action.outcome_model
    return action.outcome_model if gate in fields else degenerate


def decisive(problem: DecisionProblem, history: History, bundle: Sequence[AdaptiveAction]) -> bool:
    """Whether some reachable joint outcome of this bundle changes what we would do.

    "Changes what we would do" means the Bayes decision or its expected loss, not
    the decision's name: a reading that leaves the same action optimal at a
    materially lower expected loss is decision-relevant even though the label did
    not move. One action is the special case the reactive control tests; a bundle
    is where the contour changes, because n actions can be jointly decisive while
    no proper subset of them is.
    """

    if not bundle:
        return False
    current_decision, current_loss = terminal(problem, history)
    for steps, probability, _spend in _bundle_patterns(problem, history, bundle):
        if probability <= TOLERANCE:
            continue
        decision, loss = terminal(problem, history + steps)
        if decision != current_decision or abs(loss - current_loss) > TOLERANCE:
            return True
    return False


def isolating(problem: DecisionProblem, history: History, bundle: Sequence[AdaptiveAction]) -> bool:
    """Whether some reachable joint outcome of this bundle leaves one candidate standing."""

    if not bundle:
        return False
    for steps, probability, _spend in _bundle_patterns(problem, history, bundle):
        if probability <= TOLERANCE:
            continue
        if len(ambiguity_group(problem, history + steps)) <= 1:
            return True
    return False


def executable_bundles(
    problem: DecisionProblem, history: History, max_size: int = 3, *, limit: int = 20000
) -> tuple[tuple[AdaptiveAction, ...], ...]:
    """Every purchasable bundle up to ``max_size`` that can run in some order.

    Prerequisites are satisfied by the *declared* supplies of the actions already
    in the bundle, which is the planning-time optimism the rest of the framework
    uses: the plan bets that an assay returns a qualified result, and never that
    a different quantity means the same thing.
    """

    taken = {identifier for identifier, _ in history}
    base_fields = supplied(problem, history)
    base_spend = spent(problem, history)
    found: list[tuple[AdaptiveAction, ...]] = []
    frontier: list[tuple[AdaptiveAction, ...]] = [()]
    truncated = False
    while frontier:
        bundle = frontier.pop()
        if len(bundle) >= max_size:
            continue
        fields = base_fields | frozenset(
            field for action in bundle for outcome in action.supplies for field in action.supplies[outcome]
        )
        spend = base_spend + sum(action.cost for action in bundle)
        chosen = taken | {action.identifier for action in bundle}
        for action in problem.actions:
            if action.identifier in chosen:
                continue
            if action.cost + spend > problem.budget + TOLERANCE:
                continue
            if not set(action.prerequisites) <= fields:
                continue
            extended = bundle + (action,)
            found.append(extended)
            if len(found) >= limit:
                truncated = True
                break
            frontier.append(extended)
        if truncated:
            break
    ordered = tuple(sorted(found, key=lambda item: (sum(a.cost for a in item), tuple(a.identifier for a in item))))
    return ordered


@dataclass(frozen=True)
class AmbiguityReport:
    """What the current observations do and do not isolate."""

    candidates: tuple[str, ...]
    isolating_actions: tuple[str, ...]
    separating_bundles: tuple[tuple[tuple[str, ...], float], ...]
    complete: bool

    @property
    def isolated(self) -> bool:
        return len(self.candidates) <= 1


def ambiguity_report(
    problem: DecisionProblem,
    history: History = (),
    *,
    max_bundle: int = 3,
    tolerance: float = 1e-9,
    bundle_limit: int = 20000,
) -> AmbiguityReport:
    """The ambiguity group, the single actions that split it, and the cheapest bundles that do."""

    candidates = ambiguity_group(problem, history, tolerance=tolerance)
    bundles = executable_bundles(problem, history, max_bundle, limit=bundle_limit)
    complete = len(bundles) < bundle_limit
    isolating: list[str] = []
    separating: list[tuple[tuple[str, ...], float]] = []
    for bundle in bundles:
        if not decisive(problem, history, bundle):
            continue
        identifiers = tuple(action.identifier for action in bundle)
        cost = sum(action.cost for action in bundle)
        separating.append((identifiers, cost))
        if len(bundle) == 1:
            isolating.append(bundle[0].identifier)
    separating.sort(key=lambda item: (item[1], item[0]))
    return AmbiguityReport(
        candidates=candidates,
        isolating_actions=tuple(sorted(set(isolating))),
        separating_bundles=tuple(separating),
        complete=complete,
    )


def _horizon_value(problem: DecisionProblem, history: History, horizon: int) -> float:
    """The depth-limited optimal expected loss of a state.

    This mirrors the recursion the reference exposes as ``lookahead_policy`` and is
    used here only to price the tail that follows a candidate bundle; the exact
    reference remains `evaluation.adaptive_reference.solve_optimal_policy`.
    """

    decision, best = terminal(problem, history)
    if horizon <= 0:
        return best
    for action in legal(problem, history):
        expected = action.cost
        for outcome, probability in outcome_probabilities(problem, history, action).items():
            if probability > TOLERANCE:
                expected += probability * _horizon_value(
                    problem, history + ((action.identifier, outcome),), horizon - 1
                )
        if expected < best - TOLERANCE:
            best = expected
    return best


def ambiguity_aware_repair_policy(
    problem: DecisionProblem,
    history: History,
    *,
    max_bundle: int = 2,
    horizon: int = 3,
) -> Step:
    """Buy the bundle that best prices the decision, and never attribute an un-isolated cause.

    Two operations are combined, and both come from fault diagnosis rather than
    from search. First, a bundle is priced by the *decision value* of its joint
    outcome -- cost plus the depth-limited optimal loss on the far side of it --
    not by how informative it is and not by how cheaply a single action moves the
    label. A cheap supplier that fails has bought nothing, and pricing its failure
    branch is what makes the reliable supplier worth its premium. Second, the
    policy refuses to return a non-deferral decision while two candidate causes are
    still compatible with the observations: it either buys the reading that
    isolates them, or it defers. That discipline has a measurable cost, and the
    cost is reported wherever the policy is scored.

    It is a bounded heuristic, not the exact reference. The gap between the two is
    the honest part of every comparison it appears in.
    """

    decision, current = terminal(problem, history)
    group = ambiguity_group(problem, history)
    best: tuple[float, tuple[str, ...], tuple[AdaptiveAction, ...]] | None = None
    for bundle in executable_bundles(problem, history, max_bundle):
        score = 0.0
        for steps, probability, spend in _bundle_patterns(problem, history, bundle):
            score += probability * (spend + _horizon_value(problem, history + steps, horizon))
        key = (score, tuple(action.identifier for action in bundle), bundle)
        if best is None or key[:2] < best[:2]:
            best = key
    if best is not None and best[0] < current - TOLERANCE:
        return ("act", best[2][0].identifier)
    # Nothing worth buying. A deferral is licensed; a prior promoted into a causal
    # attribution is not, so an un-isolated non-deferral decision becomes a deferral.
    if decision != DEFER and group:
        return ("decide", DEFER)
    return ("decide", decision)


def unsupported_attribution(
    policy: Policy, problem: DecisionProblem, *, tolerance: float = 1e-9
) -> float:
    """Probability mass on which the policy names a cause it has not isolated.

    A non-deferral decision is a causal attribution: it says which explanation
    the evidence supports. If two hypotheses are both still compatible with the
    observations, the attribution rests on the prior, not on a measurement, and
    the framework's own rule forbids promoting that into an update. The metric
    makes the practice visible instead of leaving it to a reader's judgement.
    """

    total = 0.0

    def walk(history: History, weights: Mapping[str, float]) -> None:
        nonlocal total
        mass = sum(weights.values())
        if mass <= 0:
            return
        kind, name = policy(problem, history)
        if kind == "decide":
            if name != DEFER and not licensed(problem, history, name, tolerance=tolerance):
                total += mass
            return
        action = problem.action(name)
        for outcome in action.outcomes():
            next_weights = {
                h: weights[h] * action.outcome_model[h].get(outcome, 0.0) for h in problem.hypotheses
            }
            walk(history + ((name, outcome),), next_weights)

    walk((), dict(problem.prior))
    return total


def required_depth(problem: DecisionProblem, *, max_depth: int = 5, tolerance: float = 1e-6) -> int | None:
    """Smallest depth-limited lookahead that attains the exact optimum, else None.

    This is the statistic that separates a search-depth problem from a grammar
    problem. If no fixed depth in the tested range attains the exact value, then
    the instance is not solved by looking further ahead with the incumbent
    policy family; something about the grammar or the operation has to change.
    """

    from .adaptive_reference import lookahead_policy

    optimum = solve_optimal_policy(problem).expected_loss
    for depth in range(1, max_depth + 1):
        value = evaluate_policy(lookahead_policy(depth), problem).expected_loss
        if abs(value - optimum) <= tolerance:
            return depth
    return None


@dataclass(frozen=True)
class AttributedEvaluation:
    """A policy's exact expected performance plus what it claimed to know."""

    evaluation: PolicyEvaluation
    unsupported_attribution: float

    def as_row(self, name: str) -> Mapping[str, object]:
        return {
            "policy": name,
            "expected_loss": round(self.evaluation.expected_loss, 6),
            "expected_cost": round(self.evaluation.expected_cost, 6),
            "probability_wrong_decision": round(self.evaluation.probability_wrong_decision, 6),
            "probability_defer": round(self.evaluation.probability_defer, 6),
            "unsupported_attribution": round(self.unsupported_attribution, 6),
        }


def evaluate_with_attribution(
    policy: Policy, problem: DecisionProblem, *, tolerance: float = 1e-9
) -> AttributedEvaluation:
    return AttributedEvaluation(
        evaluation=evaluate_policy(policy, problem),
        unsupported_attribution=unsupported_attribution(policy, problem, tolerance=tolerance),
    )


def repair_catalogue_certificate(
    problem: DecisionProblem, *, catalogue_source: str = "repair_catalogue"
) -> Mapping[str, object]:
    """What the repair catalogue is worth, as a bound rather than as a comparison.

    Every policy restricted to the original menu -- reactive, entropy-per-cost,
    lookahead of any depth, or the exact reference itself -- cannot do better than
    the exact optimum of the menu-only problem, because that optimum is taken over
    every contingent policy the original menu admits. So the difference between
    that optimum and the optimum of the closed problem is an upper bound on what
    *any* selection policy can be missing, and the loss of a specific control is
    only interpretable against it.

    The two searches report their own completeness. A truncated search bounds
    nothing, and the returned value says so instead of printing a number as if it
    were a proof.
    """

    menu_only = problem.restricted_to(
        tuple(sorted({action.source for action in problem.actions} - {catalogue_source})),
        identifier=f"{problem.identifier}[menu_only]",
    )
    menu_solution = solve_optimal_policy(menu_only)
    closed_solution = solve_optimal_policy(problem)
    complete = menu_solution.complete and closed_solution.complete
    return {
        "menu_only_optimum": round(menu_solution.expected_loss, 6),
        "closed_optimum": round(closed_solution.expected_loss, 6),
        "value_of_the_repair_catalogue": (
            round(menu_solution.expected_loss - closed_solution.expected_loss, 6) if complete else None
        ),
        "complete": complete,
        "menu_only_states": menu_solution.states,
        "closed_states": closed_solution.states,
        "note": (
            "any policy restricted to the menu, at any depth, is bounded by menu_only_optimum"
            if complete
            else "a search was truncated; no value is certified"
        ),
    }
