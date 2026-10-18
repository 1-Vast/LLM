"""Targeted local tests for the typed ResearchEdit scaffolding and the masked interface (no data, no network, no LLM)."""
from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import masked_interface as M  # noqa: E402
import research_edit as RE  # noqa: E402


def example_edit() -> RE.ResearchEdit:
    """Illustrative template (not a finding): family-by-state interaction versus main effects."""

    return RE.ResearchEdit(
        edit_id="tmpl-interaction-001", primitive="interaction",
        observed_failure="shared response rule over-predicts kill of drug family F in context pool X",
        competing_explanations=[
            {"name": "main_effects", "description": "Y = alpha_d + beta_c", "is_strong_simple_baseline": True},
            {"name": "family_x_state", "description": "adds gamma*I(d in F)*I(z_c=1)", "is_strong_simple_baseline": False}],
        virtual_cell_edit={"drug_family": "F", "state_variable": "z_c"},
        applicability_scope={"drugs": ["family F"], "contexts": ["pool X"], "assay": "single-dose viability"},
        discriminating_assay={"bundle": "2 representative F compounds x 2 contexts per state", "cost": {"assay_wells": 4, "rounds": 1}},
        predicted_outcomes={"main_effects": {"quantity": "crossed_contrast", "direction": "none", "min_magnitude": 0.0},
                            "family_x_state": {"quantity": "crossed_contrast", "direction": "down", "min_magnitude": 0.3}},
        expected_decision_change={"nomination_change": "F compounds move up in state-1 contexts", "direction_of_qualified_hits": "up"},
        rejection_condition={"quantity": "crossed_contrast", "op": ">=", "threshold": -0.1},
        registered_before_outcome="sha256:placeholder", dependence_group="campaign-0")


def test_example_edit_is_admissible():
    assert RE.validate(example_edit()) == []


@pytest.mark.parametrize("mutate,needle", [
    (lambda e: e.competing_explanations.pop(), "two distinct"),
    (lambda e: e.competing_explanations[0].update(is_strong_simple_baseline=False), "strong simple baseline"),
    (lambda e: e.predicted_outcomes["family_x_state"].update(direction="sideways"), "direction"),
    (lambda e: e.predicted_outcomes["family_x_state"].pop("min_magnitude"), "min_magnitude"),
    (lambda e: e.rejection_condition.clear(), "rejection_condition"),
    (lambda e: e.expected_decision_change.update(nomination_change="utility up"), "utility goes up"),
    (lambda e: e.discriminating_assay.update(cost={"dollars": 3}), "itemised"),
    (lambda e: setattr(e, "registered_before_outcome", ""), "registered before"),
    (lambda e: setattr(e, "dependence_group", ""), "dependence_group"),
    (lambda e: e.virtual_cell_edit.pop("state_variable"), "needs virtual_cell_edit"),
])
def test_validator_catches_missing_parts(mutate, needle):
    e = copy.deepcopy(example_edit())
    mutate(e)
    assert any(needle in p for p in RE.validate(e)), RE.validate(e)


def test_identical_predictions_cannot_discriminate():
    e = example_edit()
    e.predicted_outcomes["family_x_state"] = dict(e.predicted_outcomes["main_effects"])
    assert any("identical predictions" in p for p in RE.validate(e))


def test_crossed_contrast_and_interaction_recovery():
    rng = np.random.default_rng(0)
    drugs = np.repeat(np.arange(8), 12)
    state = np.tile([0, 1], 48)
    y = 0.2 * drugs + 0.5 * state + rng.normal(0, 0.1, len(drugs))
    y_int = y - 0.8 * (np.isin(drugs, [0, 1, 2]) & (state == 1))
    fam = {0, 1, 2}
    null = RE.fit_interaction(y, drugs, state, fam)
    alt = RE.fit_interaction(y_int, drugs, state, fam)
    assert abs(null["gamma"]) < 0.15 and null["F"] < 8
    assert alt["gamma"] == pytest.approx(-0.8, abs=0.1) and alt["F"] > 100
    Y = {"d": {"c": 1.0, "c2": 0.2}, "d2": {"c": 0.6, "c2": 0.5}}
    assert RE.crossed_contrast(Y, "d", "d2", "c", "c2") == pytest.approx(0.7)


def test_d_dec_zero_when_decision_unchanged_or_prediction_identical():
    pi = [0.5, 0.5]
    assert RE.d_dec(pi, [[0, 0], [0, 0]], [(0, 1), (3, 1)]) == 0.0  # informative but decision unchanged
    assert RE.d_dec(pi, [[0, 2], [2, 0]], [(0, 1), (0, 1)]) == pytest.approx(0.0)  # same predictions
    assert RE.d_dec(pi, [[0, 2], [2, 0]], [(0, 1), (3, 1)]) > 0.1


