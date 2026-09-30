"""Protocol-v2 contracts: registration, archive integrity, truth semantics, public view, safe arm, gates.

File summary
- Path: research/protocol_v2/test_protocol_v2.py
- Purpose: pin every protocol-v2 boundary with a test. Registration, verification and scoring
  tests run anywhere with git. Tests that need the prepared development data or protocol-v1
  outputs skip by name when those files are absent.
- Run: python -m pytest research/protocol_v2 -q -p no:cacheprovider
"""
from __future__ import annotations

import gzip
import json
import math
import os
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from research.protocol_v2 import attribution as AT
from research.protocol_v2 import calibration as CB
from research.protocol_v2 import contracts as K
from research.protocol_v2 import headroom as H
from research.protocol_v2 import registry as G
from research.protocol_v2 import runner as RN
from research.protocol_v2 import safe as SF

ROOT = G.ROOT
DEV = ROOT / "outputs/belief_planning_20260927/registered/dev"
P, C, E = K.T.P, K.T.C, K.T.E


# ------------------------------------------------------------------------------ registration
def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run = lambda *a: subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True)  # noqa: E731
    run("init", "-q")
    (repo / ".gitattributes").write_bytes(b"* text=auto eol=lf\n")
    (repo / "protocol.json").write_bytes(b'{"version": "t"}\n')
    run("add", ".")
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init")
    return repo


def test_registration_refuses_a_dirty_tree_and_writes_once(tmp_path):
    repo = _repo(tmp_path)
    (repo / "data.csv").write_bytes(b"a,b\n1,2\n")
    record_path = tmp_path / "records" / "exp.json"
    with pytest.raises(G.DirtyTree):
        G.register(record_path, "exp", protocol_files=["protocol.json"], data_files=["data.csv"], root=repo, seed=1)
    assert not record_path.exists()
    (repo / ".gitignore").write_bytes(b"data.csv\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "ignore"], cwd=repo,
                   check=True)
    record = G.register(record_path, "exp", protocol_files=["protocol.json"], data_files=["data.csv"], root=repo,
                        seed=7, command=["python", "-m", "x"])
    for field in ("protocol_version", "git_commit", "git_dirty", "manifest_sha256", "data_sha256", "environment_lock",
                  "command", "random_seed", "protocol_sha256", "record_sha256"):
        assert field in record
    assert record["git_dirty"] is False and record["registered"] is True and record["random_seed"] == 7
    assert record["environment_lock"]["runtime_versions"]["numpy"]
    assert not os.stat(record_path).st_mode & stat.S_IWRITE
    with pytest.raises(G.AlreadyRegistered):
        G.register(record_path, "exp", protocol_files=["protocol.json"], root=repo)
    os.chmod(record_path, stat.S_IWRITE | stat.S_IREAD)


def test_development_record_discloses_a_dirty_tree(tmp_path):
    repo = _repo(tmp_path)
    (repo / "protocol.json").write_bytes(b'{"version": "changed"}\n')
    record = G.development_record(tmp_path / "dev.json", "dev", protocol_files=["protocol.json"], root=repo)
    assert record["registered"] is False and record["git_dirty"] is True
    assert record["status"] == "development_unregistered" and "protocol.json" in record["git_changes"]
    os.chmod(tmp_path / "dev.json", stat.S_IWRITE | stat.S_IREAD)


def test_verification_is_against_the_commit_and_line_ending_aware(tmp_path):
    repo = _repo(tmp_path)
    commit = G.git_state(repo)["commit"]
    lf = (repo / "protocol.json").read_bytes()
    digests = {"protocol.json": G.sha256_bytes(lf.replace(b"\n", b"\r\n"))}
    assert G.verify_at_commit(digests, commit, repo)["status"]["protocol.json"] == "eol_equivalent"
    assert G.verify_at_commit({"protocol.json": G.sha256_bytes(lf)}, commit, repo)["status"]["protocol.json"] == "exact"
    changed = G.verify_at_commit({"protocol.json": G.sha256_bytes(b"other")}, commit, repo)
    assert changed["problems"] == ["changed:protocol.json"]
    assert G.content_sha256(repo, "protocol.json") == G.sha256_bytes(lf)


