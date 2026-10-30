"""Software contracts of the functional-rule-revision pilot (synthetic fixtures only; no biological evidence)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from tests.fixtures import functional_rule_revision as fx

MODS = fx.load_study()
adapter, design, models, evaluation, llm_arm, study = (MODS[k] for k in ("adapter", "design", "models", "evaluation", "llm_arm", "study"))


def pipeline(ctx, out, proposer=None, *, stop_after=None):
    out.mkdir(parents=True, exist_ok=True)
    freeze = study.stage_freeze(ctx, out, here=fx.STUDY)
    trace = study.stage_challenge(ctx, out, freeze, proposer=proposer)
    if stop_after == "challenge":
        return freeze, trace, None, None
    retention = study.stage_retention(ctx, out, freeze)
    if stop_after == "retention":
        return freeze, trace, retention, None
    results = study.stage_final(ctx, out, freeze)
    return freeze, trace, retention, results


def strip_clock(obj):
    if isinstance(obj, dict):
        return {k: strip_clock(v) for k, v in obj.items() if k not in ("seconds", "latency_seconds")}
    if isinstance(obj, list):
        return [strip_clock(v) for v in obj]
    return obj


# ----------------------------------------------------------------------------- partition and identity
def test_partition_is_disjoint_by_pair_and_keeps_all_cells_together(tmp_path):
    ctx, table, roles = fx.build_context(MODS, tmp_path)
    assert set(roles) == {"S", "C", "G", "F"}
    for role in "SCGF":
        pairs_in_role = {int(p) for p in table.g_pair[ctx.role_g == role]}
        assert pairs_in_role == {k for k, r in enumerate(roles) if r == role}
    for p in range(len(table.pairs)):                       # every cell of a pair carries the same role
        assert len(set(ctx.role_g[table.g_pair == p])) == 1
    degree = {d: 0 for d in table.drugs}
    for pair, role in zip(table.pairs, roles):
        if role == "S":
            degree[pair[0]] += 1
            degree[pair[1]] += 1
    assert min(degree.values()) >= 6


def test_ab_swap_and_dose_swap_leave_groups_unchanged():
    comb, single = fx.comb_and_single(swap_orientation=False)
    swapped, single_b = fx.comb_and_single(swap_orientation=True)
    t1, o1 = adapter.build_groups(comb, single)
    t2, o2 = adapter.build_groups(swapped, single_b)
    assert t1.pairs == t2.pairs and t1.eligible.all() and t2.eligible.all()
    np.testing.assert_allclose(t1.a_ref, t2.a_ref)
    np.testing.assert_allclose(o1["a_obs"], o2["a_obs"])
    np.testing.assert_allclose(t1.a_mono_i, t2.a_mono_i)


def test_reference_is_derived_never_extrapolated_and_not_borrowed_across_batches():
    comb, single = fx.comb_and_single(drop_mono_batch=True)   # single-agent curves exist only in batch 2
    table, outcomes = adapter.build_groups(comb, single)
    assert not table.eligible.any() and set(table.reason) == {"missing_same_batch_monotherapy"}
    assert np.isnan(table.a_ref).all() and np.isnan(outcomes["a_obs"]).all()   # no cross-batch fallback
    comb2, single2 = fx.comb_and_single(mono_range="narrow")  # combination doses fall outside the curve range
    table2, _ = adapter.build_groups(comb2, single2)
    assert not table2.eligible.any() and "dose_outside_monotherapy_range" in set(table2.reason)


def test_endpoint_is_equal_weight_mean_without_clipping():
    comb, single = fx.comb_and_single()
    comb["x"][:16] = np.linspace(-0.5, 1.8, 16)               # values outside [0, 1] must pass through unchanged
    table, outcomes = adapter.build_groups(comb, single)
    first = int(np.nonzero(table.first_row == comb["row"][0])[0][0])
    assert outcomes["a_obs"][first] == pytest.approx(1.0 - float(np.mean(comb["x"][:16])))
    assert table.n_dose_matched[first] <= 16


# ----------------------------------------------------------------------------- access restrictions
def test_vault_orders_and_single_use(tmp_path):
    ctx, table, roles = fx.build_context(MODS, tmp_path)
    vault = ctx.vault
    vault.source()
    with pytest.raises(adapter.AccessViolation):
        vault.retention_query("revision", lambda y: y)          # G closed before disclosure
    c_pairs = [p for p, r in enumerate(roles) if r == "C"]
    with pytest.raises(adapter.AccessViolation):
        vault.disclose_challenge([p for p, r in enumerate(roles) if r == "F"][:1])   # panel outside C
    y = vault.disclose_challenge(c_pairs[:3])
    assert np.isfinite(y).sum() == 3 * len(table.cells) and not np.isfinite(y[ctx.role_g != "C"]).any()
    with pytest.raises(adapter.AccessViolation):
        vault.disclose_challenge(c_pairs[:3])
    with pytest.raises(adapter.AccessViolation):
        vault.final_evaluation(lambda y: y)                      # F closed until a retention query exists
    vault.retention_query("revision", lambda y: np.isfinite(y).sum())
    with pytest.raises(adapter.AccessViolation):
        vault.retention_query("revision", lambda y: y)           # one G query per arm
    vault.final_evaluation(lambda y: y)
    with pytest.raises(adapter.AccessViolation):
        vault.final_evaluation(lambda y: y)


def test_closed_role_files_are_not_opened_before_their_stage(tmp_path):
    ctx, table, roles = fx.build_context(MODS, tmp_path, g_poison=lambda r, n: np.full(n, np.nan), f_poison=lambda r, n: np.full(n, np.nan))
    out = tmp_path / "out"
    _, trace, _, _ = pipeline(ctx, out, stop_after="challenge")
    ops = [e["op"] for e in trace["vault_ledger"]]
    assert "G_query" not in ops and "F_final" not in ops and ops.count("disclose_C") == 1
    (tmp_path / "sealed" / "outcomes_G.npy").unlink()            # a missing closed file proves it is never needed pre-G
    (tmp_path / "sealed" / "outcomes_F.npy").unlink()
    ctx2, _, _ = fx.build_context(MODS, tmp_path / "again")
    pipeline(ctx2, tmp_path / "out2", stop_after="challenge")


def test_pre_evaluation_artifacts_are_invariant_to_hidden_f_and_g_labels(tmp_path):
    outs = []
    for k, (f_poison, g_poison) in enumerate([(None, None),
                                              (lambda r, n: 1e6 * r.standard_normal(n), lambda r, n: -1e6 * r.random(n))]):
        ctx, _, _ = fx.build_context(MODS, tmp_path / f"w{k}", f_poison=f_poison, g_poison=g_poison)
        out = tmp_path / f"o{k}"
        pipeline(ctx, out, stop_after="challenge")
        outs.append(out)
    for name in ("FREEZE.json", "PRECHALLENGE_PREDICTIONS.json", "NOMINATIONS_SEALED.json", "RULES.json", "CHALLENGE_TRACE.json"):
        a, b = (strip_clock(json.loads((o / name).read_text(encoding="utf-8"))) for o in outs)
        a.pop("code_sha256", None), b.pop("code_sha256", None)
        assert a == b, name
    za, zb = (np.load(o / "SEALED_PREDICTIONS.npz") for o in outs)
    assert za.files == zb.files
    for key in za.files:
        np.testing.assert_array_equal(za[key], zb[key])


def test_g_labels_affect_only_the_retention_decision_and_f_labels_nothing_before_final(tmp_path):
    results = []
    for k, g_poison in enumerate([None, lambda r, n: -5.0 * np.ones(n)]):
        ctx, _, _ = fx.build_context(MODS, tmp_path / f"w{k}", g_poison=g_poison)
        out = tmp_path / f"o{k}"
        _, trace, retention, _ = pipeline(ctx, out, stop_after="retention")
        results.append((out, retention, trace))
    (o0, r0, t0), (o1, r1, t1) = results
    assert (o0 / "NOMINATIONS_SEALED.json").read_bytes() == (o1 / "NOMINATIONS_SEALED.json").read_bytes()
    assert json.loads((o0 / "RULES.json").read_text()) == json.loads((o1 / "RULES.json").read_text())
    assert strip_clock(t0["arms"]) == strip_clock(t1["arms"])
    ctx_f = [fx.build_context(MODS, tmp_path / f"f{k}", f_poison=fp)[0] for k, fp in enumerate([None, lambda r, n: 9.0 * np.ones(n)])]
    reten = []
    for k, c in enumerate(ctx_f):
        _, _, ret, _ = pipeline(c, tmp_path / f"of{k}", stop_after="retention")
        reten.append(ret["decisions"])
    assert reten[0] == reten[1]                                  # F labels cannot touch the retention decision


# ----------------------------------------------------------------------------- structure and fallback
def test_one_edit_common_histories_full_dictionary_and_rule_records(tmp_path):
    ctx, table, roles = fx.build_context(MODS, tmp_path)
    out = tmp_path / "out"
    freeze, trace, retention, results = pipeline(ctx, out)
    assert freeze["dictionary_size"] == len(ctx.rules) <= 16
    assert trace["common_training_set"]["n_groups"] > 0
    arms = trace["arms"]
    assert arms["fulldict"]["candidate"] == "ALL_EDITS"
    sealed = np.load(out / "SEALED_PREDICTIONS.npz")
    rules = json.loads((out / "RULES.json").read_text(encoding="utf-8"))
    chosen = arms["revision"]["candidate"]
    if chosen is not None:                                       # an edit was proposed: one id, executable record, effect on unmeasured pairs
        rec = rules["revision"]
        assert rec["edit"]["id"] == chosen and chosen in {r.id for r in ctx.rules}
        assert rec["after"]["edit_coefficients"] and not rec["before"]["edit_coefficients"]
        assert rec["after"]["n_parameters"] == rec["before"]["n_parameters"] + 1
        assert rec["scope"]["pairs_among_unmeasured"] > 1
        assert rec["effect_on_unmeasured"]["mean_abs_change_in_scope"] > 0
        assert (out / "RULE_EFFECTS_revision.csv").exists()
        diff = sealed["resid_revision"] - sealed["resid_refit"]
        assert np.abs(diff).max() > 0
    assert set(results["methods"]) >= {"refit", "initial", "revision_deployed", "fulldict_deployed", "conventional_deployed", "bliss_reference"}


def test_structural_edit_is_not_a_refit(tmp_path):
    ctx, _, _ = fx.build_context(MODS, tmp_path)
    store = ctx.store
    rows = ctx.rows_S
    y = np.random.default_rng(0).standard_normal(len(rows)) * 0.02
    refit_a = models.fit_ridge(store, rows, y, (), (1.0, 3.0))
    refit_b = models.fit_ridge(store, rows, y, (), (30.0, 10.0))       # different coefficients, same structure
    assert refit_a.edits == refit_b.edits == () and len(refit_a.cols) == len(refit_b.cols)
    rule = ctx.rules[0]
    edited = models.fit_ridge(store, rows, y, (rule.id,), (1.0, 3.0))
    assert len(edited.cols) == len(refit_a.cols) + 1 and edited.edits == (rule.id,)
    assert store.names[store.edit_index[rule.id]].startswith("edit_")


def test_unknown_condition_is_never_satisfied():
    gates = {"glob": np.array([1, 0, -1]), "m0": np.array([1, 1, -1]), "m1": np.array([0, 1, -1]), "m2": np.array([0, 0, 1])}
    module = np.array([0, 1, 2, 0])
    g_i, g_j, g_cell = np.array([0, 0, 0]), np.array([1, 1, 1]), np.array([0, 1, 2])
    rule = design.Rule("E01", "split", "X", "glob", None)
    np.testing.assert_array_equal(design.rule_column(rule, g_i, g_j, g_cell, module, gates), [1.0, 0.0, 0.0])
    gates2 = design.make_gates(np.array([[0.2, np.nan, 0.8], [0.4, np.nan, 0.6]]), np.array([0, 0]))
    assert gates2["glob"][1] == -1                                         # no measurement -> unknown, not satisfied


def test_g_rejection_falls_back_to_the_refit_and_f_is_still_evaluated(tmp_path):
    cfg = fx.small_config(study)
    ctx, _, _ = fx.build_context(MODS, tmp_path, cfg=cfg)
    out = tmp_path / "out"
    out.mkdir()
    freeze = study.stage_freeze(ctx, out, here=fx.STUDY)
    freeze["retention_tau"] = 10.0                                         # unattainable threshold: every candidate is rejected
    study.jdump(out / "FREEZE.json", freeze)
    study.stage_challenge(ctx, out, freeze)
    retention = study.stage_retention(ctx, out, freeze)
    assert all(not d["accepted"] for d in retention["decisions"].values())
    assert all(d["deployed"] == "refit" for d in retention["decisions"].values())
    results = study.stage_final(ctx, out, freeze)
    m = results["methods"]
    assert m["revision_deployed"]["utility"] == m["refit"]["utility"] and m["conventional_deployed"]["utility"] == m["refit"]["utility"]
    assert m["revision_deployed"]["changes_vs_refit_groups"] == 0
    assert results["vault_ledger"][-1]["op"] == "F_final"


# ----------------------------------------------------------------------------- metrics and verdict
def test_shortlist_ties_and_utility():
    pred = np.array([[0.5], [0.5], [0.4], [0.9], [0.5], [0.1]])
    truth = np.array([[0.1], [0.2], [0.3], [0.4], [0.5], [0.6]])
    sel = evaluation.top_k(pred, 3)
    assert list(sel[:, 0]) == [3, 0, 1]                                    # highest first; ties by smaller row (pair id)
    assert evaluation.utility(pred, truth, k=3) == pytest.approx((0.4 + 0.1 + 0.2) / 3)
    assert evaluation.oracle_utility(truth, k=3) == pytest.approx((0.6 + 0.5 + 0.4) / 3)


def test_pair_bootstrap_resamples_whole_pairs_and_reselects():
    rng = np.random.default_rng(0)
    truth = rng.random((30, 5))
    good = truth + 0.01 * rng.standard_normal(truth.shape)
    bad = rng.random(truth.shape)
    draws, utils, _ = evaluation.paired_bootstrap({"good": good, "bad": bad}, truth, [("good", "bad")], n_boot=100, seed=3)
    assert (draws[("good", "bad")] > 0).mean() > 0.95 and len(utils["good"]) == 100


def test_verdict_logic():
    def prim(est, lb, jk):
        return {"estimate": est, "lower_bound_pair_bootstrap": lb, "lower_bound_drug_jackknife": jk, "upper_bound_pair_bootstrap": est + 0.01}
    base = {"primary": {n: prim(0.006, 0.001, 0.0005) for n in ("vs_refit", "vs_full_dictionary", "vs_conventional")},
            "revision_retained_at_G": True,
            "raw_candidate_vs_refit": {"upper_bound_pair_bootstrap": 0.02},
            "standard_vs_refit": {"full_dictionary": {"lower_bound_pair_bootstrap": -0.01}, "conventional": {"lower_bound_pair_bootstrap": -0.01}}}
    assert study.decide(base, 0.004)["label"] == "PROMISING_INTERNAL_DEVELOPMENT"
    weak = json.loads(json.dumps(base))
    weak["primary"]["vs_conventional"]["lower_bound_pair_bootstrap"] = -0.001
    assert study.decide(weak, 0.004)["label"] == "INCONCLUSIVE"
    excluded = json.loads(json.dumps(base))
    excluded["revision_retained_at_G"] = False
    excluded["raw_candidate_vs_refit"]["upper_bound_pair_bootstrap"] = 0.001
    excluded["standard_vs_refit"]["conventional"]["lower_bound_pair_bootstrap"] = 0.002
    verdict = study.decide(excluded, 0.004)
    assert verdict["label"] == "UNSUPPORTED" and verdict["STANDARD_STRUCTURE_LEARNING_SUFFICIENT_flag"]


# ----------------------------------------------------------------------------- API arm
class FakeClient:
    def __init__(self, answer=None, error=None):
        self.answer, self.error, self.calls = answer, error, 0

    def complete_json(self, messages, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return self.answer, type("R", (), {"model": "fake", "usage": {"prompt_tokens": 1, "completion_tokens": 1}})()


def _proposer(client, forbidden=("drug00",)):
    def run(summary, allowed, legal):
        return llm_arm.propose(summary, allowed, legal, forbidden, client, count_attempts=lambda: client.calls).as_dict()
    return run


def test_api_allowed_edit_validation_and_no_edit():
    summary = {"edit_menu": [{"id": "E01"}], "largest_counterexamples": [{"obs": "O001"}]}
    ok = llm_arm.propose(summary, ["E01"], ["O001"], [], FakeClient({"edit_id": "E01", "cited_observation_ids": ["O001"], "rationale": "x"}))
    assert ok.outcome == "VALID_EDIT" and ok.selected == "E01"
    none = llm_arm.propose(summary, ["E01"], ["O001"], [], FakeClient({"edit_id": "NO_EDIT", "cited_observation_ids": []}))
    assert none.outcome == "VALID_NO_EDIT"
    for answer in ({"edit_id": "E99", "cited_observation_ids": []}, {"edit_id": "E01", "cited_observation_ids": ["O777"]},
                   {"edit_id": "E01", "cited_observation_ids": ["O001"] * 7}):
        assert llm_arm.propose(summary, ["E01"], ["O001"], [], FakeClient(answer)).outcome == "INVALID_RESPONSE"


def test_api_rejects_forbidden_payloads_and_oversized_prompts():
    summary = {"note": "this mentions Drug00 and a label"}
    assert llm_arm.propose(summary, ["E01"], [], ["drug00"], FakeClient({})).outcome == "PAYLOAD_REFUSED"
    huge = {"blob": "x" * 40000}
    receipt = llm_arm.propose(huge, ["E01"], [], [], FakeClient({}))
    assert receipt.outcome == "PAYLOAD_REFUSED" and "input tokens" in receipt.error


def test_api_failure_falls_back_without_extra_search(tmp_path):
    ctx, _, _ = fx.build_context(MODS, tmp_path)
    client = FakeClient(error=RuntimeError("down"))
    freeze, trace, _, results = pipeline(ctx, tmp_path / "out", _proposer(client))
    assert client.calls == 1                                              # one logical request, no repair loop
    assert trace["arms"]["api"]["candidate"] is None and "FALLBACK_TO_REFIT" in trace["arms"]["api"]["reason"]
    assert results["methods"]["api_deployed"]["utility"] == results["methods"]["refit"]["utility"]


def test_api_valid_edit_is_compiled_locally_and_shares_the_same_gate(tmp_path):
    ctx, _, _ = fx.build_context(MODS, tmp_path)
    client = FakeClient({"edit_id": "E02", "cited_observation_ids": [], "rationale": "r"})
    _, trace, retention, _ = pipeline(ctx, tmp_path / "out", _proposer(client), stop_after="retention")
    assert trace["arms"]["api"]["candidate"] == "E02" and retention["decisions"]["api"]["candidate_available"]
    assert "api" in retention["vault_ledger_after_G"][-1]["arm"] or any(e.get("arm") == "api" for e in retention["vault_ledger_after_G"])


def test_attempt_counter_enforces_the_http_budget():
    class Module:
        _MAX_ATTEMPTS = 4
        calls = 0

        @staticmethod
        def urlopen(*a, **k):
            Module.calls += 1
            raise OSError("no network in tests")

    with llm_arm.AttemptCounter(Module, limit=3) as counter:
        assert Module._MAX_ATTEMPTS == 3
        for _ in range(2):
            with pytest.raises(OSError):
                Module.urlopen()
        assert counter() == 2
    assert Module._MAX_ATTEMPTS == 4 and Module.urlopen.__name__ == "urlopen"


def test_api_payload_contains_only_opaque_identifiers(tmp_path):
    ctx, table, _ = fx.build_context(MODS, tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    freeze = study.stage_freeze(ctx, out, here=fx.STUDY)
    study.stage_challenge(ctx, out, freeze, proposer=_proposer(FakeClient({"edit_id": "NO_EDIT", "cited_observation_ids": []})))
    sent = (out / "API_SUMMARY_SENT.json").read_text(encoding="utf-8").lower()
    for name in list(table.drugs) + list(table.cells) + ["oneil", "o'neil", "almanac", "figshare"]:
        assert name.lower() not in sent
    assert "outcome" not in json.loads(sent)
