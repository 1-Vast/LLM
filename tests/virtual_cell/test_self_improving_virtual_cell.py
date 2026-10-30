"""Software contracts of the self-improving virtual-cell prototype. Synthetic worlds only; passing says nothing about biology."""
from __future__ import annotations

import copy
import json

import numpy as np
import pytest

from tests.fixtures import self_improving_virtual_cell as fx

M = fx.load()
W, P, E, S, SM, L = (M[k] for k in ("svc_world", "svc_programs", "svc_evolution", "svc_study", "svc_summarize", "svc_llm"))


@pytest.fixture(scope="module")
def world():
    return W.make_synthetic("compositional", 3, n_drugs=12, n_cells=24)


def cells_of(world):
    return E.split_cells(world.cells, "synthetic")


def history_all(cells):
    return cells["H0"] + cells["D1"] + cells["D2"] + cells["D3"]


def replace_truth(world, column_cell, values):
    t = world._World__truth.copy()
    t[:, world._index[column_cell]] = values
    return W.World(world.static, world.cells, world._Aref, world._amin, world._amax, t)


# ----------------------------------------------------------------------------- information isolation
@pytest.mark.parametrize("contract", ["E", "T"])
def test_decisions_do_not_depend_on_unqueried_outcomes(world, contract):
    cells = cells_of(world)
    target = cells["T"][0]
    static, hist_cells = world.static, history_all(cells)
    first = E.run_arm_on_cell({"kind": "program", "spec": P.base_spec()}, world, E.Memo(world), static, target, hist_cells, 8, 0, contract)
    truth = world.truth_column(target).copy()
    keep = np.zeros(static.n, bool)
    keep[first["queried"]] = True
    truth[~keep] += np.random.default_rng(5).normal(0, 0.3, (~keep).sum())   # poison everything that was not queried
    poisoned = replace_truth(world, target, truth)
    second = E.run_arm_on_cell({"kind": "program", "spec": P.base_spec()}, poisoned, E.Memo(poisoned), static, target, hist_cells, 8, 0, contract)
    assert first["queried"] == second["queried"] and first["nominated"] == second["nominated"]
    assert np.allclose(first["pred"], second["pred"]) and np.allclose(first["z"], second["z"])


def test_fit_uses_only_released_history(world):
    cells = cells_of(world)
    static = world.static
    h = world.history(cells["H0"])
    base = P.fit_program(P.base_spec(), h, P.HistoryCache(h), static, 8, 0)
    t = world._World__truth.copy()
    for c in cells["T"] + cells["A"]:
        t[:, world._index[c]] += 1.0                      # change every non-released column
    w2 = W.World(static, world.cells, world._Aref, world._amin, world._amax, t)
    h2 = w2.history(cells["H0"])
    other = P.fit_program(P.base_spec(), h2, P.HistoryCache(h2), static, 8, 0)
    assert np.allclose(base.coef, other.coef) and base.history_version == other.history_version


def test_held_out_cell_is_never_in_its_own_fit(world):
    cells = cells_of(world)
    with pytest.raises(AssertionError):
        E.run_arm_on_cell({"kind": "zero"}, world, E.Memo(world), world.static, cells["H0"][0], cells["H0"], 8, 0, "E")


# ----------------------------------------------------------------------------- dose / reference validity
def test_reference_and_scale_validity_on_exported_environment():
    path = W.WORK / "env_export.npz"
    if not path.exists():
        pytest.skip("allowlisted export not present")
    z = np.load(path, allow_pickle=False)
    A, Aref, amin, amax = z["A"], z["Aref"], z["amin"], z["amax"]
    assert np.isfinite(A).all() and np.isfinite(Aref).all() and (amin <= amax + 1e-12).all()
    assert A.shape == (410, 39) and set(z["pair_role"].tolist()) == {"S", "C"}
    assert (z["pair_role"] == "C").sum() == 60 and (z["pair_role"] == "S").sum() == 350
    assert -0.5 < A.min() and A.max() < 1.5 and Aref.max() <= 1.0 + 1e-9
    # the derived reference is a function of the two monotherapy summaries only (multiplicative survival), never of combination outcomes
    assert np.allclose(Aref, 1 - (1 - amin) * (1 - amax), atol=1e-9)
    nonneg = amin >= 0
    assert (Aref[nonneg] >= amax[nonneg] - 1e-9).all()  # without growth stimulation the reference cannot fall below the stronger single agent


