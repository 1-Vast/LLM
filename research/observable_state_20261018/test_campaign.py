"""Synthetic-world tests of the campaign core, the baselines and the masked grader (no PRISM data, no network)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import campaign as C  # noqa: E402
import masked_interface as M  # noqa: E402
import policies as P  # noqa: E402


def world(n=12, L=24, n_ctx=6, seed=0, reads=3, rounds=3):
    rng = np.random.default_rng(seed)
    V = rng.normal(0, 1, (L, 4)) * 0.5
    S = V @ V.T + 0.2 * np.eye(L)
    m0 = np.zeros((n, L))
    G = np.zeros(L)
    y = rng.multivariate_normal(np.zeros(L), S, n)  # truth profiles drawn from the prior (belief is correctly specified)
    truth = y <= -1.2
    ctxs = [np.arange(k * (L // n_ctx), (k + 1) * (L // n_ctx)) for k in range(n_ctx)]
    camp = C.Campaign(m0=m0, S=S, noise_var=0.05, contexts=ctxs, avail=np.ones(L, bool), G=G, reads_per_compound=reads, rounds=rounds,
                      seed_context=0, follow_up=8, cap=3, progress_k=3)
    noise = rng.standard_normal(y.shape) * np.sqrt(0.05)

    def observe(i, lines):
        return y[i, lines] + noise[i, lines]

    return camp, observe, truth, list(range(n_ctx))


def test_round_sizes_and_equal_budget_for_all_policies():
    assert C.round_sizes(12, 3, 3) == [12, 12]
    assert sum(C.round_sizes(10, 4, 4)) == 30
    for mk in (lambda o: P.FixedPolicy(o), lambda o: P.BatchEIGPolicy(o), lambda o: P.PSBAXPolicy(o)):
        camp, obs, truth, order = world()
        d = C.run_campaign(camp, mk(order), obs)
        assert d["ledger"]["assay_wells"] == 12 * 3
        assert camp.done.sum() == 36 and len(d["nominations"]) <= 8


def test_fixed_policy_gives_every_compound_the_same_reads_and_batch_eig_does_not():
    camp, obs, truth, order = world()
    C.run_campaign(camp, P.FixedPolicy(order), obs)
    assert set(camp.done.sum(1)) == {3}
    camp2, obs2, _, order2 = world()
    C.run_campaign(camp2, P.BatchEIGPolicy(order2), obs2)
    assert camp2.done.sum() == 36  # same total, free allocation (counts may differ across compounds)


def test_policies_never_touch_hidden_truth():
    # replacing the hidden outcomes after planning cannot change the plan of round 1: plans depend on reads, not on values
    camp, obs, _, order = world()
    for i in range(camp.n):
        camp.apply_read(i, 0, obs(i, camp.contexts[0]))
    p1 = P.BatchEIGPolicy(order).plan_round(camp, 12)
    camp.obs_y = [y + 5.0 for y in camp.obs_y]  # eig is value-independent in the Gaussian model
    assert P.BatchEIGPolicy(order).plan_round(camp, 12) == p1


def test_nomination_constraints_unmeasured_only():
    camp, obs, truth, order = world()
    d = C.run_campaign(camp, P.FixedPolicy(order), obs)
    q = camp.queried_mask()
    assert all(not q[i, l] for i, l in d["nominations"])
    per = {}
    for i, _ in d["nominations"]:
        per[i] = per.get(i, 0) + 1
    assert max(per.values()) <= 3


def test_feedback_beats_prior_only_on_correctly_specified_world():
    gain = []
    for s in range(6):
        camp, obs, truth, order = world(seed=s, n=24, L=48, n_ctx=8, reads=4, rounds=4)
        d = C.run_campaign(camp, P.FixedPolicy(order), obs)
        fb = C.grade(d, truth, camp.avail)["hits"]
        camp0, _, _, _ = world(seed=s, n=24, L=48, n_ctx=8)
        camp0.m0 = camp0.m0 + np.random.default_rng(s).normal(0, 1e-3, camp0.m0.shape)  # untied prior-only ranking
        gain.append(fb - C.grade(camp0.decisions(), truth, camp0.avail)["hits"])
    assert np.mean(gain) > 0


def test_grade_counts_false_progression_and_rejection():
    truth = np.zeros((4, 5), bool)
    truth[1, [0, 1]] = True
    truth[2, 3] = True
    dec = {"nominations": [(0, 1), (1, 0)], "progression": [0, 2], "ledger": {"assay_wells": 7}}
    g = C.grade(dec, truth, np.ones(5, bool))
    assert g["hits"] == 1 and g["false_progression"] == 1 and g["false_rejection"] == 1 and g["assay_wells"] == 7


def test_masked_grader_integration_search_scalar_transfer_record():
    camp, obs, truth, order = world()
    d = C.run_campaign(camp, P.FixedPolicy(order), obs)
    with tempfile.TemporaryDirectory() as t:
        m = M.MaskedOutcomeInterface(C.grader_for(truth, camp.avail), Path(t) / "l.jsonl", select_threshold=0.0, freeze_check=lambda: None)
        assert isinstance(m.query("search", d), float)
        assert m.query("select", d) is True
        assert "false_progression" in m.query("transfer", d)


def test_policy_returning_wrong_budget_is_refused():
    class Bad:
        def plan_round(self, camp, size):
            return []

    camp, obs, _, _ = world()
    with pytest.raises(ValueError, match="budget"):
        C.run_campaign(camp, Bad(), obs)
