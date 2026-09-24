"""The admissible objective: the evidence boundary as a constraint, not a penalty.

File summary
- Path: src/evaluation/admissible.py
- Purpose: score repair against the objective the framework claims to optimize. The
  recorded loss convention lets a policy return a causal attribution on the prior
  whenever measuring costs more than being wrong on average, and the 2026-09-14
  record measured that the exact reference does exactly that on 68% of one family's
  probability mass. Here the framework's own licensing rule becomes a constraint on
  the admissible policy class, and the repair catalogue is priced inside it.
- Core points:
  - `admissible_terminal` is the only terminal rule of the class: a non-deferral
    decision must be accepted as optimal by every hypothesis the observations still
    support, so an un-isolated attribution is not available at any price.
  - `solve_admissible_policy` is the exact contingent optimum of that class, by the
    same exhaustive dynamic programming the unconstrained reference uses, so the two
    numbers are directly comparable.
  - `price_of_admissibility` is the difference between them: exactly what enforcing
    the framework's stated boundary costs, on a declared model.
  - `admissible_certificate` is the menu-only bound computed inside the class. A
    repair can be worth nothing under the shipped objective and something under this
    one, and that difference is a statement about the objective, not about the
    repair.
- Interfaces: `admissible_terminal`, `admissible_value`, `solve_admissible_policy`,
  `admissible_policy`, `admissible_repair_policy`, `price_of_admissibility`,
  `admissible_certificate`, `AdmissibilityRow`, `admissible_row`
- Depends on: evaluation.adaptive_reference (the unconstrained reference),
  evaluation.contingent (the licensing rule and the bundle machinery)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .adaptive_reference import (
    DEFER,
    DecisionProblem,
    History,
    OptimalSolution,
    Policy,
    evaluate_policy,
    history_key,
    legal,
    outcome_probabilities,
    posterior,
    solve_optimal_policy,
    terminal,
)
from .contingent import (
    TOLERANCE,
    ambiguity_group,
    bundle_outcome_patterns,
    executable_bundles,
    licensed,
    unsupported_attribution,
)


def admissible_terminal(
    problem: DecisionProblem, history: History, *, tolerance: float = 1e-9
) -> tuple[str, float]:
    """The best terminal decision this class admits at a state.

    The framework's rule is that only a qualified, condition-matched result may
    shrink the compatible hypothesis set, and `contingent.licensed` is that rule
    written on the decision: a decision is licensed when no still-supported
    explanation would have called for a different one. A non-deferral decision that
    fails the test is a prior promoted into a causal attribution, and this class does
    not contain it at any price. Deferral is therefore the fallback, and it is always
    available, which is what keeps the class non-empty from every state.

    The Bayes decision is tried first. When it is unlicensed, a *different* decision
    with the same Bayes loss may still be licensed -- the reference breaks ties
    alphabetically, and a tie is not a licence -- so ties are scanned rather than
    assumed away.
    """

    if DEFER not in problem.decisions:
        raise ValueError("the admissible class requires a deferral decision to fall back on")
    decision, best = terminal(problem, history)
    if licensed(problem, history, decision, tolerance=tolerance):
        return decision, best
    belief = posterior(problem, history)
    for candidate in problem.decisions:
        if candidate == decision or candidate == DEFER:
            continue
        loss = sum(belief[h] * problem.loss[candidate][h] for h in problem.hypotheses)
        if abs(loss - best) <= tolerance and licensed(problem, history, candidate, tolerance=tolerance):
            return candidate, best
    deferred = sum(belief[h] * problem.loss[DEFER][h] for h in problem.hypotheses)
    return DEFER, deferred


def admissible_value(
    problem: DecisionProblem, history: History, horizon: int, *, tolerance: float = 1e-9
) -> float:
    """Depth-limited optimal expected loss inside the admissible class.

    This is the pricing function a repair operator needs: the tail value of an
    outcome it is about to buy, computed under the same constraint the policy is
    scored under. Pricing a bundle with the unconstrained tail is what makes the
    recorded repair policy refuse a measurement that pays for itself.

    ``tolerance`` is the posterior mass below which a hypothesis stops counting as
    supported. The default is the recorded exclusion tolerance, under which only a
    determinate observation can license an attribution; a caller working with a
    measured error rate passes that rate instead, and must report which reading it
    used, because the two are different claims.
    """

    _decision, best = admissible_terminal(problem, history, tolerance=tolerance)
    if horizon <= 0:
        return best
    for action in legal(problem, history):
        expected = action.cost
        for outcome, probability in outcome_probabilities(problem, history, action).items():
            if probability > TOLERANCE:
                expected += probability * admissible_value(
                    problem, history + ((action.identifier, outcome),), horizon - 1, tolerance=tolerance
                )
        if expected < best - TOLERANCE:
            best = expected
    return best


def solve_admissible_policy(
    problem: DecisionProblem, *, state_cap: int = 500_000, tolerance: float = 1e-9
) -> OptimalSolution:
    """Exhaustive dynamic programming over the admissible contingent policies.

    Same recursion, same completeness reporting and same state cap as
    `adaptive_reference.solve_optimal_policy`; the only change is that an
    un-isolated attribution has been removed from the action space of the decision
    layer, so the two optima differ by exactly the price of the framework's boundary.
    """

    problems = problem.validate()
    if problems:
        raise ValueError("Invalid decision problem: " + ", ".join(problems))
    if DEFER not in problem.decisions:
        raise ValueError("the admissible class requires a deferral decision to fall back on")
    table: dict[History, tuple[str, str]] = {}
    memo: dict[tuple, float] = {}
    counter = {"states": 0, "truncated": False}

    def key(history: History) -> tuple:
        return history_key(problem, history)

    def replay(history: History) -> tuple[str, str]:
        _decision, best = admissible_terminal(problem, history, tolerance=tolerance)
        choice: tuple[str, str] = ("decide", admissible_terminal(problem, history, tolerance=tolerance)[0])
        for action in legal(problem, history):
            expected = action.cost
            for outcome, probability in outcome_probabilities(problem, history, action).items():
                if probability > 0:
                    expected += probability * memo.get(
                        key(history + ((action.identifier, outcome),)), float("inf")
                    )
            if expected < best - 1e-12:
                best, choice = expected, ("act", action.identifier)
        return choice

    def value(history: History) -> float:
        canonical = key(history)
        if canonical in memo:
            if history not in table:
                table[history] = replay(history)
            return memo[canonical]
        counter["states"] += 1
        if counter["states"] > state_cap:
            counter["truncated"] = True
            decision, loss = admissible_terminal(problem, history, tolerance=tolerance)
            memo[canonical] = loss
            table[history] = ("decide", decision)
            return loss
        decision, best = admissible_terminal(problem, history, tolerance=tolerance)
        choice: tuple[str, str] = ("decide", decision)
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
        lower_bound=loss,
        stopping_reason="exhausted" if not counter["truncated"] else "state_cap_reached",
    )


def admissible_policy(problem: DecisionProblem) -> Policy:
    """The optimal admissible policy, recomputed from public declarations only."""

    solution = solve_admissible_policy(problem)

    def act(public: DecisionProblem, history: History) -> tuple[str, str]:
        step = solution.policy_table.get(history)
        if step is None:
            return ("decide", admissible_terminal(public, history)[0])
        return step

    return act


def admissible_repair_policy(
    problem: DecisionProblem,
    history: History,
    *,
    max_bundle: int = 2,
    horizon: int = 3,
) -> tuple[str, str]:
    """The recorded ambiguity-aware repair, re-priced under the admissible objective.

    One change from `contingent.ambiguity_aware_repair_policy`: candidate bundles are
    scored by cost plus the *admissible* depth-limited tail, and the walk-away value is
    the admissible terminal value rather than the unconstrained Bayes loss. Everything
    else -- the jointly decisive bundle, the re-plan after every outcome, the refusal
    to attribute an un-isolated cause -- is unchanged, so the comparison against the
    recorded policy is one operator and not two policies.
    """

    decision, current = admissible_terminal(problem, history)
    group = ambiguity_group(problem, history)
    best: tuple[float, tuple[str, ...], tuple] | None = None
    for bundle in executable_bundles(problem, history, max_bundle):
        score = 0.0
        for steps, probability, spend in bundle_outcome_patterns(problem, history, bundle):
            score += probability * (spend + admissible_value(problem, history + steps, horizon))
        key = (score, tuple(action.identifier for action in bundle), bundle)
        if best is None or key[:2] < best[:2]:
            best = key
    if best is not None and best[0] < current - TOLERANCE:
        return ("act", best[2][0].identifier)
    if decision != DEFER and group:
        return ("decide", DEFER)
    return ("decide", decision)


@dataclass(frozen=True)
class AdmissibilityRow:
    """One policy's performance and what it claimed to know, under one objective."""

    policy: str
    objective: str
    expected_loss: float
    expected_cost: float
    probability_wrong_decision: float
    probability_defer: float
    unsupported_attribution: float

    def as_row(self) -> Mapping[str, object]:
        return {
            "policy": self.policy,
            "objective": self.objective,
            "expected_loss": round(self.expected_loss, 6),
            "expected_cost": round(self.expected_cost, 6),
            "probability_wrong_decision": round(self.probability_wrong_decision, 6),
            "probability_defer": round(self.probability_defer, 6),
            "unsupported_attribution": round(self.unsupported_attribution, 6),
        }