def test_anchor_only_control_keeps_shared_effects_and_breaks_pair_specific_structure(world):
    ctrl = world.anchor_only(seed=1)
    R0 = world._World__truth - world._Aref
    R1 = ctrl._World__truth - ctrl._Aref
    assert np.allclose(world._Aref, ctrl._Aref) and np.allclose(world._amin, ctrl._amin)
    st = world.static
    D = np.zeros((st.n, st.n_drugs + 1))
    D[np.arange(st.n), st.pair_i] = 1
    D[np.arange(st.n), st.pair_j] = 1
    D[:, -1] = 1
    proj = D @ np.linalg.lstsq(D, R0, rcond=None)[0]
    proj1 = D @ np.linalg.lstsq(D, R1, rcond=None)[0]
    assert np.corrcoef(proj.ravel(), proj1.ravel())[0, 1] > 0.9          # shared drug-cell effects retained
    res0, res1 = (R0 - proj).ravel(), (R1 - proj1).ravel()
    assert abs(np.corrcoef(res0, res1)[0, 1]) < 0.2                      # pair-specific relationship broken


# ----------------------------------------------------------------------------- serialisation
@pytest.mark.parametrize("contract", ["E", "T"])
def test_saved_program_reloads_and_reproduces_predictions(world, contract):
    cells = cells_of(world)
    static = world.static
    h = world.history(history_all(cells))
    cache = P.HistoryCache(h)
    spec = {"phi": [{"t": "global"}, {"t": "class", "a": 0, "b": 1}, {"t": "latent", "k": 2}],
            "Q": [{"kind": "probe", "frac": 0.5, "rule": "coverage", "cond": None},
                  {"kind": "probe", "frac": 0.25, "rule": "witness", "cond": {"coord": 1, "thr": 0.3, "else": "confirm"}}, {"kind": "confirm", "frac": 0.25}],
            "f": {"type": "ridge", "inter": ["class", "anchor"], "lam": 3.0}}
    assert not P.validate_spec(spec, static)
    cell = cells["T"][0]
    probe, pool = E.task_masks(static, cell, 0, contract)
    fit = P.fit_program(spec, h, cache, static, 8, 0, transfer=(contract == "T"), probe_mask=probe)
    reloaded = P.Fitted.from_json(json.loads(json.dumps(fit.to_json())))
    outs = []
    for f in (fit, reloaded):
        camp = world.campaign(cell, 8, probe_mask=probe)
        outs.append(P.run_program(f, static, camp, np.random.default_rng(1), pool_mask=pool, transfer=(contract == "T")))
    assert outs[0]["nominated"] == outs[1]["nominated"] and np.allclose(outs[0]["final_prediction"], outs[1]["final_prediction"], atol=1e-12)
    assert reloaded.history_version == h.version and len(reloaded.coef) == len(fit.coef)


def test_gradient_boosted_baselines_are_not_claimed_as_serialisable_programs(world):
    cells = cells_of(world)
    h = world.history(cells["H0"])
    spec = {**P.base_spec(), "f": {"type": "gbm", "inter": [], "lam": 3.0}}
    fit = P.fit_program(spec, h, P.HistoryCache(h), world.static, 8, 0)
    with pytest.raises(TypeError):
        fit.to_json()


