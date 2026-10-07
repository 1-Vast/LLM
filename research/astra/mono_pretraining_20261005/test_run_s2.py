"""Dry run of the S2 machinery on a synthetic release with random mono parameters (software only)."""
import numpy as np
import pytest

from research.astra.confirmation_campaign_20261004.design import campaign as cp
from research.astra.feedback_validation_20261003 import jaaks
from research.astra.mono_pretraining_20261005 import common as cm
from research.astra.mono_pretraining_20261005 import run_s2 as r2
from research.astra.mono_pretraining_20261005.bilinear import init_params


@pytest.fixture(scope="module")
def S(tmp_path_factory):
    d = tmp_path_factory.mktemp("s2")
    src = jaaks.synthetic_release(d / "r.csv", lines=10, drugs=8)
    ticket = {"freeze_sha256": "TEST", "data_sha256": cp.sha256_file(src)}
    panels, _, cand = jaaks.build_panels(ticket, src)
    tissues = cp.build_tissues(panels, cand)
    ids = sorted({x for t in tissues.values() for p in t.pairs for x in p})
    drow = {x: i for i, x in enumerate(ids)}
    split, row, k = {}, {}, 0
    for tname, T in tissues.items():
        lines = sorted(T.present_lines)
        split[tname] = {"HD": lines[:5], "E": lines[5:]}
        for s in lines:
            row[s] = k; k += 1
    z = np.random.default_rng(0).normal(size=(k, 14))
    return dict(tissues=tissues, z=z, row=row, drow=drow, mapped=np.ones(len(ids), bool), own={}, n_drugs=len(ids),
                split=split, fold=cm.fold_of(split))


def _fake_params(S, tmp, monkeypatch):
    monkeypatch.setattr(cm, "RESULTS", tmp)
    monkeypatch.setattr(cm, "N_PERM", 2)
    monkeypatch.setattr(cm, "N_DRAWS", 2)
    pdir = tmp / "mono_params"
    pdir.mkdir()
    tags = ["X"] + [f"F{k}" for k in range(5)] + ["E"]
    for t in tags:
        for arm in ["pre"] + [f"{p}{i}" for p in ("dperm", "cperm") for i in range(2)]:
            p = init_params(14, S["n_drugs"], 4, seed=hash((t, arm)) % 1000)
            np.savez(pdir / f"{t}_{arm}.npz", **p)


def test_dev_pipeline_runs_and_respects_invariants(S, tmp_path, monkeypatch):
    _fake_params(S, tmp_path, monkeypatch)
    specs = r2.arm_specs(S["n_drugs"])
    targets, scores, conc = r2.compute(S, "dev", specs, log=lambda m: None)
    assert targets and scores
    sel, table = r2.select_configs(conc, specs, "S_both")
    assert set(sel) == {sp["family"] for sp in specs.values()}
    recs = r2.campaigns(targets, scores, specs, sel, "S_both")
    arms = {r["arm"] for r in recs}
    assert {"S_both", "D_add", "pre_h6", "scr0_h6", "dperm1_h6", "cperm0_h6", "own_h6"} <= arms
    # identical purchase legality and cap for every arm
    caps = {}
    for r in recs:
        caps.setdefault((r["tissue"], r["line"], r["role"], r["draw"]), set()).add(r["cap"])
    assert all(len(v) == 1 for v in caps.values())
    # no target line inside any history
    for (t, sidm, role, draw, fold), (T, tg) in targets.items():
        assert sidm not in tg.history_lines


def test_eval_refuses_when_gates_not_passed(S, tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "RESULTS", tmp_path)
    (tmp_path / f"s2_dev_selection_{cm.RUN}.json").write_text('{"base":"S_both","selected":{}}')
    (tmp_path / f"s2_gates_{cm.RUN}.json").write_text('{"open_E": false}')
    monkeypatch.setattr(r2, "setup", lambda: S)
    with pytest.raises(PermissionError):
        r2.main(["eval"])


def test_summary_and_gates_run_on_dry_records(S, tmp_path, monkeypatch):
    from research.astra.mono_pretraining_20261005 import analyze as an
    _fake_params(S, tmp_path, monkeypatch)
    specs = r2.arm_specs(S["n_drugs"])
    targets, scores, conc = r2.compute(S, "dev", specs, log=lambda m: None)
    sel, _ = r2.select_configs(conc, specs, "S_both")
    recs = r2.campaigns(targets, scores, specs, sel, "S_both")
    fam = {n: sp["family"] for n, sp in specs.items()}
    pids = {(k[0], k[1], k[2]): tg.pid for k, (T, tg) in targets.items()}
    out = an.summarize(dict(conc=conc, campaigns=recs, pids=pids), "S_both", sel, fam, resamples=200)
    assert "line_pair_sensitivity" in out["contrasts"]["pre_h6 - S1"]["yield"]
    assert "pre_h6 - S1" in out["contrasts"] and "own_h6 - S1" in out["contrasts"]
    assert out["contrasts"]["pre_h6 - S1"]["yield"]["decision"]["verdict"].startswith("EXPLORATORY_")
    assert len(out["reference_concordance_gain_over_base"]["dperm_h6"]) == 2
    g = an.gates(out, {"G1": {"passed": True}})
    assert set(g) >= {"open_E", "G2_own_mono_ceiling", "G3_development"}
