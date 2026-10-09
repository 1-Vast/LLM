"""Behavioral checks for the separate v9 research calibration contract."""
import numpy as np

from . import run9


def episode(traj, truth=1, qc=None):
    return {"trajectory": traj, "truth_sign": truth,
            "qc_prefix": qc or [0] * len(traj)}


def test_first_crossing_loss_not_monotone():
    e = episode([(1., 1), (-3., 2)])
    assert not run9.outcome(e, .5)["wrong"]
    assert run9.outcome(e, 2.)["wrong"]


def test_exact_bound_accepts_evidence_not_absence():
    assert run9.upper(0, 200, run9.DELTA / run9.FAMILY) < .05
    assert run9.upper(0, 100, run9.DELTA / run9.FAMILY) > .05
    assert run9.upper(200, 200, .05) == 1
    assert run9.upper(0, 0, .05) == 1


def test_safe_family_selects_and_unsafe_abstains():
    selected, _ = run9.calibrate([episode([(100., 1)])] * 200)
    assert selected["marginal"] == .5
    assert selected["conditional"] == .5
    selected, _ = run9.calibrate([episode([(-100., 1)])] * 200)
    assert selected == {"marginal": None, "conditional": None}


def test_abstention_does_not_certify_conditional_risk():
    selected, _ = run9.calibrate([episode([])] * 200)
    assert selected["conditional"] is None
    assert selected["marginal"] == .5


def test_whole_units_stay_together():
    names = ["a", "b", "c", "d"]
    units = {"a": "u", "b": "u", "c": "v", "d": "w"}
    train, cal = run9.split_units(names, units)
    assert ("a" in train) == ("b" in train)
    assert not {units[c] for c in train} & {units[c] for c in cal}
    assert set(train + cal) == set(names)


def test_truth_sign_and_prefix_qc():
    e = episode([(-1., 1), (5., 2)], truth=-1, qc=[0, 1])
    out = run9.outcome(e, .5)
    assert out == {"decided": True, "wrong": False, "measurements": 1, "qc": 0}
    assert run9.outcome(e, None) == {"decided": False, "wrong": False, "measurements": 0, "qc": 0}


def test_scalar_purchase_trace_ignores_vector_reads_and_repeats():
    x = run9.TracedReadings(np.array([1., np.nan, 3.]))
    x[2]
    x[2]
    x[np.array([2])]
    x[1]
    assert x.observed == [2, 1]


def test_traced_simulator_matches_plain_all_acquisitions():
    from . import run8
    from .world5b import LearnedWorld
    values = np.linspace(.1, .9, 20)
    values[2] = np.nan
    pair = ((np.full(20, .3), np.full(20, .2)),
            (np.full(20, .6), np.full(20, .2)), (0, 1))
    for acquisition in run9.ACQS:
        def world():
            return LearnedWorld(np.full(20, .5), np.ones((20, 1)) * .01, np.full(20, .1),
                                np.array([pair[0][0], pair[1][0]]),
                                np.full((2, 20), .2), blend_mode="holdout", blend_w=.5)
        plain = run8.run_episode_v8(values, pair, (.01, .01), acquisition,
                                   list(range(20)), world() if acquisition == "world" else None)
        traced = run9.TracedReadings(values)
        replay = run8.run_episode_v8(traced, pair, (.01, .01), acquisition,
                                    list(range(20)), world() if acquisition == "world" else None)
        assert plain == replay
        assert len(traced.observed) == 16
        assert sum(not np.isfinite(values[j]) for j in traced.observed) == replay[2]


def test_zero_error_capacity():
    assert run9.upper(0, 152, run9.DELTA / run9.FAMILY) > .05
    assert run9.upper(0, 153, run9.DELTA / run9.FAMILY) <= .05
