from __future__ import annotations

from maestro.hypothesis_forecast import support_aware_shrinkage


PRIOR = {"match_h1": 0.45, "match_h2": 0.25, "unresolved": 0.15,
         "absent": 0.10, "qc_failed": 0.05}


def test_low_effective_support_is_shrunk_toward_the_declared_prior():
    raw = {"match_h1": 1.0, "match_h2": 0.0, "unresolved": 0.0,
           "absent": 0.0, "qc_failed": 0.0}
    low = support_aware_shrinkage(raw, effective_support=0.5, domain_shift=0.0,
                                  base_prior=PRIOR, prior_strength=4.0)
    high = support_aware_shrinkage(raw, effective_support=100.0, domain_shift=0.0,
                                   base_prior=PRIOR, prior_strength=4.0)
    assert low["match_h1"] < high["match_h1"] < 1.0
    assert abs(low["match_h2"] - PRIOR["match_h2"]) < PRIOR["match_h2"]
    assert abs(sum(low.values()) - 1.0) < 1e-9


def test_domain_shift_reduces_trust_in_the_retrieved_distribution():
    raw = {"match_h1": 0.9, "match_h2": 0.1}
    close = support_aware_shrinkage(raw, effective_support=20, domain_shift=0.0,
                                    base_prior={"match_h1": 0.5, "match_h2": 0.5})
    shifted = support_aware_shrinkage(raw, effective_support=20, domain_shift=1.0,
                                      base_prior={"match_h1": 0.5, "match_h2": 0.5})
    assert shifted["match_h1"] < close["match_h1"]
    assert shifted["match_h2"] > close["match_h2"]
