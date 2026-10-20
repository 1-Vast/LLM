"""Software contracts of the innovation-validation study (synthetic fixtures only). Passing says nothing about whether the mechanism is useful."""
from __future__ import annotations

import contextlib
import io
from pathlib import Path

import numpy as np
import pytest

from tests.fixtures import innovation_validation as fx

M = fx.load()
CORE, GATES, SEARCH, CONV, WORLDS, STATS, REPLAY, EXAMPLE, RUN, VERIFY = (M[k] for k in ("iv_core", "iv_gates", "iv_search", "iv_conv", "iv_worlds", "iv_stats", "iv_replay", "iv_example", "iv_run", "iv_verify"))
PKG = fx.STUDY


@pytest.fixture(scope="module")
def stream():
    return fx.tiny_stream("alias", 3)


@pytest.fixture(scope="module")
def models(stream):
    w, sc = stream["world"], stream["schedule"]
    cells = sc["H0"] + sc["batches"][0] + sc["batches"][1]
    return CORE.build_models(w, cells, w.static), cells


# ---------------------------------------------------------------- access isolation
def test_solver_modules_never_read_the_truth():
    for name in ("iv_core.py", "iv_gates.py", "iv_conv.py", "iv_replay.py", "iv_search.py"):
        src = (PKG / name).read_text(encoding="utf-8")
        assert "truth_column" not in src and "_World__truth" not in src, name
    assert "env_export" not in Path(fx.__file__).read_text(encoding="utf-8")


def test_campaign_enforces_budget_and_legal_probe_set(stream):
    w = stream["world"]
    cell = stream["schedule"]["batches"][0][0]
    mask = RUN.tmask(w.static)
    legal = np.nonzero(mask)[0]
    camp = w.campaign(cell, 2, probe_mask=mask)
    camp.query(legal[:2], "probe")
    with pytest.raises(Exception):
        camp.query(legal[2:3], "probe")
    camp2 = w.campaign(cell, 5, probe_mask=mask)
    with pytest.raises(Exception):
        camp2.query([int(np.nonzero(~mask)[0][0])], "probe")


def test_restricted_real_export_has_only_released_cells():
    real = PKG.parents[1] / "tmp" / "innovation_validation_20261020" / "env_export_released_only.npz"
    if not real.exists():
        pytest.skip("restricted export not generated")
    z = np.load(real, allow_pickle=False)
    assert z["A"].shape[1] == 18 and len(z["cells"]) == 18 and "withheld_names_sha256" in z.files


# ---------------------------------------------------------------- semantic identity (defect 1), missing stays missing (defect 9)
def test_program_identity_is_by_gate_id_not_position():
    a = CORE.Program("x", "gate", gates=("g1", "g2"))
    b = CORE.Program("y", "gate", gates=("g2", "g1"))
    assert a.key() == b.key()
    g_a = GATES.Gate("a", np.array([0.1, -0.2, 0.0]), scope=(0, 1))
    g_b = GATES.Gate("b", np.array([0.1, -0.2, 0.0]), scope=(0, 1))
    g_c = GATES.Gate("c", np.array([0.1, 0.2, 0.0]), scope=(0, 1))
    assert g_a.identity() == g_b.identity() != g_c.identity()


def test_unprobed_gate_keeps_its_prior_not_zero(models, stream):
    Mo, cells = models
    w = stream["world"]
    gl = GATES.discover_gates(Mo, rng=np.random.default_rng(0))
    if not gl:
        pytest.skip("no gate discovered on the tiny stream")
    prog = CORE.Program("G", "gate", gates=tuple(g.gid for g in gl))
    fit = CORE.fit_program(prog, Mo, {g.gid: g for g in gl})
    assert fit is not None
    bel = CORE.make_belief([fit], np.zeros(w.static.n))
    w_ = bel.weights()
    pi = np.array([fit.gates[g].pi for g in fit.program.gates])
    marg = np.array([sum(wi for wi, c in zip(w_, bel.comps) if c["state"][k] == 1) for k in range(len(pi))])
    assert np.allclose(marg, pi, atol=1e-9) and (marg > 0).all()


