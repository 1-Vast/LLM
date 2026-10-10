"""Open-world test (H6): exhaustion of a library-only hypothesis set, and revision.

H0 = classes with reference drugs (the library a data-only world model can represent). A query
drug runs a falsification episode against H0 with the full system's design. Outcomes:

* exhaustion rate: HYPOTHESIS_SET_EXHAUSTED for queries whose class is outside the library
  (knowledge-only stratum) against queries whose class is inside it (referenced stratum);
* revision, for exhausted out-of-library queries: five proposals from the out-of-library classes
  (a) by the agent reading the observations, (b) by the compiled agent hypotheses ranked by their
  conformal p-value on the same observations, (c) uniformly at random (expected rate computed);
  success = the true class is proposed and is not rejected by the calibrated test.
"""
from __future__ import annotations

import numpy as np

import falsify as F


def library_episode(fz: F.Falsifier, z: np.ndarray, avail: list[int], library: np.ndarray, budget: int, seed: int,
                    policy: str = "falsify") -> F.EpisodeResult:
    return fz.run(z, avail, policy, budget, None, seed=seed, hyp=library, stop_on_single=False)


def compiled_ranking(fz: F.Falsifier, z: np.ndarray, observed: list[int], outside: np.ndarray, k: int = 5) -> tuple[list[str], np.ndarray]:
    p = fz.pvalues(z, observed, outside)
    Q, b, A = fz.stats(z, observed, outside)
    s, _ = F.score_from_stats(Q, b, A, fz.noise.tau2, len(observed))
    s = np.where(np.isnan(s), np.inf, s)
    order = np.lexsort((s, -p))  # largest p first; ties in p (discrete calibration) by the raw score
    return [str(fz.names[outside[i]]) for i in order[:k]], p
