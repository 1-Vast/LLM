"""Software-invariant tests with synthetic data (no scientific claim).  Run:  python -m pytest research/dual_core_innovation_validation_20261021/test_study_software.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, pytest

sys.path.insert(0, str(Path(__file__).parent))
import ptv_env as ENV, ptv_audit as AU


def episode(n=8, budget=5.0, lam=0.5):
    drugs = [f"#{i}" for i in range(n)]
    W = {d: 1.0 - i / n for i, d in enumerate(drugs)}
    labels = {d: int(i % 2 == 0) for i, d in enumerate(drugs)}      # even ranks positive
    sim = {a: {b: 1.0 if a == b else 0.1 for b in drugs} for a in drugs}
    mol = {d: {"score": 0.5, "z": [0.0] * 8} for d in drugs}
    return dict(drugs=drugs, W=W, prior=dict(W), nn=dict(W), sim=sim, labels=labels, mol=mol, lam=lam, budget=budget)


TOP = "def run(env):\n    for d in sorted(env.drugs, key=lambda d: -env.W[d]):\n        if env.left() < 1.0:\n            break\n        env.query_f(d)\n"


def test_budget_is_enforced_and_yield_counts_distinct_positives():
    r = ENV.run_program(TOP, episode())
    assert r["f_used"] == 5 and r["spent"] == 5.0 and r["yield"] == 3        # ranks 0,2,4 are positive among the first five


def test_overspend_ends_episode_without_extra_information():
    src = "def run(env):\n    for d in env.drugs:\n        env.query_f(d)\n"
    r = ENV.run_program(src, episode())
    assert r["f_used"] == 5 and r["spent"] <= 5.0 + 1e-9


def test_rereading_a_recorded_label_is_free_and_new_information_costs():
    src = "def run(env):\n    d = env.drugs[0]\n    for _ in range(4):\n        env.query_f(d)\n"
    r = ENV.run_program(src, episode())
    assert r["f_used"] == 1 and r["spent"] == 1.0


def test_molecular_query_costs_lambda_and_can_be_disabled():
    src = "def run(env):\n    env.query_m(env.drugs[0])\n    env.query_m(env.drugs[1])\n"
    r = ENV.run_program(src, episode(lam=0.5))
    assert r["m_used"] == 2 and abs(r["spent"] - 1.0) < 1e-9
    r2 = ENV.run_program(src, dict(episode(), mol={}))
    assert r2["m_used"] == 0 and r2["error"] is not None                      # unavailable action is refused, nothing is invented


def test_private_state_and_forbidden_syntax_are_refused():
    for src in ("def run(env):\n    x = env._labels\n", "import os\ndef run(env):\n    pass\n", "def run(env):\n    open('x')\n", "def run(env):\n    getattr(env, 'x')\n"):
        r = ENV.run_program(src, episode())
        assert r["yield"] == 0 and r["error"]


def test_hung_program_times_out():
    r = ENV.run_program("def run(env):\n    while True:\n        pass\n", episode(), timeout=3.0, tries=1)
    assert r["error"] == "timeout" and r["yield"] == 0


def test_edited_program_changes_behaviour_on_a_matched_history():
    flip = "def run(env):\n    for d in sorted(env.drugs, key=lambda d: env.W[d]):\n        if env.left() < 1.0:\n            break\n        env.query_f(d)\n"
    a, b = ENV.run_program(TOP, episode()), ENV.run_program(flip, episode())
    assert [t[1] for t in a["trace"]] != [t[1] for t in b["trace"]] and a["yield"] != b["yield"]


def test_audit_flags_embedded_data_and_separates_parameter_from_structure_changes():
    stored = "def run(env):\n    known = ['#1', '#2', '#3']\n    for d in known:\n        env.query_f(d)\n"
    assert AU.audit_program(stored)["embedded_data_suspected"] is True
    assert AU.audit_program(TOP)["embedded_data_suspected"] is False
    p1, p2 = TOP.replace("1.0", "2.0"), TOP.replace("break", "continue")
    assert AU.structure_signature(p1) == AU.structure_signature(TOP)          # constant-only change = parameter refit
    assert AU.structure_signature(p2) != AU.structure_signature(TOP)          # control-flow change = structural


def test_missing_label_is_missing_not_resistant():
    pytest.importorskip("sklearn")
    import ptv_eval as E
    df = pd.DataFrame({"perts": list("abcdef"), "single": True, "y": [1, 0, np.nan, 1, 0, 0], "s": [0.9, 0.2, 0.99, 0.8, 0.3, 0.1]})
    m = E.background_metrics(df, pd.DataFrame({"perts": [], "y": []}), score="s")
    assert m["n"] == 5 and abs(m["prevalence"] - 0.4) < 1e-9                  # the NaN row is dropped, not counted as a negative


def test_final_stage_is_sealed_until_claimed(tmp_path, monkeypatch):
    import ptv_data as D
    monkeypatch.setattr(D, "LEDGER", tmp_path / "STAGE_LEDGER.json")
    monkeypatch.setattr(D, "STUDY", tmp_path)
    with pytest.raises(PermissionError):
        D.require_stage("final")
    D.require_stage("dev")                                                    # exposed stages are readable
    with pytest.raises(RuntimeError):
        D.open_stage("final")                                                 # no FREEZE.json -> refused
    (tmp_path / "f.txt").write_text("a")
    import hashlib
    (tmp_path / "FREEZE.json").write_text(json.dumps({"frozen_files": {"f.txt": hashlib.sha256(b"a").hexdigest()}}))
    (tmp_path / "f.txt").write_text("changed")
    with pytest.raises(RuntimeError):
        D.open_stage("final")                                                 # frozen file changed -> refused
    (tmp_path / "f.txt").write_text("a")
    D.open_stage("final"); D.require_stage("final")
    with pytest.raises(RuntimeError):
        D.open_stage("final")                                                 # write-once


def test_cluster_bootstrap_uses_lineages_with_multiplicity():
    pytest.importorskip("torch")
    import eval_R as R
    vals = pd.Series([1.0, 1.0, 1.0, 0.0]); lin = pd.Series(["a", "a", "b", "c"])
    lo, hi = R.boot_lineage(vals, lin, B=2000, seed=1)
    assert 0.0 <= lo < hi <= 1.0 and hi > lo
    same = R.boot_lineage(pd.Series([0.5] * 4), lin, B=200, seed=1)
    assert same == [0.5, 0.5]
