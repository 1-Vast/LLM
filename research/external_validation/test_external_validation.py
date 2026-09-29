"""Leakage, information-isolation and matching contracts for the external-validation harness.

File summary
- Path: research/external_validation/test_external_validation.py
- Purpose: pin every boundary the protocol relies on, so a future change that lets a policy read a
  hidden result, lets fitting touch a sealed study, or gives one arm different rules fails here.
- Core points:
  - Synthetic fixtures test the external boundary and the vault (no external study is local).
  - Real-data fixtures (SciPlex3 tier A fold 0, L1000 tier T fold 0, a few episodes) test the sealed
    view, identical menus and rules, the virtual-cell channel and the oracle bound. They assert
    structure and equality only and print no outcome rate.
- Run: python -m pytest research/external_validation -p no:cacheprovider
"""
from __future__ import annotations

import ast
import copy
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from . import arms as A
from . import firewall as F
from . import locked_replay as R
from . import promotion as PR
from . import statistics as S

P, C, E, V = A.P, A.C, A.E, A.V
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


# ------------------------------------------------------------------------------ fixtures
@pytest.fixture(autouse=True)
def fresh_vault():
    F._reset_for_tests()
    yield
    F._reset_for_tests()


def _fixture(dataset, tier, fold):
    data, ctx, setting = R.load(dataset, tier, fold)
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    heldout = set(comp.index[comp.fold == fold])
    sealed = F.seal(ctx, heldout, vc_factory=lambda d, det: A.StructureVC(d, det))
    sealed.extra["structure_vc"] = sealed.magnitude
    episodes = E.episode_list(ctx, fold)
    sealed.extra["vc_partner"] = A.vc_partners(sorted({e[0] for e in episodes}), fold, tier)
    return {"data": data, "ctx": ctx, "setting": setting, "heldout": heldout, "sealed": sealed,
            "episodes": episodes, "dataset": dataset, "tier": tier, "fold": fold}


@pytest.fixture(scope="module")
def sciplex():
    return _fixture("sciplex3", "A", 0)


@pytest.fixture(scope="module")
def lincs():
    return _fixture("l1000", "T", 0)


@pytest.fixture(scope="module")
def replayed():
    """Every executed arm on two episodes of each fixture through the production driver."""
    return {name: R.run_task(task, R.units(task[0]), limit=2)
            for name, task in (("sciplex", ("sciplex3", "A", 0)), ("lincs", ("l1000", "T", 0)))}


def _first_choice(arm, sealed, episode, setting):
    compound, truth, decoy, h1, h2 = episode
    sealed.extra["visible"] = F.Visible()
    menu = P.legal_menu(setting, [], setting.budget_days)
    actions = [P.make_action(k, h1, h2, setting) for k in setting.keys]
    state = P.EvidenceState.open(E.contrast_for(h1, h2, actions).hypotheses)
    key, _ = arm(sealed, compound, h1, h2, [], menu, setting.budget_days, setting, state)
    return key


# ------------------------------------------------------------------------------ boundaries
@pytest.mark.parametrize("which", ["sciplex", "lincs"])
def test_internal_folds_share_no_compound_or_group(which, request):
    f = request.getfixturevalue(which)
    unit = R.units(f["dataset"])[R.UNIT[f["dataset"]]]
    train = {c for t in f["ctx"].ft.tables.values() for c in t.names}
    assert not train & f["heldout"]
    assert not {unit.get(c) for c in train} & {unit.get(c) for c in f["heldout"] if c in unit.index}


