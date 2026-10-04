"""Core contract: the combination world model and the certified discovery loop.

File summary
- Path: tests/test_combination_world.py
- Purpose: the promoted world model cannot learn from the target line except through purchased
  measurements, its fast posterior equals a dense Gaussian process, it refuses by name, and the
  discovery loop spends exactly its budget and never reports a prediction as a measured hit.
- Depends on: numpy (synthetic screens only; asset-free).
"""
from __future__ import annotations

import numpy as np
import pytest

from agent.discovery import (CERTIFIED_NOMINATION, MEASURED_HIT, REFUSAL, YIELD_BOUND, DiscoverySpec,
                             run_discovery)
from virtual_cell.combination_world import (CombinationScreen, CombinationWorld, CombinationWorldConfig,
                                            CombinationWorldRefusal, nelder_mead, normal_cdf)


def screen(seed: int = 0, drugs: int = 10, lines: int = 6) -> CombinationScreen:
    rng = np.random.default_rng(seed)
    pairs = [(i, j) for i in range(drugs) for j in range(i + 1, drugs)]
    a = np.array([p[0] for p in pairs for _ in range(lines)], np.int32)
    b = np.array([p[1] for p in pairs for _ in range(lines)], np.int32)
    c = np.array([l for _ in pairs for l in range(lines)], np.int32)
    drug_effect = rng.normal(0, 4, size=(drugs, lines))
    y = rng.normal(0, 5, size=len(pairs)).repeat(lines) + drug_effect[a, c] + drug_effect[b, c] + rng.normal(0, 3, a.size)
    mono = rng.random((drugs, lines))
    return CombinationScreen(tuple(f"d{i}" for i in range(drugs)), tuple(f"l{i}" for i in range(lines)), a, b, c, y,
                             1 - (1 - mono[a, c]) * (1 - mono[b, c]), mono, mono ** 2, 3.0)


def test_target_labels_reach_nothing_before_feedback():
    base = screen()
    scrambled_y = base.y.copy()
    scrambled_y[base.c == 2] = np.random.default_rng(9).normal(50, 20, size=int((base.c == 2).sum()))
    other = CombinationScreen(*[getattr(base, f) for f in ("drugs", "lines", "a", "b", "c")], scrambled_y,
                              base.expected, base.mono_mean, base.mono_top, base.threshold)
    w1, w2 = CombinationWorld(base, 2), CombinationWorld(other, 2)
    assert np.allclose(w1.prior_target, w2.prior_target) and np.allclose(w1.prior_var_target, w2.prior_var_target)
    assert (w1.s_line, w1.s_drug, w1.s_noise) == pytest.approx((w2.s_line, w2.s_drug, w2.s_noise))


def test_posterior_equals_dense_gaussian_process():
    world = CombinationWorld(screen(1), 0)
    measured = np.array([0, 3, 5, 8, 13])
    values = world.screen.y[world.rows[measured]]
    mean, var = world.posterior(measured, values)
    K = world.Z_target @ world.A @ world.Z_target.T
    C = K[np.ix_(measured, measured)] + world.s_noise * np.eye(measured.size)
    assert np.allclose(mean, world.prior_target + K[:, measured] @ np.linalg.solve(C, values - world.prior_target[measured]))
    assert np.allclose(var, np.diag(K) - np.einsum("ij,ji->i", K[:, measured], np.linalg.solve(C, K[measured])) + world.s_noise)


def test_named_refusals_and_numerics():
    with pytest.raises(CombinationWorldRefusal) as unknown:
        CombinationWorld(screen(), 99)
    assert unknown.value.code == "TARGET_LINE_UNKNOWN"
    single = screen(lines=1)
    with pytest.raises(CombinationWorldRefusal) as alone:
        CombinationWorld(single, 0)
    assert alone.value.code == "NO_HISTORY"
    world = CombinationWorld(screen(), 1)
    with pytest.raises(CombinationWorldRefusal) as mismatch:
        world.posterior(np.array([0, 1]), np.array([1.0]))
    assert mismatch.value.code == "MEASUREMENT_MISMATCH"
    assert normal_cdf(np.array([0.0, 1.959963984540054]))[1] == pytest.approx(0.975, abs=1e-9)
    best = nelder_mead(lambda v: float(((v - np.array([0.3, -1.2, 2.0])) ** 2).sum()), np.zeros(3), np.full(3, -5.0), np.full(3, 5.0))
    assert np.allclose(best, [0.3, -1.2, 2.0], atol=1e-4)


def test_feedback_off_and_context_off_change_what_they_should():
    s = screen(2)
    frozen = CombinationWorld(s, 1, CombinationWorldConfig(feedback=False))
    assert np.allclose(frozen.posterior(np.array([0, 1]), np.array([30.0, 30.0]))[0], frozen.prior_target)
    assert CombinationWorld(s, 1).X_target.shape[1] > CombinationWorld(s, 1, CombinationWorldConfig(context=False)).X_target.shape[1]


@pytest.mark.parametrize("terminal", ["certify", "exploit"])
def test_discovery_loop_spends_its_budget_and_types_its_claims(terminal):
    world = CombinationWorld(screen(3), 4)
    truth = world.screen.y[world.rows]
    bought: list[int] = []

    def measure(indices):
        bought.extend(indices.tolist())
        return truth[indices]

    spec = DiscoverySpec(budget_fraction=0.3, rounds=3, kappa=2, terminal=terminal)
    report = run_discovery(world, measure, spec, seed=1)
    assert len(bought) == len(set(bought)) == report.budget
    kinds = {claim.kind for claim in report.claims}
    for claim in report.claims:
        if claim.kind == MEASURED_HIT:
            assert claim.candidate in report.labels and report.labels[claim.candidate] > world.screen.threshold
        if claim.kind == CERTIFIED_NOMINATION:
            assert claim.candidate not in report.labels           # a nomination is never a measurement
    if terminal == "certify":
        assert YIELD_BOUND in kinds and report.certificate is not None
        assert (REFUSAL in kinds) == (report.certificate.refusal is not None)
    else:
        assert report.certificate is None and not kinds & {CERTIFIED_NOMINATION, YIELD_BOUND}


def test_black_box_planner_is_accepted_and_double_purchase_refused():
    world = CombinationWorld(screen(4), 0)
    truth = world.screen.y[world.rows]

    class Repeater:
        name = "repeater"

        def scores(self, measured, values):
            return np.zeros(world.rows.size)

        def choose(self, available, measured, values, k):
            return np.flatnonzero(np.ones_like(available))[:k]       # ignores what was bought

    with pytest.raises(ValueError, match="twice"):
        run_discovery(world, lambda i: truth[i], DiscoverySpec(budget_fraction=0.3, rounds=3), planner=Repeater())
