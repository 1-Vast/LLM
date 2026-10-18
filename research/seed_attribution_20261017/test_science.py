"""Fast checks of the evaluation contract and of the masked-replay information contract (no PRISM data).

File summary
- Path: research/seed_attribution_20261017/test_science.py
- Purpose: the defects found in `program_revision_20261017` are caught by tests, and the repaired pieces
  behave as PROTOCOL.md says. Run: ``python -m pytest -q test_science.py`` from this folder.
- Checks:
  - singleton replicates are known and enter the reference median (the frozen score formula gives NaN);
  - a drug without any known reference pair is refused by name, never ranked as the worst;
  - labels equal the frozen `qualified_hits` and the score threshold is the same quantity;
  - a threshold built from reference lines does not move when target-line outcomes change;
  - fully missing outcomes are unknown, never inactive and never hits;
  - a Gaussian crossing probability is not the qualified-hit probability (sign condition);
  - the strong-model fit cache cannot be stale;
  - synthetic reserved-outcome invariance: every upstream quantity, proposal and distinguishing pair of
    the masked bench is identical when the reserved labels are redrawn, and the frozen bench is not;
  - the null-library collection obeys its registered rules; the analysis identities (net hits of the
    differing nominations equal the paired contrast; permutation rank; verdict vocabulary) hold.
"""
from __future__ import annotations

import warnings

import numpy as np
import pytest

import analyse
import contract
import corrected as C
import replay
import revise
from common import qualified_hits

STRONG = {"rank": 3, "lam": 2.0, "iters": 8}


def _frozen_score_median(X2, X3, ref):
    """The frozen `engine.Domain` formula for the reference median (kept here as the regression subject)."""

    known = np.isfinite(X2) | np.isfinite(X3)
    m23 = np.where(known, (X2 + X3) / 2, np.nan)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmedian(m23[:, ref], axis=1)


# ---------------------------------------------------------------- endpoint


def test_singleton_replicates_are_known_and_enter_the_median():
    X2 = np.array([[-2.0, np.nan, np.nan, 0.0, 0.1]])
    X3 = np.array([[np.nan, -3.0, np.nan, 0.2, 0.0]])
    ep = contract.endpoint(X2, X3, np.ones(5, bool))
    assert ep.n_rep.tolist() == [[1, 1, 0, 2, 2]]
    assert ep.known.tolist() == [[True, True, False, True, True]]
    assert ep.m[0, 0] == -2.0 and ep.m[0, 1] == -3.0 and np.isnan(ep.m[0, 2])
    assert ep.med[0] == pytest.approx(-0.975)  # median of (-3, -2, 0.05, 0.1): singleton and two-replicate pairs
    assert ep.thr[0] == pytest.approx(-1.975)
    assert ep.hit[0].tolist() == [True, True, False, False, False]


def test_frozen_score_formula_loses_singleton_pairs_and_the_contract_does_not():
    # drug 0 has only single-replicate pairs: the frozen score reference is NaN, labels are fine
    X2 = np.array([[-2.0, np.nan, 0.0], [-1.0, -0.5, -0.2]])
    X3 = np.array([[np.nan, -3.0, np.nan], [-1.2, -0.4, -0.1]])
    ref = np.ones(3, bool)
    assert np.isnan(_frozen_score_median(X2, X3, ref)[0])
    assert np.isfinite(_frozen_score_median(X2, X3, ref)[1])
    ep = contract.endpoint(X2, X3, ref)
    assert np.isfinite(ep.thr).all()
    assert ep.known[0].tolist() == [True, True, True]


def test_contract_labels_equal_the_frozen_label_function():
    rng = np.random.default_rng(3)
    X2, X3 = rng.normal(-0.4, 1.3, (60, 40)), rng.normal(-0.4, 1.3, (60, 40))
    X2[rng.random(X2.shape) < 0.2] = np.nan
    X3[rng.random(X3.shape) < 0.2] = np.nan
    ref = np.zeros(40, bool)
    ref[:25] = True
    hit_frozen, known_frozen = qualified_hits(X2, X3, line_mask=ref)
    ep = contract.endpoint(X2, X3, ref)
    assert np.array_equal(ep.hit, hit_frozen) and np.array_equal(ep.known, known_frozen)


