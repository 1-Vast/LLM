"""Fast unit tests for block N (no world, no network, no sealed data)."""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evaluate as EV  # noqa: E402
import models as M  # noqa: E402
import predictors as PR  # noqa: E402
import trust as TR  # noqa: E402


def test_selective_r_ignores_the_generic_profile():
    rng = np.random.default_rng(0)
    g = rng.normal(size=578)
    sel = rng.normal(size=578)
    obs = 2.0 * g + sel
    r_res = PR.residual(obs, g)
    assert abs(np.dot(r_res - r_res.mean(), g - g.mean())) < 1e-8
    assert EV.fin(PR.selective_r(3.0 * g, obs, g)) == 0.0  # "kills like everything" earns nothing
    assert PR.selective_r(sel + 5.0 * g, obs, g) > 0.99


def test_combine_skips_missing_parts():
    a = np.arange(10.0)
    assert np.allclose(PR.combine([a, None]), PR.z(a))
    assert PR.combine([None, None]) is None


def test_boot_mean_of_a_constant_collapses():
    r = EV.boot_mean(np.full(30, 0.1), np.repeat(np.arange(10), 3), 200, 1, {"ci95": 0.95})
    assert r["estimate"] == pytest.approx(0.1) and r["ci95"] == pytest.approx([0.1, 0.1])


def test_decide_rules():
    P = {"contrasts": [{"id": "X", "name": "x", "family": "vc", "predicted": "PASS"},
                       {"id": "Y", "name": "y", "family": "agent", "predicted": "HARM"},
                       {"id": "Z", "name": "z", "family": "agent", "predicted": "NOT_SUPPORTED"}],
         "headline": {"vc_primary": ["X"], "agent_any": ["Y", "Z"]}}
    cons = {"X": {"estimate": 0.1, "ci_family": [0.01, 0.2]}, "Y": {"estimate": -0.1, "ci_family": [-0.2, -0.01]},
            "Z": {"estimate": 0.0, "ci_family": [-0.1, 0.1]}}
    d = EV.decide(cons, P)
    assert [d[k]["verdict"] for k in "XYZ"] == ["PASS", "HARM", "NOT_SUPPORTED"]
    assert d["headline"] == {"vc_value_confirmed": True, "agent_value_shown": False, "agent_harm": ["Y"]}


def test_family_levels_are_bonferroni():
    P = json.loads((HERE / "PROTOCOL_CONFIG.json").read_text(encoding="utf-8"))
    assert EV.family_levels(P, "vc")["ci_family"] == pytest.approx(1 - 0.05 / 8)
    assert EV.family_levels(P, "agent")["ci_family"] == pytest.approx(1 - 0.05 / 7)


def test_protocol_config_is_consistent():
    P = json.loads((HERE / "PROTOCOL_CONFIG.json").read_text(encoding="utf-8"))
    ids = [c["id"] for c in P["contrasts"]]
    assert len(ids) == len(set(ids)) == 15
    assert set(P["headline"]["vc_primary"]) <= set(ids) and set(P["headline"]["agent_any"]) <= set(ids)
    assert {c["predicted"] for c in P["contrasts"]} <= {"PASS", "HARM", "NOT_SUPPORTED"}
    rehearsal = pd.read_csv(HERE / "rehearsal" / "dev_llm" / "ROWS_killers.csv")
    for c in P["contrasts"]:
        if c["kind"] == "paired":
            assert c["a"] in rehearsal and c["b"] in rehearsal, c["id"]


def test_trust_scoring():
    u = np.linspace(-0.1, 0.4, 50)
    oracle = TR.evaluate(u, u)
    rev = TR.evaluate(-u, u)
    assert oracle["spearman"] == pytest.approx(1.0) and oracle["top25"] > rev["top25"]
    assert np.all(np.diff(TR.coverage_curve(u, u)) <= 1e-12)
    assert TR.rank01([np.nan, 1.0, 2.0])[0] == 0.5


def test_agent_validator_drops_unknown_claims():
    import scientist as SC
    vocab = {"HDAC inhibitor": 5, "tubulin polymerization inhibitor": 9}
    offered = [("vorinostat", "HDAC inhibitor", 0.4, 1), ("taxol", "tubulin", 0.3, 2)]
    obj = {"routes": [{"class": "hdac INHIBITOR", "weight": 2, "pmids": ["1", "999"]}, {"class": "made up"}],
           "biomarkers": [{"gene": "not a gene!"}, {"gene": "abcb1", "feature": "expression", "effect": "protective"}],
           "keep_neighbours": ["VORINOSTAT", "ghost"], "expected_killing": "Selective"}
    out, dropped = SC.validate(obj, vocab, offered, {"1"})
    assert out["routes"] == [{"class": "HDAC inhibitor", "weight": 1.0, "pmids": ["1"]}]
    assert out["keep_neighbours"] == ["vorinostat"] and out["biomarkers"][0]["gene"] == "ABCB1"
    assert dropped == {"unknown_class": 1, "unknown_neighbour": 1, "bad_gene": 1, "foreign_pmid": 1}


def test_explainer_validator_dedups():
    import explain as EX
    out, dropped = EX.validate({"features": [{"gene": "SLFN11", "feature": "expression"},
                                             {"gene": "slfn11", "feature": "expr"}, {"gene": "?"}]}, set())
    assert len(out["features"]) == 1 and dropped["duplicate"] == 1 and dropped["bad_gene"] == 1


def test_provider_off_peak_rule_and_price():
    assert M.off_peak(dt.datetime(2026, 10, 10, 2, tzinfo=dt.timezone.utc))  # Saturday
    assert not M.off_peak(dt.datetime(2026, 10, 12, 2, tzinfo=dt.timezone.utc))  # Monday 02:00 UTC
    assert M.off_peak(dt.datetime(2026, 10, 12, 12, tzinfo=dt.timezone.utc))
    u = {"prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 1_000_000, "completion_tokens": 0}
    assert M.price(u, "deepseek-flash", dt.datetime(2026, 10, 12, 2, tzinfo=dt.timezone.utc)) == pytest.approx(0.3)


def test_sealed_tier_is_refused_before_the_freeze():
    import tiers as TI
    assert TI.TierSealed.code == "TIER_SEALED"
    if (HERE / "FREEZE.json").exists():
        pytest.skip("the confirmation tier was opened by the freeze")
    with pytest.raises(TI.TierSealed):
        TI.load("sealed")


def test_freeze_covers_protocol_and_code():
    import freeze as FR
    files = FR.frozen_files()
    for f in ("PROTOCOL.md", "PROTOCOL_CONFIG.json", "evaluate.py", "verify.py", "scientist.py", "explain.py"):
        assert f in files
    assert any(f.startswith("literature/") for f in files) and any(f.startswith("rehearsal/") for f in files)
