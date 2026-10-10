"""Contract tests for the paired increment estimator (tools/evaluation/increment.py)."""
from __future__ import annotations

import numpy as np

from tools.evaluation.increment import paired_increment


def synthetic(seed=0, n=80, tasks=3, signal=0.8):
    rng = np.random.default_rng(seed)
    latent = rng.normal(size=(n, tasks))
    prior = latent + rng.normal(scale=1.5, size=(n, tasks))
    extra = latent + rng.normal(scale=0.5, size=(n, tasks))
    outcome = signal * latent + rng.normal(scale=0.5, size=(n, tasks))
    return prior, extra, outcome


def test_informative_evidence_gives_a_positive_interval_and_noise_does_not():
    prior, extra, outcome = synthetic()
    out = paired_increment(prior, extra, outcome, n_boot=300, seed=1)
    assert out["lower"] > 0 and out["tasks_improved"] == 3
    noise = np.random.default_rng(5).normal(size=prior.shape)
    out2 = paired_increment(prior, noise, outcome, n_boot=300, seed=1)
    assert out2["lower"] < 0 < out2["upper"] or out2["upper"] < 0


def test_both_terms_use_the_same_units():
    prior, extra, outcome = synthetic(n=40, tasks=1)
    extra[:10, 0] = np.nan  # unmeasurable units are dropped from BOTH terms
    out = paired_increment(prior, extra, outcome, n_boot=50)
    rows = slice(10, 40)
    expected = np.corrcoef(prior[rows, 0], outcome[rows, 0])[0, 1]
    assert out["per_task"]["0"]["units"] == 30
    assert np.isclose(out["per_task"]["0"]["prior_r"], expected)


def test_tasks_with_too_few_paired_units_are_refused_by_name():
    prior, extra, outcome = synthetic(n=20, tasks=2)
    extra[:15, 1] = np.nan
    out = paired_increment(prior, extra, outcome, tasks=["a", "b"], n_boot=50)
    assert out["refused"] == {"b": "TOO_FEW_PAIRED_UNITS"} and set(out["per_task"]) == {"a"}


def test_deterministic_given_seed():
    prior, extra, outcome = synthetic()
    assert paired_increment(prior, extra, outcome, n_boot=100, seed=3) == paired_increment(prior, extra, outcome, n_boot=100, seed=3)
