"""Invariants of the prediction-to-measurement evaluation harness.

File summary
- Path: research/acquisition_link/test_acquisition_link.py
- Purpose: pin what the evaluation's conclusions rest on.
  - What each forecast label removes equals what `common.evidence_update` removes when the same
    reading arrives as a real result.
  - The SciPlex3 forecaster keeps every branch whole: four labels, support equal to the
    reference count, no reduction to one number.
  - Zero references refuse by name; the registered two-reference rule refuses one reference;
    the repaired rule serves it as low support.
  - The forecaster satisfies the runtime protocol, so the orchestrator can use it unchanged.
  - A rerun of one fold reproduces the recorded episodes and menu rows exactly.
- Run: python -m pytest -q research/acquisition_link/test_acquisition_link.py
  (outside the repository suite: `testpaths = ["tests"]`; the data tests need the prepared run)
- Depends on: evaluate.py, research/dynamic_world_model (common, episodes), maestro
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import evaluate as V  # noqa: E402

import common as C  # noqa: E402
import episodes as E  # noqa: E402

from maestro.acquisition import outcome_consequences, select_discriminating_action  # noqa: E402
from maestro.outcome import EvidenceState  # noqa: E402

HAVE_DATA = (C.PREPARED / "conditions.csv").is_file()
LABEL_OF = {"eliminate_b": "profile_matches_h1", "eliminate_a": "profile_matches_h2",
            "ambiguous": "profile_unresolved", "undetected": "no_detectable_response"}


def test_forecast_consequences_match_what_the_evidence_path_removes():
    key = ("A549", 24.0, 10000.0)
    action = E.make_action(key, "A", "B")
    contrast = E.contrast_for("A", "B", [action])
    consequences = outcome_consequences(V.registered_rules("A", "B"))
    for outcome, label in LABEL_OF.items():
        state = EvidenceState.open(contrast.hypotheses)
        state, _, _ = C.evidence_update(state, contrast, action, key, {"outcome": outcome, "score_a": 0.5, "score_b": 0.1},
                                        "A", "B", qc=True, agreement=0.9, source="test")
        assert state.eliminated == consequences[label], outcome


@pytest.fixture(scope="module")
def fold_a():
    protocol = C.load_protocol()
    data = C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    magnitude = E.Magnitude(data, detected)
    ctx, fold = next(E.contexts(data, protocol, detected, magnitude, tier_names=("A",), folds=(1,)))
    return ctx


@pytest.mark.skipif(not HAVE_DATA, reason="needs the prepared SciPlex3 run")
def test_branches_stay_whole_and_support_rules_differ_only_at_one_reference(fold_a):
    ctx = fold_a
    seen = {"served": 0, "one_reference": 0, "zero": 0}
    for key, table in ctx.ft.tables.items():
        classes = sorted({k for k in table.klass if k in ctx.tier.pool})
        for h1 in classes:
            for h2 in classes:
                if h1 >= h2:
                    continue
                repaired = V.ReferenceCardForecaster(ctx.ft, ctx.params, minimum_references=1).forecast_key(key, h1, h2)
                registered = V.ReferenceCardForecaster(ctx.ft, ctx.params, minimum_references=2).forecast_key(key, h1, h2)
                counts = {h: sum(1 for k in table.klass if k == h) for h in (h1, h2)}
                if min(counts.values()) == 0:
                    seen["zero"] += 1
                    assert repaired.refusal.startswith("no_reference_for_hypothesis:")
                    continue
                assert repaired.refusal is None
                seen["served"] += 1
                for branch in repaired.branches:
                    assert branch.support == counts[branch.hypothesis]
                    assert set(branch.probabilities) == set(LABEL_OF.values())
                    assert abs(sum(branch.probabilities.values()) - 1.0) < 1e-9
                if min(counts.values()) == 1:
                    seen["one_reference"] += 1
                    assert registered.refusal.startswith("too_few_references_at_condition:")
                else:
                    assert registered == V.OutcomeForecast(repaired.action_identifier, repaired.branches, registered.basis,
                                                           model_version="sciplex3_reference_cards_v2")
    assert seen["served"] and seen["one_reference"], seen


@pytest.mark.skipif(not HAVE_DATA, reason="needs the prepared SciPlex3 run")
def test_the_forecaster_satisfies_the_runtime_protocol(fold_a):
    ctx = fold_a
    h1, h2 = ctx.tier.pool[:2]
    actions = [E.make_action(key, h1, h2) for key in ctx.tier.keys]
    contrast = E.contrast_for(h1, h2, actions)
    forecaster = V.ReferenceCardForecaster(ctx.ft, ctx.params)
    forecasts = forecaster.forecast(contrast, actions, None)
    assert set(forecasts) == {action.identifier for action in actions}
    plan = select_discriminating_action(frozenset({h1, h2}), actions, E.PROFILE, E.STEP_BUDGET_DAYS, forecasts,
                                        outcome_consequences(V.registered_rules(h1, h2)))
    assert {item.action_identifier for item in plan.evaluations} == set(forecasts)
    assert plan.status in {"selected", "no_admissible_action"}


@pytest.mark.skipif(not (V.OUT / "episodes" / "episodes.jsonl").is_file(), reason="needs the recorded run")
def test_a_rerun_of_one_fold_reproduces_the_recorded_episodes_and_menu_rows():
    import pandas as pd

    recorded = [json.loads(line) for line in (V.OUT / "episodes" / "episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    recorded = [r for r in recorded if r["tier"] == "A" and r["fold"] == 1]
    rerun, audit, _ = V.run_fold(("A", 1))
    # TV is a diagnostic sum whose last bit differs across Python runtimes;
    # decisions, forecast scores and every other field must still match exactly.
    def strip(record):
        cleaned = C.clean(record)
        values = []
        for step in cleaned["steps"]:
            chosen = step.get("note", {}).get("chosen")
            if chosen is not None:
                values.append(chosen.pop("total_variation", None))
        return json.dumps(cleaned, default=C._default, sort_keys=True), values

    actual, expected = [strip(r) for r in rerun], [strip(r) for r in recorded]
    for (record, tv), (reference, reference_tv) in zip(actual, expected, strict=True):
        assert record == reference
        assert tv == pytest.approx(reference_tv, rel=0, abs=1e-14)
    menu = pd.read_csv(V.OUT / "episodes" / "menu_audit.csv")
    menu = menu[(menu.tier == "A") & (menu.fold == 1)].reset_index(drop=True)
    again = pd.DataFrame(audit)
    assert len(again) == len(menu)
    assert (again.action.to_numpy() == menu.action.to_numpy()).all()
    assert (again.reason.to_numpy() == menu.reason.to_numpy()).all()
    assert (again.realised.fillna("").to_numpy() == menu.realised.fillna("").to_numpy()).all()
    assert abs(again.p_correct.fillna(-1).to_numpy() - menu.p_correct.fillna(-1).to_numpy()).max() < 1e-12