def test_decision_comparison_ignores_float_formatting_but_not_decisions():
    row = {"arm": "a", "compound": "c", "h1": "x", "h2": "y", "stop": "eliminated", "final": "correct",
           "measurements": 1, "steps": [{"action": "k", "outcome": "eliminate_b", "qc": True, "eliminated": ["y"]}]}
    same = {**row, "p": 0.31938088801938413}
    assert G.compare_decisions([row], [same])["identical_decisions"]
    other = {**row, "steps": [{**row["steps"][0], "action": "k2"}]}
    report = G.compare_decisions([row], [other])
    assert not report["identical_decisions"] and report["problems"][0]["problem"] == "step0_action_differs"


# ------------------------------------------------------------------------------ archive
def _evidence(name):
    path = ROOT / "research/experiments" / name / "EVIDENCE.json"
    if not path.is_file():
        pytest.skip(f"{path} is written by `python -m research.protocol_v2.archive --write`")
    return json.loads(path.read_text(encoding="utf-8"))


def _entries(value):
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            yield value
        for v in value.values():
            yield from _entries(v)
    elif isinstance(value, list):
        for v in value:
            yield from _entries(v)


@pytest.mark.parametrize("name", ["external-validation-1", "belief-planning-1"])
def test_archived_evidence_is_unchanged(name):
    """Any rewrite of an archived protocol-v1 artefact after 2026-09-27 12:04 fails here."""
    checked = 0
    for entry in _entries(_evidence(name)):
        path = ROOT / entry["path"]
        if path.is_file():
            assert G.sha256_file(path) == entry["sha256"], entry["path"]
            checked += 1
    assert checked or pytest.skip("no archived artefact is present locally")


def test_archive_records_what_protocol_v1_left():
    ev1, bp1 = _evidence("external-validation-1"), _evidence("belief-planning-1")
    original = ev1["freezes"]["original"]["verification_at_archive_commit"]["problems"]
    assert len(original) == 9 and "changed:research/external_validation/arms.py" in original
    rewritten = [f["path"] for f in ev1["replay_folds"] if f["status"] == "rewritten_post_hoc"]
    assert rewritten == ["outputs/external_validation_20260927/replay/l1000_T_1.jsonl.gz"]
    assert bp1["freeze"]["registered_from_dirty_tree"] is True
    assert bp1["freeze"]["unchanged_since_vault_opened"] is True and bp1["vault"]["opened_once"] is True
    assert all(f["status"] == "original" for f in bp1["development_run"]["folds"])


def test_belief_planning_1_freeze_verifies_at_its_archive_commit():
    bp1 = _evidence("belief-planning-1")
    freeze = json.loads((ROOT / "research/belief_planning/freeze.json").read_text(encoding="utf-8"))
    check = G.verify_at_commit(freeze["sha256"], bp1["archive_commit"], ROOT)
    if all(s == "missing" for s in check["status"].values()):
        pytest.skip("archive commit and data absent")
    # files not re-derivable from the commit are those protocol v2 edited after the session-start
    # witness (archive.EDITED_AFTER_WITNESS); absent untracked data is reported, not failed
    from research.protocol_v2.archive import EDITED_AFTER_WITNESS
    allowed = {f"changed:{p}" for p in EDITED_AFTER_WITNESS}
    assert set(check["problems"]) <= allowed | {
        p for p in check["problems"] if p.startswith("missing:outputs/") or p.startswith("missing:data/")}


# ------------------------------------------------------------------------------ truth semantics
def _trace(steps=(), remaining=("x", "y")):
    return {"arm": "a", "compound": "c", "h1": "x", "h2": "y", "steps": list(steps), "remaining": list(remaining)}


def test_scoring_fails_closed_without_a_truth():
    for missing in (None, float("nan"), ""):
        with pytest.raises(K.TruthMissing):
            K.score(_trace(), missing)
    with pytest.raises(K.TruthMissing):
        K.score(_trace(), "z")
    with pytest.raises(ValueError):
        K.score({**_trace(), "truth": "x"}, "x")