def test_undefined_reference_is_refused_by_name_and_never_a_hit():
    X2 = np.array([[np.nan, np.nan, -2.5], [-2.0, -0.2, -0.1]])
    X3 = np.array([[np.nan, np.nan, -2.5], [-2.2, -0.3, 0.0]])
    ref = np.array([True, True, False])  # drug 0 is measured only on the third (non-reference) line
    ep = contract.endpoint(X2, X3, ref)
    assert ep.undefined_reference.tolist() == [True, False]
    assert not ep.hit[0].any()
    with pytest.raises(ValueError, match=contract.UNDEFINED_REFERENCE):
        contract.require_defined(ep, np.array([0, 1]))
    contract.require_defined(ep, np.array([1]))


def test_fully_missing_outcomes_are_unknown_not_inactive():
    X2 = np.full((2, 4), np.nan)
    X3 = np.full((2, 4), np.nan)
    X2[1, 0] = -3.0
    ep = contract.endpoint(X2, X3, np.ones(4, bool))
    assert not ep.known[0].any() and not ep.hit[0].any()
    assert ep.known[1, 0] and not ep.known[1, 1:].any()
    assert np.isnan(ep.m[0]).all()


def test_sign_condition_and_crossing_probability_are_different_events():
    X2 = np.array([[-3.0, -3.0, 0.0, 0.0, 0.0, 0.0]])
    X3 = np.array([[-3.0, 0.4, 0.0, 0.0, 0.0, 0.0]])
    ep = contract.endpoint(X2, X3, np.ones(6, bool))
    assert ep.thr[0] == pytest.approx(-1.0)
    assert ep.hit[0, 0] and not ep.hit[0, 1]  # mean -1.3 crosses the threshold but a replicate is positive
    d = contract.sign_discordance(ep)
    assert d["threshold_crossing_pairs"] == 2 and d["fail_sign_condition"] == 1
    p = contract.crossing_probability(np.array([-2.0]), np.array([0.01]), np.array([-1.0]))
    assert p[0] > 0.99  # crossing probability is near 1 regardless of the sign condition


def test_threshold_is_independent_of_target_line_outcomes():
    rng = np.random.default_rng(5)
    X2, X3 = rng.normal(-0.3, 1, (30, 20)), rng.normal(-0.3, 1, (30, 20))
    ref = np.zeros(20, bool)
    ref[:12] = True
    a = contract.endpoint(X2, X3, ref)
    X2b, X3b = X2.copy(), X3.copy()
    X2b[:, 12:], X3b[:, 12:] = rng.normal(5, 1, (30, 8)), rng.normal(5, 1, (30, 8))
    b = contract.endpoint(X2b, X3b, ref)
    assert np.array_equal(a.thr, b.thr, equal_nan=True)
    contract.assert_prospective(ref, np.arange(12, 20), 20)
    with pytest.raises(ValueError, match=contract.RESERVED_OVERLAP):
        contract.assert_prospective(ref, np.arange(10, 20), 20)


# ---------------------------------------------------------------- synthetic world and the information contract


@pytest.fixture(scope="module")
def world():
    truth, reserved = replay.synthetic_world(0, 0)
    return truth, reserved


def test_synthetic_world_has_the_defect_patterns(world):
    truth, _ = world
    stack_n = np.isfinite(truth.X2).astype(int) + np.isfinite(truth.X3).astype(int)
    assert (stack_n[truth.src_drug] == 1).any() and (stack_n[truth.src_drug] == 0).any()
    assert truth.endpoint.singleton_share() > 0.05


def test_corrected_domain_threshold_matches_contract(world):
    truth, _ = world
    ep = contract.endpoint(truth.X2, truth.X3, truth.src_line)
    assert np.array_equal(truth.thr, ep.thr, equal_nan=True)
    assert np.array_equal(truth.hit, ep.hit)
    assert np.array_equal(truth.hit & ~truth.known, np.zeros_like(truth.hit))


