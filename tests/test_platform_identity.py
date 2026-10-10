"""Contract tests for the cross-platform axis identity check (tools/analysis/platform_identity.py)."""
from __future__ import annotations

import numpy as np

from tools.analysis.platform_identity import identity_test


def platforms(seed=0, lines=12, genes=300, shift=0.3, noise=0.3):
    rng = np.random.default_rng(seed)
    base = rng.normal(size=(lines, genes))
    reference = {f"L{i}": base[i] for i in range(lines)}
    platform_effect = rng.normal(scale=shift, size=genes)  # gene-wise offset shared by all query lines
    query = {f"L{i}": base[i] + platform_effect + rng.normal(scale=noise, size=genes) for i in range(lines)}
    return reference, query


def test_matching_axes_identify_every_line_and_beat_the_permuted_null():
    ref, qry = platforms()
    out = identity_test(ref, qry, n_null=50)
    assert out["passed"] and out["top1"] == 1.0 and out["null_top1_mean"] < 0.3


def test_a_scrambled_query_axis_fails_by_name():
    ref, qry = platforms()
    perm = np.random.default_rng(9).permutation(300)
    scrambled = {k: v[perm] for k, v in qry.items()}
    out = identity_test(ref, scrambled, n_null=50)
    assert not out["passed"] and out["refusal"] == "AXIS_IDENTITY_FAILED"


def test_too_few_shared_lines_is_refused():
    ref, qry = platforms(lines=4)
    assert identity_test(ref, qry)["refusal"] == "TOO_FEW_SHARED_LINES"
