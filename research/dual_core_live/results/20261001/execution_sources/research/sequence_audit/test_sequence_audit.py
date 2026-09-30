"""Counterexamples for behaviour-matched sequence replays and the uninformed-stop fallback.

Run: python -m pytest research/sequence_audit/test_sequence_audit.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import policies as P  # noqa: E402

C, E, S, V = P.C, P.E, P.S, P.V
EARLY, LATE, OTHER = ("A549", 24.0, 10.0), ("A549", 72.0, 10.0), ("A549", 72.0, 100.0)
SETTING = P.Setting("test", (EARLY, LATE, OTHER), (EARLY, LATE), E.days, 16.0)


def forecast(key, *, correct=0.0, wrong=0.0, absent=0.0, support=100):
    branches = []
    for own, good, bad in (("H1", S.LABELS[0], S.LABELS[1]), ("H2", S.LABELS[1], S.LABELS[0])):
        branches.append(V.OutcomeBranch(own, {good: correct, bad: wrong, V.ABSENT: absent,
                                              V.UNRESOLVED: 1 - correct - wrong - absent}, support))
    return V.OutcomeForecast(C.action_id(key), tuple(branches))


def refused(key, reason="no_paired_reference_for_branch:H1:no_detectable_response"):
    return V.OutcomeForecast(C.action_id(key), refusal=reason)


def outcomes(*readings):
    """An `execute` stub returning the given readings in order: 'undetected', 'eliminate_b', 'qc_failed', ..."""
    queue = list(readings)

    def execute(ctx, compound, key, h1, h2):
        reading = queue.pop(0)
        if reading == "qc_failed":
            return {"qc": False, "outcome": "quality_failed", "agreement": float("nan")}
        return {"qc": True, "outcome": reading, "agreement": 0.5, "score_a": 0.0, "score_b": 0.0}
    return execute


def recording_arm(choices):
    seen = []

    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        seen.append((tuple(tuple(e["key"]) for e in executed), tuple(menu), remaining))
        for key in choices:
            if key in menu:
                return key, {}
        return None, {"reason": "nothing_left"}
    return arm, seen


def test_plan_contingent_reproduces_the_follow_up_planner():
    cases = [
        ({C.action_id(EARLY): forecast(EARLY, absent=0.5), C.action_id(LATE): forecast(LATE, correct=0.4),
          C.action_id(OTHER): forecast(OTHER, correct=0.4)},
         lambda a, y, b: forecast(b, correct=1.0 if (y == V.ABSENT and b == LATE) else 0.2, wrong=0.05)),
        ({C.action_id(k): forecast(k, absent=1, support=3) for k in (EARLY, LATE, OTHER)},
         lambda a, y, b: forecast(b, correct=0.5, wrong=0.1, support=2)),
        ({C.action_id(EARLY): forecast(EARLY, absent=0.7, correct=0.1), C.action_id(LATE): refused(LATE),
          C.action_id(OTHER): forecast(OTHER, correct=0.3, wrong=0.2)},
         lambda a, y, b: refused(b) if b == OTHER else forecast(b, correct=0.6, support=1)),
    ]
    for forecasts, conditional in cases:
        for horizon in (1, 2):
            for budget in (8.0, 14.0, 16.0):
                original = S.plan_two_step(SETTING.keys, "H1", "H2", forecasts, conditional, budget=budget, horizon=horizon)
                port = P.plan_contingent(SETTING.keys, "H1", "H2", forecasts, conditional, days=E.days, budget=budget,
                                         horizon=horizon)
                assert port == original


def test_every_arm_is_offered_the_same_legal_menu_and_budget():
    """Two arms that choose the same actions must see identical menus: the runner, not the arm, sets them."""
    menus = []
    for choices in ((EARLY, LATE), (EARLY, LATE)):
        arm, seen = recording_arm(choices)
        P.run_matched("arm", arm, None, "c", "H1", "H1", "H2", SETTING, execute=outcomes("undetected", "undetected"))
        menus.append(seen)
    assert menus[0] == menus[1]
    first, second = menus[0]
    assert first == ((), (EARLY, LATE, OTHER), 16.0)
    # after a 24 h measurement: distinct, not earlier, affordable
    assert second == ((EARLY,), (LATE, OTHER), 10.0)


def test_a_later_first_measurement_removes_earlier_actions_for_every_arm():
    arm, seen = recording_arm((LATE, EARLY, OTHER))
    record = P.run_matched("arm", arm, None, "c", "H1", "H1", "H2", SETTING, execute=outcomes("undetected", "undetected"))
    assert seen[1][1] == (OTHER,)
    assert [s["action"] for s in record["steps"]] == [C.action_id(LATE), C.action_id(OTHER)]


def test_qc_failure_rule_is_the_runners_and_charges_the_failed_assay():
    for rule, calls, measurements in (("continue", 2, 2), ("stop", 1, 1)):
        arm, seen = recording_arm((EARLY, LATE))
        record = P.run_matched("arm", arm, None, "c", "H1", "H1", "H2", SETTING, qc_rule=rule,
                               execute=outcomes("qc_failed", "undetected"))
        assert len(seen) == calls
        assert record["measurements"] == measurements
        assert record["steps"][0]["qc"] is False and record["steps"][0]["eliminated"] == []
        assert P.audit_record(record, SETTING) == []
    arm, seen = recording_arm((EARLY, LATE))
    P.run_matched("arm", arm, None, "c", "H1", "H1", "H2", SETTING, execute=outcomes("qc_failed", "undetected"))
    assert seen[1][2] == 16.0 - E.days(EARLY)


def test_an_illegal_choice_is_refused():
    def backwards(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        return (LATE if not executed else EARLY), {}
    with pytest.raises(ValueError, match="not in the legal menu"):
        P.run_matched("backwards", backwards, None, "c", "H1", "H1", "H2", SETTING, execute=outcomes("undetected", "undetected"))


def test_only_a_real_result_changes_evidence_and_elimination_stops_every_arm():
    arm, seen = recording_arm((EARLY, LATE))
    record = P.run_matched("arm", arm, None, "c", "H1", "H1", "H2", SETTING, execute=outcomes("eliminate_b"))
    assert record["final"] == "correct" and record["measurements"] == 1 and record["stop"] == "eliminated"
    arm, seen = recording_arm((EARLY, LATE))
    record = P.run_matched("arm", arm, None, "c", "H2", "H1", "H2", SETTING, execute=outcomes("undetected", "ambiguous"))
    assert record["final"] == "undetermined" and record["utility"] == 0
    assert all(step["eliminated"] == [] for step in record["steps"])


@pytest.mark.parametrize("record, problem", [
    ({"qc_rule": "stop", "stop": "measurement_budget_spent",
      "steps": [{"key": ["A549", 24.0, 10.0], "action": "a", "qc": False, "eliminated": []},
                {"key": ["A549", 72.0, 10.0], "action": "b", "qc": True, "eliminated": []}]},
     "continued_after_qc_failure_under_stop_rule"),
    ({"qc_rule": "continue", "stop": "qc_failure_stop_rule",
      "steps": [{"key": ["A549", 24.0, 10.0], "action": "a", "qc": False, "eliminated": []}]},
     "stopped_by_harness_after_qc_failure_under_continue_rule"),
    ({"qc_rule": "continue", "stop": "x",
      "steps": [{"key": ["A549", 72.0, 10.0], "action": "a", "qc": True, "eliminated": []},
                {"key": ["A549", 24.0, 10.0], "action": "b", "qc": True, "eliminated": []}]}, "time_order"),
    ({"qc_rule": "continue", "stop": "x",
      "steps": [{"key": ["A549", 24.0, 10.0], "action": "a", "qc": False, "eliminated": ["H1"]}]},
     "qc_failure_changed_evidence"),
    ({"qc_rule": "continue", "stop": "x",
      "steps": [{"key": ["A549", 72.0, 10.0], "action": "a", "qc": True, "eliminated": []},
                {"key": ["A549", 72.0, 100.0], "action": "b", "qc": True, "eliminated": []},
                {"key": ["A549", 72.0, 1000.0], "action": "c", "qc": True, "eliminated": []}]}, "too_many_measurements"),
])
def test_record_audit_catches_asymmetries(record, problem):
    assert problem in P.audit_record(record, P.Setting("t", (), (), lambda k: 1.0, 16.0))


def _stub_planner(monkeypatch, forecasts, conditional):
    monkeypatch.setattr(P, "_forecasts", lambda ctx, h1, h2, keys, permuted=False: forecasts)
    monkeypatch.setattr(P, "_conditional", lambda ctx, h1, h2, permuted=False: conditional)
    return SimpleNamespace(extra={})


def _run(ctx, *, fallback, readings, rule="continue"):
    arm = (lambda *a: P.contingent(*a, fallback=True)) if fallback else P.contingent
    return P.run_matched("arm", arm, ctx, "c", "H1", "H1", "H2", SETTING, qc_rule=rule, execute=outcomes(*readings))


def test_fallback_continues_with_the_fixed_sequence_when_paired_references_are_missing(monkeypatch):
    forecasts = {C.action_id(EARLY): forecast(EARLY, correct=0.3, absent=0.6),
                 C.action_id(LATE): forecast(LATE, correct=0.2), C.action_id(OTHER): forecast(OTHER, correct=0.2)}
    ctx = _stub_planner(monkeypatch, forecasts, lambda a, y, b: refused(b))
    base = _run(ctx, fallback=False, readings=("undetected",))
    assert base["measurements"] == 1 and base["stop"].endswith(":no_paired_references")
    ctx = _stub_planner(monkeypatch, forecasts, lambda a, y, b: refused(b))
    revised = _run(ctx, fallback=True, readings=("undetected", "eliminate_b"))
    assert [s["action"] for s in revised["steps"]] == [C.action_id(EARLY), C.action_id(LATE)]
    assert revised["steps"][1]["note"] == {"fallback": "fixed_sequence", "planner_refusal": "no_paired_references"}
    assert revised["final"] == "correct"


def test_fallback_respects_an_informed_stop(monkeypatch):
    forecasts = {C.action_id(EARLY): forecast(EARLY, correct=0.3, absent=0.6),
                 C.action_id(LATE): forecast(LATE, correct=0.2), C.action_id(OTHER): forecast(OTHER, correct=0.2)}
    # well-supported references forecast mostly wrong eliminations after absence: no continuation
    ctx = _stub_planner(monkeypatch, forecasts, lambda a, y, b: forecast(b, correct=0.1, wrong=0.3, support=50))
    revised = _run(ctx, fallback=True, readings=("undetected",))
    assert revised["measurements"] == 1
    assert revised["stop"] == "no_supported_positive_utility_continuation:wrong_elimination_risk"


def test_fallback_after_thin_support_but_not_after_a_forecast_of_nothing(monkeypatch):
    forecasts = {C.action_id(EARLY): forecast(EARLY, correct=0.3, absent=0.6),
                 C.action_id(LATE): forecast(LATE, correct=0.2), C.action_id(OTHER): forecast(OTHER, correct=0.2)}
    # one reference per branch that eliminated correctly: positive on raw counts, not after shrinkage
    thin = lambda a, y, b: V.OutcomeForecast(C.action_id(b), (  # noqa: E731
        V.OutcomeBranch("H1", {S.LABELS[0]: 1.0}, 1), V.OutcomeBranch("H2", {V.ABSENT: 1.0}, 1)))
    rows = P.continuation_audit(SETTING.keys, EARLY, "H1", "H2", forecasts, thin, days=E.days, budget=16.0)[V.ABSENT]
    assert P.stop_reason(rows) == "inadequate_support_or_uncertainty"
    ctx = _stub_planner(monkeypatch, forecasts, thin)
    revised = _run(ctx, fallback=True, readings=("undetected", "undetected"))
    assert revised["steps"][1]["note"]["planner_refusal"] == "inadequate_support_or_uncertainty"
    nothing = lambda a, y, b: forecast(b, absent=1.0, support=50)  # noqa: E731
    ctx = _stub_planner(monkeypatch, forecasts, nothing)
    revised = _run(ctx, fallback=True, readings=("undetected",))
    assert revised["stop"].endswith(":predicted_non_positive_continuation_utility")


def test_deferral_falls_back_only_when_no_reference_informs_any_action(monkeypatch):
    ctx = _stub_planner(monkeypatch, {C.action_id(k): refused(k, "no_reference_for_hypothesis:H1") for k in SETTING.keys},
                        lambda a, y, b: refused(b))
    revised = _run(ctx, fallback=True, readings=("undetected", "undetected"))
    assert [s["action"] for s in revised["steps"]] == [C.action_id(EARLY), C.action_id(LATE)]
    assert revised["steps"][0]["note"]["planner_refusal"] == "no_references"
    ctx = _stub_planner(monkeypatch, {C.action_id(k): forecast(k, correct=0.1, wrong=0.3) for k in SETTING.keys},
                        lambda a, y, b: forecast(b, correct=0.1, wrong=0.3))
    revised = _run(ctx, fallback=True, readings=())
    assert revised["final"] == "deferred" and revised["stop"].endswith(":wrong_elimination_risk")


def test_after_a_qc_failure_the_planner_values_one_measurement_and_invents_no_branch(monkeypatch):
    forecasts = {C.action_id(EARLY): forecast(EARLY, correct=0.5), C.action_id(LATE): refused(LATE),
                 C.action_id(OTHER): refused(OTHER)}
    ctx = _stub_planner(monkeypatch, forecasts, lambda a, y, b: refused(b))
    base = _run(ctx, fallback=False, readings=("qc_failed",))
    assert base["measurements"] == 1
    assert base["stop"] == "no_positive_single_measurement_after_qc_failure:no_references"
    ctx = _stub_planner(monkeypatch, forecasts, lambda a, y, b: refused(b))
    revised = _run(ctx, fallback=True, readings=("qc_failed", "undetected"))
    assert [s["action"] for s in revised["steps"]] == [C.action_id(EARLY), C.action_id(LATE)]
    stopped = _run(_stub_planner(monkeypatch, forecasts, lambda a, y, b: refused(b)), fallback=True,
                   readings=("qc_failed",), rule="stop")
    assert stopped["stop"] == "qc_failure_stop_rule" and stopped["measurements"] == 1


@pytest.mark.skipif(not (P.ROOT / "outputs/sequence_audit_20260926/phase2_matched_replay/episodes.jsonl").exists(),
                    reason="replay not run")
def test_the_recorded_matched_replay_obeys_the_shared_rules():
    setting = {"A": P.Setting("sciplex3", (), P.SCIPLEX3_FIXED["A"], E.days, 16.0),
               "B": P.Setting("sciplex3", (), P.SCIPLEX3_FIXED["B"], E.days, 16.0)}
    path = P.ROOT / "outputs/sequence_audit_20260926/phase2_matched_replay/episodes.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        assert P.audit_record(record, setting[record["tier"]]) == []


@pytest.mark.skipif(not C.PREPARED.exists(), reason="prepared SciPlex3 data not present")
def test_plan_contingent_matches_the_original_on_every_sciplex3_contrast_of_two_folds():
    data, protocol = C.load(), C.load_protocol()
    detected = C.detected_flags(data, C.detection_null(data, protocol))
    for tier, fold in (("A", 1), ("B", 1)):
        for ctx, f in E.contexts(data, protocol, detected, None, tier_names=(tier,), folds=(fold,)):
            for h1 in ctx.tier.pool:
                for h2 in ctx.tier.pool:
                    if h1 == h2:
                        continue
                    forecasts = P._forecasts(ctx, h1, h2, ctx.tier.keys)
                    conditional = P._conditional(ctx, h1, h2)
                    for horizon in (1, 2):
                        assert P.plan_contingent(ctx.tier.keys, h1, h2, forecasts, conditional, days=E.days, budget=16.0,
                                                 horizon=horizon) == \
                            S.plan_two_step(ctx.tier.keys, h1, h2, forecasts, conditional, horizon=horizon)


def test_fallback_first_replans_when_a_continuation_is_supported():
    """A real neutral result makes its supported continuation eligible even without an initial plan."""
    forecasts = {C.action_id(k): forecast(k, absent=0.9, correct=0.02, wrong=0.02) for k in SETTING.keys}
    conditional = lambda a, y, b: forecast(b, correct=0.9)  # noqa: E731
    # the planner had no plan, so the first measurement was the fixed sequence's
    ctx = SimpleNamespace(extra={"sequence_audit_plans": {("H1", "H2", 2, False): (None, forecasts, conditional)}})
    executed = [{"key": list(EARLY), "action": C.action_id(EARLY), "outcome": "undetected", "qc": True, "eliminated": []}]
    menu = P.legal_menu(SETTING, executed, 16.0 - E.days(EARLY))
    key, note = P.contingent(ctx, "c", "H1", "H2", executed, menu, 16.0 - E.days(EARLY), SETTING, None, fallback=True)
    assert key == LATE
    assert note["after"] == V.ABSENT
    assert note["replanned_from"] == C.action_id(EARLY)
    legacy, legacy_note = P.arms("l1000", frozen_replay=True)["two_step_fallback"](
        ctx, "c", "H1", "H2", executed, menu, 16.0 - E.days(EARLY), SETTING, None)
    assert legacy is None
    assert legacy_note["reason"] == "no_supported_positive_utility_continuation:implementation_defect"


def test_fallback_replanning_uses_the_actual_first_action_and_legal_menu():
    forecasts = {C.action_id(k): forecast(k, absent=0.9, correct=0.02, wrong=0.02) for k in SETTING.keys}
    seen = []

    def conditional(first, label, second):
        seen.append((first, label, second))
        return forecast(second, correct=0.7 if first == LATE and second == OTHER else 0.1, wrong=0.2)

    stale = {"first": EARLY, "followups": {V.ABSENT: LATE}}
    ctx = SimpleNamespace(extra={"sequence_audit_plans": {("H1", "H2", 2, False): (stale, forecasts, conditional)}})
    executed = [{"key": list(LATE), "action": C.action_id(LATE), "outcome": "undetected", "qc": True, "eliminated": []}]
    menu = P.legal_menu(SETTING, executed, 8.0)
    chosen, note = P.contingent(ctx, "c", "H1", "H2", executed, menu, 8.0, SETTING, None, fallback=True)
    assert chosen == OTHER
    assert note["replanned_from"] == C.action_id(LATE)
    assert all(first == LATE and second == OTHER for first, _, second in seen)
    chosen, note = P.contingent(ctx, "c", "H1", "H2", executed, [], 7.0, SETTING, None, fallback=True)
    assert chosen is None


def test_unknown_first_forecast_does_not_become_zero_risk_when_replanning():
    forecasts = {C.action_id(k): refused(k, "no_reference_for_hypothesis:H1") for k in SETTING.keys}

    def conditional(first, label, second):
        raise AssertionError("an unknown first likelihood cannot weight the conditional branches")

    ctx = SimpleNamespace(extra={"sequence_audit_plans": {("H1", "H2", 2, False): (None, forecasts, conditional)}})
    executed = [{"key": list(EARLY), "action": C.action_id(EARLY), "outcome": "undetected", "qc": True, "eliminated": []}]
    key, note = P.contingent(ctx, "c", "H1", "H2", executed, [LATE, OTHER], 10.0, SETTING, None, fallback=True)
    assert key == LATE
    assert note == {"fallback": "fixed_sequence", "planner_refusal": "no_paired_references"}


@pytest.mark.parametrize("correct,wrong,reason", [
    (0.1, 0.3, "wrong_elimination_risk"), (0.0, 0.0, "predicted_non_positive_continuation_utility"),
])
def test_replanning_after_fallback_preserves_informed_stops(correct, wrong, reason):
    forecasts = {C.action_id(k): forecast(k, absent=0.9, correct=0.02, wrong=0.02) for k in SETTING.keys}
    conditional = lambda a, y, b: forecast(b, correct=correct, wrong=wrong, support=100)
    ctx = SimpleNamespace(extra={"sequence_audit_plans": {("H1", "H2", 2, False): (None, forecasts, conditional)}})
    executed = [{"key": list(EARLY), "action": C.action_id(EARLY), "outcome": "undetected", "qc": True, "eliminated": []}]
    key, note = P.contingent(ctx, "c", "H1", "H2", executed, [LATE, OTHER], 10.0, SETTING, None, fallback=True)
    assert key is None
    assert note["reason"] == f"no_supported_positive_utility_continuation:{reason}"


L1000_EPISODES = P.ROOT / "outputs/sequence_audit_20260926/l1000/episodes/episodes.jsonl"


@pytest.mark.skipif(not L1000_EPISODES.exists(), reason="L1000 evaluation not run")
def test_l1000_prepared_data_encode_qc_and_the_records_obey_the_shared_rules():
    import lincs_prepare as LP
    data = LP.load()
    assert all(C.qc_passed(data, i) == bool(q) for i, q in enumerate(data.conditions.qc))
    settings = {name: LP.setting(tier) for name, tier in LP.tiers().items()}
    for line in L1000_EPISODES.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        assert P.audit_record(record, settings[record["tier"]]) == []
        # every step is a real measurement; no L1000 episode compound can fail QC
        assert all(step["qc"] for step in record["steps"])


@pytest.mark.skipif(not L1000_EPISODES.exists(), reason="L1000 evaluation not run")
def test_a_rerun_of_one_l1000_fold_reproduces_the_recorded_episodes():
    import lincs_evaluate as LE
    recorded = [json.loads(line) for line in L1000_EPISODES.read_text(encoding="utf-8").splitlines()]
    recorded = [r for r in recorded if r["tier"] == "T" and r["fold"] == 1]
    _, _, rerun, _, _ = LE.run_fold(("T", 1))
    assert [json.dumps(C.clean(r), sort_keys=True) for r in rerun] == [json.dumps(r, sort_keys=True) for r in recorded]
