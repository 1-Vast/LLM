"""Scientific input contracts: effect scales, independent replicates and contexts."""
from dataclasses import replace

import pytest

from maestro.problem_compiler import MeasurementRecord, compile_problem


def _row(record_id="r1", gene="EGR1", value=2.0, **kwargs):
    return MeasurementRecord(record_id, gene, value, "treated", **kwargs)


def _compile(rows, **kwargs):
    return compile_problem("problem", "What next?", rows,
                           assay_hint="transcriptomic_profile", **kwargs)


def _codes(compiled):
    return {d.code for d in compiled.diagnostics}


@pytest.mark.parametrize("kind", ["raw_counts", "normalized_expression", "expression_z_score"])
def test_expression_cannot_be_interpreted_as_signed_response(kind):
    compiled = _compile([_row(value=120.0, value_kind=kind)])
    assert not compiled.usable
    assert "unsupported:value_kind" in _codes(compiled)
    assert compiled.directional_state.signed_feature_delta == {}
    assert compiled.candidate_actions == ()


@pytest.mark.parametrize("kind", ["signed_effect", "log_fold_change", "differential_z_score"])
def test_signed_effects_remain_compatible(kind):
    compiled = _compile([_row(value=-2.0, value_kind=kind)])
    assert compiled.usable
    assert compiled.directional_state.signed_feature_delta == {"EGR1": -2.0}


def test_gene_rows_and_group_labels_are_not_independent_replicates():
    compiled = _compile([_row(replicate_group="group1"),
                         _row("r2", "FOS", replicate_group="group1")])
    assert compiled.replicates is None
    assert "thin:replicates" in _codes(compiled)


def test_biological_replicates_are_aggregated_without_last_row_overwrite():
    rows = [_row(biological_replicate_id="bio1", value=-4.0),
            _row("r2", biological_replicate_id="bio2", value=2.0),
            _row("r3", "FOS", biological_replicate_id="bio1", value=5.0),
            _row("r4", "FOS", biological_replicate_id="bio2", value=7.0)]
    compiled = _compile(rows)
    assert compiled.usable
    assert compiled.replicates == 2
    assert compiled.directional_state.signed_feature_delta == {"EGR1": -1.0, "FOS": 6.0}
    assert _compile(rows[::-1]).directional_state == compiled.directional_state


def test_sparse_replication_reports_minimum_feature_support():
    compiled = _compile([_row(biological_replicate_id="bio1"),
                         _row("r2", biological_replicate_id="bio2"),
                         _row("r3", "FOS", biological_replicate_id="bio1")])
    assert compiled.replicates == 1
    assert compiled.context["replicates_per_feature"] == {"EGR1": 2, "FOS": 1}


@pytest.mark.parametrize("replicate", [None, "bio1"])
def test_duplicate_feature_replicate_is_refused(replicate):
    compiled = _compile([_row(biological_replicate_id=replicate),
                         _row("r2", value=-5.0, biological_replicate_id=replicate)])
    assert not compiled.usable
    assert "ambiguous:feature_replicate" in _codes(compiled)
    assert compiled.directional_state.signed_feature_delta == {}


def test_duplicate_record_ids_are_refused():
    compiled = _compile([_row(), _row(gene="FOS")])
    assert not compiled.usable
    assert "duplicate:record_id" in _codes(compiled)


def test_multiple_conditions_require_explicit_selection():
    rows = [_row(), replace(_row("r2", value=-2.0), condition="other")]
    assert "ambiguous:condition" in _codes(_compile(rows))
    selected = _compile(rows, condition="other")
    assert selected.usable
    assert selected.directional_state.signed_feature_delta == {"EGR1": -2.0}
    assert "invalid:condition" in _codes(_compile(rows, condition="absent"))


@pytest.mark.parametrize("changes", [dict(cell_line="K562"),
                                    dict(time_value=48.0, time_unit="h"),
                                    dict(dose_value=1.0, dose_unit="uM")])
def test_a_reused_condition_name_cannot_hide_multiple_contexts(changes):
    first = _row(cell_line="A549", time_value=24.0, time_unit="h",
                 dose_value=10.0, dose_unit="uM")
    second = replace(first, record_id="r2", feature="FOS", **changes)
    compiled = _compile([first, second])
    assert not compiled.usable
    assert "ambiguous:experimental_context" in _codes(compiled)


def test_control_dose_does_not_replace_treated_dose():
    first = _row(time_value=24.0, time_unit="h", dose_value=10.0, dose_unit="uM")
    control = replace(first, record_id="ctrl", condition="vehicle", is_control=True,
                      dose_value=0.0)
    compiled = _compile([first, control])
    assert compiled.usable
    assert compiled.dose_nM == 10000.0


def test_incompatible_effect_scales_are_not_averaged():
    compiled = _compile([_row(value_kind="log_fold_change"),
                         _row("r2", "FOS", value_kind="differential_z_score")])
    assert not compiled.usable
    assert "mixed:effect_scales" in _codes(compiled)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "3"])
def test_invalid_effects_are_reported_before_state_construction(value):
    compiled = _compile([_row(value=value)])
    assert not compiled.usable
    assert "invalid:measurement_value" in _codes(compiled)


@pytest.mark.parametrize("changes", [dict(time_value=-1, time_unit="h"),
                                    dict(dose_value=float("inf"), dose_unit="uM"),
                                    dict(time_value=1, time_unit="unknown")])
def test_invalid_conditions_block_compilation(changes):
    compiled = _compile([_row(**changes)])
    assert not compiled.usable