def test_scoring_semantics():
    step = [{"action": "k"}]
    assert K.score(_trace(), "x")["final"] == "deferred"
    assert K.score(_trace(step, ("x",)), "x")["final"] == "correct"
    assert K.score(_trace(step, ("y",)), "x")["final"] == "wrong"
    assert K.score(_trace(step, ()), "x")["final"] == "exhausted"
    assert K.score(_trace(step), "x")["final"] == "undetermined"
    assert K.score(_trace(step, ("y",)), "x")["utility"] == -2


def test_historical_scoring_fails_closed():
    state = SimpleNamespace(candidates=frozenset({"x", "y"}))
    setting = P.Setting("t", (("L", 24.0, 1.0),), (), lambda k: 1.0, 2.0)
    with pytest.raises(ValueError, match="scoring_truth_missing"):
        P.finish("a", "c", None, "x", "y", state, [], None, setting, "continue")
    with pytest.raises(ValueError, match="scoring_truth_outside_contrast"):
        P.finish("a", "c", "z", "x", "y", state, [], None, setting, "continue")
    with pytest.raises(ValueError, match="scoring_truth_missing"):
        E.finish("a", "c", float("nan"), "x", "y", state, [])


def test_forced_choice_episodes_skip_unscorable_compounds():
    key = ("A549", 24.0, 100.0)
    data = SimpleNamespace(index={key: {"labelled": 0, "unlabelled": 1, "outside": 2}},
                           compounds=pd.DataFrame({"compound": ["labelled", "unlabelled", "outside"],
                                                   "klass": ["H1", None, "H9"], "fold": [0, 0, 0]}))
    ctx = SimpleNamespace(data=data, tier=C.Tier("B", (key,), ("H1", "H2"), ("labelled", "unlabelled", "outside")))
    episodes = E.episode_list(ctx, 0)
    assert {e[0] for e in episodes} == {"labelled"} and all(e[1] == "H1" for e in episodes)


def test_measurement_states_are_distinct():
    assert K.measurement_state({"row": None, "qc": False, "outcome": "quality_failed"}) is K.MeasurementState.NOT_MEASURED
    assert K.measurement_state({"row": 3, "qc": False, "outcome": "quality_failed"}) is K.MeasurementState.QUALITY_FAILED
    assert K.measurement_state({"row": 3, "qc": True, "outcome": "undetected"}).value == "measured_undetected"
    assert K.measurement_state({"row": 3, "qc": True, "outcome": "ambiguous"}).value == "measured_ambiguous"
    assert K.measurement_state({"row": 3, "qc": True, "outcome": "eliminate_a"}).value == "measured_eliminating"
    assert not K.MeasurementState.NOT_MEASURED.biological and not K.MeasurementState.QUALITY_FAILED.biological
    assert K.MeasurementState.MEASURED_UNDETECTED.biological


def test_contamination_bounds_the_likelihood_ratio():
    from maestro.acquisition import OutcomeBranch, OutcomeForecast
    from research.belief_planning import arms as BA
    f = OutcomeForecast("a", (OutcomeBranch("x", {"m": 1.0, "n": 0.0}, 3), OutcomeBranch("y", {"m": 0.0, "n": 1.0}, 3)))
    assert BA._contaminated(f, 0.0) is f
    g = BA._contaminated(f, 0.3)
    assert math.isclose(sum(g.branch_for("x").probabilities.values()), 1.0)
    assert g.branch_for("x").probabilities["n"] == pytest.approx(0.15)
    b = pd.DataFrame({"p_truth": [0.0], "p_other": [1.0]})
    assert CB.posterior_truth(b, 0.0)[0] == 0.0 and CB.posterior_truth(b, 0.3)[0] > 0.05


# ------------------------------------------------------------------------------ gates
def _frame(arms_finals, units=("u1", "u2", "u3")):
    rows = []
    for arm, finals in arms_finals.items():
        for i, final in enumerate(finals):
            rows.append({"arm": arm, "dataset": "d", "tier": "T", "fold": 0, "compound": f"c{i}", "h1": "x", "h2": "y",
                         "final": final, "unit": units[i % len(units)], "measurements": 1, "days": 1.0,
                         "sequence": arm if final != "undetermined" else "same"})
    frame = pd.DataFrame(rows)
    frame["correct"] = (frame.final == "correct").astype(float)
    frame["wrong"] = (frame.final == "wrong").astype(float)
    frame["deferred"] = (frame.final == "deferred").astype(float)
    frame["utility"] = frame.correct - 2 * frame.wrong
    frame["episode"] = frame.compound
    return frame