def test_gbm_features_keep_missing_as_nan(stream):
    w = stream["world"]
    st = w.static
    camp = w.campaign(stream["schedule"]["batches"][0][0], 1)
    X = CONV.features(st, camp.Aref, camp.amin, camp.amax, np.zeros(st.n), [0], [0.1], len(st.classes))
    assert np.isnan(X[:, 6:]).sum() > 0 and not np.isnan(X[0, 6 + st.pair_class[0]])


# ---------------------------------------------------------------- updates after feedback and the worked example
def test_worked_example_two_outcomes_different_posterior_and_decision():
    c = EXAMPLE.main()["checks"]
    assert c["same_probe"] and c["posterior_differs"] and c["decisions_differ"] and c["mismatch_flagged"]
    assert c["A_support_after_A_outcome"] > 0.9 and c["A_support_after_B_outcome"] < 0.1 and c["B_support_after_B_outcome"] > 0.9
    assert c["variance_only_probe_is_the_decoy"] and c["variance_probe_leaves_posterior_unchanged"]


def test_pre_probe_record_lists_competing_programs_and_acquisition_score():
    bel = EXAMPLE.build()
    legal = np.zeros(EXAMPLE.N, bool)
    legal[[EXAMPLE.DECOY, EXAMPLE.DIAG]] = True
    p, rec = CORE.pick("kg", bel, legal, np.ones(EXAMPLE.N, bool), {8: 0.82}, np.random.default_rng(0), np.arange(EXAMPLE.N) // 3)
    assert {"program_weights", "competing_predictions_for_probe", "kg_score", "nominations_that_could_change", "alternatives"} <= set(rec)
    assert len(rec["competing_predictions_for_probe"]) == 4


def test_observation_changes_program_support():
    bel = EXAMPLE.build()
    before = bel.program_weights()
    bel.observe(EXAMPLE.DIAG, 0.15)
    assert bel.program_weights() != before and bel.probed[-1] == EXAMPLE.DIAG


# ---------------------------------------------------------------- equal validation, promotion strictness (defects 4-5)
def test_ties_and_zero_gain_never_promote():
    assert SEARCH.promote_rule({"gain": 0.0, "wins": 0, "losses": 0, "n": 4}) != "demonstrated"
    assert SEARCH.promote_rule({"gain": 0.0, "wins": 4, "losses": 0, "n": 4}) != "demonstrated"
    assert SEARCH.promote_rule({"gain": 0.02, "wins": 1, "losses": 0, "n": 4}) != "demonstrated"
    assert SEARCH.promote_rule({"gain": 0.02, "wins": 3, "losses": 1, "n": 4}) == "demonstrated"
    assert SEARCH.promote_rule({"gain": -0.05, "wins": 0, "losses": 4, "n": 4}) == "retired"


def test_both_arms_use_the_same_validation_rule_and_validate(stream):
    w, sc, st = stream["world"], stream["schedule"], stream["world"].static
    for arm in ("inherit", "restart"):
        lib = SEARCH.Library()
        rec = SEARCH.evolve(arm, lib, w, st, "t|" + arm, 1, list(sc["H0"]), sc["batches"][0], sc["H0"] + sc["batches"][0], 2, False, 4)
        assert rec["n_candidates"] <= 4 and "incumbent_val" in rec
        for c in rec["candidates"]:
            if c.get("fit"):
                assert SEARCH.promote_rule({k: c[k] for k in ("gain", "wins", "losses", "n")}) == c["status"]


def test_restart_arm_drops_the_inherited_library(stream):
    w, sc, st = stream["world"], stream["schedule"], stream["world"].static
    lib = SEARCH.Library()
    lib.deployed = CORE.Program("old", "gate", gates=("zzz",), status="demonstrated")
    lib.gates = {"zzz": GATES.Gate("zzz", np.zeros(len(st.classes)), scope=())}
    SEARCH.evolve("restart", lib, w, st, "t|r", 1, list(sc["H0"]), sc["batches"][0], sc["H0"] + sc["batches"][0], 2, False, 2)
    assert "zzz" not in lib.gates and (lib.deployed is None or lib.deployed.pid != "old")


def test_capacity_and_archive_are_bounded():
    assert SEARCH.DEPLOY_MAX_GATES <= 4 and SEARCH.ARCHIVE_MAX <= 3 and SEARCH.CAND_PER_GEN <= 12


# ---------------------------------------------------------------- checkpoint = actual deployed program after rollback (defect 6)
def test_checkpoint_reports_what_is_actually_deployed_after_rollback(stream, monkeypatch):
    w, sc, st = stream["world"], stream["schedule"], stream["world"].static
    lib = SEARCH.Library()
    lib.deployed = CORE.Program("inc", "gate", gates=("g",), status="demonstrated")
    lib.gates = {"g": GATES.Gate("g", np.ones(len(st.classes)) * 0.1, scope=(0,))}
    real = CORE.fit_program

    def fake(prog, Mo, gates, ref_basis=None, E=None, static=None):
        if prog.kind == "gate":
            return None
        return real(prog, Mo, gates, ref_basis=ref_basis, E=E, static=static)
    monkeypatch.setattr(CORE, "fit_program", fake)
    rec = SEARCH.evolve("inherit", lib, w, st, "t|ck", 2, list(sc["H0"]), sc["batches"][0], sc["H0"] + sc["batches"][0], 2, False, 2, search=False)
    assert rec["rolled_back_on_refit"] == "inc" and rec["deployed_at_checkpoint"] is None and lib.deployed is None


# ---------------------------------------------------------------- serialization and reload equality (defect 7), latent basis (defect 8)
def test_stored_programs_reproduce_nomination_without_refit(stream, models, tmp_path):
    w, st = stream["world"], stream["world"].static
    Mo, cells = models
    lib = SEARCH.Library()
    gl = GATES.discover_gates(Mo, rng=np.random.default_rng(0))
    prog = CORE.Program("PX", "gate", gates=tuple(g.gid for g in gl)) if gl else None
    fits = SEARCH.make_fits(lib, Mo, prog, {g.gid: g for g in gl}, 2)
    cell = stream["schedule"]["batches"][2][0]
    r, camp, nom, bel, tr = SEARCH.run_task(w, st, cell, Mo, fits, "kg", 3, "E", None, 7)
    flat = {f"inh_kg|b3|{k}": v for k, v in RUN.pack_fits(fits).items()}
    flat.update({"prior|b3|pm": Mo.prior.pm, "prior|b3|w": Mo.prior.w, "prior|b3|fbar": Mo.prior.fbar})
    path = tmp_path / "m.npz"
    np.savez_compressed(path, **flat)
    z = np.load(path, allow_pickle=False)
    c0 = w.campaign(cell, 3)
    nom2, _ = REPLAY.replay_nomination(z, "inh_kg", 3, c0.Aref, c0.amin, c0.amax, list(camp.queried), [camp.queried[p] for p in camp.queried], np.ones(st.n, bool))
    assert nom2 == [int(q) for q in nom]


def test_aligned_latent_basis_keeps_meaning_across_histories(models, stream):
    Mo, cells = models
    w, st = stream["world"], stream["world"].static
    M2 = CORE.build_models(w, cells[:-1], st)
    prog = CORE.Program("C", "cont", k=2)
    f1 = CORE.fit_program(prog, Mo, {})
    f2 = CORE.fit_program(prog, M2, {}, ref_basis=f1.V)
    for j in range(2):
        assert np.corrcoef(f1.V[:, j], f2.V[:, j])[0, 1] > 0.0          # same coordinate, no sign flip


# ---------------------------------------------------------------- skill reuse and deletion ablation
def test_deployed_gate_program_is_invoked_and_deletion_removes_it(stream, models):
    w, st = stream["world"], stream["world"].static
    Mo, cells = models
    gl = GATES.discover_gates(Mo, rng=np.random.default_rng(0))
    if not gl:
        pytest.skip("no gate on the tiny stream")
    lib = SEARCH.Library()
    prog = CORE.Program("PX", "gate", gates=tuple(g.gid for g in gl))
    with_fits = SEARCH.make_fits(lib, Mo, prog, {g.gid: g for g in gl}, 2)
    without = SEARCH.make_fits(lib, Mo, None, None, 2)
    cell = stream["schedule"]["batches"][2][0]
    bel_with = SEARCH.run_task(w, st, cell, Mo, with_fits, "kg", 2, "E", None, 5)[3]
    bel_wo = SEARCH.run_task(w, st, cell, Mo, without, "kg", 2, "E", None, 5)[3]
    assert "PX" in bel_with.program_weights() and "PX" not in bel_wo.program_weights()


# ---------------------------------------------------------------- statistics (defect 2: paired oracle) and decision rule
def test_decision_rule_and_stream_level_bootstrap():
    assert STATS.decide(0.012, 0.03) == "SUPPORT" and STATS.decide(-0.01, 0.004) == "NO_SUPPORT" and STATS.decide(0.0, 0.02) == "INCONCLUSIVE"
    d = np.array([0.02] * 10 + [0.0] * 10)
    lo, hi = STATS.boot_ci(d, 0.95)
    assert lo < d.mean() < hi
    assert STATS.contrast_row("x", np.array([0.1, 0.2]), 0.95)["verdict"] == "NOT_TESTED"


def test_oracle_is_paired_with_the_cells_it_belongs_to():
    rows = [{"arm": "prior", "contract": "E", "role": "task", "gen": 2, "oracle": 0.9, "utility": 0.8, "cell": "a"},
            {"arm": "prior", "contract": "E", "role": "task", "gen": 3, "oracle": 0.7, "utility": 0.6, "cell": "b"}]
    tab = STATS.oracle_table({"s": {"rows": rows}}, "E", 2)
    assert abs(tab["s"] - 0.8) < 1e-12


# ---------------------------------------------------------------- the verifier fails on missing evidence (defect 3)
def test_verifier_fails_on_empty_and_partial_package(tmp_path):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = VERIFY.main([str(tmp_path)])
    assert rc != 0 and "VERIFY OK" not in buf.getvalue() and "INCOMPLETE" in buf.getvalue()
    (tmp_path / "CONFIG.json").write_text("{}")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = VERIFY.main([str(tmp_path)])
    assert rc != 0 and "missing mandatory evidence" in buf.getvalue()


# ---------------------------------------------------------------- runner smoke on a tiny stream
def test_runner_refuses_second_evaluation_and_writes_models(tmp_path):
    s = fx.tiny_stream("alias", 4, n_drugs=8)
    sched = {"H0": s["schedule"]["H0"], "batches": s["schedule"]["batches"][:2], "A_old": s["schedule"]["A_old"][:1], "A_new": s["schedule"]["A_new"][:1]}
    s2 = {"world": s["world"], "schedule": sched, "meta": s["meta"]}
    sid = "tiny_alias_4"
    RUN.run_stream("alias", 4, False, tmp_path, {}, stream=s2, sid_override=sid)
    assert (tmp_path / "streams" / f"{sid}.json.gz").exists() and (tmp_path / "models" / f"{sid}.npz").exists()
    with pytest.raises(FileExistsError):
        RUN.run_stream("alias", 4, False, tmp_path, {}, stream=s2, sid_override=sid)
    d = STATS.load_streams(tmp_path)[sid]
    assert {"inh_kg", "rst_kg", "prior", "lat_aopt", "gbm_ucb"} <= {r["arm"] for r in d["rows"]}
    for r in d["rows"]:
        assert len(set(r["nominated"])) == 5
