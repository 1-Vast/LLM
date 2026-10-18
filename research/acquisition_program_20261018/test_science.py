"""Behaviour tests for the acquisition-program study (run: pytest research/acquisition_program_20261018).

File summary
- Path: research/acquisition_program_20261018/test_science.py
- Purpose: probes never reveal target entries; features do not read the hidden side beyond the seed observation; the
  program grammar rejects unsafe or unknown expressions and ties go to the fixed order; the counterfactual table equals an
  explicitly executed run for the chosen action.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ap_task as A  # noqa: E402
import bench  # noqa: E402


@pytest.fixture(scope="module")
def task():
    return A.make_task(bench.make_fold(bench.load_tables(), 0, (1,)), 0, 1)


def test_target_is_whole_pools_and_never_probed(task):
    fold = task.fold
    assert set(np.unique(fold.pid[task.target]).tolist()) <= set(task.pools_target)
    for p in task.fixed:
        assert p not in task.pools_target
        assert not task.target[bench.pool_lines(fold, p)].any()


def test_groups_partition_the_pools(task):
    g = A.groups(task.fold)
    flat = sorted(p for x in g for p in x)
    assert flat == sorted(set(int(p) for p in task.fold.pid)) and [len(x) for x in g] == [6, 6, 6, 5]


def test_features_ignore_everything_but_the_seed_observation(task):
    from dataclasses import replace
    small = replace(task, rows=task.rows[:3])
    fold = task.fold
    f1 = A.build_scenario(small, "t1")
    seed = bench.pool_lines(fold, task.fixed[0])
    h = fold.hidden
    Y = h.Y.copy()
    other = np.setdiff1d(np.arange(Y.shape[1]), seed)
    Y[np.ix_(small.rows, other)] = 5.0                    # scramble every cell except the seed pool
    saved, fold.hidden = h, bench.Hidden(Y=Y, truth=h.truth, sd=h.sd, z=h.z, family=h.family)
    try:
        f2 = A.build_scenario(small, "t1")
    finally:
        fold.hidden = saved
    assert all(np.array_equal(f1["features"][k], f2["features"][k]) for k in f1["features"])
    assert not np.array_equal(f1["final"], f2["final"])    # the table (executed outcomes) does depend on them


def test_program_grammar():
    A.compile_program("la + 0.5*zs(vr_rel) - rank")
    for bad in ("__import__('os')", "la**2", "open('x')", "foo + la", "la if la else 1", "[1,2]", "lambda: 1"):
        with pytest.raises(A.ProgramError):
            A.compile_program(bad)


def test_ties_go_to_the_fixed_order():
    f = {k: np.zeros((3, 4)) for k in A.FEATURES}
    f["rank"] = np.tile(np.arange(4.0), (3, 1))
    assert (A.choose(f, A.compile_program("la")) == 0).all()
    assert (A.choose(f, A.compile_program("-rank")) == 0).all()
    assert (A.choose(f, A.compile_program("rank")) == 3).all()


def test_table_matches_an_executed_run(task):
    import rules as R
    fold = task.fold
    sc = A.build_scenario(task, "t2", with_features=False)
    i_pos = 5
    i = int(task.rows[i_pos])
    j = 2
    o = bench.Oracle(sc["hidden"])
    seed = bench.pool_lines(fold, task.fixed[0])
    c = task.fixed[1 + j]
    q3 = next(p for p in task.fixed[1:] if p != c)
    P = np.concatenate([seed, bench.pool_lines(fold, c), bench.pool_lines(fold, q3)])
    y = np.concatenate([o.observe(i, seed), o.observe(i, bench.pool_lines(fold, c)), o.observe(i, bench.pool_lines(fold, q3))])
    prof = R.conditional_mean(fold, fold.prior[i], P, y)
    assert np.allclose(bench.call_score(prof, fold.G)[sc["T"]], sc["final"][i_pos, j], atol=1e-4)