def test_headroom_gate():
    finals = {"fixed": ["undetermined"] * 6 + ["correct"] * 4, "oracle": ["correct"] * 10,
              "belief": ["undetermined"] * 6 + ["correct"] * 4}
    out = H.task_headroom(_frame(finals))
    assert out["headroom_correct"]["difference"] == pytest.approx(0.6)
    assert out["gate"]["eligible_primary"] and out["decision_changeable_unit_share"] == 1.0
    low = H.task_headroom(_frame({"fixed": ["correct"] * 10, "oracle": ["correct"] * 10, "belief": ["correct"] * 10}))
    assert low["gate"]["status"] == "ineligible_low_headroom"


def test_attribution_verdicts():
    def c(d, lo, hi, action=0.3, decision=0.1, wrong_hi=0.0, meas_hi=0.0):
        return {"action_change_rate": action, "decision_change_rate": decision,
                "correct": {"difference": d, "ci": [lo, hi]}, "wrong": {"ci": [-0.01, wrong_hi]},
                "measurements": {"ci": [-0.1, meas_hi]}}
    assert AT.verdict(c(0.05, 0.01, 0.09), [c(0.05, 0.01, 0.09)]) == "KEEP"
    assert AT.verdict(c(0.05, 0.01, 0.09), [c(0.0, -0.02, 0.02)]) == "INCONCLUSIVE"
    assert AT.verdict(c(0.05, 0.01, 0.09, wrong_hi=0.02), [c(0.05, 0.01, 0.09)]) == "INCONCLUSIVE"
    assert AT.verdict(c(0.0, -0.01, 0.01), []) == "REJECT_AS_DEFAULT"
    assert AT.verdict(c(0.05, 0.01, 0.09, action=0.3, decision=0.0), [c(0.05, 0.01, 0.09)]) == "INCONCLUSIVE"


def test_hierarchical_calibration_shrinks_thin_strata_to_the_parent():
    src = pd.DataFrame({"y_wrong": [1.0] * 2 + [0.0] * 98, "p_wrong": [0.01] * 100,
                        "stratum": ["a"] * 50 + ["b"] * 50})
    model = CB.fit(src)
    assert model["parent"] == pytest.approx(0.02)
    a, b = CB._posterior(model, "unseen")
    assert a / (a + b) == pytest.approx((CB.KAPPA * 0.02 + 0.5) / (CB.KAPPA + 1.0))
    ad, bd = CB._posterior(model, "a", CB.DISCOUNT)
    af, bf = CB._posterior(model, "a")
    assert ad + bd < af + bf


# ------------------------------------------------------------------------------ safe arm (stubbed plan)
class _Value:
    def __init__(self, utility, se=0.0, p_wrong=0.01, upper=0.1, cost=6.0):
        self.utility, self.standard_error, self.p_wrong, self.p_wrong_upper, self.cost = utility, se, p_wrong, upper, cost


def _stub(monkeypatch, *, chosen, reason=None, evaluations, supported):
    keys = {"F": ("L", 24.0, 1.0), "G": ("L", 24.0, 2.0)}
    plan = SimpleNamespace(chosen=chosen, reason=reason, status="selected" if chosen else "stopped",
                           evaluations=evaluations, refusals={})
    world = SimpleNamespace(forecast=lambda *a, **k: None)
    monkeypatch.setattr(SF, "_plan", lambda *a, **k: (world, (), {"x": 0.5, "y": 0.5}, plan, {C.action_id(k): k for k in keys.values()}))
    monkeypatch.setattr(SF, "effective_support", lambda view, world, compound, key, *a, **k: {
        "supported": supported.get(C.action_id(key), False), "reasons": [] if supported.get(C.action_id(key)) else ["thin"]})
    setting = P.Setting("t", tuple(keys.values()), (keys["F"],), lambda k: 6.0, 12.0)
    view = SimpleNamespace(params={"eliminates": True}, extra={})
    return view, setting, keys, [keys["F"], keys["G"]]


def _ids(keys):
    return C.action_id(keys["F"]), C.action_id(keys["G"])


