"""JSON admission tests for reviewed biological rules and authentic QC values.

File summary
- Path: tests/test_biological_closure_cli.py
- Purpose: Ensure the CLI preserves typed evidence requirements and rejects coercive QC/count inputs.
- Core points: constructed inputs only; no provider or biological experiment is executed.
- Interfaces: test_* functions
- Depends on: agent.cli, maestro.models, maestro.outcome
"""
import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from agent import cli
from maestro.models import BiologicalQuantity, EvidenceActionKind, EvidenceScope, MeasurementStatus, PremiseRequirement
from maestro.outcome import OutcomeRule


@pytest.fixture
def rule_data():
    return {
        "identifier": "reviewed_activity",
        "outcome_label": "activity_sufficient",
        "matched_fields": ["functional:target_activity:sufficient"],
    }


@pytest.fixture
def result_data():
    return {
        "statement": "Measured proximal activity.",
        "source_id": "assay-source",
        "quality_passed": True,
        "independent_units": 3,
        "record_count": 12,
        "biological_replicates": 2,
    }


def test_rules_json_round_trip_preserves_biological_constraints(rule_data):
    requirement = {
        "field": "functional:target_activity:sufficient",
        "quantity": "proximal_activity",
        "entity": "TARGET",
        "site": "S123",
        "units": "percent",
        "context_identifier": "cell-context",
        "time_hours": 6.5,
        "time_tolerance_hours": 0.25,
        "require_direct_measurement": True,
        "note": "Require a direct activity assay.",
    }
    prior_requirement = {
        "field": "abundance:target:measured",
        "quantity": "protein_abundance",
        "entity": "TARGET",
        "site": None,
        "units": None,
        "context_identifier": "cell-context",
        "time_hours": None,
        "time_tolerance_hours": None,
        "require_direct_measurement": False,
        "note": "Reviewed prior evidence.",
    }
    rule_data.update(
        forbidden_fields=["functional:target_activity:insufficient"],
        required_prefixes=["functional:"],
        eliminates=["incomplete"],
        scope="mechanism_contrast",
        action_identifier="activity-assay",
        required_conditions=["dose", "sample"],
        requires_time_match=True,
        boundary="Only the registered context is supported.",
        allowed_action_kinds=["functional_measurement", "orthogonal_control"],
        field_requirements=[requirement],
        evidence_requirements=[prior_requirement],
        matched_condition_keys=["dose", "sample"],
        minimum_independent_units=3,
        metric_bounds={"activity": [0.2, 0.8], "coverage": [1, None], "error": [None, 0.1]},
    )
    expected = OutcomeRule(
        identifier="reviewed_activity",
        outcome_label="activity_sufficient",
        matched_fields=frozenset({requirement["field"]}),
        forbidden_fields=frozenset({"functional:target_activity:insufficient"}),
        required_prefixes=frozenset({"functional:"}),
        eliminates=frozenset({"incomplete"}),
        scope=EvidenceScope.MECHANISM_CONTRAST,
        action_identifier="activity-assay",
        required_conditions=frozenset({"dose", "sample"}),
        requires_time_match=True,
        boundary="Only the registered context is supported.",
        allowed_action_kinds=frozenset({EvidenceActionKind.FUNCTIONAL_MEASUREMENT, EvidenceActionKind.ORTHOGONAL_CONTROL}),
        field_requirements=(PremiseRequirement(**{**requirement, "quantity": BiologicalQuantity.PROXIMAL_ACTIVITY}),),
        evidence_requirements=(PremiseRequirement(**{**prior_requirement, "quantity": BiologicalQuantity.PROTEIN_ABUNDANCE}),),
        matched_condition_keys=("dose", "sample"),
        minimum_independent_units=3,
        metric_bounds={"activity": (0.2, 0.8), "coverage": (1.0, None), "error": (None, 0.1)},
    )

    rules = cli._rules(json.loads(json.dumps([rule_data])))
    assert rules == (expected,)
    assert rules[0].field_requirements[0].quantity is BiologicalQuantity.PROXIMAL_ACTIVITY
    assert all(isinstance(kind, EvidenceActionKind) for kind in rules[0].allowed_action_kinds)
    assert all(isinstance(bounds, tuple) for bounds in rules[0].metric_bounds.values())
    assert cli._rules(json.loads(json.dumps(rules, default=cli._json_default))) == rules


