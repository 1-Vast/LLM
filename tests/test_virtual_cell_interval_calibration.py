"""Interval calibration: quantile math, binding refusals, reproducible fit.

File summary
- Path: tests/test_virtual_cell_interval_calibration.py
- Purpose: pin the interval-calibration asset that lets a STATE readout carry a
  coverage-claiming band.
- Core points: assertions here are contract tests, not biological results; the
  pairs are synthetic, so nothing here measures the checkpoint's accuracy.
- Interfaces: `test_conformal_quantile_takes_the_level_index_of_the_sample()`,
  `test_fit_interval_reproduces_its_quantiles_and_support()`,
  `test_interval_calibration_refuses_a_different_binding()`.
- Depends on: virtual_cell
"""
from dataclasses import replace

from virtual_cell.calibration import IntervalCalibration, ResidualPair, conformal_quantile, fit_interval


def _pairs(readout: str, count: int, *, offset: float = 0.0) -> tuple[ResidualPair, ...]:
    return tuple(
        ResidualPair(readout, float(index), float(index) + 1.0 + offset) for index in range(count)
    )


def test_conformal_quantile_takes_the_level_index_of_the_sample():
    # With n residuals the index is ceil((n + 1) * level): the level is a
    # marginal guarantee of at least level under exchangeability, not an exact
    # equality, and that correction is what makes the number auditable rather
    # than nominal.
    assert conformal_quantile(range(10), 0.9) == 9.0
    assert conformal_quantile(range(20), 0.9) == 18.0
    assert conformal_quantile(range(10), 0.5) == 5.0


def test_conformal_quantile_refuses_a_sample_that_cannot_support_the_level():
    # At 0.90 the order statistic is ceil((n + 1) * 0.9); for n <= 8 it lies
    # beyond the sample, and the old behaviour clamped it to the largest
    # residual while still claiming nominal coverage. A finite interval cannot
    # claim 0.90 from fewer than 9 residuals, so it refuses by name.
    for count in (1, 2, 8):
        try:
            conformal_quantile(range(count), 0.9)
        except ValueError as error:
            assert "no finite interval can claim this coverage" in str(error)
            assert f"at least 9" in str(error)
        else:
            raise AssertionError(f"{count} residuals must not yield a nominal-0.90 quantile")
    # The boundary itself: 9 residuals is exactly enough, and the quantile is
    # the largest residual.
    assert conformal_quantile(range(9), 0.9) == 8.0


def test_conformal_quantile_refuses_empty_nonfinite_and_invalid_input():
    for values, level, message in (
        ((), 0.9, "at least one residual"),
        ([1.0, float("nan")], 0.9, "finite residuals"),
        ([1.0, float("inf")], 0.9, "finite residuals"),
        ([1.0], 1.0, "strictly between 0 and 1"),
        ([1.0], 0.0, "strictly between 0 and 1"),
        ([1.0], -0.5, "strictly between 0 and 1"),
    ):
        try:
            conformal_quantile(values, level)
        except ValueError as error:
            assert message in str(error), (values, level)
        else:
            raise AssertionError(f"{values} at {level} must be refused")


def test_fit_interval_names_the_readout_that_cannot_support_the_level():
    # Support is checked per readout: a thick readout never lends its sample
    # to a thin one, and the whole fit refuses rather than clamp one quantile.
    pairs = _pairs("thick", 48) + _pairs("thin", 8)
    try:
        fit_interval(
            pairs,
            endpoint="x_hvg_perturbation_shift",
            context_identifier="NCI-H596",
            fitted_on="synthetic",
            independent_units=56,
        )
    except ValueError as error:
        assert "'thin'" in str(error)
        assert "nominal 0.9" in str(error)
    else:
        raise AssertionError("a readout with 8 residuals must not yield a nominal-0.90 quantile")


def test_fit_interval_reproduces_its_quantiles_and_support():
    calibration = fit_interval(
        _pairs("embedding_delta_l2", 48),
        endpoint="x_hvg_perturbation_shift",
        context_identifier="NCI-H596",
        fitted_on="synthetic calibration partition",
        independent_units=48,
    )
    assert calibration.level == 0.9
    # 48 identical unit residuals: the quantile is that residual, however thin.
    assert calibration.quantiles == {"embedding_delta_l2": 1.0}
    assert calibration.support == {"embedding_delta_l2": 48}
    assert calibration.readouts == ("embedding_delta_l2",)
    assert calibration.half_width("embedding_delta_l2") == 1.0
    assert calibration.half_width("never_fitted") is None

    repeated = fit_interval(
        _pairs("embedding_delta_l2", 48),
        endpoint="x_hvg_perturbation_shift",
        context_identifier="NCI-H596",
        fitted_on="synthetic calibration partition",
        independent_units=48,
    )
    assert repeated == calibration


def test_fit_interval_reports_the_residual_it_was_fitted_on_and_declines_empty_input():
    calibration = fit_interval(
        (
            ResidualPair("r", 0.0, 1.0),
            ResidualPair("r", 0.0, 5.0),
            ResidualPair("other", 0.0, 2.0),
        ),
        endpoint="e",
        context_identifier="c",
        fitted_on="synthetic",
        independent_units=3,
        level=0.5,
    )
    assert calibration.quantiles == {"r": 5.0, "other": 2.0}
    assert calibration.support == {"r": 2, "other": 1}
    try:
        fit_interval((), endpoint="e", context_identifier="c", fitted_on="synthetic", independent_units=0)
    except ValueError as error:
        assert "at least one paired observation" in str(error)
    else:
        raise AssertionError("an empty pair set must not produce a calibration")


def test_interval_calibration_refuses_a_different_binding():
    calibration = fit_interval(
        _pairs("embedding_delta_l2", 10),
        endpoint="x_hvg_perturbation_shift",
        context_identifier="NCI-H596",
        fitted_on="synthetic",
        independent_units=10,
        model_version="state_generalization_zeroshot_X_hvg",
        input_schema="X_hvg:2000",
        control_protocol="seed=42",
        development_partition_sha256="ebb40bf3",
    )
    matched = dict(
        endpoint="x_hvg_perturbation_shift",
        context_identifier="NCI-H596",
        model_version="state_generalization_zeroshot_X_hvg",
        input_schema="X_hvg:2000",
        control_protocol="seed=42",
        development_partition_sha256="ebb40bf3",
    )
    assert calibration.binding_mismatches(**matched) == ()
    assert calibration.applies_to(**matched)

    for field, wrong, expected in (
        ("endpoint", "another_endpoint", "endpoint_mismatch"),
        ("context_identifier", "another-context", "context_mismatch"),
        ("model_version", "another_checkpoint", "model_version_mismatch"),
        ("input_schema", "X_hvg:1000", "input_schema_mismatch"),
        ("control_protocol", "seed=7", "control_protocol_mismatch"),
        ("development_partition_sha256", "another-partition", "development_partition_sha256_mismatch"),
    ):
        offered = dict(matched, **{field: wrong})
        assert calibration.binding_mismatches(**offered) == (expected,), field
        assert not calibration.applies_to(**offered)

    # A declared binding the query does not state is a mismatch, not a free pass.
    unstated = dict(matched, model_version=None)
    assert calibration.binding_mismatches(**unstated) == ("model_version_unstated",)

    # An undeclared binding is not checked: a calibration that never named a
    # partition does not refuse a query that names one.
    undeclared = replace(calibration, development_partition_sha256=None)
    assert undeclared.binding_mismatches(**matched) == ()