def test_external_boundary_refuses_compound_scaffold_and_batch_overlap():
    base = {"compounds": {"a", "b"}, "groups": {"g1"}, "scaffolds": {"s1"}, "batches": {"p1"}}
    clean = F.boundary_report(base, {"compounds": {"c"}, "groups": {"g2"}, "scaffolds": {"s2"}, "batches": {"p2"}})
    assert F.external_boundary_problems(clean) == []
    leaky = F.boundary_report(base, {"compounds": {"a"}, "groups": {"g2"}, "scaffolds": {"s1"}, "batches": {"p1"}})
    assert F.external_boundary_problems(leaky) == ["compounds_cross_external_boundary",
                                                   "scaffolds_cross_external_boundary",
                                                   "batches_cross_external_boundary"]
    # Internal folds tolerate shared plates (recorded), never shared compounds or groups.
    assert F.internal_boundary_problems(leaky) == ["compounds_cross_fold_boundary"]


def test_internal_batch_crossing_is_reported_not_hidden(sciplex):
    f = sciplex
    train = {c for t in f["ctx"].ft.tables.values() for c in t.names}
    test = {e[0] for e in f["episodes"]}
    report = F.boundary_report({"compounds": train, "batches": R.batches_of(f["data"], "sciplex3", train, f["setting"].keys)},
                               {"compounds": test, "batches": R.batches_of(f["data"], "sciplex3", test, f["setting"].keys)})
    assert report["batches"]["shared"] > 0          # hashing puts every compound on shared plates
    assert F.internal_boundary_problems(report) == []


# ------------------------------------------------------------------------------ sealed view
@pytest.mark.parametrize("which", ["sciplex", "lincs"])
def test_sealed_view_holds_no_heldout_measurement_or_annotation(which, request):
    f = request.getfixturevalue(which)
    sealed, heldout = f["sealed"], f["heldout"]
    assert F.sealed_view_problems(sealed, heldout) == []
    rows = F.sealed_rows(f["data"], heldout)
    assert rows and np.isnan(sealed.data.shift[rows]).all()
    assert not sealed.detected[rows].any()
    assert not any(C.qc_passed(sealed.data, r) for r in rows)
    held = sealed.data.compounds[sealed.data.compounds.compound.isin(heldout)]
    assert held.klass.isna().all()
    # The executor's real data still holds them: sealing copies, never edits.
    assert np.isfinite(f["data"].shift[rows]).any()


def _corrupt(data, heldout, seed=7):
    rng = np.random.default_rng(seed)
    other = copy.copy(data)
    rows = F.sealed_rows(data, heldout)
    other.shift = data.shift.copy()
    other.shift[rows] = rng.normal(size=other.shift[rows].shape).astype(other.shift.dtype)
    other.agreement = data.agreement.astype(float).copy()
    other.agreement[rows] = rng.uniform(size=len(rows))
    other.compounds = data.compounds.copy()
    held = other.compounds.compound.isin(heldout)
    other.compounds.loc[held, "klass"] = rng.permutation(other.compounds.loc[held, "klass"].to_numpy())
    return other


@pytest.mark.parametrize("which", ["sciplex", "lincs"])
def test_policies_cannot_read_hidden_outcomes(which, request):
    """Two studies that differ only in held-out results give identical policy views and choices."""
    f = request.getfixturevalue(which)
    ctx, heldout = f["ctx"], f["heldout"]
    changed = copy.copy(ctx)
    changed.data = _corrupt(ctx.data, heldout)
    views = [F.seal(c, heldout, vc_factory=lambda d, det: A.StructureVC(d, det)) for c in (ctx, changed)]
    a, b = (v.data for v in views)
    assert np.array_equal(a.shift, b.shift, equal_nan=True)
    assert np.array_equal(a.agreement, b.agreement, equal_nan=True)
    assert a.index == b.index
    pd.testing.assert_frame_equal(a.compounds, b.compounds)
    for view in views:
        view.extra["structure_vc"] = view.magnitude
        view.extra["vc_partner"] = f["sealed"].extra["vc_partner"]
    table = {n: A.REGISTRY[n]["build"]() for n in A.executed_arms() if n != "oracle"}
    for episode in f["episodes"][:3]:
        for name, arm in table.items():
            assert _first_choice(arm, views[0], episode, f["setting"]) == \
                _first_choice(arm, views[1], episode, f["setting"]), name