def test_grammar_rejects_unknown_structure(world):
    st = world.static
    good = P.base_spec()
    assert not P.validate_spec(good, st)
    bad = []
    s = copy.deepcopy(good); s["extra"] = 1; bad.append(s)
    s = copy.deepcopy(good); s["phi"].append({"t": "global"}); bad.append(s)
    s = copy.deepcopy(good); s["phi"].append({"t": "mystery"}); bad.append(s)
    s = copy.deepcopy(good); s["Q"][0]["frac"] = 0.3; bad.append(s)
    s = copy.deepcopy(good); s["Q"][0]["rule"] = "bayes_voi"; bad.append(s)          # baseline-only rule is not in the proposer grammar
    s = copy.deepcopy(good); s["Q"] = [s["Q"][1], s["Q"][0]]; bad.append(s)           # confirm must be last
    s = copy.deepcopy(good); s["f"]["type"] = "forest"; bad.append(s)
    s = copy.deepcopy(good); s["phi"].append({"t": "class", "a": 9, "b": 9}); bad.append(s)
    for spec in bad:
        assert P.validate_spec(spec, st), spec


# ----------------------------------------------------------------------------- budget accounting and nominations
def test_budget_probe_mask_and_reread_accounting(world):
    st = world.static
    mask = np.zeros(st.n, bool)
    mask[:20] = True
    camp = world.campaign(world.cells[0], 3, probe_mask=mask)
    camp.query([0, 1, 1, 0], "probe")
    assert camp.spent == 2 and camp.left == 1                          # repeated reads of the same unit count once
    with pytest.raises(W.IllegalAction):
        camp.query([30], "probe")
    camp.query([2], "probe")
    with pytest.raises(W.BudgetExceeded):
        camp.query([3], "probe")
    assert camp.spent == 3


@pytest.mark.parametrize("contract", ["E", "T"])
def test_every_arm_respects_budget_pool_and_has_unique_nominations(world, contract):
    cells = cells_of(world)
    static, hist_cells = world.static, history_all(cells)
    memo = E.Memo(world)
    for name, arm in E.baseline_arms().items():
        if contract == "T" and name == "direct":
            continue
        for cell in cells["T"][:2]:
            r = E.run_arm_on_cell(arm, world, memo, static, cell, hist_cells, 8, 0, contract)
            probe, pool = E.task_masks(static, cell, 0, contract)
            assert r["spent"] <= 8 and len(set(r["nominated"])) == len(r["nominated"]) == W.SHORTLIST_K
            assert all(pool[p] for p in r["nominated"])
            if contract == "T":
                assert all(probe[p] for p in r["queried"]) and not set(r["queried"]) & set(r["nominated"])
            assert r["n_nominated_queried"] <= r["spent"]


def test_duplicate_or_out_of_pool_nomination_is_refused(world):
    camp = world.campaign(world.cells[0], 4)
    pool = np.ones(world.static.n, bool)
    with pytest.raises(AssertionError):
        W.realized_utility(world, camp, [1, 1, 2, 3, 4], pool)
    pool[7] = False
    with pytest.raises(AssertionError):
        W.realized_utility(world, camp, [7, 1, 2, 3, 4], pool)


def test_direct_confirmation_counts_recorded_values_and_reports_the_unqueried_endpoint_separately(world):
    cells = cells_of(world)
    r = E.run_arm_on_cell({"kind": "direct"}, world, E.Memo(world), world.static, cells["T"][0], history_all(cells), 8, 0, "E")
    assert r["n_nominated_queried"] > 0
    truth = world.truth_column(cells["T"][0])
    assert np.isclose(r["utility"], truth[r["nominated"]].mean())          # recorded outcomes, not imputations
    unq = [p for p in r["nominated"] if p not in r["queried"]]
    assert (r["unqueried_only_utility"] is None) == (not unq)


# ----------------------------------------------------------------------------- evolution, library rules and inheritance ablations
def test_operator_sets_isolate_representation_from_procedure(world):
    cells = cells_of(world)
    base = P.base_spec()
    for ops, frozen_key in ((E.REPR_OPS, "Q"), (E.PROC_OPS, "phi")):
        lib, inc, recs, final = E.evolve("t", world, E.Memo(world), world.static, cells, 0, 8, "E", ops, generations=1)
        assert recs[0]["candidate_specs"], "operators produced no candidates"
        for s in recs[0]["candidate_specs"]:
            assert s[frozen_key] == base[frozen_key]