def test_masked_domain_hides_reserved_cells_and_rederives_the_reference(world):
    truth, reserved = world
    vis = replay.mask_cells(truth, reserved)
    for X in (vis.X1, vis.X2, vis.X3):
        assert np.isnan(X[:, reserved]).all()
    assert not vis.endpoint.ref_mask[reserved].any()
    assert vis.endpoint.ref_mask.sum() == truth.src_line.sum() - len(reserved)
    assert np.isnan(vis.Ymean[:, reserved]).all()
    # the reference median of the visible domain is the historical one, not the full-source one
    assert not np.allclose(vis.med, truth.med, equal_nan=True)


def test_probe_readouts_stay_visible_when_declared_as_purchased(world):
    truth, reserved = world
    keep = np.array([3, 5, 8])
    vis = replay.mask_cells(truth, reserved, keep_x1_rows=keep)
    assert np.array_equal(vis.X1[np.ix_(keep, reserved)], truth.X1[np.ix_(keep, reserved)], equal_nan=True)
    others = np.setdiff1d(np.arange(vis.X1.shape[0]), keep)
    assert np.isnan(vis.X1[np.ix_(others, reserved)]).all()
    assert np.isnan(vis.X2[np.ix_(keep, reserved)]).all()


def test_masked_bench_is_invariant_to_reserved_labels_and_frozen_bench_is_not(world):
    truth, reserved = world
    truth2, reserved2 = replay.synthetic_world(0, 11)
    assert np.array_equal(reserved, reserved2)
    assert not np.array_equal(truth.X2[:, reserved], truth2.X2[:, reserved], equal_nan=True)
    assert np.array_equal(truth.X2[:, np.setdiff1d(np.arange(truth.X2.shape[1]), reserved)],
                          truth2.X2[:, np.setdiff1d(np.arange(truth.X2.shape[1]), reserved)], equal_nan=True)

    def snap_masked(t):
        vis = replay.mask_cells(t, reserved)
        bench = replay.MaskedBench(vis, t, "I1", [], strong=STRONG)
        lib, _ = revise.seed_library(bench)
        return replay.snapshot(bench, lib, bench.projects[0]), lib

    a, lib = snap_masked(truth)
    b, _ = snap_masked(truth2)
    assert replay.differences(a, b) == []

    def snap_frozen(t):
        bench = revise.Bench(t, "I1", [], strong=STRONG)
        return replay.snapshot(bench, lib, bench.projects[0])

    assert len(replay.differences(snap_frozen(truth), snap_frozen(truth2))) > 0  # negative control


def test_masked_bench_reveals_only_through_reveal_and_counts_new_pairs(world):
    truth, reserved = world
    vis = replay.mask_cells(truth, reserved)
    bench = replay.MaskedBench(vis, truth, "I1", [], strong=STRONG)
    d, c = int(bench.drows[0]), int(reserved[0])
    assert not np.isfinite(vis.X2[d, c])
    out, new = bench.reveal([(d, c), (d, c)])
    assert new == 1 and (d, c) in out
    out2, new2 = bench.reveal([(d, c)])
    assert new2 == 0
    with pytest.raises(NotImplementedError, match="MEASURE_EDIT_NEEDS_PURCHASE"):
        bench.with_design(["x"])


def test_safe_fit_cache_follows_the_data_and_the_frozen_cache_does_not(world):
    import engine

    truth, _ = world
    dom = C.CorrectedDomain.__new__(C.CorrectedDomain)
    dom.__dict__.update(truth.__dict__)
    dom.Ymean = truth.Ymean.copy()
    dom._model_cache, dom._safe_model_cache = {}, {}
    train = np.flatnonzero(dom.src_line)[:40]
    target = np.flatnonzero(dom.src_line)[40:50]
    frozen1 = engine.ContextFold(dom, train, target, "I1", [], strong=STRONG)
    safe1 = C.SafeContextFold(dom, train, target, "I1", [], strong=STRONG)
    dom.Ymean[:, train] += 1.0  # the data change, the lines and the object do not
    frozen2 = engine.ContextFold(dom, train, target, "I1", [], strong=STRONG)
    safe2 = C.SafeContextFold(dom, train, target, "I1", [], strong=STRONG)
    assert np.allclose(frozen1.base_mean, frozen2.base_mean)  # stale: the fit ignores the new labels
    assert np.nanmean(safe2.base_mean - safe1.base_mean) > 0.5  # follows the labels
    dom.Ymean[:, train] -= 1.0
    safe3 = C.SafeContextFold(dom, train, target, "I1", [], strong=STRONG)
    assert np.allclose(safe1.base_mean, safe3.base_mean)