# ------------------------------------------------------------------------------ fitting, retrieval, calibration
def _freeze_for(tmp_path, manifest_digest="m" * 64):
    frozen = tmp_path / "frozen.txt"
    frozen.write_text("frozen", encoding="utf-8")
    return frozen, {"sha256": {frozen.name: F.sha256_file(frozen)}, "external_study": {"manifest_sha256": manifest_digest}}


def test_vault_opens_once_only_under_a_verified_freeze(tmp_path):
    frozen, freeze = _freeze_for(tmp_path)
    with pytest.raises(F.FreezeMismatch):
        F.Vault("x", {"y": 1}, manifest_sha256="n" * 64).open(freeze, root=tmp_path)
    frozen.write_text("edited", encoding="utf-8")
    with pytest.raises(F.FreezeMismatch):
        F.Vault("x", {"y": 1}, manifest_sha256="m" * 64).open(freeze, root=tmp_path)
    assert F.revealed() is None
    frozen.write_text("frozen", encoding="utf-8")
    vault = F.Vault("x", {"y": 1}, manifest_sha256="m" * 64)
    log = tmp_path / "access.jsonl"
    assert vault.open(freeze, root=tmp_path, access_log=log) == {"y": 1}
    assert json.loads(log.read_text(encoding="utf-8"))["study"] == "x"
    with pytest.raises(RuntimeError):
        vault.open(freeze, root=tmp_path)


def test_no_fitting_after_the_external_study_is_revealed(tmp_path, sciplex):
    fresh = F.seal(sciplex["ctx"], sciplex["heldout"], vc_factory=lambda d, det: A.StructureVC(d, det))
    fresh.extra["structure_vc"] = fresh.magnitude
    prepared = F.seal(sciplex["ctx"], sciplex["heldout"], vc_factory=lambda d, det: A.StructureVC(d, det))
    prepared.extra["structure_vc"] = prepared.magnitude
    A.prepare(prepared)
    _, freeze = _freeze_for(tmp_path)
    F.Vault("x", {}, manifest_sha256="m" * 64).open(freeze, root=tmp_path)
    for step in (A.build_reference_model, A.fit_ridge, A.prepare):
        assert getattr(step, "is_fitting_step", False)
        with pytest.raises(F.ExternalOutcomesRevealed):
            step(fresh)
    episode, setting = sciplex["episodes"][0], sciplex["setting"]
    with pytest.raises(F.ExternalOutcomesRevealed):
        _first_choice(A.myopic_edv(), fresh, episode, setting)
    # Components built before the reveal keep predicting.
    _first_choice(A.myopic_edv(), prepared, episode, setting)
    _first_choice(A.ridge, prepared, episode, setting)


@pytest.mark.parametrize("which", ["sciplex", "lincs"])
def test_calibration_and_reference_library_use_training_rows_only(which, request):
    f = request.getfixturevalue(which)
    rebuilt = C.build_fold_tables(f["sealed"].data, f["ctx"].tier, f["fold"], f["sealed"].detected)
    for key, table in f["ctx"].ft.tables.items():
        assert rebuilt.tables[key].names == table.names
        assert np.array_equal(rebuilt.tables[key].Y, table.Y)
        assert not set(table.names) & f["heldout"]
    spec = C.load_protocol()
    assert C.calibrate(rebuilt, spec) == C.calibrate(f["ctx"].ft, spec)


def test_retrieval_neighbours_come_from_the_reference_library(replayed):
    for result in replayed.values():
        heldout = {r["compound"] for r in result["records"]}
        for record in result["records"]:
            if record["policy"] != "retrieval":
                continue
            for step in record["steps"]:
                for branch in (step.get("note") or {}).get("prediction_by_hypothesis", {}).values():
                    assert not set(branch.get("local_compounds", [])) & heldout