def test_rules_defaults_preserve_optional_requirement_fields(rule_data):
    field = rule_data["matched_fields"][0]
    rule_data["field_requirements"] = [{"field": field}]
    rule = cli._rules([rule_data])[0]

    assert rule.field_requirements == (PremiseRequirement(field=field),)
    assert rule.field_requirements[0].units is None
    assert rule.field_requirements[0].require_direct_measurement is True
    assert rule.allowed_action_kinds == frozenset()
    assert rule.evidence_requirements == ()
    assert rule.matched_condition_keys == ()
    assert rule.minimum_independent_units == 1
    assert rule.metric_bounds == {}
    assert rule.requires_time_match is False


@pytest.mark.parametrize("key", ["field_requirements", "evidence_requirements"])
def test_rules_reject_unknown_quantity(rule_data, key):
    rule_data[key] = [{"field": rule_data["matched_fields"][0], "quantity": "unknown_quantity"}]
    with pytest.raises(ValueError, match="unknown_quantity"):
        cli._rules([rule_data])


def test_action_rejects_unknown_quantity():
    with pytest.raises(ValueError, match="unknown_quantity"):
        cli._action({
            "identifier": "assay",
            "description": "Measure activity.",
            "cost": 1,
            "distinguishes": [],
            "quantity": "unknown_quantity",
        })


def test_rules_reject_unknown_action_kind(rule_data):
    rule_data["allowed_action_kinds"] = ["unknown_assay"]
    with pytest.raises(ValueError, match="unknown_assay"):
        cli._rules([rule_data])


@pytest.mark.parametrize("key", ["field_requirements", "evidence_requirements"])
def test_rules_reject_non_object_requirement(rule_data, key):
    rule_data[key] = ["activity"]
    with pytest.raises(ValueError, match="requirement must be an object"):
        cli._rules([rule_data])


@pytest.mark.parametrize("bad_bool", ["false", "true", 0, 1, None, [], {}])
@pytest.mark.parametrize("key", ["requires_time_match", "field_requirements", "evidence_requirements"])
def test_rules_reject_non_boolean_flags(rule_data, key, bad_bool):
    if key == "requires_time_match":
        rule_data[key] = bad_bool
    else:
        rule_data[key] = [{"field": rule_data["matched_fields"][0], "require_direct_measurement": bad_bool}]
    with pytest.raises(ValueError, match="JSON boolean"):
        cli._rules([rule_data])


@pytest.mark.parametrize("bad_count", [1.5, 1.0, True, False, "3", 0, -1, None, [], {}])
def test_rules_reject_non_positive_integer_minimum(rule_data, bad_count):
    rule_data["minimum_independent_units"] = bad_count
    with pytest.raises(ValueError, match="minimum_independent_units"):
        cli._rules([rule_data])


@pytest.mark.parametrize("bad_bounds", [None, [], {"activity": [0]}, {"activity": [0, 1, 2]}, {"activity": "01"}, {"activity": [False, 1]}, {"activity": ["0", 1]}])
def test_rules_reject_malformed_metric_bounds(rule_data, bad_bounds):
    rule_data["metric_bounds"] = bad_bounds
    with pytest.raises(ValueError, match="[Mm]etric"):
        cli._rules([rule_data])


@pytest.mark.parametrize("quality_passed", [True, False])
def test_results_preserve_positive_and_negative_qc(result_data, quality_passed):
    result_data["quality_passed"] = quality_passed
    result = cli._results(json.loads(json.dumps({"assay": result_data})))["assay"]
    assert result.quality_passed is quality_passed
    assert result.independent_units == 3
    assert result.record_count == 12
    assert result.biological_replicates == 2