def test_robust_objective_single_cost_entry():
    assert RE.robust_objective(0.5, 0.2, 0.05, 0.1, lam=1, eta=1, rho=2) == pytest.approx(0.05)


def test_sufficiency_three_verdicts():
    assert RE.sufficiency_verdict(np.zeros(50), 0.1)["verdict"] == "SUFFICIENT"
    assert RE.sufficiency_verdict(np.full(50, 0.5), 0.1)["verdict"] == "INSUFFICIENT"
    assert RE.sufficiency_verdict(np.r_[np.full(10, 0.3), np.zeros(10)], 0.15)["verdict"] == "UNRESOLVED"


def test_e90_saving_and_break_even():
    b, u = [10, 20, 40, 80], [1, 3, 5, 6]
    assert RE.e90(b, u, 6.0) == pytest.approx(40 + (5.4 - 5) * 40 / 1)
    assert RE.e90(b, u, 10.0) is None
    assert RE.saving90(30, 40) == pytest.approx(0.25)
    assert RE.break_even_projects(100, 25) == 4 and RE.break_even_projects(100, 0) == float("inf")


def test_route_table():
    kw = dict(h_min=0.15, i_min=0.7, t_min=0.5)
    assert RE.route(0.07, 0.9, 0.9, **kw) == "EXPAND_ACTION_ABSTRACTION"  # the +7% second-pool task
    assert RE.route(0.34, 0.5, 0.9, **kw) == "NEW_DISCRIMINATING_MEASUREMENT"
    assert RE.route(0.34, 0.9, 0.1, **kw) == "REVISE_STATE_OR_SCOPE"
    assert RE.route(0.34, 0.9, 0.9, policy_ok=False, **kw) == "CONSIDER_ALGORITHM_SEARCH"
    assert RE.route(0.34, 0.9, 0.9, all_strong_independent_ready=True, **kw) == "FREEZE_FOR_INDEPENDENT_EVALUATION"
    with pytest.raises(TypeError):  # thresholds have no defaults
        RE.route(0.3, 0.9, 0.9)


def _iface(tmp, **kw):
    return M.MaskedOutcomeInterface(lambda role, d: 0.6 if role != "transfer" else {"u": 0.6, "per_cluster": [1, 2]},
                                    Path(tmp) / "ledger.jsonl", **kw)


def test_search_scalar_and_cap():
    with tempfile.TemporaryDirectory() as t:
        m = _iface(t, caps={"search": 2})
        assert isinstance(m.query("search", [1]), float)
        m.query("search", [2])
        with pytest.raises(M.AccessRefused, match="SEARCH_CAP_REACHED"):
            m.query("search", [3])
        assert len(m.ledger()) == 2


def test_select_releases_one_bit_only():
    with tempfile.TemporaryDirectory() as t:
        m = _iface(t, select_threshold=0.5)
        out = m.query("select", [1])
        assert out is True and m.ledger()[0]["released"] == {"kind": "pass_fail", "bits": 1}
    with tempfile.TemporaryDirectory() as t:
        assert _iface(t, select_threshold=0.9).query("select", [9]) is False


def test_select_requires_threshold_and_transfer_requires_holding_freeze_once():
    with tempfile.TemporaryDirectory() as t:
        with pytest.raises(M.AccessRefused, match="SELECT_NEEDS_THRESHOLD"):
            _iface(t).query("select", [1])
    with tempfile.TemporaryDirectory() as t:
        with pytest.raises(M.AccessRefused, match="NEEDS_FREEZE_CHECK"):
            _iface(t).query("transfer", [1])
    with tempfile.TemporaryDirectory() as t:
        def bad():
            raise SystemExit("FREEZE_MISMATCH")
        with pytest.raises(M.AccessRefused, match="FREEZE_NOT_HOLDING"):
            _iface(t, freeze_check=bad).query("transfer", [1])
    with tempfile.TemporaryDirectory() as t:
        m = _iface(t, freeze_check=lambda: None)
        assert m.query("transfer", [1])["u"] == 0.6
        with pytest.raises(M.AccessRefused, match="TRANSFER_ALREADY_USED"):
            m.query("transfer", [1])
        # a fresh object over the same ledger still refuses (counts persist)
        with pytest.raises(M.AccessRefused, match="TRANSFER_ALREADY_USED"):
            _iface(t, freeze_check=lambda: None).query("transfer", [1])