def admissible_row(policy: Policy, problem: DecisionProblem, name: str) -> AdmissibilityRow:
    evaluation = evaluate_policy(policy, problem)
    return AdmissibilityRow(
        policy=name,
        objective="admissible",
        expected_loss=evaluation.expected_loss,
        expected_cost=evaluation.expected_cost,
        probability_wrong_decision=evaluation.probability_wrong_decision,
        probability_defer=evaluation.probability_defer,
        unsupported_attribution=unsupported_attribution(policy, problem),
    )


def price_of_admissibility(problem: DecisionProblem) -> Mapping[str, object]:
    """The exact cost of the framework's evidence boundary on one declared problem."""

    unconstrained = solve_optimal_policy(problem)
    constrained = solve_admissible_policy(problem)
    unconstrained_rows = _unconstrained_reference_row(problem, unconstrained)
    complete = unconstrained.complete and constrained.complete
    return {
        "unconstrained_optimum": round(unconstrained.expected_loss, 6),
        "admissible_optimum": round(constrained.expected_loss, 6),
        "price_of_admissibility": (
            round(constrained.expected_loss - unconstrained.expected_loss, 6) if complete else None
        ),
        "unconstrained_unsupported_attribution": unconstrained_rows["unsupported_attribution"],
        "unconstrained_probability_defer": unconstrained_rows["probability_defer"],
        "admissible_probability_defer": round(
            evaluate_policy(admissible_policy(problem), problem).probability_defer, 6
        ),
        "complete": complete,
        "unconstrained_states": unconstrained.states,
        "admissible_states": constrained.states,
        "note": (
            "the difference is the exact price of refusing un-isolated attribution"
            if complete
            else "a search was truncated; no price is certified"
        ),
    }


