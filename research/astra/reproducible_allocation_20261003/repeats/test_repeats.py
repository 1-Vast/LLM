"""Behaviour tests for the repeats workstream (synthetic data only; no Jaaks outcome is read).

File summary
- Path: research/astra/reproducible_allocation_20261003/repeats/test_repeats.py
- Purpose: check that lambda = 0 reproduces the static validation prior, that a line's held-out repeat /
  validation labels never change anything fitted or purchased for that line, that development worlds
  exclude the evaluation lines, that lambda is recovered on a known linear relation, that the V0 helper
  equals the frozen world's history feature, and that event roles are ordered by seeding date.
- Interfaces: pytest.
- Depends on: numpy, pandas; the frozen feedback-validation `jaaks.synthetic_release` / `build_panels`.
"""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd
import pytest

from research.astra.feedback_validation_20261003 import jaaks
from research.astra.reproducible_allocation_20261003.repeats import model_id as mi
from research.astra.reproducible_allocation_20261003.repeats import provenance
from research.certified_discovery.screens import sha256
from research.certified_discovery.world import TransferWorld


@pytest.fixture(scope="module")
def synthetic(tmp_path_factory):
    path = jaaks.synthetic_release(tmp_path_factory.mktemp("rel") / "release.csv", seed=5, lines=8, drugs=12)
    panels, _, candidates = jaaks.build_panels({"freeze_sha256": "TEST", "data_sha256": sha256(path)}, path)
    rng = np.random.default_rng(1)
    repeat = {}
    for name, p in panels.items():
        sidms = p.library.lines
        repeat.setdefault(p.stratum, set(sidms[:3]))
    events = {}
    for name, p in panels.items():
        n = len(p.library)
        arr = {s: {k: np.full(n, np.nan) for k in ("y1", "h1", "y2", "h2", "y3", "h3")} for s in mi.SCHEMES}
        rep_rows = np.isin(np.array(p.library.lines)[p.library.c], list(repeat[p.stratum]))
        base = p.library.y
        for s in mi.SCHEMES:
            for r in (1, 2, 3):
                y = base + rng.normal(0, 3, n)
                arr[s][f"y{r}"][rep_rows] = y[rep_rows]
                arr[s][f"h{r}"][rep_rows] = (y[rep_rows] > 20).astype(float)
        events[name] = arr
    return panels, candidates, events, repeat


def _spec(panels, target="ii", exclude=()):
    name = sorted(panels)[0]
    return {"target": target, "panel": name, "line": 0, "exclude": list(exclude)}


def test_lambda_zero_reproduces_static_prior(synthetic):
    panels, _, events, _ = synthetic
    for target in ("ii", "i"):
        u = mi.unit_table(_spec(panels, target), panels, events)
        rec = next(v for v in u["schemes"].values() if "eligible" in v)
        for e, arm, base in (("U", "U_lambda", "U_V0"), ("P", "P_lambda", "P_V0")):
            pr = mi.predictions(rec, e, 0.0)
            np.testing.assert_array_equal(pr[arm], pr[base])
            np.testing.assert_array_equal(pr[arm], rec["V0"])


def test_held_out_labels_never_used_for_the_line(synthetic):
    panels, _, events, _ = synthetic
    spec = _spec(panels, "ii")
    base = mi.unit_table(spec, panels, events)
    p2 = copy.deepcopy(panels)
    name = spec["panel"]
    rows = np.flatnonzero(p2[name].library.c == spec["line"])
    p2[name].valid_y[rows] += 50.0
    p2[name].valid_hit[rows] = ~p2[name].valid_hit[rows]
    pert = mi.unit_table(spec, p2, events)
    a, b = base["schemes"]["pooled"], pert["schemes"]["pooled"]
    for key in ("S0", "hm", "V0", "F_U", "F_U10", "F_P", "bought", "r1", "p_pair", "p_cond", "p_cond_pair"):
        np.testing.assert_array_equal(a[key], b[key])
    assert not np.array_equal(a["v"], b["v"])
    # target (i): the held-out repeat (R2) and the final evaluation (R3) of the line never enter anything fitted
    spec_i = _spec(panels, "i")
    base_i = mi.unit_table(spec_i, panels, events)
    e2 = copy.deepcopy(events)
    for s in mi.SCHEMES:
        for k in ("y2", "y3"):
            e2[name][s][k][rows] += 40.0
        for k in ("h2", "h3"):
            e2[name][s][k][rows] = 1.0 - e2[name][s][k][rows]
    pert_i = mi.unit_table(spec_i, panels, e2)
    for s in mi.SCHEMES:
        a, b = base_i["schemes"][s], pert_i["schemes"][s]
        for key in ("S0", "V0", "F_U", "F_U10", "F_P", "bought", "r1", "p_pair", "p_cond", "p_cond_pair"):
            np.testing.assert_array_equal(a[key], b[key])


def test_dev_worlds_exclude_evaluation_lines(synthetic):
    panels, _, _, repeat = synthetic
    sidms = set().union(*repeat.values())
    specs, meta = mi.specs_for(panels, sidms)
    keys = meta["keys"]
    for k, entry in meta["plan"]["ii"].items():
        for key in entry["eval"]:
            assert keys[key]["exclude"] == []
        for key in entry["dev"]:
            s = keys[key]
            lib = panels[s["panel"]].library
            fold_lines = [i for i, x in enumerate(lib.lines) if meta["fold_ii"][x] == k]
            assert sorted(s["exclude"]) == fold_lines and s["line"] not in fold_lines
    for sidm, entry in meta["plan"]["i"].items():
        for key in entry["dev"]:
            s = keys[key]
            lib = panels[s["panel"]].library
            assert lib.lines[s["line"]] != sidm
            if sidm in lib.lines:
                assert lib.lines.index(sidm) in s["exclude"]


