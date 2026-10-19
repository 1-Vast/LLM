"""Checks for the heavy-tail RSD study (real arena at the development dose; run explicitly, not in the default suite).

python -B -m pytest research/heavy_tail_rsd_20261019/test_ht.py -p no:cacheprovider -q
"""
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import t as student_t

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ht_core as H  # noqa: E402
import ht_data as HD  # noqa: E402
import rsd_core as C  # noqa: E402
import rsd_data as D  # noqa: E402
import rsd_run as R  # noqa: E402


def test_t_quadrature_matches_student_t():
    e = np.linspace(-12, 12, 241)
    for nu in (2.0, 3.0, 4.0, 10.0, 20.0):
        F = H.predictive_cdf(e, np.zeros_like(e), np.ones_like(e), nu)
        assert np.max(np.abs(F - student_t.cdf(e, nu))) < 2e-3, nu


def test_difference_density_matches_simulation():
    rng = np.random.default_rng(1)
    for nu in (2.5, 5.0):
        x = 0.7 * (rng.standard_t(nu, 400000) - rng.standard_t(nu, 400000)) / np.sqrt(2)
        edges = np.linspace(-6, 6, 61)
        emp, _ = np.histogram(x, edges, density=False)
        emp = emp / len(x) / np.diff(edges)
        mid = 0.5 * (edges[1:] + edges[:-1])
        th = H.t_scale_pdf_diff(mid, 0.7, nu)
        assert np.max(np.abs(emp - th)) < 0.01, nu


def test_tail_fit_recovers_nu_and_scale():
    rng = np.random.default_rng(2)
    nu, s = 4.0, 0.8
    z = s * (rng.standard_t(nu, 200000) - rng.standard_t(nu, 200000)) / np.sqrt(2)
    fit = H.fit_tail(z)
    assert 3.0 <= fit["nu_ml"] <= 5.5
    assert abs(fit["profile"][4.0]["s"] - s) < 0.03


def test_test_doses_refused_before_freeze():
    if (HERE / "FREEZE.json").exists():
        pytest.skip("frozen: the guard is open by design")
    for dose in HD.TEST_DOSES:
        with pytest.raises(PermissionError):
            HD.guard(dose)


@pytest.fixture(scope="module")
def dev_search():
    return HD.setup("search", HD.DEV_DOSE)


def test_dev_dose_reads_equal_frozen_reads(dev_search):
    t, lines, *_ = HD.arena()
    A0, B0, T0 = D.load_reads(t, lines)                      # frozen loader (cache exists; writes nothing)
    S = dev_search
    for X0, X in ((A0, S["A"]), (B0, S["B"]), (T0, S["T"])):
        assert np.array_equal(np.isnan(X0), np.isnan(X)) and np.allclose(np.nan_to_num(X0), np.nan_to_num(X))
    Sf = R.setup("search")
    assert np.array_equal(Sf["ref"], S["ref"]) and np.array_equal(Sf["q"], S["q"])


def test_gaussian_limit_reproduces_frozen_posterior(dev_search):
    S = dev_search
    cfg = dict(q=2, rho=0.0, use_prior=False)
    vc0 = R.build_vc(S, cfg)
    fvc = H.build_factor_vc(S, 2, False)
    assert np.array_equal(vc0.S0, fvc.S0) and np.array_equal(vc0.N0, fvc.N0)
    assert np.allclose((fvc.U * fvc.w) @ fvc.U.T + np.diag(fvc.d), fvc.S0, atol=1e-12)
    q = S["q"][:60]
    A = S["A"][q]
    tier = C.tier_of(A)
    mu = np.zeros((len(q), A.shape[1]))
    m0, v0, n1 = vc0.posterior(mu, A, np.ones(len(q)), tier)
    p = H.ht_posterior(fvc, mu, A, tier, np.inf, 1.0)
    assert np.allclose(p["mean"], m0, atol=1e-8) and np.allclose(p["var"], v0, atol=1e-8)
    assert np.allclose(p["sig2"], n1, atol=1e-12)


def test_compound_level_weight_tracks_compound_noise(dev_search):
    S = dev_search
    fvc = H.build_factor_vc(S, 2, False)
    q = S["q"][:40]
    A = S["A"][q].copy()
    tier = C.tier_of(S["A"][q])
    rng = np.random.default_rng(3)
    sd = np.sqrt(fvc.beta[tier][0] * fvc.noise_diag())
    A[0] = A[0] + 2.0 * sd * rng.standard_normal(A.shape[1])          # compound 0: much noisier read
    mu = np.zeros_like(A)
    p = H.ht_posterior(fvc, mu, A, tier, 10.0, 0.9, level="compound")
    assert np.allclose(p["lam"], p["lam"][:, :1])                       # one weight per compound
    assert p["lam"][0, 0] < 0.5 * np.median(p["lam"][1:, 0])
    assert (p["pred_sig2"][0] > p["sig2"][0]).all() and p["pred_nu"] == np.inf


def test_heavy_tail_downweights_isolated_extreme_pair(dev_search):
    S = dev_search
    fvc = H.build_factor_vc(S, 2, False)
    q = S["q"][:5]
    A = S["A"][q].copy()
    j = int(np.where(np.isfinite(A[0]))[0][10])
    A[0, j] -= 8.0
    tier = C.tier_of(S["A"][q])
    mu = np.zeros_like(A)
    g = H.ht_posterior(fvc, mu, A, tier, np.inf, 1.0)
    h = H.ht_posterior(fvc, mu, A, tier, 3.0, 0.8)
    assert h["lam"][0, j] < 0.2 and h["mean"][0, j] > g["mean"][0, j]