def test_no_inheritance_restarts_every_generation_from_the_base_program(world):
    cells = cells_of(world)
    lib, inc, recs, final = E.evolve("ni", world, E.Memo(world), world.static, cells, 0, 8, "E", E.REPR_OPS + E.PROC_OPS, inherit=False, generations=3)
    root = lib.entries[0]["id"]
    assert all(e["parent"] in (None, root) for e in lib.entries)


def test_provisional_programs_are_demonstrated_or_retired_with_parent_restored(world):
    cells = cells_of(world)
    lib = E.Library("v")
    root = lib.add(P.base_spec(), None, "base", 0, "demonstrated")
    bad = {**P.base_spec(), "Q": [{"kind": "probe", "frac": 1.0, "rule": "random", "cond": None}], "f": {"type": "ridge", "inter": [], "lam": 1000.0}}
    prov = lib.add(bad, root["id"], "manual", 1, "provisional")
    hist = cells["H0"] + cells["D1"]
    out, retired = E.validate(lib, prov, cells["D1"], hist, "v", world, E.Memo(world), world.static, 8, 0, "E", {})
    assert prov["status"] in ("demonstrated", "retired")
    assert (prov["status"] == "retired") == (out is root and retired == prov["id"])
    assert "validation" in prov["evidence"]


def test_diagnosis_can_decline_when_nothing_explains_the_data():
    w = W.make_synthetic("null_anchor", 1, n_drugs=12, n_cells=24)
    cells = E.split_cells(w.cells, "synthetic")
    verdicts = [E.diagnose(w, E.Memo(w), w.static, {"kind": "program", "spec": P.base_spec()}, cells["H0"] + cells["D1"], 8, seed, "T")["verdict"] for seed in range(3)]
    assert set(verdicts) <= {"explainable", "no_program_explains", "direct_confirmation_dominates"}
    assert "no_program_explains" in verdicts          # a pure shared-anchor world should not always produce an explanation


def test_compositional_positive_control_is_expressible_in_the_grammar():
    w = W.make_synthetic("compositional", 0, n_drugs=12, n_cells=24)
    cl = w.static.classes
    tc = w.meta["target_classes"] + [w.meta["conjunction_class"]]
    spec = {"phi": [{"t": "global"}] + [{"t": "class", "a": cl[c][0], "b": cl[c][1]} for c in tc],
            "Q": [{"kind": "probe", "frac": 0.75, "rule": "witness", "cond": None}, {"kind": "confirm", "frac": 0.25}], "f": {"type": "ridge", "inter": [], "lam": 3.0}}
    assert not P.validate_spec(spec, w.static)


@pytest.mark.parametrize("kind", ["null_anchor", "low_rank", "compositional"])
def test_synthetic_pipeline_runs_end_to_end_and_budget_is_common(kind):
    w = W.make_synthetic(kind, 0, n_drugs=12, n_cells=24)
    r = S.run_condition(w, "synthetic", 8, "T", 0, generations=1)
    assert {"evo_full", "evo_repr", "evo_proc", "evo_noinherit", "refit", "frozen_library", "parameter_only", "hindsight_superset_DIAGNOSTIC"} <= set(r["test"])
    assert all(len(v) == 8 for v in r["test"].values())
    assert all(d["spent"] <= 8 for rows in r["test_detail"].values() for d in rows)
    assert "direct" not in r["test"]                                    # not a legal action under the transfer contract
    json.dumps(r, default=float)


