"""Mathematical invariants; no real assay values or implementation snapshots."""
import numpy as np

from audit import SLICES, audit, curves, derivative_min


def test_arbitrary_scale_linear_and_power_equivalence():
    result = audit()
    assert result["linear_clock_amplitude_max_error"] < 1e-12
    assert result["power_clock_amplitude_max_error"] < 1e-9


def test_amplitude_restriction_changes_identifiability():
    result = audit()
    assert result["single_power_clock_amplitude_rank"] == 1
    assert result["different_powers_common_amplitude_rank"] == 2
    assert result["different_powers_separate_amplitudes_rank"] == 2
    assert result["different_powers_separate_amplitudes_with_clock_rank"] == 2


def test_same_observed_slices_do_not_determine_derivatives():
    base, alternative = curves()
    np.testing.assert_allclose(base(SLICES), alternative(SLICES), atol=1e-12)
    assert np.all(np.abs(base.deriv()(SLICES) - alternative.deriv()(SLICES)) > 1e-4)


def test_same_paid_support_can_leave_different_withheld_forecast():
    base, alternative = curves()
    assert abs(base(8 * 0.5) - alternative(8 * 0.5)) < 1e-12
    assert abs(alternative(24 * 0.5) - base(24 * 0.5) - 0.02) < 1e-12


def test_counterexample_remains_monotonic_on_whole_observed_interval():
    base, alternative = curves()
    assert derivative_min(base) > 0
    assert derivative_min(alternative) > 0
    assert abs(alternative(2) - base(2)) < 1e-12
    assert abs(alternative(24) - base(24)) < 1e-12
