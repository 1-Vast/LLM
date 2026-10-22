"""Constructive outcome-free identifiability audit; not a biological simulation."""
import hashlib
import json
from pathlib import Path

import numpy as np
from numpy.polynomial import Polynomial

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification/clock_observability"
SLICES = np.array([2.0, 8.0, 24.0])


def curves():
    base = Polynomial([0.0, 1.0 / 24.0])
    q = Polynomial.fromroots([2.0, 8.0, 24.0, 4.0])
    alternative = base + 0.02 * q / q(12.0)
    return base, alternative


def derivative_min(poly, low=2.0, high=24.0):
    derivative = poly.deriv()
    critical = derivative.deriv().roots()
    points = [low, high] + [float(x.real) for x in critical if abs(x.imag) < 1e-10 and low <= x.real <= high]
    return min(float(derivative(point)) for point in points)


def audit():
    times = np.linspace(2.0, 24.0, 31)
    eta_values = [-1.0, -0.2, 0.0, 0.7]
    z0, velocity = np.array([0.2, 0.7]), np.array([0.02, -0.01])
    linear_errors = []
    power_errors = []
    for eta in eta_values:
        scale = np.exp(eta)
        warped = z0 + times[:, None] * scale * velocity
        amplitude = z0 + scale * ((z0 + times[:, None] * velocity) - z0)
        linear_errors.append(float(np.max(np.abs(warped - amplitude))))
        for power in (0.5, 1.0, 2.0, 3.0):
            warped_power = 0.3 + 0.4 * (times * scale) ** power
            amplitude_power = 0.3 + 0.4 * np.exp(power * eta) * times ** power
            power_errors.append(float(np.max(np.abs(warped_power - amplitude_power))))

    x = SLICES / 24.0
    single_amplitude = x ** 2
    single_clock = 2.0 * single_amplitude
    # Flatten output1 followed by output2. Clock of powers1/2 can be
    # distinguished from one shared amplitude, but not separate amplitudes.
    output1, output2 = x, x ** 2
    joint_clock = np.concatenate([output1, 2.0 * output2])
    shared_amp = np.concatenate([output1, output2])
    separate_amps = np.column_stack([np.concatenate([output1, np.zeros(3)]), np.concatenate([np.zeros(3), output2])])

    base, alternative = curves()
    results = {
        "source": "analytic_constructed_counterexamples_no_real_responses",
        "linear_clock_amplitude_max_error": max(linear_errors),
        "power_clock_amplitude_max_error": max(power_errors),
        "single_power_clock_amplitude_rank": int(np.linalg.matrix_rank(np.column_stack([single_clock, single_amplitude]))),
        "different_powers_common_amplitude_rank": int(np.linalg.matrix_rank(np.column_stack([joint_clock, shared_amp]))),
        "different_powers_separate_amplitudes_rank": int(np.linalg.matrix_rank(separate_amps)),
        "different_powers_separate_amplitudes_with_clock_rank": int(np.linalg.matrix_rank(np.column_stack([separate_amps, joint_clock]))),
        "slices_h": SLICES.tolist(),
        "base_slice_values": base(SLICES).tolist(),
        "alternative_slice_values": alternative(SLICES).tolist(),
        "base_slice_derivatives": base.deriv()(SLICES).tolist(),
        "alternative_slice_derivatives": alternative.deriv()(SLICES).tolist(),
        "warp_scale": 0.5,
        "paid_support_h": 8.0,
        "paid_warped_time_h": 4.0,
        "base_paid_forecast": float(base(4.0)),
        "alternative_paid_forecast": float(alternative(4.0)),
        "withheld_h": 24.0,
        "withheld_warped_time_h": 12.0,
        "base_withheld_forecast": float(base(12.0)),
        "alternative_withheld_forecast": float(alternative(12.0)),
        "base_min_derivative_2_to_24": derivative_min(base),
        "alternative_min_derivative_2_to_24": derivative_min(alternative),
        "interpretation": "nonparametric_identifiability_fails_not_a_test_of_fixed_bias_predictive_value",
    }
    return results


if __name__ == "__main__":
    result_path = OUT / "RESULT.json"
    if result_path.exists():
        raise FileExistsError(result_path)
    results = audit()
    sources = [Path(__file__), Path(__file__).with_name("test_audit.py"), OUT / "PROTOCOL.md"]
    results["input_sha256"] = {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    result_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False))
