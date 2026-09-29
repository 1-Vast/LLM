"""Posterior forecast means survive planning; costs and uncertainty remain auditable."""
from dataclasses import replace
import math

import pytest

from maestro.acquisition import OutcomeBranch, OutcomeForecast, _score
from maestro.case_memory import CandidateAction
from maestro.case_update import _discrimination, rank_actions_by_decision_value


CONSEQUENCES = {"match_h1": frozenset({"H2"}), "match_h2": frozenset({"H1"})}
CANDIDATES = frozenset({"H1", "H2"})


def forecast(concentration=8.0, support=2):
    return OutcomeForecast("a", (
        OutcomeBranch("H1", {"match_h1": .7, "match_h2": .1, "unresolved": .2},
                      support, concentration),
        OutcomeBranch("H2", {"match_h1": .1, "match_h2": .7, "unresolved": .2},
                      support, concentration),
    ))


def test_posterior_mean_and_label_space_are_not_smoothed_twice():
    # Adding an unforecast registered outcome must not create probability mass.
    consequences = {**CONSEQUENCES, "other_assay_outcome": frozenset({"H1"})}
    correct, wrong, variance, tv, support, _ = _score(forecast(), CANDIDATES, consequences)
    assert (correct, wrong, tv) == pytest.approx((.7, .1, .6))
    assert variance == pytest.approx(.5 * (.8 - .6 ** 2) / 9)
    assert support == 2  # Prior mass is not new measured support.


def test_posterior_concentration_changes_uncertainty_without_changing_mean():
    thin = _score(forecast(8), CANDIDATES, CONSEQUENCES)
    thick = _score(forecast(80), CANDIDATES, CONSEQUENCES)
    assert thin[:2] == pytest.approx(thick[:2])
    assert thin[2] > thick[2] > 0


def test_legacy_empirical_branches_keep_jeffreys_smoothing():
    correct, wrong, _, _, _, _ = _score(forecast(None), CANDIDATES, CONSEQUENCES)
    assert correct == pytest.approx((2 * .7 + .5) / (2 + 3 * .5))
    assert wrong == pytest.approx((2 * .1 + .5) / (2 + 3 * .5))


@pytest.mark.parametrize("concentration", [0, -1, math.nan, math.inf, True, "8"])
def test_invalid_posterior_concentration_is_rejected(concentration):
    with pytest.raises(ValueError, match="invalid_posterior_concentration"):
        forecast(concentration)


def rank(f, cost=1, **kwargs):
    action = CandidateAction("a", "assay", "l1000", cost, 1, "response")
    return rank_actions_by_decision_value(
        tuple(CANDIDATES), (action,), {"a": f}, CONSEQUENCES, **kwargs)[0]


def test_posterior_does_not_receive_legacy_low_support_loss_again():
    posterior = rank(forecast())
    empirical = rank(forecast(None))
    assert posterior.model_uncertainty == empirical.model_uncertainty == 1.0
    assert posterior.net_value == pytest.approx(posterior.expected_terminal_decision_value - .02)
    assert posterior.net_value - empirical.net_value == pytest.approx(.5)
    assert posterior.admissible


@pytest.mark.parametrize("kwargs", [{"cost": 100}, {"prerequisite_costs": {"a": 1}},
                                    {"adaptation_uncertainties": {"a": 2}}])
def test_nonpositive_net_value_is_not_admissible(kwargs):
    result = rank(forecast(), **kwargs)
    assert result.net_value < 0
    assert not result.admissible
    assert result.reason == "non_positive_net_value"


def test_exact_break_even_is_not_admissible():
    zero_cost = rank(forecast(), cost=0)
    result = rank(forecast(), cost=0,
                  prerequisite_costs={"a": zero_cost.expected_terminal_decision_value})
    assert result.net_value == pytest.approx(0)
    assert not result.admissible
    assert result.reason == "non_positive_net_value"


def test_partial_posterior_declaration_does_not_bypass_legacy_risk_penalty():
    posterior = forecast()
    mixed = replace(posterior, branches=(posterior.branches[0],
                    replace(posterior.branches[1], posterior_concentration=None)))
    assert rank(mixed).net_value == pytest.approx(rank(forecast(None)).net_value)


def test_separation_metric_detects_mirrored_distributions_and_ignores_label_order():
    original = forecast()
    separated = _discrimination(original)
    assert separated == pytest.approx(.7 * math.log(.7 / .4) + .1 * math.log(.1 / .4))
    identical = replace(original, branches=(original.branches[0],
                        replace(original.branches[0], hypothesis="H2")))
    assert _discrimination(identical) == pytest.approx(0)
    assert _discrimination(replace(original, branches=original.branches[::-1])) == pytest.approx(separated)