def _unconstrained_reference_row(problem: DecisionProblem, solution: OptimalSolution) -> Mapping[str, object]:
    from .adaptive_reference import optimal_policy

    policy = optimal_policy(problem)
    evaluation = evaluate_policy(policy, problem)
    if abs(evaluation.expected_loss - solution.expected_loss) > 1e-6:
        raise ValueError("the recorded reference and its re-evaluation disagree")
    return {
        "expected_loss": round(evaluation.expected_loss, 6),
        "probability_defer": round(evaluation.probability_defer, 6),
        "unsupported_attribution": round(unsupported_attribution(policy, problem), 6),
    }


def admissible_certificate(
    problem: DecisionProblem,
    *,
    catalogue_source: str = "repair_catalogue",
    tolerance: float = 1e-9,
) -> Mapping[str, object]:
    """What the repair catalogue is worth inside the admissible class.

    The menu-only problem is the closed problem with every action that only a repair
    could have proposed removed, exactly as in `contingent.repair_catalogue_certificate`.
    Both optima are recomputed under the admissible objective, and the unconstrained
    pair is reported beside them so a reader can see which objective the repair's
    value belongs to. Completeness is reported for all four searches: a truncated
    search certifies nothing.
    """

    menu_only = problem.restricted_to(
        tuple(sorted({action.source for action in problem.actions} - {catalogue_source})),
        identifier=f"{problem.identifier}[menu_only]",
    )
    menu_unconstrained = solve_optimal_policy(menu_only)
    closed_unconstrained = solve_optimal_policy(problem)
    menu_admissible = solve_admissible_policy(menu_only, tolerance=tolerance)
    closed_admissible = solve_admissible_policy(problem, tolerance=tolerance)
    complete = all(
        solution.complete
        for solution in (menu_unconstrained, closed_unconstrained, menu_admissible, closed_admissible)
    )
    return {
        "menu_only_unconstrained": round(menu_unconstrained.expected_loss, 6),
        "closed_unconstrained": round(closed_unconstrained.expected_loss, 6),
        "value_of_the_repair_catalogue_unconstrained": (
            round(menu_unconstrained.expected_loss - closed_unconstrained.expected_loss, 6)
            if complete
            else None
        ),
        "menu_only_admissible": round(menu_admissible.expected_loss, 6),
        "closed_admissible": round(closed_admissible.expected_loss, 6),
        "value_of_the_repair_catalogue_admissible": (
            round(menu_admissible.expected_loss - closed_admissible.expected_loss, 6)
            if complete
            else None
        ),
        "price_of_admissibility_menu_only": (
            round(menu_admissible.expected_loss - menu_unconstrained.expected_loss, 6) if complete else None
        ),
        "price_of_admissibility_closed": (
            round(closed_admissible.expected_loss - closed_unconstrained.expected_loss, 6)
            if complete
            else None
        ),
        "complete": complete,
        "licence_tolerance": tolerance,
        "menu_only_states": menu_admissible.states,
        "closed_states": closed_admissible.states,
        "note": (
            "a strictly positive admissible value means the repair is required once the "
            "boundary is enforced, whether or not it was worth anything before"
            if complete
            else "a search was truncated; no value is certified"
        ),
    }


