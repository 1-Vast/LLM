"""Contract tests for frozen information, conservative bounds and the sole policy change."""
import gzip
import json
from types import SimpleNamespace
from unittest.mock import patch

from research.dual_core_followup import anchored as A


def test_unpurchased_unresolved_reachable_condition_keeps_bounds_open():
    key = ("MCF7", 24.0, 10.0)
    from research.protocol_v2.contracts import C
    action = C.action_id(key)
    row = {"outcomes": {action: {"lifecycle": "measured_valid", "outcome": "undetected"}}}
    coverage = A.potential_coverage("compound", [key], row, {("compound", action)})
    assert coverage["potential_unresolved_sources"] == [action]
    assert A.bounds(1, coverage) == (-2, 1)


def test_qc_failure_is_observed_but_absent_result_is_unknown():
    key = ("cell", 24.0, 1.0)
    from research.protocol_v2.contracts import C
    action = C.action_id(key)
    observed = {"outcomes": {action: {"lifecycle": "measured_qc_failed"}}}
    assert A.bounds(0, A.potential_coverage("c", [key], observed, set())) == (0, 0)
    assert A.bounds(0, A.potential_coverage("c", [key], {"outcomes": {}}, set())) == (-2, 1)


def test_identical_observed_unknown_paths_are_not_zero_identified():
    uncertain = {"point_identified": False}
    lo, hi = A.bounds(0, uncertain)
    assert (lo - hi, hi - lo) == (-3, 3)


def test_global_banks_deduplicate_content_and_preserve_call_counts(tmp_path):
    log = A.ForecastLog(tmp_path)
    content = {"refusal": None, "version": "frozen", "branches": []}
    q, o = log.forecast({"input": 1}, content)
    assert log.forecast({"input": 1}, content) == (q, o)
    receipt = log.bundle([(q, o, "selector"), (q, o, "selector")])
    assert receipt["calls"] == 2 and receipt["unique_queries"] == 1
    log.close()
    with gzip.open(tmp_path / "queries.jsonl.gz", "rt") as f:
        assert len(list(f)) == 1
    with gzip.open(tmp_path / "call_bundles.jsonl.gz", "rt") as f:
        assert json.loads(next(f))["queries"][0]["calls"] == 2


def test_protocol_freezes_four_arms_and_information_limits():
    protocol = json.loads(A.PROTOCOL.read_text())
    assert protocol["arms"] == [a[0] for a in A.ARMS]
    assert protocol["deviation_z"] == 1.645 and protocol["price"] == .02
    assert protocol["folds"] == list(range(5))
    assert "well OR plate" in protocol["bounds"]


def test_anchored_policy_adds_only_legal_fixed_anchor_and_z():
    from research.belief_planning import arms as BA
    from research.belief_planning import planner
    key = ("cell", 24.0, 1.0)
    identifier = BA.C.action_id(key)
    fake_action = SimpleNamespace(identifier=identifier)
    setting = SimpleNamespace(keys=(key,), max_measurements=2, budget_days=2, days=lambda k: 1)
    ctx = SimpleNamespace(params={"eliminates": True})
    audited = SimpleNamespace(calls=[], log=SimpleNamespace(bundle=lambda calls: {"calls": len(calls)}))
    plan = planner.BeliefPlan(identifier, "chosen", None, planner.PlanValue())
    with patch.object(BA.P, "legal_menu", return_value=[key]), patch.object(BA.P, "make_action", return_value=fake_action), \
         patch.object(BA.P, "fixed", return_value=(key, {})), patch.object(planner, "plan_measurement", return_value=plan) as plan_call:
        arguments = (ctx, "c", "H1", "H2", [], [key], 2, setting, None)
        assert A.selector("baseline", audited)(*arguments)[0] == key
        baseline = plan_call.call_args.kwargs
        assert A.selector("anchored", audited)(*arguments)[0] == key
        anchored = plan_call.call_args.kwargs
    assert {k: v for k, v in anchored.items() if k not in ("baseline", "deviation_z")} == baseline
    assert anchored["baseline"] == identifier and anchored["deviation_z"] == 1.645


def test_structural_validator_never_consults_forecast():
    audited = SimpleNamespace(forecast=lambda *a: (_ for _ in ()).throw(AssertionError("forecast called")))
    result = A.selector("anchored", audited)(SimpleNamespace(params={"eliminates": False}), "c", "a", "b", [], [], 2, None, None)
    assert result[0] is None and result[1]["reason"] == "registered_validator_cannot_eliminate"
