"""Contracts that distinguish injected predictions, actual costs and unidentified results."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.identifiability_audit import round2 as R
from maestro.acquisition import OutcomeBranch, OutcomeForecast


def test_charges_only_executed_actions_and_charges_qc_failures():
    row = {"h1": "a", "h2": "b", "truth": "a", "outcomes": {
        "early": {"lifecycle": "measured_valid", "outcome": "eliminate_b"},
        "later": {"lifecycle": "measured_qc_failed", "outcome": "quality_failed"}}}
    result = R.walk_sequence(row, ["early", "later"], {"early": 6, "later": 6})
    assert result["days"] == 6 and result["measurements"] == 1 and result["correct"] == 1
    result = R.walk_sequence(row, ["later", "early"], {"early": 6, "later": 6})
    assert result["days"] == 12 and result["measurements"] == 2
    with pytest.raises(KeyError):
        R.walk_sequence(row, ["absent"], {})


def test_source_uncertainty_bounds_are_not_imputed():
    assert R.utility_bounds("correct", True) == (-2, 1)
    assert R.utility_bounds("wrong", False) == (-2, -2)
    assert R.utility_bounds("deferred", False) == (0, 0)


class StubWorld:
    ft = SimpleNamespace(classes=("a", "b"))
    def __init__(self):
        self.seen = []
    def forecast(self, key, h1, h2, compound, history):
        from research.protocol_v2.contracts import C
        from research.belief_planning import world as W
        self.seen.append((key, history))
        p = 0.1 if key[0] == "A" else 0.9
        return OutcomeForecast(C.action_id(key), (OutcomeBranch(h1, {W.MATCH_H1: p, W.ABSENT: 1-p}, 10),
                                                   OutcomeBranch(h2, {W.MATCH_H2: p, W.ABSENT: 1-p}, 10)))


def test_forecast_permutation_preserves_context_and_action_identity():
    menu = (("A", 24.0, 1000.0), ("B", 24.0, 1000.0))
    world = StubWorld()
    audit = R.AuditWorld("permuted", world, menu, "frozen-input", 0)
    fc = audit.forecast(menu[0], "a", "b", "compound", ((menu[1], "no_detectable_response"),))
    assert world.seen == [(menu[1], ((menu[0], "no_detectable_response"),))]
    from research.protocol_v2.contracts import C
    assert fc.action_identifier == C.action_id(menu[0])
    assert len(audit.calls[0]["input_sha256"]) == len(audit.calls[0]["output_sha256"]) == 64


def test_none_and_constant_do_not_read_the_reference_backend():
    menu = (("A", 24.0, 1000.0), ("B", 24.0, 1000.0))
    world = StubWorld()
    none = R.AuditWorld("none", world, menu, "frozen", 0).forecast(menu[0], "a", "b", "x")
    assert none.refusal == "forecast_disabled_by_audit"
    constant = R.AuditWorld("constant", world, menu, "frozen", 0)
    a = constant.forecast(menu[0], "a", "b", "x")
    b = constant.forecast(menu[1], "a", "b", "y")
    assert a.branches == b.branches and world.seen == []


def test_each_policy_consumes_injected_forecasts_without_modifying_evidence():
    from research.sequence_audit import policies as P
    from maestro.outcome import EvidenceState
    menu = (("A", 24.0, 1000.0), ("B", 24.0, 1000.0))
    setting = P.Setting("stub", menu, menu, lambda key: 6.0, 12, 2)
    view = SimpleNamespace(params={"eliminates": True})
    state = EvidenceState(candidates=frozenset(("a", "b")))
    for policy in ("fixed", "baseline", "discrimination", "risk_select"):
        audited = R.AuditWorld("reference", StubWorld(), menu, "frozen", 0)
        arm = R.selector(policy, audited, 1.0)
        before = state
        action, _ = arm(view, "x", "a", "b", [], menu, 12, setting, state)
        assert action in menu or action is None
        assert bool(audited.calls) == (policy != "fixed")
        assert state == before
    none = R.AuditWorld("none", StubWorld(), menu, "frozen", 0)
    action, _ = R.selector("baseline", none, 1.0)(view, "x", "a", "b", [], menu, 12, setting, state)
    assert action is None


def test_bootstrap_clusters_chemical_units_and_keeps_physical_dependence_separate():
    frame = pd.DataFrame({"independent_unit": ["a", "a", "b"], "value": [1, 1, 0]})
    assert R.paired_ci(frame, "value")["mean"] == 0.5
    assert R.paired_ci(frame, "value")["units"] == 2
    source = pd.DataFrame({"compound": ["a", "b", "c"], "plates": ["P1", "P1|P2", "P2"]})
    components, plates = R.physical_components(source, ["plates"])
    assert len(set(components.values())) == 1 and plates == 2


def test_writes_are_exclusive_and_no_worldv2_substitution(tmp_path):
    path = tmp_path / "frozen.json"
    R.save(path, {"value": 1})
    with pytest.raises(FileExistsError):
        R.save(path, {"value": 2})
    assert all(f != "world_ref" for f, _ in R.CELLS)
    assert "world_v2" in R.NOT_RUN
    assert R.finite_json({"floor": float("inf")}) == {"floor": {"nonfinite": "inf"}}
    assert len(R.digest({"floor": float("inf")})) == 64