def test_prompt_carries_no_episode_examples(sciplex, lincs):
    """The registered Jev prompt is zero-shot: no compound identifier from either study appears."""
    source = (ROOT / "research/dynamic_world_model/agent_arms.py").read_text(encoding="utf-8")
    system = next(ast.literal_eval(node.value) for node in ast.walk(ast.parse(source))
                  if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "SYSTEM" for t in node.targets))
    names = set()
    for f in (sciplex, lincs):
        comp = f["data"].compounds
        names |= {str(n).strip().lower() for n in comp.compound if len(str(n).strip()) >= 5}
        if "name" in comp.columns:
            names |= {str(n).strip().lower() for n in comp.name.dropna() if len(str(n).strip()) >= 5}
    text = system.lower()
    assert not [n for n in names if n in text]


# ------------------------------------------------------------------------------ matched rules
def test_all_arms_share_menus_budget_and_qc_rules(replayed):
    for result in replayed.values():
        assert result["problems"] == []
        frame = pd.DataFrame(result["records"])
        for _, group in frame.groupby(["compound", "h1", "h2"]):
            first = {tuple(o[0]) for o in group.offered if o}
            assert len(first) == 1
            assert set(group.qc_rule) == {"continue"}
            assert group.policy.nunique() == len(group)
        assert set(frame.policy) == set(A.executed_arms()) | {f"{n}@{p:g}" for n in A.SWEEP for p in A.SWEEP_PRICES}


def test_failed_assay_cost_is_symmetric(sciplex):
    """Every arm that meets a QC failure is charged its assay-days and re-offered the same menu."""
    f = sciplex
    sealed, setting, ctx = f["sealed"], f["setting"], f["ctx"]
    compound, truth, decoy, h1, h2 = f["episodes"][0]
    table = {n: A.REGISTRY[n]["build"]() for n in A.executed_arms() if n not in ("oracle", "defer_floor")}
    for name, arm in table.items():
        calls = {"n": 0}

        def failing(_ctx, compound_, key, h1_, h2_):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"qc": False, "outcome": "quality_failed", "row": None, "agreement": float("nan")}
            return E.execute(ctx, compound_, key, h1_, h2_)

        offered = []

        def wrapped(*args, arm=arm):
            offered.append([C.action_id(k) for k in args[5]])
            return arm(*args)

        sealed.extra["visible"] = F.Visible()
        record = P.run_matched(name, wrapped, sealed, compound, truth, h1, h2, setting, qc_rule="continue", execute=failing)
        if not record["steps"]:
            continue
        failed = record["steps"][0]
        assert not failed["qc"] and failed["eliminated"] == []
        assert record["days"] == sum(setting.days(tuple(s["key"])) for s in record["steps"])
        assert R.menu_problems(record, offered, setting) == []
        assert P.audit_record(record, setting) == []


# ------------------------------------------------------------------------------ virtual-cell channel
def test_structure_vc_reproduces_the_frozen_magnitude_rule(sciplex):
    data, ctx = sciplex["data"], sciplex["ctx"]
    frozen = E.Magnitude(data, ctx.detected)
    ours = A.StructureVC(data, ctx.detected)
    keys = [k for k in sciplex["setting"].keys]
    for compound in sorted({e[0] for e in sciplex["episodes"]})[:6]:
        for key in keys:
            assert frozen.predict(compound, key) == ours.predict(compound, key)