def test_lambda_recovered_and_eval_units_do_not_move_it(synthetic):
    panels, _, events, _ = synthetic
    units = []
    for name, p in panels.items():
        for line in range(len(p.library.lines)):
            u = mi.unit_table({"target": "ii", "panel": name, "line": line, "exclude": []}, panels, events)
            rec = u["schemes"]["pooled"]
            rec["v"] = rec["V0"] + 0.5 * np.where(rec["bought"], rec["F_P"], rec["F_U"])
            units.append(u)
    fit_u = mi.fit_lambda(units, "U", "primary", None, "pooled", boot=50)
    fit_p = mi.fit_lambda(units, "P", "primary", None, "pooled", boot=50)
    assert fit_u["lambda"] == pytest.approx(0.5, abs=1e-9)
    assert fit_p["lambda"] == pytest.approx(0.5, abs=1e-9)


def test_shrunk_mean_equals_world_history_feature(synthetic):
    panels, _, _, _ = synthetic
    p = panels[sorted(panels)[0]]
    world = TransferWorld(p.library, 1, mi.WORLD)
    hist = np.flatnonzero(p.library.c != 1)
    got = mi.shrunk_mean(world.pair_id[hist], p.library.y[hist], world.pair_id[world.rows])
    np.testing.assert_allclose(got, world.X_target[:, 0], rtol=1e-12, atol=1e-12)


def test_event_roles_follow_seeding_dates(synthetic):
    panels, candidates, _, _ = synthetic
    name = sorted(panels)[0]
    p = panels[name]
    s, v = candidates[p.stratum]["pairs_s_v"][0]
    sidm = p.library.lines[int(p.library.c[0])]
    anchor, library = (s, v) if p.replicate == "SV" else (v, s)
    frame = pd.DataFrame({"Tissue": p.stratum, "SIDM": sidm, "ANCHOR_ID": anchor, "LIBRARY_ID": library,
                          "event": ["e3", "e1", "e2", "e4"], "hit": [True, False, False, True],
                          "y": [3.0, 1.0, 2.0, 4.0],
                          "seeded": pd.to_datetime(["2018-03-01", "2018-01-01", "2018-02-01", "2018-04-01"])})
    arr = mi.event_arrays({name: p}, candidates, frame, {sidm})[name]
    assert [arr["chrono"][f"y{r}"][0] for r in (1, 2, 3)] == [1.0, 2.0, 3.0]
    assert [arr["reverse"][f"y{r}"][0] for r in (1, 2, 3)] == [4.0, 3.0, 2.0]


def test_provenance_status_rule():
    checks = {"fitted_plates_unmatched_in_raw": 0, "sidm_matches": 10, "fitted_plates": 10,
              "cell_id_constant_within_event": True, "fitted_plates_with_exactly_one_day1_plate": 9,
              "day1_groups_equal_seeding_events_one_to_one": True, "inferred_repeat_lines_equal_paper_lines": True}
    tuples = {"events_per_tuple_ge2": {"min": 2, "max": 18, "median": 4.0}, "plates_per_tuple_event": {"median": 3.0}}
    s = provenance.status_from(checks, tuples)
    assert s["plate_to_seeding_event_and_culture_expansion"] == "CORROBORATED_NOT_AUTHENTICATED"
    checks["fitted_plates_with_exactly_one_day1_plate"] = 10
    s = provenance.status_from(checks, tuples)
    assert s["plate_to_seeding_event_and_culture_expansion"] == "AUTHENTICATED"
    assert s["seeding_event_equals_papers_biological_replicate"] == "CORROBORATED_NOT_AUTHENTICATED"


def test_pipeline_dry_run_and_eval_labels_do_not_move_lambda(synthetic):
    panels, _, events, repeat = synthetic
    sidms = set().union(*repeat.values())
    specs, meta = mi.specs_for(panels, sidms)
    units = {mi.key_of(s): mi.unit_table(s, panels, events) for s in specs}
    for target, scheme in (("ii", "pooled"), ("i", "chrono")):
        plan = meta["plan"][target]
        cell = mi.analyse_cell(units, plan, target, scheme, "primary")
        assert cell["units"]
        first = next(iter(plan))
        lam = cell["folds"][str(first)]["primary"]["U"]["lambda"]["lambda"]
        moved = copy.deepcopy(units)
        for key in plan[first]["eval"]:
            rec = moved[key]["schemes"].get(scheme, {})
            if "v" in rec:
                rec["v"] = rec["v"] + 100.0
        again = mi.analyse_cell(moved, plan, target, scheme, "primary")
        assert again["folds"][str(first)]["primary"]["U"]["lambda"]["lambda"] == lam
        stop = mi.stop_decision(cell, "U")
        assert set(stop) >= {"stop_rule_fires", "folds_lambda_near_zero"}
        assert mi.calibration(units, plan, cell, target, scheme)


def test_full_analysis_assembles_and_serialises(synthetic):
    import json

    panels, _, events, repeat = synthetic
    sidms = set().union(*repeat.values())
    specs, meta = mi.specs_for(panels, sidms)
    units = {mi.key_of(s): mi.unit_table(s, panels, events) for s in specs}
    cells, rows = mi.analyse_all(units, meta)
    assert {"ii|pooled|primary|swap", "i|chrono|primary|R2", "i|chrono|primary|R3"} <= set(cells)
    json.dumps(mi._jsonable(cells))
    json.dumps(mi._jsonable(rows))
