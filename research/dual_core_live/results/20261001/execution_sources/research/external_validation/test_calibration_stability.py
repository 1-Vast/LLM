"""Regression tests for thin-stratum calibration and direct risk reporting."""

import warnings

import numpy as np
import pandas as pd

from . import calibration_audit as C
from . import statistics as S


def test_thin_or_separated_calibration_is_finite_and_bounded():
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        metrics = S.calibration_metrics([0.01, 0.02], [1.0, 0.0])

    assert not [warning for warning in seen if issubclass(warning.category, RuntimeWarning)]
    assert metrics["support"] == 2
    assert "beta_binomial" in metrics["calibration_method"]
    assert metrics["calibration_stable"] is False
    assert np.isfinite(metrics["intercept"])
    assert np.isfinite(metrics["slope"])
    assert metrics["direct_rate_upper95"] == metrics["observed_wilson_upper95"]
    assert metrics["direct_rate_upper95"] >= metrics["observed"]
    assert metrics["beta_binomial_rate"] == (1.0 + 0.5) / 3.0


def test_complete_separation_at_nominal_support_uses_finite_fallback():
    p = np.linspace(0.01, 0.99, 20)
    y = (p > 0.5).astype(float)
    metrics = S.calibration_metrics(p, y)

    assert "beta_binomial" in metrics["calibration_method"]
    assert np.isfinite(metrics["intercept"])
    assert np.isfinite(metrics["slope"])


def test_calibration_audit_reports_direct_wrong_risk_and_support():
    frame = pd.DataFrame({
        "dataset": ["d"] * 3, "tier": ["t"] * 3, "policy": ["myopic_edv"] * 3,
        "p_correct": [0.9, 0.8, 0.7], "p_wrong": [0.1, 0.2, 0.3],
        "correct": [1.0, 1.0, 0.0], "wrong": [0.0, 0.0, 1.0],
        "line": ["L"] * 3, "action_type": ["24h|100nM"] * 3,
        "support_bin": ["1"] * 3, "novelty_bin": ["<0.3"] * 3,
        "batch": ["B"] * 3, "magnitude_tercile": ["low"] * 3, "basis": ["fallback"] * 3,
    })

    result = C.audit(frame)["d|t|myopic_edv"]["all"]
    assert result["support"] == 3
    assert result["direct_wrong_risk"]["support"] == 3
    assert result["direct_wrong_risk"]["estimate"] == 1 / 3
    assert result["direct_wrong_risk_upper95"] >= result["direct_wrong_risk"]["estimate"]
    assert result["wrong"]["direct_wrong_risk_upper95"] == result["direct_wrong_risk_upper95"]