def test_vc_masking_changes_only_the_vc_channel(sciplex):
    f = sciplex
    sealed, setting = f["sealed"], f["setting"]
    for compound, truth, decoy, h1, h2 in f["episodes"][:4]:
        menu = P.legal_menu(setting, [], setting.budget_days)
        actions = [P.make_action(k, h1, h2, setting) for k in menu]
        state = P.EvidenceState.open(E.contrast_for(h1, h2, actions).hypotheses)
        forecasts = V.ReferenceCardForecaster(sealed.ft, sealed.params, minimum_references=1).forecast(
            E.contrast_for(h1, h2, actions), actions, state)
        rules = A.outcome_consequences(V.registered_rules(h1, h2))
        plans = [A.select_discriminating_action(frozenset({h1, h2}), actions, E.PROFILE, setting.step_budget, forecasts,
                                                rules, action_priorities=A._vc_priorities(sealed, compound, menu, vc))
                 for vc in ("masked", "on")]
        masked, on = ({k: {x: y for x, y in v.items() if x != "priority"} for k, v in p.payload()["evaluations"].items()}
                      for p in plans)
        assert masked == on
        # The explicit arms are block 4's discrimination arm with and without the virtual cell.
        for vc, magnitude in (("masked", None), ("on", sealed.magnitude)):
            reference = copy.copy(sealed)
            reference.magnitude = magnitude
            expected, _ = P.discrimination(reference, compound, h1, h2, [], menu, setting.budget_days, setting, state)
            chosen, note = A.maestro(vc)(sealed, compound, h1, h2, [], menu, setting.budget_days, setting, state)
            assert chosen == expected
            assert note.get("used_vc", False) == (vc == "on" and bool(A._vc_priorities(sealed, compound, menu, "on")))


def test_permuted_vc_preserves_schema_but_breaks_alignment(sciplex):
    f = sciplex
    compounds = sorted({e[0] for e in f["episodes"]})
    partner = f["sealed"].extra["vc_partner"]
    assert sorted(partner) == compounds and sorted(partner.values()) == compounds
    assert all(partner[c] != c for c in compounds)
    menu = list(f["setting"].keys)
    differs = 0
    for c in compounds:
        own = A._vc_priorities(f["sealed"], c, menu, "on")
        permuted = A._vc_priorities(f["sealed"], c, menu, "permuted")
        assert set(own) == set(permuted)
        assert permuted == A._vc_priorities(f["sealed"], partner[c], menu, "on")
        differs += own != permuted
    assert differs > 0


# ------------------------------------------------------------------------------ oracle, statistics, promotion
def test_oracle_bounds_every_arm_and_never_errs(replayed):
    for result in replayed.values():
        frame = pd.DataFrame(result["records"])
        for _, group in frame.groupby(["compound", "h1", "h2"]):
            oracle = group[group.policy == "oracle"].iloc[0]
            assert oracle.final in ("correct", "deferred")
            if (group.final == "correct").any():
                assert oracle.final == "correct"


def test_mutual_information_limits():
    same = {"a": dict(zip(A.LABELS, (0.25,) * 4)), "b": dict(zip(A.LABELS, (0.25,) * 4))}
    split = {"a": dict(zip(A.LABELS, (1.0, 0, 0, 0))), "b": dict(zip(A.LABELS, (0, 1.0, 0, 0)))}
    assert A.mutual_information({"a": .5, "b": .5}, same) == pytest.approx(0.0)
    assert A.mutual_information({"a": .5, "b": .5}, split) == pytest.approx(1.0)


def test_manifest_schemas_accept_and_reject():
    episode = {"manifest_version": "1", "dataset": "d", "tier": "t", "fold": 0,
               "setting": {"menu": ["a"], "budget_days": 1.0, "max_measurements": 2, "qc_rule": "continue", "fixed_order": []},
               "episodes": [{"episode_id": "e", "compound": "c", "h1": "x", "h2": "y", "unit": "u"}]}
    F.check_manifest(episode, "episode_manifest")
    leaked = copy.deepcopy(episode)
    leaked["episodes"][0]["truth"] = "x"
    with pytest.raises(ValueError):
        F.check_manifest(leaked, "episode_manifest")
    assert F.validate({"role": "external"}, F.schema("dataset_manifest"))


