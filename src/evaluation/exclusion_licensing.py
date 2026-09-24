"""The licensing rule with a declared exclusion tolerance, so a rule-out can license.

File summary
- Path: src/evaluation/exclusion_licensing.py
- Purpose: make the framework's evidence boundary usable by a *rule-out test with a
  declared error rate*. The recorded admissible class treats a hypothesis as excluded
  only when its posterior falls below `contingent.licensed`'s hard-wired 1e-9, so a
  rule-out whose declared false-exclusion rate is 0.01 leaves the ruled-out explanation
  surviving and licenses nothing. Here the threshold becomes a declared field: a decision
  is licensed when every hypothesis above the declared exclusion tolerance accepts it.
- Core points:
  - The tolerance is not a tuning knob. It is the reviewer's accepted false-exclusion
    budget, and every number produced here is reported against the tolerance it required,
    so a reader can refuse the budget and read the value as 0.000 instead.
  - At the recorded tolerance of 1e-9 every function here reproduces `admissible.py`
    exactly. `tests/test_exclusion_licensing.py` pins that equivalence, so this module is
    an extension of the recorded objective rather than a competing one.
  - Two quantities the recorded implementation passes as one argument are separated: the
    belief threshold below which a hypothesis counts as excluded, and the loss tolerance
    used to detect a tie between terminal acts. Conflating them means raising the
    exclusion budget also loosens tie-breaking, which would move numbers for a second,
    unstated reason.
  - Nothing here is biological evidence. Every value is an exact optimum over a declared
    finite model.
- Interfaces: `admissible_terminal_at`, `solve_admissible_policy_at`,
  `admissible_policy_at`, `price_of_admissibility_at`, `admissible_certificate_at`,
  `exclusion_tolerance_sweep`, `RECORDED_EXCLUSION_TOLERANCE`
- Depends on: evaluation.adaptive_reference, evaluation.contingent, evaluation.admissible
"""
from __future__ import annotations

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
from .contingent import licensed, unsupported_attribution

# The threshold the recorded implementation hard-wires. Passing this value makes every
# function in this module agree with `admissible.py` to the digit.
RECORDED_EXCLUSION_TOLERANCE = 1e-9

# The loss tolerance used only to decide that two terminal acts are tied. It is held
# fixed so that raising the exclusion budget cannot silently loosen tie-breaking.
TIE_TOLERANCE = 1e-9


def admissible_terminal_at(
    problem: DecisionProblem,
    history: History,
    *,
    exclusion_tolerance: float = RECORDED_EXCLUSION_TOLERANCE,
) -> tuple[str, float]:
    """The best terminal decision this class admits, at a declared exclusion budget.

    Identical in structure to `admissible.admissible_terminal`: the Bayes decision is
    tried first, ties are scanned because a tie is not a licence, and deferral is the
    fallback that keeps the class non-empty. The single change is that a hypothesis is
    treated as excluded once its posterior falls below ``exclusion_tolerance`` rather
    than below a hard-wired 1e-9.
    """

    if not 0.0 <= exclusion_tolerance < 1.0:
        raise ValueError("an exclusion tolerance is a probability mass in [0, 1)")
    if DEFER not in problem.decisions:
        raise ValueError("the admissible class requires a deferral decision to fall back on")
    decision, best = terminal(problem, history)
    if licensed(problem, history, decision, tolerance=exclusion_tolerance):
        return decision, best
    belief = posterior(problem, history)
    for candidate in problem.decisions:
        if candidate == decision or candidate == DEFER:
            continue
        loss = sum(belief[h] * problem.loss[candidate][h] for h in problem.hypotheses)
        if abs(loss - best) <= TIE_TOLERANCE and licensed(
            problem, history, candidate, tolerance=exclusion_tolerance
        ):
            return candidate, best
    deferred = sum(belief[h] * problem.loss[DEFER][h] for h in problem.hypotheses)
    return DEFER, deferred


def solve_admissible_policy_at(
    problem: DecisionProblem,
    *,
    exclusion_tolerance: float = RECORDED_EXCLUSION_TOLERANCE,
    state_cap: int = 500_000,
) -> OptimalSolution:
    """Exhaustive dynamic programming over the admissible policies at one budget.

    The same recursion, memo key, state cap and completeness reporting as the recorded
    solver; only the terminal rule differs, so the two optima are directly comparable.
    """

    invalid = problem.validate()
    if invalid:
        raise ValueError("Invalid decision problem: " + ", ".join(invalid))
    table: dict[History, tuple[str, str]] = {}
    memo: dict[tuple, float] = {}
    counter = {"states": 0, "truncated": False}

    def key(history: History) -> tuple:
        return history_key(problem, history)

    def replay(history: History) -> tuple[str, str]:
        decision, best = admissible_terminal_at(
            problem, history, exclusion_tolerance=exclusion_tolerance
        )
        choice: tuple[str, str] = ("decide", decision)
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
            decision, loss = admissible_terminal_at(
                problem, history, exclusion_tolerance=exclusion_tolerance
            )
            memo[canonical] = loss
            table[history] = ("decide", decision)
            return loss
        decision, best = admissible_terminal_at(
            problem, history, exclusion_tolerance=exclusion_tolerance
        )
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


