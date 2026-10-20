"""Regression tests for the procedure-inheritance study. Fixtures establish implementation correctness only; they are not evidence of scientific benefit."""
from __future__ import annotations

import copy
import gzip
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

STUDY = Path(__file__).resolve().parents[1] / "research" / "procedure_inheritance_20261020"
if str(STUDY) not in sys.path:
    sys.path.insert(0, str(STUDY))

import pi_factors as F  # noqa: E402
import pi_fixtures as X  # noqa: E402
import pi_model as M  # noqa: E402
import pi_plan as PL  # noqa: E402
import pi_run as R  # noqa: E402
import pi_stats as ST  # noqa: E402
import pi_verify as V  # noqa: E402
import pi_world as W  # noqa: E402


# ------------------------------------------------------------------ analytical / synthetic fixtures
def test_one_step_kg_agrees_with_monte_carlo_and_quadrature_converges():
    lib, a = X.fixture_lib(), X.base_a()
    w = M.posterior(lib, {})
    cand = np.array([1, 2])
    exact = M.kg1_all(lib, a, {}, w, cand, G=25)[0]
    approx = M.kg1_all(lib, a, {}, w, cand, G=5)[0]
    cur = M._topk_mean(M.scores(lib, a, {}, w))
    rng = np.random.default_rng(1)
    for j, p in enumerate(cand):
        n = 12000
        c = rng.choice(lib.C, size=n, p=w)
        r = lib.Lfull[c, p] + lib.sd[c] * rng.standard_normal(n)
        v = np.array([M._topk_mean(M.scores(lib, a, {int(p): float(x)}, M.posterior(lib, {int(p): float(x)}))) for x in r])
        se = v.std() / np.sqrt(n)
        assert abs((v.mean() - cur) - exact[j]) < 4 * se + 1e-4
        assert abs(approx[j] - exact[j]) / exact[j] < 0.06           # production 5-node quadrature error is documented (<= 6 % here)


def test_two_step_value_is_at_least_one_step_value_and_never_negative():
    lib, a = X.fixture_lib(), X.base_a()
    w = M.posterior(lib, {})
    rk, k1 = M.kg2_rank(lib, a, {}, w, np.arange(X.P))
    assert rk[0][1] >= 0.97 * k1 and all(v > -1e-6 for _, v in rk)


def test_branching_plan_executes_different_second_reads_for_different_observations():
    lib, pl, out = X.run_branching()
    q1, q3 = [q[0] for q in out[1]["queries"]], [q[0] for q in out[3]["queries"]]
    assert q1[0] == q3[0] == 0                                       # same first measurement
    assert q1[1] == X.EFF[1][0] and q3[1] == 1                        # observation-dependent second measurement
    assert out[1]["branch"] == 1 and out[3]["branch"] == 0
    assert sorted(out[1]["nominated"]) == sorted(X.EFF[1][:5]) or set(out[1]["nominated"]) <= set(X.EFF[1])
    assert set(out[3]["nominated"]) <= set(X.EFF[3])
    assert out[1]["utility"] == pytest.approx(out[1]["oracle"]) and out[3]["utility"] == pytest.approx(out[3]["oracle"])


def test_unused_metadata_is_not_execution_and_changing_a_branch_is():
    lib, pl, out = X.run_branching()
    meta = PL.Plan(pl.p1, pl.edges, pl.second, pl.B, pl.aref_mu, pl.aref_sd, pl.lib_fp, bin_mass=[0.9, 0.1], parents=("x",))
    assert meta.exec_sha == pl.exec_sha and meta.pid != pl.pid        # history changes identity, not the executable content
    row = M.run_campaign(lib, X.camp_for(3), 4, meta, arm="plan")
    assert row["queries"] == out[3]["queries"]
    altered = PL.Plan(pl.p1, pl.edges, [2, X.EFF[1][0]], pl.B, pl.aref_mu, pl.aref_sd, pl.lib_fp)
    assert altered.exec_sha != pl.exec_sha
    row = M.run_campaign(lib, X.camp_for(3), 4, altered, arm="plan")
    assert [q[0] for q in row["queries"]][1] == 2


def test_branch_collapse_ablation_removes_the_observation_dependence():
    lib, pl, out = X.run_branching()
    col = PL.Plan(pl.p1, pl.edges, pl.second, pl.B, pl.aref_mu, pl.aref_sd, pl.lib_fp, bin_mass=[0.2, 0.8]).collapsed()
    seconds = {r: [q[0] for q in M.run_campaign(lib, X.camp_for(r), 4, col, arm="c")["queries"]][1] for r in (1, 3)}
    assert seconds[1] == seconds[3]


def test_unknown_exit_triggers_and_later_reads_are_direct():
    row, lib = X.run_unknown_exit()
    assert row["exit_unknown"] and row["unknown_step"] is not None and row["post_unknown"] > 0.5
    a = X.base_a()
    qs = [q[0] for q in row["queries"]]
    obs = {p: y - a[p] for p, y in row["queries"][:row["unknown_step"] - 1]}
    w = M.posterior(lib, obs)
    s = M.scores(lib, a, obs, w)
    legal = [i for i in range(X.P) if i not in obs]
    assert qs[row["unknown_step"] - 1] == max(legal, key=lambda i: (s[i], -i))


