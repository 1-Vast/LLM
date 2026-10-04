"""Behaviour tests for the feedback-validation study (synthetic data only).

File summary
- Path: research/astra/feedback_validation_20261003/test_feedback_validation.py
- Purpose: check the frozen doublet split and plate disjointness, the panel builder's menu, budget
  accounting, the offset-only identity, that neither validation outcomes nor unpurchased target
  labels can influence purchases, vault refusals and the frozen verdict categories.
- Interfaces: pytest (research scope).
- Depends on: numpy, pandas, study modules.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from research.astra.feedback_validation_20261003 import jaaks, study, verdict
from research.certified_discovery.screens import sha256


@pytest.fixture(scope="module")
def release(tmp_path_factory):
    return jaaks.synthetic_release(tmp_path_factory.mktemp("rel") / "release.csv", seed=3, lines=6, drugs=8)


@pytest.fixture(scope="module")
def panels(release):
    return jaaks.build_panels({"freeze_sha256": "TEST", "data_sha256": sha256(release)}, release)


def test_split_is_frozen_and_plates_are_disjoint(release):
    design = jaaks.plate_design(release)
    again = jaaks.plate_design(release)
    for tissue, d in design.items():
        assert d == again[tissue]
        assert d["mixed_plates"] == 0
        assert len(d["S"]) == len(d["V"]) == 4                      # 4 doublets -> 2 per side
        assert d["menu_pair_x_line"] == 6 * 4 * 4


def test_builder_menu_and_replicates(panels):
    built, report, candidates = panels
    assert set(built) == {"Colon_SV", "Colon_VS", "Pancreas_SV", "Pancreas_VS"}
    for tissue in ("Colon", "Pancreas"):
        sv, vs = built[f"{tissue}_SV"], built[f"{tissue}_VS"]
        assert report["panels"][tissue]["plate_overlap"] == 0
        assert len(sv.library) == 6 * 16 == len(candidates[tissue]["pairs_s_v"])
        assert np.all(sv.library.a < sv.library.b)
        # the swap replicate exchanges screen and validation measurements of the same menu
        assert np.array_equal(sv.valid_hit, vs.screen_hit) and np.array_equal(sv.screen_hit, vs.valid_hit)
        assert np.allclose(sv.valid_y, vs.library.y)


def test_vault_refusals(release, tmp_path):
    with pytest.raises(PermissionError):
        jaaks.build_panels({}, release)
    with pytest.raises(PermissionError):
        jaaks.build_panels({"freeze_sha256": "X", "data_sha256": "wrong"}, release)


def test_budget_and_offset_identity(panels):
    panel = panels[0]["Colon_SV"]
    record = study.run_line(panel, 0, {"primary": study.Budget(0.25, 4)})
    arms = record["budgets"]["primary"]["arms"]
    n = record["candidates"]
    for name in ("feedback", "ridge_static", "history_rate", "rate_feedback", "shuffle", "wrong_line", "random"):
        runs = arms[name] if isinstance(arms[name], list) else [arms[name]]
        for run in runs:
            bought = sum(run["purchases"], [])
            assert len(bought) == int(np.ceil(0.25 * n)) == len(set(bought))
    assert sorted(sum(arms["offset_only"]["purchases"], [])) == sorted(sum(arms["ridge_static"]["purchases"], []))


def _purchases(panel, line):
    arms = study.run_line(panel, line, {"p": study.Budget(0.25, 4)})["budgets"]["p"]["arms"]
    return {k: (v["purchases"] if isinstance(v, dict) else [r["purchases"] for r in v])
            for k, v in arms.items() if not k.startswith("oracle")}


def test_validation_outcomes_never_change_purchases(panels):
    panel = panels[0]["Pancreas_SV"]
    flipped = replace(panel, valid_hit=~panel.valid_hit, valid_y=-panel.valid_y,
                      valid_efficacious=~panel.valid_efficacious)
    assert _purchases(panel, 1) == _purchases(flipped, 1)


def test_unpurchased_target_labels_never_change_purchases(panels):
    panel = panels[0]["Colon_VS"]
    line = 2
    base = _purchases(panel, line)
    bought = set()
    for value in base.values():
        runs = value if isinstance(value[0], list) and value and isinstance(value[0][0], list) else [value]
        for run in runs:
            bought.update(sum(run, []))
    rows = np.flatnonzero(panel.library.c == line)
    never = np.array([r for i, r in enumerate(rows) if i not in bought], int)
    y = panel.library.y.copy()
    y[never] = np.random.default_rng(0).normal(0, 50, never.size)
    hits = panel.screen_hit.copy()
    hits[never] = ~hits[never]
    noisy = replace(panel, library=replace(panel.library, y=y), screen_hit=hits)
    assert _purchases(noisy, line) == base


def test_verdict_categories():
    assert verdict.category({"relative_gain": 0.2, "relative_gain_ci": [0.05, 0.4]}) == "MEANINGFUL_GAIN"
    assert verdict.category({"relative_gain": 0.05, "relative_gain_ci": [0.01, 0.09]}) == "SMALL_GAIN"
    assert verdict.category({"relative_gain": 0.05, "relative_gain_ci": [-0.02, 0.15]}) == "INCONCLUSIVE"
    assert verdict.category({"relative_gain": 0.01, "relative_gain_ci": [-0.03, 0.06]}) == "NO_MEANINGFUL_GAIN"
    assert verdict.category({"relative_gain": -0.1, "relative_gain_ci": [-0.2, -0.01]}) == "HARM"
    assert verdict.category({"relative_gain": None, "relative_gain_ci": [0, 0]}) == "UNDEFINED"