def admissible_policy_at(
    problem: DecisionProblem, *, exclusion_tolerance: float = RECORDED_EXCLUSION_TOLERANCE
) -> Policy:
    """The optimal admissible policy at one budget, from public declarations only."""

    solution = solve_admissible_policy_at(problem, exclusion_tolerance=exclusion_tolerance)

    def act(public: DecisionProblem, history: History) -> tuple[str, str]:
        step = solution.policy_table.get(history)
        if step is None:
            return (
                "decide",
                admissible_terminal_at(
                    public, history, exclusion_tolerance=exclusion_tolerance
                )[0],
            )
        return step

    return act


def price_of_admissibility_at(
    problem: DecisionProblem, *, exclusion_tolerance: float = RECORDED_EXCLUSION_TOLERANCE
) -> Mapping[str, object]:
    """What the boundary costs on one problem, at one declared exclusion budget."""

    unconstrained = solve_optimal_policy(problem)
    constrained = solve_admissible_policy_at(problem, exclusion_tolerance=exclusion_tolerance)
    complete = unconstrained.complete and constrained.complete
    return {
        "exclusion_tolerance": exclusion_tolerance,
        "unconstrained_optimum": round(unconstrained.expected_loss, 6),
        "admissible_optimum": round(constrained.expected_loss, 6),
        "price_of_admissibility": (
            round(constrained.expected_loss - unconstrained.expected_loss, 6) if complete else None
        ),
        "admissible_probability_defer": round(
            evaluate_policy(
                admissible_policy_at(problem, exclusion_tolerance=exclusion_tolerance), problem
            ).probability_defer,
            6,
        ),
        "admissible_unsupported_attribution": round(
            unsupported_attribution(
                admissible_policy_at(problem, exclusion_tolerance=exclusion_tolerance), problem
            ),
            6,
        ),
        "complete": complete,
    }


def admissible_certificate_at(
    problem: DecisionProblem,
    *,
    exclusion_tolerance: float = RECORDED_EXCLUSION_TOLERANCE,
    catalogue_source: str = "repair_catalogue",
) -> Mapping[str, object]:
    """What the repair catalogue is worth inside the class, at one declared budget.

    The menu-only problem drops every action only a repair could have proposed, exactly
    as the recorded certificate does, so the difference between the two optima is an
    upper bound on what any selection policy restricted to the menu can be missing.
    """

    menu_only = problem.restricted_to(
        tuple(sorted({action.source for action in problem.actions} - {catalogue_source})),
        identifier=f"{problem.identifier}[menu_only]",
    )
    menu = solve_admissible_policy_at(menu_only, exclusion_tolerance=exclusion_tolerance)
    closed = solve_admissible_policy_at(problem, exclusion_tolerance=exclusion_tolerance)
    menu_unconstrained = solve_optimal_policy(menu_only)
    closed_unconstrained = solve_optimal_policy(problem)
    complete = all(
        solution.complete for solution in (menu, closed, menu_unconstrained, closed_unconstrained)
    )
    return {
        "exclusion_tolerance": exclusion_tolerance,
        "menu_only_admissible": round(menu.expected_loss, 6),
        "closed_admissible": round(closed.expected_loss, 6),
        "value_of_the_repair_catalogue_admissible": (
            round(menu.expected_loss - closed.expected_loss, 6) if complete else None
        ),
        "menu_only_unconstrained": round(menu_unconstrained.expected_loss, 6),
        "closed_unconstrained": round(closed_unconstrained.expected_loss, 6),
        "value_of_the_repair_catalogue_unconstrained": (
            round(menu_unconstrained.expected_loss - closed_unconstrained.expected_loss, 6)
            if complete
            else None
        ),
        "complete": complete,
    }


def exclusion_tolerance_sweep(
    problem: DecisionProblem,
    tolerances: Sequence[float],
    *,
    catalogue_source: str = "repair_catalogue",
) -> tuple[Mapping[str, object], ...]:
    """Both certificates across declared exclusion budgets, for one problem.

    This is the reporting form the module exists for: a rule-out with a declared
    false-exclusion rate `alpha` is credited only at a tolerance at or above the
    posterior mass it leaves on the excluded hypothesis, so the sweep shows which budget
    each number required instead of presenting one number as unconditional.
    """

    rows: list[Mapping[str, object]] = []
    for tolerance in tolerances:
        price = price_of_admissibility_at(problem, exclusion_tolerance=tolerance)
        certificate = admissible_certificate_at(
            problem, exclusion_tolerance=tolerance, catalogue_source=catalogue_source
        )
        rows.append(
            {
                "exclusion_tolerance": tolerance,
                "unconstrained_optimum": price["unconstrained_optimum"],
                "admissible_optimum": price["admissible_optimum"],
                "price_of_admissibility": price["price_of_admissibility"],
                "value_of_the_repair_catalogue_admissible": certificate[
                    "value_of_the_repair_catalogue_admissible"
                ],
                "value_of_the_repair_catalogue_unconstrained": certificate[
                    "value_of_the_repair_catalogue_unconstrained"
                ],
                "admissible_probability_defer": price["admissible_probability_defer"],
                "admissible_unsupported_attribution": price["admissible_unsupported_attribution"],
                "complete": price["complete"] and certificate["complete"],
            }
        )
    return tuple(rows)
