"""Unit tests of the decoupled calibration layer (fast; no read is loaded).

python -B -m pytest test_dc.py -p no:cacheprovider -q   (maestro environment, from this folder)
"""
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dc_run as DC  # noqa: E402


def test_decoupled_arms_rank_with_the_gaussian_posterior():
    assert all(DC.RANK_BY[a] == "rsd" for a in DC.DECOUPLED)
    assert DC.RANK_BY["ht_compound"] == "ht_compound"
    assert {"raw", "raw2", "shrink", "rsd", "ht_compound", "dec"} <= set(DC.ARMS)


def test_compound_candidates_are_the_frozen_heavy_tail_compound_class():
    assert [c[1] for c in DC.COMPOUND_CANDS] == list(DC.H.NU_GRID)
    assert all(c[0] == "compound" and not np.isfinite(c[2]) for c in DC.COMPOUND_CANDS)


def test_flat_prior_raw_and_raw2_intervals_are_calibrated_under_gaussian_replicates():
    rng = np.random.default_rng(0)
    n1 = rng.uniform(0.2, 2.0, 200000)
    x = rng.normal(0, 3, n1.size)
    A, B, T = (x + rng.normal(0, np.sqrt(n1)) for _ in range(3))
    F = DC.H.predictive_cdf(T - A, n1, n1, np.inf)
    assert abs(np.mean(np.abs(F - 0.5) <= 0.4) - 0.8) < 0.005
    F2 = DC.H.predictive_cdf(T - 0.5 * (A + B), 0.5 * n1, n1, np.inf)
    assert abs(np.mean(np.abs(F2 - 0.5) <= 0.4) - 0.8) < 0.005


def test_bootstrap_p_values_and_holm():
    bs = np.linspace(0.0, 1.0, 1001)
    assert DC.p_le(bs, 0.5) == pytest.approx(502 / 1002)
    assert DC.p_ge(bs, 0.9) == pytest.approx(102 / 1002)
    h = DC.holm(dict(P1=0.01, P2=0.02, P3=0.04))
    assert h == pytest.approx(dict(P1=0.03, P2=0.04, P3=0.04))


def _agg(p, cov, opt, d1=0.0, d2=0.0):
    tests = {k: dict(statistic=k, estimate=0.0, ci95=[0, 0], p_one_sided=v) for k, v in p.items()}
    return dict(tests=tests,
                calibration=dict(dec=dict(coverage80_selected=dict(estimate=cov), coverage80_all=dict(estimate=0.8)),
                                 rsd=dict(coverage80_selected=dict(estimate=0.69))),
                selected_optimism_D2=dict(dec=dict(optimism=opt)),
                contrasts={"dec-rsd": dict(D1=dict(estimate=d1), D2=dict(estimate=d2))})


def test_verdict_rule():
    ok = dict(P1=0.001, P2=0.001, P3=0.001)
    assert DC.verdict(_agg(ok, 0.75, 0.0), True)["overall"] == "DECOUPLED_CALIBRATION_HOLDS"
    assert DC.verdict(_agg(ok, 0.75, 0.0), True)["grade"] == "DEVELOPMENT_ONLY"
    assert DC.verdict(_agg(ok, 0.75, 0.0), False)["overall"] == "DEFECT_DECISIONS_CHANGED"
    assert DC.verdict(_agg(ok, 0.75, 0.0, d2=1e-9), True)["overall"] == "DEFECT_DECISIONS_CHANGED"
    weak = dict(P1=0.001, P2=0.2, P3=0.001)
    assert DC.verdict(_agg(weak, 0.71, 0.0), True)["overall"] == "PARTIAL"
    assert DC.verdict(_agg(weak, 0.69, 0.0), True)["overall"] == "DECOUPLED_CALIBRATION_FAILS"
    assert DC.verdict(_agg(weak, 0.75, 0.2), True)["overall"] == "DECOUPLED_CALIBRATION_FAILS"


def test_confirmatory_stage_refuses_without_an_authorised_arena():
    with pytest.raises(SystemExit, match="BLOCKED"):
        DC.stage_confirm()


def test_unopened_dose_is_refused_and_nothing_is_written():
    before = DC.cache_snapshot()
    with pytest.raises(PermissionError):
        DC.require_cache(0.156)
    assert DC.cache_snapshot() == before


def test_write_once(tmp_path):
    p = tmp_path / "x.json"
    DC.write_once(p, dict(a=1))
    with pytest.raises(SystemExit):
        DC.write_once(p, dict(a=2))
