"""Behaviour tests for the allocation replay (synthetic data only; no Jaaks outcome is read).

File summary
- Path: research/astra/reproducible_allocation_20261003/allocation/test_allocation.py
- Purpose: pin the properties the repaired replay relies on: budget conservation with carry-over,
  terminal verification capacity, legal access to labels, condition identity of verification,
  the plate-packing model, and fidelity of the instrumented copy of the original follow-up.
- Core points: hand-made `Line` objects for scheduler properties; a synthetic Jaaks-format release
  (`jaaks.synthetic_release`, fake ticket) for the panel/design path.
- Interfaces: `pytest research/astra/reproducible_allocation_20261003/allocation/test_allocation.py`.
- Depends on: numpy, pytest, the replay module, the frozen jaaks/followup modules (imported).
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from research.astra.feedback_validation_20261003 import followup_verification as original
from research.astra.feedback_validation_20261003 import jaaks
from research.certified_discovery.screens import sha256

from . import replay as rp

ALL_SPECS = rp.BASE + rp.GRID + rp.RANDOM[:2] + rp.RANDOM[rp.RANDOM_SEEDS:rp.RANDOM_SEEDS + 2]


def make_line(n: int = 40, seed: int = 0, varied: bool = False, p_s: float | None = None, all_hits: bool = False) -> rp.Line:
    rng = np.random.default_rng(seed)
    y = rng.normal(10, 15, n)
    screen_hit = np.ones(n, bool) if all_hits else y > 18
    valid_hit = rng.random(n) < 0.5
    plates_s = rng.integers(1, 4, n) if varied else np.ones(n, int)
    plates_v = rng.integers(1, 4, n) if varied else np.ones(n, int)
    static = y + rng.normal(0, 10, n)
    weights = rng.normal(0, 1, n)

    def feedback(idx, values):
        values = np.asarray(values, float)
        return static + (weights * values.mean() if values.size else 0.0)

    ps = np.full(n, p_s) if p_s is not None else np.clip(rng.random(n) * 0.4, 0.02, 1.0)
    return rp.Line(
        tissue="T", replicate="SV", sidm="L0", index=seed, y=y, screen_hit=screen_hit, valid_hit=valid_hit,
        cost_s=14 * plates_s, cost_v=14 * plates_v, p_s=ps, p_sv=0.5 * ps, p_vs=np.clip(rng.random(n), 0.05, 1),
        static=static, orient_s=[(f"S{i}", f"V{i}") for i in range(n)], orient_v=[(f"V{i}", f"S{i}") for i in range(n)],
        plates_s=plates_s, plates_v=plates_v, qc_plates_s=plates_s.copy(), qc_plates_v=plates_v.copy(),
        rows_s=2 * plates_s, rows_v=2 * plates_v,
        barcodes_s=[tuple(f"bv{i}_{k}" for k in range(plates_s[i])) for i in range(n)],
        barcodes_v=[tuple(f"bs{i}_{k}" for k in range(plates_v[i])) for i in range(n)], feedback=feedback)


def _with(line: rp.Line, **arrays) -> rp.Line:
    from dataclasses import replace
    return replace(line, **arrays)


# ------------------------------------------------------------------------- budget conservation
@pytest.mark.parametrize("n", [40, 43, 157, 168])
def test_measurement_budget_spent_exactly(n):
    line = make_line(n, seed=n)
    for spec in ALL_SPECS:
        rec = rp.simulate(line, spec, "measurement")
        if spec.scheduler == "paired":
            assert rec["spent"] == line.M - line.M % 2, spec
            assert rec["remainder"] <= 1
            assert rec["remainder_class"] == ("unavoidable" if line.M % 2 else "none")
        else:
            assert rec["spent"] == line.M, spec
            assert rec["remainder_class"] == "none"


def test_carry_over_recovers_per_round_odd_capacity():
    line = make_line(168, seed=3)           # M = 34, nominal per round = 9 (odd)
    assert line.M == 34
    rec = rp.simulate(line, rp.Spec("p", "static", "paired"), "measurement")
    assert rec["spent"] == 34
    rounds = rec["rounds"]
    assert [r["available"] for r in rounds] == [9, 10, 9, 8]
    assert [r["unused"] for r in rounds] == [1, 0, 1, 0]
    nominal = [min((r + 1) * 9, 34) for r in range(4)]
    spent = np.cumsum([r["screen_spent"] + r["verify_spent"] for r in rounds])
    assert all(s <= c for s, c in zip(spent, nominal))


def test_original_paired_loses_capacity_but_repaired_does_not():
    line = make_line(168, seed=3)
    batch = math.ceil(line.M / 4)
    spent = 0
    for _ in range(4):
        b = min(batch, line.M - spent)
        spent += 2 * (b // 2)
    assert spent == 32                      # original arithmetic: 2 units lost, 0 unavoidable (M even)
    assert rp.simulate(line, rp.Spec("p", "static", "paired"), "measurement")["spent"] == 34


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_physical_budget_feasible_and_remainder_classified(seed):
    line = make_line(60, seed=seed, varied=True)
    for spec in ALL_SPECS:
        rec = rp.simulate(line, spec, "physical")
        assert rec["spent"] <= line.W
        assert rec["remainder_class"] in ("none", "unavoidable"), (spec, rec["remainder"], rec["min_available_cost"])
        if rec["remainder"]:
            assert rec["min_available_cost"] is None or rec["remainder"] < rec["min_available_cost"]


# ------------------------------------------------------------------------- terminal verification
def test_terminal_round_verifies_final_round_hits_when_reserve_suffices():
    line = make_line(80, seed=0, p_s=1.0)          # reserve = one verification per round-4 screen
    rec = rp.simulate(line, rp.Spec("v", "static", "verify_hits", terminal=True), "measurement")
    assert rec["spent"] == line.M
    assert rec["unverified_screen_hits"] - rec["terminal_screen_hits"] == 0
    round4_hits = {i for r, b, i in rec["purchases"] if b == "screen" and r == 4 and line.screen_hit[i]}
    assert round4_hits and round4_hits <= {i for r, b, i in rec["purchases"] if b == "verify" and r == 5}
    assert rec["last_round"] == 5
    ref = rp.simulate(line, rp.Spec("v", "static", "verify_hits"), "measurement")
    assert ref["unverified_screen_hits"] > 0          # without the terminal round final hits stay unverified
    all_hits = make_line(80, seed=5, p_s=1.0, all_hits=True)
    rec = rp.simulate(all_hits, rp.Spec("v", "static", "verify_hits", terminal=True), "measurement")
    assert rec["spent"] == all_hits.M and rec["unverified_screen_hits"] == 0


def test_unverified_hits_after_terminal_round_are_only_terminal_or_capacity_bound():
    for seed in range(10):
        line = make_line(120, seed=seed)
        for spec in (rp.Spec("v", "static", "verify_hits", terminal=True),
                     rp.Spec("c", "history_value", "conf_per_cost", terminal=True)):
            rec = rp.simulate(line, spec, "measurement")
            terminal = rec["rounds"][-1]
            verified = {i for r, b, i in rec["purchases"] if b == "verify"}
            screened_before = {i: r for r, b, i in rec["purchases"] if b == "screen"}
            for i, r in screened_before.items():
                if line.screen_hit[i] and i not in verified and r <= spec.rounds:
                    assert terminal["verify_spent"] == terminal["available"]      # capacity was exhausted


def test_results_arrive_at_end_of_round():
    line = make_line(120, seed=7)
    for spec in ALL_SPECS:
        rec = rp.simulate(line, spec, "measurement")
        screen_round = {i: r for r, b, i in rec["purchases"] if b == "screen"}
        for r, b, i in rec["purchases"]:
            if b != "verify":
                continue
            assert i in screen_round
            if spec.scheduler == "paired":
                assert screen_round[i] == r
            else:
                assert screen_round[i] < r and line.screen_hit[i]


def test_fixed_split_zero_equals_screen_only():
    line = make_line(150, seed=11)
    a = rp.simulate(line, rp.Spec("f", "static", "fixed_split", terminal=True, f=0.0), "measurement")
    b = rp.simulate(line, rp.Spec("s", "static", "screen_only"), "measurement")
    assert a["purchases"] == b["purchases"]


# ------------------------------------------------------------------------- legal access
@pytest.mark.parametrize("unit", ["measurement", "physical"])
def test_unpurchased_labels_never_change_purchases(unit):
    line = make_line(120, seed=13, varied=True)
    rng = np.random.default_rng(1)
    for spec in ALL_SPECS:
        rec = rp.simulate(line, spec, unit)
        screened = {i for _, b, i in rec["purchases"] if b == "screen"}
        verified = {i for _, b, i in rec["purchases"] if b == "verify"}
        y, sh, vh = line.y.copy(), line.screen_hit.copy(), line.valid_hit.copy()
        for i in range(line.n):
            if i not in screened:
                y[i] = rng.normal(0, 50)
                sh[i] = rng.random() < 0.5
            if i not in verified:
                vh[i] = rng.random() < 0.5
        again = rp.simulate(_with(line, y=y, screen_hit=sh, valid_hit=vh), spec, unit)
        assert again["purchases"] == rec["purchases"], spec


@pytest.mark.parametrize("unit", ["measurement", "physical"])
def test_validation_labels_never_change_any_purchase(unit):
    line = make_line(120, seed=17, varied=True)
    for spec in ALL_SPECS:
        rec = rp.simulate(line, spec, unit)
        for seed in range(3):
            vh = np.random.default_rng(seed).random(line.n) < 0.5
            again = rp.simulate(_with(line, valid_hit=vh), spec, unit)
            assert again["purchases"] == rec["purchases"], spec


def test_purchased_screen_labels_do_reach_feedback():
    line = make_line(120, seed=19)
    spec = rp.Spec("fb", "feedback", "verify_hits", terminal=True)
    rec = rp.simulate(line, spec, "measurement")
    first = [i for r, b, i in rec["purchases"] if b == "screen" and r == 1]
    y = line.y.copy()
    y[first] = y[first] + 500.0
    again = rp.simulate(_with(line, y=y), spec, "measurement")
    assert again["purchases"] != rec["purchases"]          # control: the test above is not vacuous


# ------------------------------------------------------------------------- packing model
def test_pack_custom_layers_controls_and_conflicts():
    items = [("A1", "L1", 2, None), ("A2", "L1", 1, None), ("A1", "L2", 1, None)]
    out = rp.pack_custom(items)
    assert out["plates"] == 2                          # replicate layer 2 on its own plate
    assert out["control_wells"] == 2 * rp.CONTROL_WELLS
    assert out["combination_wells"] == 4 * 14
    assert out["single_anchor_wells"] == (2 + 1) * rp.ANCHOR_SINGLE_WELLS
    assert out["single_library_wells"] == (2 + 1) * rp.LIBRARY_SINGLE_WELLS
    total = out["control_wells"] + out["combination_wells"] + out["single_anchor_wells"] + \
        out["single_library_wells"] + out["empty_wells"]
    assert total == out["plates"] * rp.PLATE_WELLS
    conflict = rp.pack_custom([("A", "B", 1, 7), ("B", "A", 1, 7)])
    assert conflict["plates"] == 2                     # both orientations of one pair never share a plate
    many = rp.pack_custom([(f"A{i}", "L", 1, None) for i in range(60)])
    assert many["plates"] == 2                         # 28 + 60 x 24 wells exceed one plate's 1336


# ------------------------------------------------------------------------- panel path (synthetic release)
@pytest.fixture(scope="module")
def synthetic(tmp_path_factory):
    path = jaaks.synthetic_release(tmp_path_factory.mktemp("rel") / "release.csv")
    ticket = {"freeze_sha256": "TEST_NOT_A_VAULT", "data_sha256": sha256(path)}
    panels, _, candidates = jaaks.build_panels(ticket, path)
    design = rp.load_design(path)
    return panels, candidates, design, rp.build_lines(panels, candidates, design)


def test_condition_identity_of_verification(synthetic):
    panels, candidates, design, lines = synthetic
    by = {(L.tissue, L.replicate, L.sidm): L for L in lines}
    for L in lines:
        pairs = candidates[L.tissue]["pairs_s_v"]
        for i, g in enumerate(L.world.rows):
            assert L.orient_v[i] == L.orient_s[i][::-1]
            assert set(L.orient_s[i]) == set(pairs[g])
            assert not set(L.barcodes_s[i]) & set(L.barcodes_v[i])
            assert (L.tissue, L.sidm, *L.orient_v[i]) in design["orient"]
        other = by[(L.tissue, "VS" if L.replicate == "SV" else "SV", L.sidm)]
        assert other.orient_s == L.orient_v and other.barcodes_s == L.barcodes_v
        assert np.array_equal(other.qc_plates_s, L.qc_plates_v)
        assert np.array_equal(other.valid_hit, L.screen_hit)      # the swap replicate's validation is this screen
        rec = rp.simulate(L, rp.Spec("v", "static", "verify_hits", terminal=True), "measurement")
        screened = {i for _, b, i in rec["purchases"] if b == "screen"}
        assert all(i in screened for _, b, i in rec["purchases"] if b == "verify")


def test_history_probabilities_ignore_target_line_outcomes(synthetic):
    panels, _, _, lines = synthetic
    L = next(x for x in lines if x.replicate == "SV")
    panel = L.panel
    rows = L.world.rows
    from dataclasses import replace
    flipped = replace(panel, valid_hit=panel.valid_hit.copy(), screen_hit=panel.screen_hit.copy())
    flipped.valid_hit[rows] = ~flipped.valid_hit[rows]
    flipped.screen_hit[rows] = ~flipped.screen_hit[rows]
    a = rp.history_probabilities(L.world, panel)
    b = rp.history_probabilities(L.world, flipped)
    for x, z in zip(a, b):
        assert np.allclose(x, z)


def test_instrumented_copy_matches_original_policy_run(synthetic):
    _, _, _, lines = synthetic
    for L in lines:
        for rank in ("static", "feedback"):
            for mode in ("screen_only", "verify_hits", "paired"):
                ref = original.policy_run(L.world, L.panel, rank, mode, L.index)
                rec = rp.original_campaign(L.world, L.panel, rank, mode, L.index)
                assert all(ref[f] == rec[f] for f in rp.ORIGINAL_FIELDS)


def test_noterminal_reference_reproduces_original_verify_hits_purchases(synthetic):
    _, _, _, lines = synthetic
    for L in lines:
        ref = rp.original_campaign(L.world, L.panel, "static", "verify_hits", L.index)
        rec = rp.simulate(L, rp.Spec("v", "static", "verify_hits"), "measurement")
        assert sorted(map(tuple, ref["purchases"])) == sorted(map(tuple, rec["purchases"]))
        scr = rp.simulate(L, rp.Spec("s", "static", "screen_only"), "measurement")
        ref_s = rp.original_campaign(L.world, L.panel, "static", "screen_only", L.index)
        assert sorted(map(tuple, ref_s["purchases"])) == sorted(map(tuple, scr["purchases"]))


def test_accounting_matches_purchases(synthetic):
    _, _, design, lines = synthetic
    L = lines[0]
    rec = rp.simulate(L, rp.Spec("p", "static", "paired"), "measurement")
    acc = rp.account(L, rec, design["native"])
    n_pairs = rec["screens"]
    assert acc["by_branch"]["screen"]["orientation_measurements"] == n_pairs
    assert acc["by_branch"]["verify"]["orientation_measurements"] == n_pairs
    assert acc["total"]["dose_points"] == 14 * 2 * n_pairs
    assert acc["total"]["failed_measurements"] == 0
    assert acc["total"]["combination_wells"] == 14 * (L.plates_s[[i for _, b, i in rec["purchases"] if b == "screen"]].sum()
                                                      + L.plates_v[[i for _, b, i in rec["purchases"] if b == "verify"]].sum())