@pytest.mark.parametrize("bad_bool", ["false", "true", 0, 1, None, [], {}])
def test_results_reject_non_boolean_qc(result_data, bad_bool):
    result_data["quality_passed"] = bad_bool
    with pytest.raises(ValueError, match="quality_passed.*JSON boolean"):
        cli._results({"assay": result_data})


@pytest.mark.parametrize("key", ["independent_units", "record_count", "biological_replicates"])
@pytest.mark.parametrize("bad_count", [1.5, 1.0, True, False, "3", 0, -1, [], {}])
def test_results_reject_non_positive_integer_counts(result_data, key, bad_count):
    result_data[key] = bad_count
    with pytest.raises(ValueError, match=key + ".*positive integer"):
        cli._results({"assay": result_data})


@pytest.mark.parametrize("units", [None, 1, 7])
@pytest.mark.parametrize("replicates", [None, 1, 4])
def test_results_preserve_valid_counts_and_explicit_none(result_data, units, replicates):
    result_data.update(independent_units=units, biological_replicates=replicates)
    result = cli._results({"assay": result_data})["assay"]
    assert result.independent_units == units
    assert type(result.independent_units) is type(units)
    assert result.biological_replicates == replicates
    assert type(result.biological_replicates) is type(replicates)
    assert result.record_count == 12


def test_results_keep_omitted_units_unknown(result_data):
    result_data.pop("independent_units")
    result_data.pop("biological_replicates")
    result_data.pop("record_count")
    result = cli._results({"assay": result_data})["assay"]
    assert result.independent_units is None
    assert result.biological_replicates is None
    assert result.record_count == 1


def test_results_reject_null_record_count(result_data):
    result_data["record_count"] = None
    with pytest.raises(ValueError, match="record_count.*positive integer"):
        cli._results({"assay": result_data})


@pytest.fixture
def mocked_main(monkeypatch):
    profile_data = {"mode": "inhibition"}
    inputs = {"actions.json": [], "profile.json": profile_data}
    monkeypatch.setattr(cli, "_read_json", lambda path: inputs[path.name])
    monkeypatch.setattr(sys, "argv", [
        "maestro", "Assess the measurement.",
        "--actions", "actions.json", "--profile", "profile.json", "--virtual-cell", "none",
    ])
    backend = Mock(return_value=None)
    monkeypatch.setattr(cli, "_virtual_cell", backend)
    controller = Mock()
    controller.run.return_value = SimpleNamespace(response="Reviewed.", session_id="test-session")
    factory = Mock(return_value=controller)
    monkeypatch.setattr(cli, "MAESTROOrchestrator", SimpleNamespace(from_workspace=factory))
    return profile_data, controller, factory


def test_main_maps_measured_fields_to_existing_status_enum(mocked_main):
    profile_data, controller, factory = mocked_main
    profile_data["measured_fields"] = {
        "abundance:target": "measured",
        "activity:estimate": "estimated",
        "engagement:unknown": "unknown",
    }
    assert cli.main() == 0
    profile = controller.run.call_args.kwargs["intervention_profile"]
    for name, value in profile_data["measured_fields"].items():
        assert profile.measured_fields[name] is MeasurementStatus(value)
        assert profile.measurement_status(name) is MeasurementStatus(value)
    assert factory.call_args.kwargs["enable_virtual_cell"] is False
    controller.run.assert_called_once()


def test_main_defaults_measured_fields_to_empty(mocked_main):
    _, controller, _ = mocked_main
    assert cli.main() == 0
    assert controller.run.call_args.kwargs["intervention_profile"].measured_fields == {}


def test_main_rejects_unknown_measurement_status(mocked_main):
    profile_data, controller, factory = mocked_main
    profile_data["measured_fields"] = {"abundance:target": "unsupported"}
    with pytest.raises(ValueError, match="unsupported"):
        cli.main()
    factory.assert_not_called()
    controller.run.assert_not_called()