def test_crossfit_variance_is_exact_outside_scopes_and_finite(world):
    truth, reserved = world
    vis = replay.mask_cells(truth, reserved)
    bench = replay.MaskedBench(vis, truth, "I1", [], strong=STRONG)
    lib, _ = revise.seed_library(bench)
    f = bench.query[bench.projects[0]]
    v = C.crossfit_variance(f, lib)
    assert v.shape == f.oos_var.shape and np.isfinite(v).all() and (v > 0).all()
    in_scope = np.zeros(len(f.drows), bool)
    from vc import scope_mask
    for p in lib.programs:
        in_scope |= scope_mask(p.scope, vis.df, f.drows)
    assert np.allclose(v[~in_scope], f.oos_var[~in_scope])


# ---------------------------------------------------------------- null collection and analysis identities


def test_null_collection_obeys_its_registered_rules():
    import json
    from pathlib import Path

    rec = json.loads((Path(__file__).resolve().parent / "NULLS.json").read_text(encoding="utf-8"))
    seed = [(p["scope"], p["state"]) for p in rec["seed_library"]]
    assert len(rec["nulls"]) == rec["n_nulls"] == 20
    seed_gates = sorted(g for _, g in seed)
    for n in rec["nulls"]:
        pairs = [(p["scope"], p["state"]) for p in n["programs"]]
        assert [s for s, _ in pairs] == [s for s, _ in seed]  # scope slots unchanged
        assert sorted(g for _, g in pairs) == seed_gates  # gate multiset unchanged: same capacity
        assert not set(pairs) & set(seed) and len(set(pairs)) == len(pairs)
        assert all(not p["refusals"] for p in n["programs"])
        assert abs(n["total_observed_quadrant_cells"] / rec["seed_total_observed_quadrant_cells"] - 1) <= rec["tolerance"] + 1e-12
    assert len({tuple(n["permutation"]) for n in rec["nulls"]}) == 20


