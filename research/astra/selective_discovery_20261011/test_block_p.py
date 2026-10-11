"""Contract tests for block P (selective discovery). No network, no sealed outcome.

They check the machinery the registered claims depend on:
* the sealed tier refuses by name before the freeze;
* kNN transfer handles missing values and ties as declared;
* the stacked model cannot see a candidate's own profile;
* the campaign ledger reveals exactly the compounds that were bought, and the permutation control
  changes what the agent believes without changing the truth;
* the unexpected-hit definition depends only on the reference set's annotated classes;
* the LLM reply validator refuses malformed selections by name.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import campaign as CA  # noqa: E402
import extract as EX  # noqa: E402
import world as WM  # noqa: E402


def test_sealed_tier_refuses_before_freeze():
    if (HERE / "FREEZE.json").exists():
        pytest.skip("freeze exists; the sealed tier is open by design")
    with pytest.raises(EX.TierSealed) as e:
        EX.load_prism("sealed")
    assert e.value.args[0].startswith("TIER_SEALED")


def test_knn_skips_missing_and_weights_by_similarity():
    S = np.array([[0.9, 0.5, np.nan], [np.nan, np.nan, np.nan]])
    Y = np.array([[1.0, np.nan], [3.0, 4.0], [9.0, 9.0]])
    out, top = WM.knn_profiles(S, Y, k=2)
    assert out[0, 0] == pytest.approx((0.9 * 1.0 + 0.5 * 3.0) / 1.4)
    assert out[0, 1] == pytest.approx(4.0)            # the only reference with a value in column 1
    assert top[0] == pytest.approx(0.9)
    assert np.isnan(out[1]).all() and np.isnan(top[1])


def test_knn_equal_weights_when_similarities_non_positive():
    S = np.array([[-0.2, -0.4]])
    Y = np.array([[2.0], [4.0]])
    out, _ = WM.knn_profiles(S, Y, k=2)
    assert out[0, 0] == pytest.approx(3.0)


def test_concat_cos_ignores_absent_options():
    g = 4
    A = np.full((1, 2, g), np.nan, np.float32)
    A[0, 0] = np.array([1, 0, 0, 0], np.float32)
    B = np.zeros((2, 2, g), np.float32)
    B[0, 0] = np.array([1, 0, 0, 0], np.float32)
    B[0, 1] = np.array([0, 1, 0, 0], np.float32)
    B[1, 0] = np.array([0, 1, 0, 0], np.float32)
    B[1, 1] = np.array([1, 0, 0, 0], np.float32)
    s = WM.concat_cos(A, B)
    assert s[0, 0] == pytest.approx(1.0)              # option 1 is absent in A and does not dilute
    assert s[0, 1] == pytest.approx(0.0)


def _toy():
    """A 6-compound, 4-line universe: lines 0-1 are lineage 'a', 2-3 are 'b'."""
    P = np.array([[-2.0, -2.0, 0.0, 0.0],             # selective for a
                  [-1.8, -2.2, 0.1, -0.1],            # selective for a
                  [0.0, 0.0, -2.0, -2.0],             # selective for b
                  [-1.0, -1.0, -1.0, -1.0],           # broad
                  [0.0, 0.0, 0.0, 0.0],               # inactive
                  [-2.0, -2.0, 0.0, 0.0]], np.float32)
    U = WM.Universe(brd=np.array([f"B{i}" for i in range(6)]), name=np.array([f"c{i}" for i in range(6)]),
                    group=np.array(["blockn"] * 6), P=P, S2=np.full_like(P, np.nan),
                    lines=np.array([f"L{i}" for i in range(4)]), tissue=np.array(["a", "a", "b", "b"]),
                    lineages=["a", "b"], moa=np.array(["x", "x", "y", "z", "w", "v"]),
                    targets=[set() for _ in range(6)], has_p2=np.ones(6, bool), has_p1=np.ones(6, bool))
    sim = np.full((6, 6), 0.5, np.float32)
    np.fill_diagonal(sim, np.nan)
    U.sims = {k: sim.copy() for k in WM.SOURCES}
    cls = (U.moa[:, None] == U.moa[None, :])
    U.sims["klass"] = np.where(cls, 1.0, np.nan).astype(np.float32)
    np.fill_diagonal(U.sims["klass"], np.nan)
    return U


def test_hit_definition_requires_both_contrast_and_depth():
    U = _toy()
    H = U.hits()
    assert H[0, 0] and H[1, 0] and H[2, 1]
    assert not H[3].any()                             # broad killing is not selective
    assert not H[4].any()


def test_stack_never_uses_a_candidate_own_profile():
    U = _toy()
    st = WM.Stack(U, ("chem",)).fit(np.arange(6))
    base = st.score(np.arange(6), np.array([0]))
    U2 = _toy()
    U2.P[0] = 0.0                                     # change only compound 0's own profile
    st2 = WM.Stack(U2, ("chem",))
    st2.mu, st2.sd, st2.model = st.mu, st.sd, st.model
    assert st2.score(np.arange(1, 6), np.array([0])) == pytest.approx(
        st.score(np.arange(1, 6), np.array([0])))


def test_campaign_ledger_reveals_only_bought_compounds():
    U = _toy()
    st = CA.State.start(U, 0, ref=np.array([2, 3, 4]), pool=np.array([0, 1, 5]), budget=2, batch=1)
    st.reveal(U, [0])
    assert [c for _, c in st.screened] == [0]
    assert st.Y.shape[0] == 4 and np.allclose(st.Y[-1], U.P[0])
    assert 0 not in st.left and set(st.left) == {1, 5}


def test_permutation_control_changes_beliefs_not_truth():
    U = _toy()
    truth = U.P[[0, 2]]
    swapped = 0
    for seed in range(8):
        st = CA.State.start(U, 0, ref=np.array([3, 4]), pool=np.array([0, 2]), budget=2, batch=2)
        st.reveal(U, [0, 2], permute_rng=np.random.default_rng(seed))
        believed = st.Y[-2:]
        assert sorted(believed[:, 0].tolist()) == sorted(truth[:, 0].tolist())   # always the same multiset
        assert CA.hits_found(U, st) == int(U.hits()[[0, 2], 0].sum())            # scoring always uses the truth
        swapped += not np.allclose(believed, truth)
    assert swapped > 0, "permutation never changed the revealed profiles"


def test_oof_shape_and_range():
    U = _toy()
    st = WM.Stack(U, ("chem",))
    p = st.oof(np.arange(6), np.arange(6), folds=2, seed=1)
    assert p.shape == (6, 2) and np.all((p >= 0) & (p <= 1))


def test_llm_selection_refusal_codes():
    import conv_agent as CV
    cand = np.arange(5)
    p = np.array([0.5, 0.4, 0.3, 0.2, 0.1])

    class FakeResp:
        usage = {"prompt_tokens": 10, "completion_tokens": 5}
        model = "deepseek-flash"
        finish_reason = "stop"

    class FakeClient:
        def __init__(self, obj):
            self.obj = obj

        def complete_json(self, messages, **kw):
            return self.obj, FakeResp()

    class FakeLedger:
        def reserve(self, *a, **k):
            pass

        def charge(self, *a, **k):
            pass

        def write(self):
            pass

    U = _toy()
    agent = CV.ConvAgent.__new__(CV.ConvAgent)
    agent.U, agent.names, agent.lock = U, U.name, __import__("threading").Lock()
    agent.ledger = FakeLedger()
    st = CA.State.start(U, 0, ref=np.array([3, 4]), pool=cand, budget=2, batch=2)
    agent.client = FakeClient({"picks": [0, 1]})
    picks, rec = agent.choose(st, cand, p, p, 2, "t")
    assert rec["reason_code"] is None and picks == [0, 1] and rec["filled"] == 0
    agent.client = FakeClient({"picks": [0, 1, 2]})
    picks, rec = agent.choose(st, cand, p, p, 2, "t")
    assert rec["reason_code"] == "LLM_INVALID_SELECTION" and len(picks) == 2
    agent.client = FakeClient({"picks": ["not-an-id", 99]})
    picks, rec = agent.choose(st, cand, p, p, 2, "t")
    assert rec["reason_code"] == "LLM_INVALID_SELECTION" and rec["filled"] == 2 and picks == [0, 1]


def test_extract_receipt_records_source_digest_and_disclosure():
    rec = json.loads((HERE / "EXTRACT_RECEIPT.json").read_text(encoding="utf-8"))
    assert len(rec["source_sha512"]) == 128
    assert rec["prism"]["new"]["n"] > 900 and rec["landmark"]["n_compounds"] > 1400
    assert "disclosure" in rec and "325" in rec["disclosure"]