def test_stop_branch_hands_over_to_the_default_planner():
    row, ref = X.run_stop_branch()
    assert row.get("plan_stop") is True
    lib, a = X.fixture_lib(), X.base_a()
    (p0, y0) = row["queries"][0]
    obs = {p0: y0 - a[p0]}
    expect = M.Kg1().choose(M.Ctx(lib, a, obs, [[p0, y0]], M.posterior(lib, obs), 2, 4, {}))
    assert p0 == 0 and row["queries"][1][0] == expect


def test_inapplicable_plan_is_exactly_the_default_planner():
    row, ref, row2 = X.run_inapplicable()
    assert row["plan_applicable"] is False and row["queries"] == ref["queries"] and row["nominated"] == ref["nominated"]
    assert row2["plan_applicable"] is False                              # public reference outside the validated range


def test_plan_artifact_roundtrip_and_tamper_detection():
    lib, pl, _ = X.run_branching()
    j = pl.to_json()
    assert PL.Plan.from_json(json.loads(json.dumps(j))).pid == pl.pid
    bad = copy.deepcopy(j)
    bad["content"]["second"][0] = 5
    with pytest.raises(AssertionError):
        PL.Plan.from_json(bad)
    bad = copy.deepcopy(j)
    bad["history"]["lib_fp"] = "f" * 64
    with pytest.raises(AssertionError):
        PL.Plan.from_json(bad)


def test_library_fingerprint_changes_with_a_profile_value():
    lib = X.fixture_lib()
    L2 = lib.L.copy()
    L2[1, 0] += 1e-3
    assert M.Lib(L2, lib.counts, lib.s2).fingerprint() != lib.fingerprint()
    z = lib.arrays()
    assert M.Lib.from_arrays({f"p{k}": v for k, v in z.items()}, "p").fingerprint() == lib.fingerprint()


def test_promotion_rules_never_promote_ties():
    assert not F.promote_rule(0.1, 2, 2) and not F.promote_rule(0.1, 1, 0) and F.promote_rule(0.01, 3, 1)
    assert not F.promote_rule_plan(0.1, 0, 0) and not F.promote_rule_plan(0.003, 3, 0) and F.promote_rule_plan(0.01, 1, 0)


# ------------------------------------------------------------------ world and learning
def test_world_is_deterministic_and_released_reads_use_the_same_noise_table():
    a, b = W.make_stream("alias", 5), W.make_stream("alias", 5)
    assert all(np.array_equal(a["bgs"][i]["y"], b["bgs"][i]["y"]) for i in a["bgs"])
    assert a["schedule"]["H0"] == list(range(8)) and len(a["schedule"]["A_old"]) == 4
    E, A, Y = W.released_residuals(a, [0, 1])
    assert np.allclose(Y, [a["bgs"][0]["y"], a["bgs"][1]["y"]])


def test_factor_learning_finds_planted_regimes_and_none_in_the_null_world():
    s = W.make_stream("alias", 5)
    ids = s["schedule"]["H0"]
    E, A, Y = W.released_residuals(s, ids)
    r = F.learn("off", None, E, A, ids)
    assert r["n_regimes"] == 2 and r["n_candidates"] <= F.CAND_CAP
    s0 = W.make_stream("null", 5)
    E, A, Y = W.released_residuals(s0, s0["schedule"]["H0"])
    assert F.learn("off", None, E, A, s0["schedule"]["H0"])["n_regimes"] == 0


def test_factor_inheritance_on_reuses_the_previous_library_labels():
    s = W.make_stream("alias", 5)
    sc = s["schedule"]
    ids0 = sc["H0"]
    E, A, Y = W.released_residuals(s, ids0)
    r0 = F.learn("on", None, E, A, ids0)
    ids1 = ids0 + sc["batches"][0]
    E, A, Y = W.released_residuals(s, ids1)
    r1 = F.learn("on", r0["labels"], E, A, ids1)
    assert r1["n_regimes"] >= r0["n_regimes"] and r1["n_candidates"] <= F.CAND_CAP


# ------------------------------------------------------------------ mini-run: writes, replays, verifier
@pytest.fixture(scope="module")
def mini(tmp_path_factory):
    out = tmp_path_factory.mktemp("pi_mini") / "eval"
    for seed in (5, 6):
        R.run_stream("alias", seed, out)
    for seed, partner in ((5, 6), (6, 5)):
        R.run_xplant("alias", seed, partner, out)
    return out


def test_runs_are_write_once(mini):
    with pytest.raises(SystemExit):
        R.run_stream("alias", 5, mini)
    with pytest.raises(SystemExit):
        R.run_xplant("alias", 5, 6, mini)


