"""Deterministic arithmetic/counterexamples; no biological data or model fitting."""
import json
import math
from pathlib import Path


def phi(x):
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)


def cdf(x):
    return (1 + math.erf(x / math.sqrt(2))) / 2


def detectability(mu, sigma=1.0, threshold=1.96):
    return 1 - cdf((threshold - mu) / sigma) + cdf((-threshold - mu) / sigma)


def value(mu, boundary=2.025, prior_sd=0.5, obs_sd=1.0):
    # Expected improvement in the Bayes value of a binary choice versus a known
    # alternative after one noisy normal observation. This is a constructed
    # decision problem, not a claim about the archived drug top-k problem.
    tau = prior_sd**2 / math.sqrt(prior_sd**2 + obs_sd**2)
    gap = abs(mu - boundary)
    return tau * phi(gap / tau) - gap * cdf(-gap / tau)


mus = [2.0, 2.051]
v = [value(m) for m in mus]
d = [detectability(m) for m in mus]
out = {
    "status": "analytical_constructed_example_not_biological_evidence",
    "fixed_repeat_and_noise_does_not_prove_order_equivalence": {
        "mu": mus, "boundary": 2.025, "obs_sd": 1.0, "prior_sd": 0.5,
        "value_of_information": v, "detectability_factor": d,
        "product": [a*b for a, b in zip(v, d)],
        "value_prefers_first": v[0] > v[1],
        "product_prefers_second": v[0]*d[0] < v[1]*d[1],
        "scope": "Refutes inference from fixed repeats/near-boundary alone; not validation of I003 or its exact top-k implementation.",
    },
    "combocat_unit_arithmetic": {
        "total_cell_pair_units": 806, "reported_drugs": 136, "reported_cells": 36,
        "rows": [{"heldout_drugs": k,
                  "distinct_pair_bound": math.comb(k, 2),
                  "cell_pair_trivial_bound": min(806, 36*math.comb(k, 2)),
                  "expected_units_uniform_fixed_k": 806*k*(k-1)/(136*135)}
                 for k in (27, 41, 54)],
        "scope": "No entity map is available; these bounds do not make the resource qualified.",
    },
    "repeat_agreement_not_universal_prediction_ceiling": {
        "example_model": "Y1=T+e1,Y2=T+e2; mutually independent, Var(T)=1, Var(e)=1",
        "corr_Y1_Y2": 0.5,
        "corr_true_T_Y2": 1/math.sqrt(2),
        "scope": "Pearson illustration only, not a Kendall-tau conversion or an estimate of real reliability.",
    },
}
Path(__file__).with_name("audit_arithmetic.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
