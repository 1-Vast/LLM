"""Post-freeze promotion parity: promoted src/tools code reproduces the frozen study arithmetic."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analysis as A  # noqa: E402
import phenotypes as P  # noqa: E402
from tools.datasets.tahoe_phenotypes import phenotype_frame  # noqa: E402
from virtual_cell.context_transfer import transfer_prior  # noqa: E402


@pytest.mark.parametrize("seed", range(5))
def test_promoted_transfer_prior_matches_the_frozen_kernel_arm(seed):
    rng = np.random.RandomState(seed)
    basal, outcomes = rng.normal(size=(40, 50)), rng.normal(size=(40, 30))
    outcomes[rng.rand(40, 30) < 0.05] = np.nan
    target = rng.normal(size=50)
    frozen = A.kernel_prior(target, basal, outcomes, 0.1, 40)
    promoted = transfer_prior(target, basal, outcomes, tau=0.1, top_m=40).values
    assert np.allclose(np.nan_to_num(promoted), frozen, atol=1e-12)


def test_promoted_phenotype_frame_matches_the_frozen_study_module():
    rng = np.random.RandomState(3)
    table = {}
    for line in ("a", "b", "c"):
        for label in (P.DMSO, "[('X', 5.0, 'uM')]", "[('Y', 0.5, 'uM')]"):
            n = int(rng.randint(100, 2000))
            g1, s = int(n * 0.6), int(n * 0.1)
            table[(line, label, "p1")] = {"n": n, "G1": g1, "S": s, "G2M": n - g1 - s}
    frozen = P.phenotype_frame(table, ["a", "c"], ["a", "b"])
    promoted = phenotype_frame(table, ["a", "c"], ["a", "b"])
    assert frozen.keys() == promoted.keys()
    for key in frozen:
        for field in ("survival", "G1", "S", "G2M"):
            assert promoted[key][field] == pytest.approx(frozen[key][field], abs=1e-12)