def test_safe_arm_follows_the_baseline_unless_a_departure_is_supported(monkeypatch):
    ids = _ids({"F": ("L", 24.0, 1.0), "G": ("L", 24.0, 2.0)})
    better = {ids[0]: _Value(0.1), ids[1]: _Value(0.5)}
    arm = SF.safe_arm(allow_model_stop=False)
    # unsupported favourite: keep the baseline
    view, setting, keys, menu = _stub(monkeypatch, chosen=ids[1], evaluations=better, supported={ids[0]: True})
    assert arm(view, "c", "x", "y", [], menu, 12.0, setting, None)[0] == keys["F"]
    # supported, better, no riskier: depart
    view, setting, keys, menu = _stub(monkeypatch, chosen=ids[1], evaluations=better, supported={ids[0]: True, ids[1]: True})
    key, note = arm(view, "c", "x", "y", [], menu, 12.0, setting, None)
    assert key == keys["G"] and note["decision"] == "departure"
    # riskier: keep the baseline
    risky = {ids[0]: _Value(0.1), ids[1]: _Value(0.5, p_wrong=0.05)}
    view, setting, keys, menu = _stub(monkeypatch, chosen=ids[1], evaluations=risky, supported={ids[0]: True, ids[1]: True})
    assert arm(view, "c", "x", "y", [], menu, 12.0, setting, None)[0] == keys["F"]
    # gain within the standard-error margin: keep the baseline
    noisy = {ids[0]: _Value(0.1, se=0.2), ids[1]: _Value(0.5, se=0.2)}
    view, setting, keys, menu = _stub(monkeypatch, chosen=ids[1], evaluations=noisy, supported={ids[0]: True, ids[1]: True})
    assert arm(view, "c", "x", "y", [], menu, 12.0, setting, None)[0] == keys["F"]


def test_safe_arm_never_turns_a_refusal_into_a_stop(monkeypatch):
    ids = _ids({"F": ("L", 24.0, 1.0), "G": ("L", 24.0, 2.0)})
    view, setting, keys, menu = _stub(monkeypatch, chosen=None, reason="world_model_refused", evaluations={},
                                      supported={})
    assert SF.safe_arm(allow_model_stop=True)(view, "c", "x", "y", [], menu, 12.0, setting, None)[0] == keys["F"]
    negative = {ids[0]: _Value(-0.5, se=0.01)}
    view, setting, keys, menu = _stub(monkeypatch, chosen=None, reason="no_positive_value", evaluations=negative,
                                      supported={ids[0]: True})
    assert SF.safe_arm(allow_model_stop=False)(view, "c", "x", "y", [], menu, 12.0, setting, None)[0] == keys["F"]
    key, note = SF.safe_arm(allow_model_stop=True)(view, "c", "x", "y", [], menu, 12.0, setting, None)
    assert key is None and note["why"] == "supported_stop"


# ------------------------------------------------------------------------------ data-backed contracts
@pytest.fixture(scope="module")
def sciplex_a1():
    try:
        data, real_ctx, setting = K.T.load("sciplex3", "A", 1)
    except (FileNotFoundError, OSError) as exc:
        pytest.skip(f"prepared SciPlex3 data unavailable: {exc}")
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    heldout = set(comp.index[comp.fold == 1])
    training = tuple(c for c in real_ctx.tier.compounds if comp.fold.get(c) != 1)
    view = K.public_view(real_ctx, heldout, training_compounds=training)
    return {"data": data, "real": real_ctx, "setting": setting, "view": view, "heldout": heldout,
            "episodes": E.episode_list(real_ctx, 1)}


def test_public_view_is_a_whitelist(sciplex_a1):
    view, heldout = sciplex_a1["view"], sciplex_a1["heldout"]
    assert K.public_view_problems(view, heldout) == []
    assert "klass" not in view.data.compounds.columns and view.tier.compounds == ()
    for attr in ("index", "shift", "conditions"):
        with pytest.raises(AttributeError):
            getattr(view.data, attr)
    with pytest.raises(AttributeError):
        getattr(view, "detected")