def _synthetic_units(seed=0, n=60, nulls=20, gain=0.0):
    rng = np.random.default_rng(seed)
    clusters = np.array([f"L{i % 12}" for i in range(n)])
    A = rng.integers(2, 7, n).astype(float)
    arms = {}

    def layer(h, with_sets):
        rec = {"hits": h.tolist(), "unknown": np.zeros(n).tolist()}
        return rec

    def sets_for(hits_a):
        # ten nominated positions per line; statuses consistent with the hit count
        nom, status = [], []
        for j in range(n):
            nom.append(list(rng.permutation(60)[:10]))
            st = [1] * int(hits_a[j]) + [0] * (10 - int(hits_a[j]))
            status.append(list(rng.permutation(st)))
        return nom, status

    nomA, stA = sets_for(A)
    B = A + gain
    # B shares the first six nominations with A and differs in the rest; statuses chosen to match its hit count
    nomB, stB = [], []
    for j in range(n):
        keep = nomA[j][:6]
        extra = [int(d) for d in rng.permutation(np.setdiff1d(np.arange(60), nomA[j]))[:4]]
        st_keep = stA[j][:6]
        need = int(B[j]) - sum(1 for v in st_keep if v == 1)
        need = max(0, min(4, need))
        st_extra = [1] * need + [0] * (4 - need)
        nomB.append(keep + extra)
        stB.append(list(st_keep) + st_extra)
    B = np.array([sum(1 for v in st if v == 1) for st in stB], float)
    for name, h, nm, st in (("A_S", A, nomA, stA), ("B_seed", B, nomB, stB)):
        arms[name] = {}
        for L in ("I1", "I2"):
            arms[name][L] = {"hits": h.tolist(), "unknown": np.zeros(n).tolist(), "nominated": nm, "status": st}
        arms[name]["policy"] = {"hits": h.tolist(), "unknown": np.zeros(n).tolist(), "wells": [28] * n, "rounds": [3] * n,
                                "confirmed": [10] * n, "confirmed_drugs": nm, "status": st}
    for name in ("D_shared_only", "C0_additive", "C1_global_ridge", "C1x_global_ridge_cross", "C2_per_drug_ridge", "C3_pooled_gbm"):
        arms[name] = {L: {"hits": (A + rng.normal(0, 0.3, n)).tolist(), "unknown": np.zeros(n).tolist()} for L in ("I1", "I2")}
        arms[name]["policy"] = {"hits": (A + rng.normal(0, 0.3, n)).tolist(), "unknown": np.zeros(n).tolist(), "wells": [28] * n,
                                "rounds": [3] * n, "confirmed": [10] * n}
    for i in range(nulls):
        h = (A + rng.normal(0, 0.3, n)).tolist()
        arms[f"E{i:02d}"] = {L: {"hits": h, "unknown": np.zeros(n).tolist()} for L in ("I1", "I2", "policy")}
        arms[f"E{i:02d}"]["policy"].update(wells=[28] * n, rounds=[3] * n, confirmed=[10] * n)
    return {"_meta": {"cluster": clusters.tolist(), "stratum": ["future_line" if i % 2 else "future_lineage" for i in range(n)],
                      "structure_group": [f"g{i}" for i in range(60)], "undefined_reference_drugs": 0,
                      "gates": {"BRAF": (rng.random(n) < 0.3).astype(int).tolist()}, "source_any_gate_prevalence": 0.5},
            "arms": arms, "variants": {}, "seconds": {}, "parity": {"all_match": True}}


def test_contrast_verdict_vocabulary():
    g = np.array(["a", "b", "c", "d", "e", "f"] * 10)
    rng = np.random.default_rng(1)
    base = rng.normal(4, 1, 60)
    assert analyse.contrast(base + 0.5, base, g)["verdict"] == "X_BETTER"
    assert analyse.contrast(base - 0.5, base, g)["verdict"] == "Y_BETTER"
    assert analyse.contrast(base + rng.normal(0, 0.01, 60), base, g)["verdict"] == "EQUIVALENT_WITHIN_MARGIN"
    assert analyse.contrast(base + rng.normal(0, 3, 60), base, g)["verdict"] == "NOT_DISTINGUISHABLE"


def test_disagreement_net_hits_equal_the_paired_contrast():
    units = _synthetic_units(gain=1.0)
    groups = np.array(units["_meta"]["cluster"])
    d = analyse.disagreement(units, groups)
    for layer in ("policy", "I2", "I1"):
        assert d[layer]["net_equals_B_minus_A_contrast"]
        assert d[layer]["differing_nominations_per_line_B_only"] == d[layer]["differing_nominations_per_line_A_only"]


def test_permutation_rank_and_primary_survival_rule():
    units = _synthetic_units(seed=3, gain=1.5)
    groups = np.array(units["_meta"]["cluster"])
    attr = analyse.attribution(units, groups)
    n = attr["policy"]["null_collection"]
    assert n["n_nulls"] == 20 and n["seed_exceeds_every_null"] and abs(n["p_permutation"] - 1 / 21) < 1e-12
    prim = analyse.primary_family(units, groups)
    assert prim["tests"]["P1_policy_B_vs_A"]["frozen_verdict"] == "CONFIRMED" and prim["seed_signal_survives_primary_layer"]
    flat = _synthetic_units(seed=3, gain=0.0)
    prim0 = analyse.primary_family(flat, np.array(flat["_meta"]["cluster"]))
    assert not prim0["seed_signal_survives_primary_layer"]