def binding_diagnostics(problem: DecisionProblem, *, tolerance: float = 1e-9) -> Mapping[str, object]:
    """Why the admissible constraint does or does not bind on this problem.

    Three measured conditions decide whether a package can express the case the
    framework's own boundary creates. If the prior is uniform and the menu contains a
    single decisive action at unit cost, then deciding after a measurement is already
    cheap and the boundary is never tested, which is what makes a package unable to
    certify anything about repair.
    """

    from .adaptive_reference import optimal_policy

    belief = posterior(problem, ())
    from .contingent import decisive

    decisive_singles = [action for action in problem.actions if decisive(problem, (), (action,))]
    return {
        "prior_max": round(max(problem.prior.values()), 6),
        "prior_is_uniform": max(problem.prior.values()) - min(problem.prior.values()) <= tolerance,
        "root_licensed": licensed(problem, (), terminal(problem, ())[0], tolerance=tolerance),
        "root_bayes_decision": terminal(problem, ())[0],
        "unsupported_attribution_of_the_unconstrained_reference": round(
            unsupported_attribution(optimal_policy(problem), problem), 6
        ),
        "individually_decisive_actions": len(decisive_singles),
        "cheapest_decisive_cost": min((action.cost for action in decisive_singles), default=None),
        "actions": len(problem.actions),
        "budget": problem.budget,
        "root_belief": {h: round(value, 6) for h, value in belief.items()},
    }


def sweep(
    build: "object", values: Sequence[float], *, key: str
) -> tuple[Mapping[str, object], ...]:
    """Recompute both certificates across a one-parameter family of declarations."""

    rows: list[Mapping[str, object]] = []
    for value in values:
        problem = build(**{key: value})  # type: ignore[operator]
        certificate = admissible_certificate(problem)
        rows.append(
            {
                key: value,
                "value_of_the_repair_catalogue_unconstrained": certificate[
                    "value_of_the_repair_catalogue_unconstrained"
                ],
                "value_of_the_repair_catalogue_admissible": certificate[
                    "value_of_the_repair_catalogue_admissible"
                ],
                "price_of_admissibility_menu_only": certificate["price_of_admissibility_menu_only"],
                "menu_only_admissible": certificate["menu_only_admissible"],
                "closed_admissible": certificate["closed_admissible"],
                "complete": certificate["complete"],
            }
        )
    return tuple(rows)
