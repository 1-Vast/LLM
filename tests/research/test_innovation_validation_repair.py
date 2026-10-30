"""Analytic and synthetic regressions; these do not establish scientific benefit."""
from __future__ import annotations

import copy
import importlib
import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest


STUDY = Path(__file__).resolve().parents[2] / "research" / "routes" / "functional_prediction" / "innovation_validation_repair1_20261020"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))
CORE = importlib.import_module("r1_core")
GATES = importlib.import_module("r1_gates")
SEARCH = importlib.import_module("r1_search")
WORLD = importlib.import_module("svc_world")


def latent_belief(loadings, base=None, noise=1e-6):
    loadings = np.asarray(loadings, dtype=float)[:, None]
    fit = CORE.Fitted(CORE.Program("C", "cont", k=1), np.full(len(loadings), noise), V=loadings)
    return CORE.make_belief([fit], np.zeros(len(loadings)) if base is None else np.asarray(base, dtype=float))


def synthetic_world(offset=0.0):
    """One binary state, explicitly generated released outcomes, no external data."""
    n_drugs, n_cells = 6, 12
    ii, jj = np.triu_indices(n_drugs, 1)
    st = WORLD.Static(tuple(f"d{k}" for k in range(n_drugs)), ii, jj, np.array([0, 0, 1, 1, 2, 2]),
                      tuple(f"d{i}+d{j}" for i, j in zip(ii, jj)))
    cells = tuple(f"c{k}" for k in range(n_cells))
    state = np.tile([0.0, 1.0], n_cells // 2)
    beta = np.linspace(0.14, 0.18, st.n)
    noise = np.random.default_rng(7821).normal(0, 0.0005, (st.n, n_cells))
    aref = np.full((st.n, n_cells), 0.6)
    activity = aref + beta[:, None] * (state - 0.5) + noise
    activity[0, 0] += offset
    w = WORLD.World(st, cells, aref, np.full_like(aref, 0.3), np.full_like(aref, 0.4), activity,
                    label="repair_analytic_fixture")
    gate = GATES.Gate("lineage_g", np.full(len(st.classes), 0.16), beta=beta, pi=0.5,
                      scope=tuple(range(len(st.classes))), probe_order=tuple(range(st.n)))
    return w, gate


def test_kg_matches_analytic_value_of_a_shared_latent_probe():
    # Y0=z is measured; targets are z, -z, and four zeros. Choosing five gives E|z| / 5.
    bel = latent_belief([1, 1, -1, 0, 0, 0, 0])
    pool = np.array([False, True, True, True, True, True, True])
    values, _, _ = CORE.kg_values(bel, np.array([0]), pool, {}, np.random.default_rng(77221), samples=50_000)
    assert values[0] == pytest.approx(math.sqrt(2 / math.pi) / 5, abs=0.003)
    assert values[0] > CORE.EPS_STOP


def test_independent_probe_has_zero_transfer_decision_value():
    bel = latent_belief([1, 0, 0, 0, 0, 0, 0])
    pool = np.array([False, True, True, True, True, True, True])
    values, _, _ = CORE.kg_values(bel, np.array([0]), pool, {}, np.random.default_rng(77221), samples=128)
    assert values[0] == pytest.approx(0.0, abs=1e-12)


def test_kg_keeps_recorded_target_values_fixed():
    # Four known large values always win. The last place switches from recorded .5 to z.
    bel = latent_belief([1, 1, 0, 0, 0, 0, 0])
    pool = np.array([False, True, True, True, True, True, True])
    recorded = {2: 0.5, 3: 100.0, 4: 100.0, 5: 100.0, 6: 100.0}
    expected = (math.exp(-0.5 ** 2 / 2) / math.sqrt(2 * math.pi)
                - 0.5 * 0.5 * math.erfc(0.5 / math.sqrt(2))) / 5
    values, _, _ = CORE.kg_values(bel, np.array([0]), pool, recorded, np.random.default_rng(77221), samples=50_000)
    assert values[0] == pytest.approx(expected, abs=0.0015)
    assert recorded == {2: 0.5, 3: 100.0, 4: 100.0, 5: 100.0, 6: 100.0}


def test_aoptimal_search_considers_all_legal_actions():
    loadings = np.zeros(100)
    loadings[-1] = 1.0
    bel = latent_belief(loadings, noise=0.01)
    action, _ = CORE.pick("aopt", bel, np.ones(100, bool), np.ones(100, bool), {},
                          np.random.default_rng(2), np.zeros(100, int))
    assert action == 99


def test_kg_screen_keeps_latent_information_and_respects_its_cap(monkeypatch):
    loadings = np.zeros(100)
    loadings[98:] = [-1.0, 1.0]
    bel = latent_belief(loadings)
    captured = []

    def fake_kg(belief, candidates, pool, recorded, rng, samples=128):
        captured.extend(candidates.tolist())
        values = (candidates == 99).astype(float)
        return values, [[] for _ in candidates], CORE.top_k(CORE.shortlist_scores(belief, pool, recorded))

    monkeypatch.setattr(CORE, "kg_values", fake_kg)
    action, _ = CORE.pick("kg", bel, np.ones(100, bool), np.ones(100, bool), {},
                          np.random.default_rng(2), np.zeros(100, int))
    assert 99 in captured and action == 99
    assert len(captured) == len(set(captured)) <= CORE.KG_CANDIDATES


def gate_pair():
    a = GATES.Gate("a", np.array([0.1, 0.2]), beta=np.array([0.3, 0.4, 0.5]),
                   pi=0.4, scope=(0, 1), probe_order=(2, 1, 0))
    b = copy.deepcopy(a)
    b.gid = "b"
    return a, b


def test_gate_fingerprint_does_not_depend_on_its_lineage_name():
    a, b = gate_pair()
    assert a.identity() == b.identity()


@pytest.mark.parametrize("field,value", [
    ("b", np.array([0.15, 0.2])),
    ("beta", np.array([0.35, 0.4, 0.5])),
    ("pi", 0.6),
    ("scope", (1,)),
    ("probe_order", (0, 1, 2)),
])
def test_gate_execution_fingerprint_covers_its_full_profile(field, value):
    a, b = gate_pair()
    setattr(b, field, value)
    assert a.identity() != b.identity()


def test_program_execution_key_distinguishes_same_lineage_different_profile():
    a, b = gate_pair()
    b.gid = a.gid
    b.beta = a.beta * 2
    program = CORE.Program("P", "gate", gates=(a.gid,))
    assert program.key({a.gid: a}) != program.key({b.gid: b})


def test_program_key_canonicalizes_unordered_conjunction_edges():
    a, b = gate_pair()
    store = {"a": a, "b": b}
    p = CORE.Program("P", "gate", gates=("a", "b"), conj=(("a", "b"),))
    q = CORE.Program("Q", "gate", gates=("b", "a"), conj=(("b", "a"),))
    assert p.key() == q.key()
    assert p.key(store) == q.key(store)


def test_history_version_changes_when_observations_change_under_same_cell_names():
    w1, _ = synthetic_world()
    w2, _ = synthetic_world(offset=0.04)
    a = CORE.build_models(w1, w1.cells, w1.static)
    b = CORE.build_models(w2, w2.cells, w2.static)
    assert a.cells == b.cells
    assert a.version != b.version
    assert a.version == CORE.build_models(w1, w1.cells, w1.static).version


def cached_library():
    w, gate = synthetic_world()
    lib = SEARCH.Library()
    lib.gates = {gate.gid: gate}
    lib.deployed = CORE.Program("incumbent", "gate", gates=(gate.gid,), status="demonstrated")
    rec = SEARCH.evolve("inherit", lib, w, w.static, "cache_unit", 1, list(w.cells), [], list(w.cells),
                        1, False, 0, search=False)
    assert lib.deployed is not None, rec
    assert lib.deployed_fit is not None
    return w, CORE.build_models(w, w.cells, w.static), lib


def test_repeated_same_history_deployment_reuses_exact_gate_fit(monkeypatch):
    _, models, lib = cached_library()
    original = CORE.fit_program
    calls = []

    def counted(program, *args, **kwargs):
        if program.kind == "gate":
            calls.append(program.pid)
        return original(program, *args, **kwargs)

    monkeypatch.setattr(CORE, "fit_program", counted)
    one = SEARCH.make_fits(lib, models, lib.deployed, lib.gates)
    two = SEARCH.make_fits(lib, models, lib.deployed, lib.gates)
    first_gate = next(f for f in one if f.program.kind == "gate")
    second_gate = next(f for f in two if f.program.kind == "gate")
    assert first_gate is second_gate is lib.deployed_fit
    copied = SEARCH.make_fits(lib, models, copy.deepcopy(lib.deployed), lib.gates)
    assert next(f for f in copied if f.program.kind == "gate") is first_gate
    assert calls == []


@pytest.mark.parametrize("defect", ["missing", "different_history", "changed_profile"])
def test_invalid_deployed_cache_fails_instead_of_silently_dropping_the_program(defect):
    _, models, lib = cached_library()
    if defect == "missing":
        lib.deployed_fit = None
    elif defect == "different_history":
        models = replace(models, version=models.version + "_other")
    else:
        gid = lib.deployed.gates[0]
        lib.gates[gid] = copy.deepcopy(lib.gates[gid])
        lib.gates[gid].beta *= 1.1
    with pytest.raises(RuntimeError):
        SEARCH.make_fits(lib, models, lib.deployed, lib.gates)


def test_unfittable_candidate_can_be_rejected_without_changing_deployment(monkeypatch):
    w, gate = synthetic_world()
    models = CORE.build_models(w, w.cells, w.static)
    lib = SEARCH.Library()
    program = CORE.Program("candidate", "gate", gates=(gate.gid,))
    original = CORE.fit_program

    def fail_gate(prog, *args, **kwargs):
        return None if prog.kind == "gate" else original(prog, *args, **kwargs)

    monkeypatch.setattr(CORE, "fit_program", fail_gate)
    fits = SEARCH.make_fits(lib, models, program, {gate.gid: gate})
    assert not any(f.program.kind == "gate" for f in fits)
    assert lib.deployed is None


def test_failed_generation_refit_records_explicit_rollback(monkeypatch):
    w, _, lib = cached_library()
    pid = lib.deployed.pid
    original = CORE.fit_program

    def fail_gate(prog, *args, **kwargs):
        return None if prog.kind == "gate" else original(prog, *args, **kwargs)

    monkeypatch.setattr(CORE, "fit_program", fail_gate)
    rec = SEARCH.evolve("inherit", lib, w, w.static, "rollback_unit", 2, list(w.cells), [], list(w.cells),
                        1, False, 0, search=False)
    assert rec["rolled_back_on_refit"] == pid
    assert rec["deployed_at_checkpoint"] is None
    assert lib.deployed is None and lib.deployed_fit is None


def test_noninferior_count_is_not_reported_as_an_actual_reusable_archive(monkeypatch):
    w, gate = synthetic_world()
    lib = SEARCH.Library()
    program = CORE.Program("candidate", "gate", gates=(gate.gid,))
    monkeypatch.setattr(SEARCH, "propose", lambda *args, **kwargs: [(program, {gate.gid: gate})])
    monkeypatch.setattr(SEARCH, "replay", lambda *args, **kwargs: np.array([0.5, 0.5, 0.5, 0.5]))
    rec = SEARCH.evolve("inherit", lib, w, w.static, "archive_unit", 1, list(w.cells[:8]), list(w.cells[8:]),
                        list(w.cells), 1, False, 1)
    assert rec["candidates"][0]["status"] == "noninferior"
    assert rec["archive_size_after"] == len(lib.archive) == len(rec["library_after"]["archive"]) == 0
    assert rec["archive_reuse_status"] == "NOT_IMPLEMENTED"