def test_mini_run_verifies_and_every_row_replays_from_stored_artifacts(mini):
    problems, stats = V.verify(mini, subset=True)
    assert problems == [] and stats["rows_replayed"] > 800


def test_all_arms_share_backgrounds_budgets_and_the_read_table(mini):
    streams, xp = ST.load(mini)
    d = streams["alias_5"]
    by = {}
    for r in d["rows"]:
        if r["role"] == "task" and r["budget_arm"] == 4:
            by.setdefault(r["bg"], {})[r["arm"]] = r
    assert len(by) == 16 and all(set(v) == set(R.ARMS) for v in by.values())
    reads = {}
    for v in by.values():
        for arm, r in v.items():
            for p, y in r["queries"]:
                assert reads.setdefault((r["bg"], p), y) == y          # identical read value in every arm
    assert all(r["n_spent"] == 4 for v in by.values() for a, r in v.items() if a not in ("prior",))


def test_plan_and_candidate_caps_and_deletion_equals_fresh_planner_when_no_plan(mini):
    streams, xp = ST.load(mini)
    d = streams["alias_5"]
    assert all(g["factors"][m]["n_candidates"] <= 12 for g in d["generations"] for m in ("on", "off"))
    assert all(r["n_candidates"] <= 12 for g in d["generations"] for r in g["plans"].values())
    undeployed = {(g["ckpt"], int(k.split("|")[1])) for g in d["generations"] for k, r in g["plans"].items() if k.startswith("f1_plan|") and r["deployed"] is None}
    assert undeployed
    for r in d["rows"]:
        if r["arm"] == "f1_plan" and r["role"] == "task" and (r["ckpt"], r["budget_arm"]) in undeployed:
            k = next(x for x in d["rows"] if x["arm"] == "f1_kg1" and x["bg"] == r["bg"] and x["budget_arm"] == r["budget_arm"] and x["role"] == "task")
            assert k["queries"] == r["queries"] and k["nominated"] == r["nominated"]


def _copy_run(mini, tmp_path):
    dst = tmp_path / "eval"
    shutil.copytree(mini, dst)
    return dst


def _edit_stream(run, name, fn):
    p = run / "streams" / name
    with gzip.open(p, "rt", encoding="utf-8") as f:
        d = json.load(f)
    fn(d)
    with gzip.open(p, "wt", encoding="utf-8") as f:
        f.write(json.dumps(d))


def test_verifier_rejects_missing_rows_altered_reads_tampered_plans_and_wrong_libraries(mini, tmp_path):
    def drop(d):
        d["rows"].pop(100)

    def alter_read(d):
        r = next(x for x in d["rows"] if x["arm"] == "f1_kg1" and x["queries"])
        r["queries"][0][1] += 1e-3

    def alter_nom(d):
        r = next(x for x in d["rows"] if x["arm"] == "f1_kg2")
        r["nominated"] = r["nominated"][::-1][:4] + [r["nominated"][0]]

    def wrong_lib(d):
        r = next(x for x in d["rows"] if x["arm"] == "f1_kg1")
        r["lib_fp"] = "0" * 64

    def tamper_plan(d):
        k = next(k for k, v in d["plans"].items() if v and k.startswith("f1_plan|"))
        d["plans"][k]["content"]["second"][0] = (d["plans"][k]["content"]["second"][0] + 1) % 66

    def exceed_cap(d):
        d["generations"][1]["plans"]["f1_plan|3"]["n_candidates"] = 13

    for i, fn in enumerate((drop, alter_read, alter_nom, wrong_lib, tamper_plan, exceed_cap)):
        run = _copy_run(mini, tmp_path / f"m{i}")
        _edit_stream(run, "alias_5.json.gz", fn)
        problems, _ = V.verify(run, subset=True)
        assert problems, f"mutation {fn.__name__} was not detected"
        shutil.rmtree(run)


def test_verifier_reports_incomplete_when_streams_are_absent(tmp_path):
    (tmp_path / "streams").mkdir()
    problems, _ = V.verify(tmp_path, subset=True)
    assert problems and "missing mandatory evidence" in problems[0]


def test_summary_is_rebuildable_and_decision_label_is_defined(mini):
    streams, xp = ST.load(mini)
    s = ST.build_summary(mini)
    assert s["n_streams"] == 2 and s["decision"]["label"] in ("ADVANCE_TO_POWERED_INDEPENDENT_DESIGN", "CLOSE_NO_PRACTICAL_BENEFIT_OVER_FRESH_ONE_STEP_PLANNING",
                                                             "CLOSE_EXPLAINED_BY_CONVENTIONAL_LOOKAHEAD_OR_DISTILLATION", "INCONCLUSIVE_DEVELOPMENT")
    assert ST.diff_summaries(s, ST.build_summary(mini)) == []
    assert "f1_plan@3 - f1_kg2@3" in s["contrasts"] and "PRIMARY f1_plan@3 - f1_kg2@4 (one assay unit saved?)" in s["contrasts"]