def _synthetic(correct, wrong, measurements, units=60, per=4, seed=0):
    rows = []
    for arm, (c, w, m) in {"maestro_vc": (correct, wrong, measurements), "fixed": (.4, .02, 1.5),
                           "myopic_edv": (.3, .01, 1.0), "maestro_masked": (.4, .02, 1.5),
                           "maestro_vc_permuted": (.4, .02, 1.5)}.items():
        local = np.random.default_rng([seed, E.stable(arm)])
        for u in range(units):
            for e in range(per):
                draw = local.random()
                final = "correct" if draw < c else ("wrong" if draw < c + w else "undetermined")
                rows.append({"policy": arm, "compound": f"c{u}", "h1": f"h{e}", "h2": "z", "unit": f"u{u}",
                             "final": final, "measurements": m, "days": 6 * m})
    return S.outcome_columns(pd.DataFrame(rows))


def test_promotion_statuses_follow_the_registered_gates():
    spec = PR.protocol()
    strong = _synthetic(.9, .0, 1.2)
    assert PR.strongest_baseline(strong, spec) == "fixed"
    result = PR.gates(strong, "maestro_vc", "fixed", "unit", spec, integrity=[])
    assert result["G3_effectiveness"]["superior"] and result["G4_benefit"]["pass"]
    assert PR.status(result) == "SHADOW"                          # no external replication
    external = PR.gates(strong, "maestro_vc", "fixed", "unit", spec, integrity=[], role="external_test")
    assert PR.status(external, PR.vc_gate(strong, "unit", spec)) == "DEFAULT_CANDIDATE"
    assert PR.status(PR.gates(strong, "maestro_vc", "fixed", "unit", spec, integrity=["x"])) == "REJECTED"
    unsafe = _synthetic(.9, .3, 1.2)
    assert PR.status(PR.gates(unsafe, "maestro_vc", "fixed", "unit", spec, integrity=[])) == "REJECTED"
    same = _synthetic(.4, .02, 1.5)
    assert PR.status(PR.gates(same, "maestro_vc", "fixed", "unit", spec, integrity=[])) in ("INCONCLUSIVE", "REJECTED")
    assert PR.overall(["SHADOW", "INCONCLUSIVE", "DEFAULT_CANDIDATE"]) == "INCONCLUSIVE"


def test_calibration_metrics_recover_known_miscalibration():
    rng = np.random.default_rng(0)
    p = rng.uniform(0.05, 0.95, 20000)
    y = (rng.uniform(size=p.size) < p).astype(float)
    good = S.calibration_metrics(p, y)
    assert abs(good["intercept"]) < 0.05 and abs(good["slope"] - 1) < 0.05 and good["ece"] < 0.02
    over = S.calibration_metrics(np.clip(p + 0.2, 0, 1), y)
    assert over["intercept"] < -0.3 and over["ece"] > 0.1


# ------------------------------------------------------------------------------ freeze and reproduction
def test_freeze_verifies_and_detects_a_change(tmp_path):
    """This freeze is historical: it is checked at the archive commit against the archived record.

    It was regenerated post hoc at 02:53 on 2026-09-27 and verified against no commit even then
    (research/experiments/external-validation-1/EVIDENCE.json). Comparing it with the moving
    working tree, as this test used to, tested later edits instead of the registration.
    """
    from research.protocol_v2 import registry as G
    freeze_path = HERE / "freeze.json"
    evidence_path = ROOT / "research/experiments/external-validation-1/EVIDENCE.json"
    if not freeze_path.is_file() or not evidence_path.is_file():
        pytest.skip("freeze.json and its archive record are required")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    archived = json.loads(evidence_path.read_text(encoding="utf-8"))["freezes"]["regenerated_02_53"]
    assert F.sha256_file(freeze_path) == archived["sha256"]
    check = G.verify_at_commit(freeze["sha256"], archived["verification_at_archive_commit"]["commit"], ROOT)
    if check["problems"] and all(s == "missing" for s in check["status"].values()):
        pytest.skip("the archive commit is not in this clone")
    from research.protocol_v2.archive import EDITED_AFTER_WITNESS
    allowed = set(archived["verification_at_archive_commit"]["problems"]) | {f"changed:{p}" for p in EDITED_AFTER_WITNESS}
    assert set(check["problems"]) <= allowed
    relative = "research/external_validation/protocol.json"
    copy_root = tmp_path / "root"
    target = copy_root / relative
    target.parent.mkdir(parents=True)
    target.write_bytes((ROOT / relative).read_bytes() + b" ")
    assert f"changed:{relative}" in F.verify_freeze({"sha256": {relative: freeze["sha256"][relative]}}, copy_root)


