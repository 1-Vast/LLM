"""Synthetic statistical counterexamples; no biological data or model fits.

Reads no project data. The examples audit logical claims, not effect sizes.
Run with the existing maestro Python environment. Output is written beside this file.
"""
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm, rankdata


def rho(x, y):
    a = rankdata(x)
    b = rankdata(y)
    a -= a.mean()
    b -= b.mean()
    return float(a @ b / math.sqrt(float(a @ a) * float(b @ b)))


def main():
    rng = np.random.default_rng(20261027)
    z80 = norm.ppf(0.975) + norm.ppf(0.8)
    n, reps = 600, 3000
    y = rng.normal(size=n)
    fixed_z = rng.normal(size=n)
    fixed_units, fixed_predictor, redraw_and_boot = [], [], []
    for _ in range(reps):
        z = rng.normal(size=n)
        ii = rng.integers(0, n, size=n)
        fixed_units.append(rho(z, y))
        fixed_predictor.append(rho(fixed_z[ii], y[ii]))
        redraw_and_boot.append(rho(z[ii], y[ii]))
    ses = {k: float(np.std(v, ddof=1)) for k, v in {
        "redraw_z_fixed_units": fixed_units,
        "fixed_z_bootstrap_units": fixed_predictor,
        "redraw_z_and_bootstrap_units": redraw_and_boot,
    }.items()}
    paired = []
    for correlation in (0.0, 0.9, 0.99):
        se = 0.1 * math.sqrt(2 * (1 - correlation))
        paired.append({"single_arm_se": 0.1, "correlation": correlation,
                       "contrast_se": se, "contrast_mde80": z80 * se})

    # PB's c=delta/rho_pm becomes c=delta with one observation per pair.
    # Even here it does not set Spearman's population correlation to delta.
    target = 0.1183
    calibration = []
    for distribution in ("normal", "lognormal_sigma3"):
        signal = rng.normal(size=200000)
        if distribution == "lognormal_sigma3":
            signal = np.exp(3 * signal)
        standardized = (signal - signal.mean()) / signal.std()
        pred = target * standardized + math.sqrt(1 - target ** 2) * rng.normal(size=signal.size)
        calibration.append({"synthetic_signal_distribution": distribution,
                            "target_parameter": target,
                            "realized_spearman": rho(pred, signal),
                            "n": int(signal.size)})

    # Illustrate the shared-main-arm dependence omitted by a product of powers.
    s = 0.075 / z80
    true = 0.1183
    size = 500000
    estimate = true + rng.normal(scale=s, size=size)
    c1 = rng.normal(scale=s, size=size)
    c2 = rng.normal(scale=s, size=size)
    r1 = estimate >= 0.0947
    r2 = estimate > 1.96 * s
    dthreshold = 1.96 * math.sqrt(2) * s
    cavg = rng.normal(scale=s / math.sqrt(10), size=size)
    average_threshold = 1.96 * math.sqrt(s * s + s * s / 10)
    joint = {
        "assumptions": "synthetic independent normal control estimates; main estimate shared by all rules",
        "mde80": 0.075, "main_se": s, "rho_true": true, "draws": size,
        "point_threshold_pass_probability": float(r1.mean()),
        "two_control_joint_pass_probability": float((r1 & r2 & (estimate-c1 > dthreshold) & (estimate-c2 > dthreshold)).mean()),
        "incorrect_product_of_marginal_probabilities": float(r1.mean() * ((estimate-c1) > dthreshold).mean() * ((estimate-c2) > dthreshold).mean()),
        "average_of_ten_independent_controls_joint_pass_probability": float((r1 & r2 & (estimate-cavg > average_threshold)).mean()),
        "power_at_true_equal_point_threshold_upper_bound": 0.5,
    }
    # A bivariate Gaussian repeated-measurement counterexample to a universal tau ceiling.
    repeat_tau = 0.891
    repeat_pearson = math.sin(math.pi * repeat_tau / 2)
    latent_tau = 2 / math.pi * math.asin(math.sqrt(repeat_pearson))
    combo = []
    for k in (27, 41, 54):
        combo.append({"k": k, "distinct_pairs_cap": math.comb(k, 2),
                      "cell_pair_cap_from_only_total_and_36_cells": min(806, 36 * math.comb(k, 2)),
                      "fixed_k_random_holdout_expected_units": 806 * k * (k-1) / (136 * 135),
                      "cap_if_all_136_drugs_are_confirmed_to_participate": 806 - math.ceil((136-k)/2)})
    observed_var, borrowed_noise_var = 0.052196 ** 2, 0.0408 ** 2
    out = {
        "status": "simulated_or_analytic_counterexamples_only",
        "seed": 20261027,
        "data_read": [],
        "double_randomness": {"n": n, "replicates": reps, "se": ses,
                              "ratio_redraw_and_boot_to_redraw_only": ses["redraw_z_and_bootstrap_units"] / ses["redraw_z_fixed_units"],
                              "linear_score_exact_sd_ratio": math.sqrt(2 - 1/n)},
        "paired_contrast": paired,
        "spearman_calibration": calibration,
        "joint_power": joint,
        "kendall_repeatability_counterexample": {"two_noisy_measurements_tau": repeat_tau,
                                                 "latent_truth_vs_one_measurement_tau": latent_tau,
                                                 "model": "independent additive Gaussian measurement errors"},
        "combocat_combinatorics": combo,
        "reliability_formula_illustration_not_validated_noise_estimate": {
            "a0_report_formula": math.sqrt(observed_var/(observed_var+borrowed_noise_var)),
            "classical_observed_total_variance_formula": math.sqrt(max(0, observed_var-borrowed_noise_var)/observed_var),
            "pure_noise_reported_ceiling": math.sqrt(0.5),
            "pure_noise_actual_signal_ceiling": 0.0,
        },
    }
    dest = Path(__file__).with_suffix(".json")
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