# ----------------------------------------------------------------------------- summaries
def test_descriptive_summary_is_paired_and_has_no_confidence_claim():
    d = SM.describe(np.array([0.01, -0.02, 0.0, 0.03]))
    assert d["wins"] == 2 and d["losses"] == 1 and d["ties"] == 1 and "ci" not in d
    assert SM.label(None, 0.005) == "NOT_RUN"
    assert SM.label({"n_cells": 10, "mean": 0.02, "wins": 8}, 0.005) == "SUPPORTED_DEV"
    assert SM.label({"n_cells": 10, "mean": 0.02, "wins": 8}, 0.005, {"mean": 0.015}) == "ANCHOR_CONFOUNDED"
    assert SM.label({"n_cells": 10, "mean": -0.01, "wins": 3}, 0.005) == "NOT_SUPPORTED"


# ----------------------------------------------------------------------------- API arm (fake client; no network)
class FakeResponse:
    model = "fake"
    usage = {"prompt_tokens": 900, "completion_tokens": 120}


class FakeClient:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def complete_json(self, messages, max_tokens=1024):
        self.calls += 1
        return self.replies.pop(0), FakeResponse()


class FakeLlm:
    _MAX_ATTEMPTS = 3

    def urlopen(self, *a, **k):
        raise AssertionError("no network in tests")


def fake_proposer(world, replies):
    p = L.ApiProposer.__new__(L.ApiProposer)
    p.static, p.seed, p.contract, p.budget = world.static, 0, "T", 8
    p.to_class, p.to_opaque = L.opaque_ids(world.static, 0)
    p.receipts, p.tokens, p.attempts, p.config_error = [], 0, 0, None
    p.client, p.llm = FakeClient(replies), FakeLlm()
    return p


def small_diag(world):
    cells = cells_of(world)
    return E.diagnose(world, E.Memo(world), world.static, {"kind": "program", "spec": P.base_spec()}, cells["H0"], 8, 0, "T"), cells


def test_api_candidates_are_validated_before_execution_and_logged_with_opaque_ids(world):
    diag, cells = small_diag(world)
    kid = next(iter(L.opaque_ids(world.static, 0)[0]))
    good = {"decision": "propose", "cited": ["E1"], "rationale": "x",
            "program": {"phi": [{"t": "global"}, {"t": "class", "id": kid}], "Q": [{"kind": "probe", "frac": 1.0, "rule": "witness", "cond": None}], "f": {"type": "ridge", "inter": [], "lam": 3.0}}}
    p = fake_proposer(world, [good, {"decision": "propose", "program": {"phi": [{"t": "class", "a": 0, "b": 0}]}, "cited": ["E1"]},
                              {"decision": "propose", "program": {}, "cited": ["E99"]}, {"decision": "none", "cited": []}])
    out = [p.candidates(g, diag, P.base_spec(), cells["H0"]) for g in range(4)]
    assert [len(o) for o in out] == [1, 0, 0, 0]
    assert not P.validate_spec(out[0][0]["spec"], world.static)
    assert [r["outcome"] for r in p.receipts] == ["VALID_PROGRAM", "INVALID_PROGRAM", "INVALID_RESPONSE", "VALID_NO_PROGRAM"]
    text = json.dumps(p.ledger())
    assert "d00" not in text and p.ledger()["http_attempts"] == 0
    assert p.tokens > 0 and p.ledger()["no_credentials_or_headers_persisted"]


def test_api_cumulative_token_cap_refuses_a_request(world):
    diag, cells = small_diag(world)
    p = fake_proposer(world, [{"decision": "none", "cited": []}])
    p.tokens = L.MAX_TOTAL_TOKENS - 10
    assert p.candidates(1, diag, P.base_spec(), cells["H0"]) == []
    assert p.receipts[-1]["outcome"] == "BUDGET_REFUSED" and p.client.calls == 0


def test_api_failure_is_a_fallback_not_a_blocker(world):
    diag, cells = small_diag(world)
    p = fake_proposer(world, [])
    p.client, p.config_error = None, "RuntimeError"
    assert p.candidates(1, diag, P.base_spec(), cells["H0"]) == []
    assert p.receipts[-1]["outcome"] == "API_FAILURE"