def test_public_view_does_not_move_with_held_out_labels(sciplex_a1):
    real, heldout = sciplex_a1["real"], sciplex_a1["heldout"]
    before = K.public_view(real, heldout, training_compounds=sciplex_a1["view"].extra["training_compounds"])
    compounds = real.data.compounds.copy()
    changed = real.data.compounds.copy()
    changed.loc[changed.compound.isin(heldout), "klass"] = "hidden_label_changed"
    real.data.compounds = changed
    try:
        after = K.public_view(real, heldout, training_compounds=sciplex_a1["view"].extra["training_compounds"])
    finally:
        real.data.compounds = compounds
    assert before.data.compounds.equals(after.data.compounds)
    assert dict(before.data.availability) == dict(after.data.availability)


def test_runner_offers_only_planned_conditions_and_traces_carry_no_truth(sciplex_a1):
    view, real, setting = sciplex_a1["view"], sciplex_a1["real"], sciplex_a1["setting"]
    from research.external_validation import arms as A
    compound, truth, _, h1, h2 = sciplex_a1["episodes"][0]
    trace = RN.run_episode("fixed", A.fixed, view, real, compound, h1, h2, setting)
    assert "truth" not in trace and RN.audit_trace(trace, RN.local_setting(setting, view.data.availability[compound])) == []
    assert K.score(trace, truth)["final"] in ("correct", "wrong", "undetermined", "exhausted", "deferred")
    unavailable = [k for k in setting.keys if k not in view.data.availability[compound]]
    offered = {a for menu in trace["offered"] for a in menu}
    assert not offered & {C.action_id(k) for k in unavailable}
    if unavailable:
        with pytest.raises(K.NotMeasured):
            RN.run_episode("bad", lambda *a: (unavailable[0], {}), view, real, compound, h1, h2, setting)


def test_v2_runner_reproduces_registered_decisions(sciplex_a1):
    """Replay determinism: shared arms decide exactly as the registered belief-planning-1 records."""
    path = DEV / "sciplex3_A_1.jsonl.gz"
    if not path.is_file():
        pytest.skip("registered belief-planning-1 records unavailable")
    from research.belief_planning import arms as BA
    from research.external_validation import arms as A
    arms = {"fixed": A.fixed, "belief": BA.belief_arm(), "oracle": A.make_oracle(sciplex_a1["real"], E.execute)}
    new = []
    for compound, truth, _, h1, h2 in sciplex_a1["episodes"]:
        for name, arm in arms.items():
            trace = RN.run_episode(name, arm, sciplex_a1["view"], sciplex_a1["real"], compound, h1, h2,
                                   sciplex_a1["setting"])
            new.append({**{k: trace[k] for k in ("arm", "compound", "h1", "h2", "stop", "measurements", "steps")},
                        "final": K.score(trace, truth)["final"]})
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        old = [r for r in (json.loads(line) for line in fh) if r["arm"] in arms]
    fields = ("arm", "compound", "h1", "h2", "stop", "final", "measurements", "steps")
    report = G.compare_decisions([{k: r[k] for k in fields} for r in old],
                                 [{k: r[k] for k in fields} for r in new])
    problems = [p for p in report["problems"] if not p["problem"].endswith("_state_differs")]
    assert problems == []


# ------------------------------------------------------------------------------ truth-free episodes
def test_truth_free_episodes_do_not_depend_on_labels():
    reference = {"r1": "H1", "r2": "H1", "r3": "H2", "r4": "H2", "r5": "H3", "t1": None}
    pool = K.reference_pool({c: k for c, k in reference.items() if c.startswith("r")}, min_units=2)
    assert pool == ("H1", "H2")
    episodes = K.truth_free_episodes(dataset="d", tier="T", fold=1, compounds=["t1", "t2"], pool=pool)
    assert {(e.compound, e.h1, e.h2) for e in episodes} == {("t1", "H1", "H2"), ("t2", "H1", "H2")}
    assert all(not hasattr(e, "truth") for e in episodes)
    scorable, rest = K.mechanism_endpoint(episodes, {"t1": "H2", "t2": "H9"})
    assert [e.compound for e in scorable] == ["t1"] and [e.compound for e in rest] == ["t2"]
    again = K.truth_free_episodes(dataset="d", tier="T", fold=1, compounds=["t1", "t2"], pool=pool)
    assert again == episodes