def test_replay_float_canonicalisation_collapses_last_bit_only():
    """Persisted replay values have an explicit cross-runtime float rule."""
    left = R.canonical_replay_value(0.31938088801938413)
    right = R.canonical_replay_value(0.3193808880193838)
    assert left == right == 0.319380888019384
    # The rule is recursive and does not turn decision labels or integer counts into floats.
    value = R.canonical_replay_value({"decision": "defer", "steps": [{"support": np.int64(2), "p": left}]})
    assert value == {"decision": "defer", "steps": [{"support": 2, "p": 0.319380888019384}]}


def _assert_replay_record_matches(current, saved):
    current, saved = R.canonical_replay_value(current), R.canonical_replay_value(saved)
    current.pop("compute_seconds", None)
    saved.pop("compute_seconds", None)
    # RidgeCV/BLAS builds differ by up to 3e-15 in this diagnostic. Actions,
    # outcomes, fitted alpha and all other fields must still match exactly.
    if current["arm"] == saved["arm"] == "ridge":
        for new_step, old_step in zip(current["steps"], saved["steps"]):
            new_note, old_note = new_step.get("note") or {}, old_step.get("note") or {}
            if "score_gap" in new_note and "score_gap" in old_note:
                assert new_note.pop("score_gap") == pytest.approx(old_note.pop("score_gap"), rel=0, abs=1e-14)
    assert current == saved


def test_replay_comparison_preserves_decisions_and_meaningful_score_changes():
    saved = {"arm": "ridge", "steps": [{"key": ["A549", 24, 10], "outcome": "eliminate_a",
                                           "note": {"score_gap": 0.319380888019384}}]}
    current = copy.deepcopy(saved)
    current["steps"][0]["note"]["score_gap"] += 3e-15
    _assert_replay_record_matches(current, saved)
    current["steps"][0]["note"]["score_gap"] += 1e-10
    with pytest.raises(AssertionError):
        _assert_replay_record_matches(current, saved)
    current = copy.deepcopy(saved)
    current["steps"][0]["outcome"] = "eliminate_b"
    with pytest.raises(AssertionError):
        _assert_replay_record_matches(current, saved)


def test_replay_reproduces_a_saved_fold():
    """Rerun an original registered fold and compare every registered arm's records.

    `l1000_T_1` was rewritten post hoc with an added arm, so comparing against it was circular.
    `l1000_T_0` is original (record count and time match the registered run), and only the arms
    the original run registered are compared.
    """
    saved = R.OUT / "replay" / "l1000_T_0.jsonl.gz"
    manifest = ROOT / "log/20260927/0927/external_validation_replay_manifest.json"
    if not saved.is_file() or not manifest.is_file():
        pytest.skip("the registered replay has not been run")
    registered_arms = set(json.loads(manifest.read_text(encoding="utf-8"))["arms"])
    result = R.run_task(("l1000", "T", 0), R.units("l1000"))
    with gzip.open(saved, "rt", encoding="utf-8") as stream:
        old = [json.loads(line) for line in stream]
    assert len(old) == json.loads(manifest.read_text(encoding="utf-8"))["files"]["l1000_T_0"]
    def keep(rows):
        selected = [r for r in rows if r["arm"].split("@")[0] in registered_arms]
        return sorted(selected, key=lambda r: (r["arm"], r["compound"], r["h1"], r["h2"], str(r["price"])))
    current, saved_rows = keep(result["records"]), keep(old)
    assert len(current) == len(saved_rows)
    for new_row, old_row in zip(current, saved_rows):
        _assert_replay_record_matches(new_row, old_row)
