"""Tests of the resources engines on a synthetic Jaaks-format release (no Jaaks outcome is read).

File summary
- Path: research/astra/confirmation_campaign_20261004/resources/test_resources.py
- Purpose: pin the properties the frontier and native replays rely on: integer cap arithmetic and
  tie-break of contract v2, history without E or target rows, spend <= cap, no final-round screens,
  verification only of earlier-round hits, legal access to hidden outcomes, co-produced measurements
  credited exactly once, accounting sums and reproducibility.
- Interfaces: `pytest -o addopts= research/astra/confirmation_campaign_20261004/resources`.
- Depends on: pytest, numpy; the frozen jaaks builder (synthetic release, fake ticket); resources code.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest

from research.astra.feedback_validation_20261003 import jaaks
from research.certified_discovery.screens import sha256

from . import frontier as fr
from . import native as nt
from .layout import build_layout, check_against_panels

ROUNDS = (1, 2, 3)


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    path = jaaks.synthetic_release(tmp_path_factory.mktemp("synthetic") / "release.csv", seed=3, lines=8, drugs=8)
    ticket = {"freeze_sha256": "TEST_NOT_A_VAULT", "data_sha256": sha256(path)}
    panels, report, candidates = jaaks.build_panels(ticket, path)
    layout = build_layout(path, events={})
    part = {}
    for tissue, tl in layout.tissues.items():
        lines = list(tl.lines)
        part[tissue] = {"E": lines[:4], "HD": lines[4:]}
    units = fr.build_units(layout, panels, part)
    return {"path": path, "panels": panels, "candidates": candidates, "layout": layout, "part": part,
            "units": units}


def _all_custom(units, cps=(10, 20, 40), kinds=("measurement", "wells"), preds=fr.ALL_SCORES):
    for u in units:
        for pred in preds:
            for cp in cps:
                for kind in kinds:
                    for rounds in ROUNDS:
                        fps = fr.FP_GRID if rounds == 2 else (None,)
                        for fp in fps:
                            yield u, fr.run_custom(u, pred, rounds, fp=fp, cap_kind=kind, cp=cp)


# ---------------------------------------------------------------------------- contract arithmetic
def test_layout_menu_equals_builder_menu(synth):
    out = check_against_panels(synth["layout"], synth["panels"], synth["candidates"])
    assert all(v["identical"] for v in out.values())


@pytest.mark.parametrize("n", list(range(1, 400)))
def test_integer_caps(n):
    M = -(-20 * n // 100)
    assert M == (n + 4) // 5 == math.ceil(Fraction(n, 5))
    for fp in fr.FP_GRID:
        assert ((100 - fp) * M) // 100 == math.floor(Fraction(100 - fp, 100) * M)


def test_cap_values_and_split_sizes(synth):
    for u in synth["units"]:
        M = u.cap(20)
        assert M == (u.n + 4) // 5
        W = u.wells_cap(20)
        tot = sum(14 * int(a + b) for a, b in zip(u.plates_s, u.plates_v))
        assert W == math.ceil(Fraction(M) * Fraction(tot, 2 * u.n))
        for fp in fr.FP_GRID:
            rec = fr.run_custom(u, "R", 2, fp=fp)
            assert rec["n1"] == ((100 - fp) * M) // 100 == rec["screens"]
        assert fr.run_custom(u, "R", 3)["per_round"][0]["screens"] == (M + 1) // 2
        assert fr.run_custom(u, "R", 1)["screens"] == M // 2


def test_tie_break_is_the_registered_permutation(synth):
    u = synth["units"][0]
    perm = np.random.default_rng([20261004, u.code, u.line_index, u.role_index]).permutation(u.n)
    assert np.array_equal(fr.order_by(np.zeros(u.n), u.rank), perm)
    scores = np.round(np.linspace(0, 1, u.n), 3)
    expected = np.lexsort((u.rank, -np.round(scores, 12)))
    assert np.array_equal(fr.order_by(scores, u.rank), expected)
    assert u.line_index == synth["layout"].tissues[u.tissue].lines.index(u.sidm)


# ---------------------------------------------------------------------------- history legality
def test_history_excludes_target_and_evaluation_lines(synth):
    for u in synth["units"]:
        e = set(synth["part"][u.tissue]["E"])
        assert u.sidm not in u.history_lines
        assert not (set(u.history_lines) & e)
        if u.group == "E":
            assert set(u.history_lines) == set(synth["part"][u.tissue]["HD"])


def test_scores_ignore_evaluation_outcomes(synth):
    """Flipping every E-line outcome leaves every score unchanged (E rows never enter H)."""
    layout, part = synth["layout"], synth["part"]
    flipped = {}
    for name, p in synth["panels"].items():
        tissue = p.stratum
        e_rows = np.isin(layout.tissues[tissue].sidm, part[tissue]["E"])
        lib = replace(p.library, y=np.where(e_rows, -p.library.y, p.library.y))
        flipped[name] = replace(p, library=lib, screen_hit=np.where(e_rows, ~p.screen_hit, p.screen_hit),
                                valid_hit=np.where(e_rows, ~p.valid_hit, p.valid_hit),
                                valid_y=np.where(e_rows, -p.valid_y, p.valid_y))
    units2 = fr.build_units(layout, flipped, part)
    for a, b in zip(synth["units"], units2):
        for pred in fr.PREDICTORS:
            assert np.array_equal(a.scores[pred][0], b.scores[pred][0])
            assert np.array_equal(a.scores[pred][1], b.scores[pred][1])
        assert np.array_equal(a.p_s, b.p_s)


def test_history_scores_formula():
    pair_id = np.array([0, 1, 0, 1, 0, 1])
    arr = {"h_s": np.array([1, 0, 1, 1, 0, 0], bool), "h_v": np.array([1, 0, 0, 1, 1, 0], bool),
           "y_s": np.array([30., 0, 25, 40, 1, 2]), "y_v": np.array([20., 1, 0, 30, 25, 3])}
    hist = np.array([True, True, True, True, False, False])
    q = fr.history_scores(arr, pair_id, hist, np.array([4, 5]))
    pooled_s = 3 / 4
    assert q["p_s"][0] == pytest.approx((2 + 2 * pooled_s) / 4)
    assert q["p_s"][1] == pytest.approx((1 + 2 * pooled_s) / 4)
    pooled_vs = 2 / 3                                   # joint 2 of 3 screen hits
    assert q["p_vs"][0] == pytest.approx((1 + 2 * pooled_vs) / (2 + 2))
    assert q["p_sv"][1] == pytest.approx((1 + 2 * 0.5) / 4)
    pooled_y = (30 + 0 + 25 + 40) / 4
    assert q["S"][0] == pytest.approx((55 + 2 * pooled_y) / 4)
    both = (np.array([30., 0, 25, 40]) + np.array([20., 1, 0, 30])) / 2
    assert q["S_both"][1] == pytest.approx((both[1] + both[3] + 2 * both.mean()) / 4)
    assert q["scores"]["C_prod"][0][0] == pytest.approx(q["p_s"][0] * q["p_v"][0])


# ---------------------------------------------------------------------------- custom engine
def test_spend_within_cap_and_no_final_round_screens(synth):
    n = 0
    for u, rec in _all_custom(synth["units"]):
        n += 1
        assert rec["spent"] <= rec["cap"]
        assert rec["unused_cap"] == rec["cap"] - rec["spent"]
        assert rec["spent"] == rec["screen_units"] + rec["verify_units"]
        if rec["rounds"] > 1:
            assert rec["final_round_screens"] == 0
            assert all(not (r == rec["rounds"] and b == "screen") for r, b, _ in rec["purchases"])
    assert n > 1000


def test_verification_only_of_earlier_round_hits(synth):
    for u, rec in _all_custom(synth["units"], cps=(20, 40)):
        if rec["rounds"] == 1:
            continue
        screen_round = {i: r for r, b, i in rec["purchases"] if b == "screen"}
        for r, b, i in rec["purchases"]:
            if b == "verify":
                assert i in screen_round and screen_round[i] < r and bool(u.hidden.hit_s[i])
        if rec["rounds"] == 3:
            for r, b, i in rec["purchases"]:
                if b == "verify" and r == 3:
                    assert screen_round[i] == 2


def test_p3_reserve_stops_at_first_failure(synth):
    u = synth["units"][0]
    n = u.n
    hidden = fr.Hidden(np.zeros(n, bool), np.zeros(n, bool), np.zeros(n), np.zeros(n))   # no hits: B2 = M - n_r1
    p_s = np.full(n, 0.05)
    order = fr.order_by(u.scores["R"][0], u.rank)
    M = u.cap(40)
    n_r1 = (M + 1) // 2
    B2 = M - n_r1
    assert B2 == 3
    p_s[order[n_r1 + 1]] = 0.99                               # second round-2 candidate breaks the reserve
    v = replace(u, hidden=hidden, p_s=p_s)
    rec = fr.run_custom(v, "R", 3, cp=40)

    def accepted(skip: bool) -> int:
        acc, s = 0, 0.0
        for j in order[n_r1:]:
            if (acc + 1) + math.ceil(round(s + p_s[j], 12)) <= B2:
                acc, s = acc + 1, s + p_s[j]
            elif not skip:
                break
        return acc

    assert accepted(skip=False) == 1 != accepted(skip=True)
    assert rec["reserve"]["accepted"] == 1 == rec["per_round"][1]["screens"]


def test_unpurchased_outcomes_never_change_purchases(synth):
    rng = np.random.default_rng(0)
    for u in synth["units"][:8]:
        for rounds in ROUNDS:
            for fp in (fr.FP_GRID if rounds == 2 else (None,)):
                base = fr.run_custom(u, "R", rounds, fp=fp, cp=40)
                bought_s = {i for _, b, i in base["purchases"] if b == "screen"}
                bought_v = {i for _, b, i in base["purchases"] if b == "verify"}
                h = u.hidden
                hs = np.where(np.isin(np.arange(u.n), list(bought_s)), h.hit_s, rng.random(u.n) < 0.5)
                hv = np.where(np.isin(np.arange(u.n), list(bought_v)), h.hit_v, rng.random(u.n) < 0.5)
                v = replace(u, hidden=fr.Hidden(hs, hv, h.y_s, h.y_v))
                again = fr.run_custom(v, "R", rounds, fp=fp, cp=40)
                assert again["purchases"] == base["purchases"]


def test_round2_oracle_changes_only_round2_screens(synth):
    for u in synth["units"]:
        joint = (u.hidden.hit_s & u.hidden.hit_v).astype(float)
        base = fr.run_custom(u, "R", 3, cp=40)
        n2 = base["per_round"][1]["screens"] if len(base["per_round"]) > 1 else 0
        orc = fr.run_custom(u, "R", 3, cp=40, round2_screen_score=joint, round2_count=n2)
        assert orc["screens_ordered"][:orc["n1"]] == base["screens_ordered"][:base["n1"]]
        assert orc["screens"] == base["screens"]
        assert [i for r, b, i in orc["purchases"] if r == 2 and b == "verify"] ==             [i for r, b, i in base["purchases"] if r == 2 and b == "verify"]


def test_terminal_reference_spends_more_and_confirms_the_same(synth):
    for u in synth["units"]:
        for rounds, fp in ((2, 30), (3, None)):
            stop = fr.run_custom(u, "R", rounds, fp=fp, cp=40)
            ref = fr.run_custom(u, "R", rounds, fp=fp, cp=40, terminal=True)
            assert ref["confirmed"] == stop["confirmed"]
            assert ref["spent"] >= stop["spent"]
            assert ref["spent"] == ref["cap"] or ref["screens"] == u.n


def test_pack_custom_matches_earlier_replay():
    from research.astra.reproducible_allocation_20261003.allocation import replay as rp
    rng = np.random.default_rng(1)
    for _ in range(200):
        k = int(rng.integers(0, 60))
        items = [(f"A{rng.integers(0, 12)}", f"L{rng.integers(0, 15)}", int(rng.integers(1, 4)),
                  (None if rng.random() < 0.5 else int(rng.integers(0, 30)))) for _ in range(k)]
        assert fr.pack_custom(items, 200) == rp.pack_custom(items)


def test_custom_accounting_sums(synth):
    layout = synth["layout"]
    for u in synth["units"][:6]:
        for rounds in ROUNDS:
            rec = fr.run_custom(u, "S_both", rounds, fp=25, cp=40)
            acc = fr.account_custom(u, rec, layout)
            tot = acc["total"]
            assert tot["orientation_measurements"] == rec["screens"] + rec["verifications"] == rec["spent"]
            assert tot["combination_wells"] == 14 * (sum(u.plates_s[i] for _, b, i in rec["purchases"] if b == "screen")
                                                     + sum(u.plates_v[i] for _, b, i in rec["purchases"] if b == "verify"))
            summed: dict = {}
            for r in acc["by_round"].values():
                for b in ("screen", "verify"):
                    fr.add_into(summed, r[b])
            branches: dict = {}
            for b in ("screen", "verify"):
                fr.add_into(branches, acc["by_branch"][b])
            for key in ("orientation_measurements", "combination_wells", "native_plates_touched", "dose_points"):
                assert summed[key] == branches[key] == tot[key]
            for name in fr.CONTROL_VARIANTS:
                c = tot[f"custom_{name}"]
                assert c["control_wells"] == fr.CONTROL_VARIANTS[name] * c["plates"]
                assert c["combination_wells"] == tot["combination_wells"]
                assert (c["plates"] * 1536 == c["control_wells"] + c["single_anchor_wells"] + c["single_library_wells"]
                        + c["combination_wells"] + c["empty_wells"])
            assert tot["failed_measurements"] == 0


def test_reproducible(synth):
    def digest():
        recs = [rec for _, rec in _all_custom(synth["units"][:4], cps=(20,), preds=("R", "S_both", "S"))]
        return hashlib.sha256(json.dumps(recs, sort_keys=True, default=str).encode()).hexdigest()
    assert digest() == digest()


# ---------------------------------------------------------------------------- native engine
def _all_native(synth, preds=("R", "S_both", "S", "oracle")):
    layout = synth["layout"]
    for u in synth["units"]:
        view = nt.native_view(u, layout)
        for pct, K in nt.native_caps(view).items():
            for pred in preds:
                for rounds in ROUNDS:
                    for fp in (fr.FP_GRID if rounds == 2 else (None,)):
                        yield u, view, K, nt.run_native(u, view, pred, rounds, K, fp=fp)


def test_native_view_partitions_menu_orientations(synth):
    for u in synth["units"]:
        view = nt.native_view(u, synth["layout"])
        s_pairs = sorted(i for k in view["screen_comps"] for i in view["comps"][k]["pairs"])
        v_pairs = sorted(i for k in view["verify_comps"] for i in view["comps"][k]["pairs"])
        assert s_pairs == list(range(u.n)) == v_pairs              # every orientation on exactly one component


def test_native_cap_final_round_and_legality(synth):
    n = 0
    for u, view, K, rec in _all_native(synth):
        n += 1
        assert rec["plate_starts"] <= K
        assert rec["plate_starts"] == sum(view["comps"][k]["cost"] for _, k in rec["bought"])
        ks = [k for _, k in rec["bought"]]
        assert len(ks) == len(set(ks))                                # bought once
        if rec["rounds"] > 1:
            assert all(not (r == rec["rounds"] and view["comps"][k]["kind"] == "screen") for r, k in rec["bought"])
        assert rec["confirmed"] == (rec["confirmed_screen_first"] + rec["confirmed_same_round"]
                                    + rec["confirmed_verification_first"])
        if rec["rounds"] == 2:
            assert rec["confirmed_verification_first"] == 0
    assert n > 500


def test_native_credits_each_measurement_once(synth):
    layout = synth["layout"]
    for u, view, K, rec in _all_native(synth, preds=("R",)):
        screens = sum(len(view["comps"][k]["pairs"]) for _, k in rec["bought"] if view["comps"][k]["kind"] == "screen")
        verifs = sum(len(view["comps"][k]["pairs"]) for _, k in rec["bought"] if view["comps"][k]["kind"] == "verify")
        assert rec["screen_orientations"] == screens
        assert rec["verification_orientations"] == verifs
        acc = nt.account_native(u, view, rec, layout)
        assert acc["total"]["menu_orientation_measurements"] == screens + verifs
        assert acc["total"]["plate_starts"] == rec["plate_starts"]
        summed = {}
        for r in acc["by_round"].values():
            for kind in ("screen", "verify"):
                for key, v in r[kind].items():
                    summed[key] = summed.get(key, 0) + v
        assert all(summed.get(key, 0) == v for key, v in acc["total"].items())


def test_native_full_cap_one_round_confirms_every_joint_hit(synth):
    for u in synth["units"]:
        view = nt.native_view(u, synth["layout"])
        rec = nt.run_native(u, view, "R", 1, view["menu_plates"])
        assert rec["confirmed"] == rec["joint_hits_menu"]
        assert rec["plate_starts"] == view["menu_plates"]


def test_native_unpurchased_outcomes_never_change_purchases(synth):
    rng = np.random.default_rng(2)
    layout = synth["layout"]
    for u in synth["units"][:8]:
        view = nt.native_view(u, layout)
        K = nt.native_caps(view)[50]
        for rounds in ROUNDS:
            base = nt.run_native(u, view, "R", rounds, K, fp=30)
            comps = view["comps"]
            seen_s = {i for _, k in base["bought"] if comps[k]["kind"] == "screen" for i in comps[k]["pairs"]}
            seen_v = {i for _, k in base["bought"] if comps[k]["kind"] == "verify" for i in comps[k]["pairs"]}
            h = u.hidden
            idx = np.arange(u.n)
            hs = np.where(np.isin(idx, list(seen_s)), h.hit_s, rng.random(u.n) < 0.5)
            hv = np.where(np.isin(idx, list(seen_v)), h.hit_v, rng.random(u.n) < 0.5)
            again = nt.run_native(replace(u, hidden=fr.Hidden(hs, hv, h.y_s, h.y_v)), view, "R", rounds, K, fp=30)
            assert again["bought"] == base["bought"]
