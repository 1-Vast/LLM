"""Protocol-v2.1 boundary fixes: design menus, lifecycle states, per-fold pools and unit weighting.

File summary
- Path: research/protocol_v2/test_protocol_v2_1.py
- Purpose: pin the three block-4 prerequisite fixes (gated plan P0-1 to P0-3). Each data-backed test
  also asserts the protocol-v2 behaviour it replaces, so the test documents the defect as well as
  the fix. Tests that need prepared data skip by name when it is absent.
- Run: python -m pytest research/protocol_v2/test_protocol_v2_1.py -q -p no:cacheprovider
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.protocol_v2 import contracts as K
from research.protocol_v2 import headroom as H
from research.protocol_v2 import runner as RN

P, C, E = K.T.P, K.T.C, K.T.E
PANOBINOSTAT = "Panobinostat (LBH589)"
A549_72H_10UM = ("A549", 72.0, 10000.0)


# ------------------------------------------------------------------------------ lifecycle (no data)
def test_lifecycle_is_separate_from_readout_and_maps_back_losslessly():
    valid = {"row": 3, "qc": True, "outcome": "eliminate_a"}
    assert K.lifecycle_state(True, valid) is K.Lifecycle.MEASURED_VALID and K.readout(valid) == "eliminating"
    assert K.lifecycle_state(True, {"row": None, "qc": False, "outcome": "quality_failed"}) is K.Lifecycle.MEASURED_QC_FAILED
    assert K.lifecycle_state(True, {"row": 3, "qc": False, "outcome": "quality_failed"}) is K.Lifecycle.MEASURED_QC_FAILED
    assert K.lifecycle_state(True, None) is K.Lifecycle.PLANNED_NOT_MEASURED
    assert K.lifecycle_state(False, None) is K.Lifecycle.NOT_PLANNED
    assert K.lifecycle_state(None, None) is K.Lifecycle.MISSING_OR_UNKNOWN
    assert K.readout({"row": None, "qc": False, "outcome": "quality_failed"}) is None
    # every v2 state is reached from exactly one (lifecycle, readout) pair of a measured condition
    pairs = {K.MeasurementState.QUALITY_FAILED: (K.Lifecycle.MEASURED_QC_FAILED, None),
             K.MeasurementState.MEASURED_UNDETECTED: (K.Lifecycle.MEASURED_VALID, "undetected"),
             K.MeasurementState.MEASURED_AMBIGUOUS: (K.Lifecycle.MEASURED_VALID, "ambiguous"),
             K.MeasurementState.MEASURED_ELIMINATING: (K.Lifecycle.MEASURED_VALID, "eliminating")}
    for state, (lifecycle, reading) in pairs.items():
        assert K.v2_state(lifecycle, reading) is state
    for lifecycle in (K.Lifecycle.NOT_PLANNED, K.Lifecycle.PLANNED_NOT_MEASURED, K.Lifecycle.MISSING_OR_UNKNOWN):
        assert K.v2_state(lifecycle, None) is K.MeasurementState.NOT_MEASURED
    with pytest.raises(ValueError):
        K.v2_state(K.Lifecycle.MEASURED_QC_FAILED, "eliminating")
    with pytest.raises(ValueError):
        K.v2_state(K.Lifecycle.MEASURED_VALID, None)


def test_fold_pools_ignore_held_out_labels_and_detection():
    klass = {f"t{i}": ("A" if i < 6 else "B") for i in range(12)} | {"h1": "B", "h2": "C"}
    identity = {c: c for c in klass}
    training = [f"t{i}" for i in range(12)]
    complete = set(klass)
    detected = {"t0": {1}, "t1": {1}, "t6": {1}, "h1": {1}}
    pool = K.fold_pools(klass, identity, training, complete, detected, min_identities=6, min_detected=2)
    assert pool == ("A",)  # B has 6 training identities but only one detected training identity
    flipped = {**detected, "h1": set(), "h2": {1}}
    relabelled = {**klass, "h1": "A", "h2": "B"}
    assert K.fold_pools(relabelled, identity, training, complete, flipped, min_identities=6, min_detected=2) == pool


def test_unit_mean_equals_episode_mean_only_when_units_are_balanced():
    def frame(counts):
        rows = []
        for u, n in enumerate(counts):
            for j in range(n):
                episode = f"u{u}e{j}"
                rows.append({"arm": "x", "episode": episode, "unit": f"u{u}", "correct": float(u == 0)})
                rows.append({"arm": "y", "episode": episode, "unit": f"u{u}", "correct": 0.0})
        return pd.DataFrame(rows)
    balanced = H.unit_paired(frame([2, 2, 2, 2]), "x", "y", "correct")
    assert balanced["difference"] == pytest.approx(balanced["episode_mean"]) == pytest.approx(0.25)
    skewed = H.unit_paired(frame([7, 1, 1, 1]), "x", "y", "correct")
    assert skewed["difference"] == pytest.approx(0.25) and skewed["episode_mean"] == pytest.approx(0.7)
    assert skewed["ci"][0] <= skewed["difference"] <= skewed["ci"][1]


# ------------------------------------------------------------------------------ data-backed
@pytest.fixture(scope="module")
def sciplex_a3():
    from research.protocol_v2 import tasks_v21 as V
    try:
        data, ctx, setting, design = V.load("sciplex3", "A", 3)
    except (FileNotFoundError, OSError) as exc:
        pytest.skip(f"prepared SciPlex3 data or raw release unavailable: {exc}")
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    heldout = set(comp.index[comp.fold == 3])
    return {"data": data, "ctx": ctx, "setting": setting, "design": design, "heldout": heldout,
            "training": V.training_compounds(ctx, 3)}


def test_design_menu_does_not_move_when_a_held_out_outcome_removes_rows(sciplex_a3):
    ctx, heldout, design = sciplex_a3["ctx"], sciplex_a3["heldout"], sciplex_a3["design"]
    assert PANOBINOSTAT in heldout, "fold 3 holds Panobinostat out; the fixture assumes it"
    training = sciplex_a3["training"]
    v21 = K.public_view(ctx, heldout, training_compounds=training, design=design)
    v2 = K.public_view(ctx, heldout, training_compounds=training)
    # the condition was profiled (design) but dropped by the 20-cell rule (no prepared row)
    assert A549_72H_10UM in v21.data.availability[PANOBINOSTAT]
    assert A549_72H_10UM not in v2.data.availability[PANOBINOSTAT]
    # removing every prepared row of a held-out compound moves the v2 menu, not the v2.1 menu
    index = ctx.data.index
    victim = PANOBINOSTAT
    saved = {k: v[victim] for k, v in index.items() if victim in v}
    for k in saved:
        del index[k][victim]
    try:
        after21 = K.public_view(ctx, heldout, training_compounds=training, design=design)
        after2 = K.public_view(ctx, heldout, training_compounds=training)
    finally:
        for k, row in saved.items():
            index[k][victim] = row
    assert dict(after21.data.availability) == dict(v21.data.availability)
    assert after2.data.availability[victim] != v2.data.availability[victim]


def test_buying_a_planned_but_excluded_condition_is_a_charged_qc_failure(sciplex_a3):
    from research.protocol_v2 import tasks_v21 as V
    ctx, heldout, design = sciplex_a3["ctx"], sciplex_a3["heldout"], sciplex_a3["design"]
    view = K.public_view(ctx, heldout, training_compounds=sciplex_a3["training"], design=design)
    episodes = [e for e in V.episode_list(ctx, 3) if e[0] == PANOBINOSTAT]
    assert episodes, "Panobinostat must be scorable in fold 3 for this test"
    compound, truth, _, h1, h2 = episodes[0]

    def arm(view, compound, h1, h2, history, menu, remaining, setting, state):
        return (A549_72H_10UM, {}) if not history else (None, {"reason": "done"})

    trace = RN.run_episode("forced", arm, view, ctx, compound, h1, h2, sciplex_a3["setting"], design_menu=True)
    step = trace["steps"][0]
    assert step["lifecycle"] == "measured_qc_failed" and step["readout"] is None
    assert step["state"] == "quality_failed" and step["eliminated"] == []
    assert trace["measurements"] == 1 and trace["days"] > 0 and trace["wells"] > 0
    assert RN.audit_trace(trace, RN.local_setting(sciplex_a3["setting"], view.data.availability[compound])) == []
    assert K.score(trace, truth)["final"] == "undetermined"
    # protocol v2 refuses the same purchase: the condition is not on its menu
    v2 = K.public_view(ctx, heldout, training_compounds=sciplex_a3["training"])
    with pytest.raises(K.NotMeasured):
        RN.run_episode("forced", arm, v2, ctx, compound, h1, h2, sciplex_a3["setting"])


def test_sciplex3_pools_ignore_held_out_labels(sciplex_a3):
    from research.protocol_v2 import tasks_v21 as V
    data, heldout, design = sciplex_a3["data"], sciplex_a3["heldout"], sciplex_a3["design"]
    spec = C.load_protocol()
    before = {name: V._sciplex3_tier(data, spec, design, 3, name) for name in ("A", "B")}
    saved = data.compounds.copy()
    changed = saved.copy()
    changed.loc[changed.compound.isin(heldout), "klass"] = "Glucocorticoid receptor agonism"
    data.compounds = changed
    try:
        after = {name: V._sciplex3_tier(data, spec, design, 3, name) for name in ("A", "B")}
        legacy_after = C.tiers(data, spec)["B"].pool
    finally:
        data.compounds = saved
    legacy_before = C.tiers(data, spec)["B"].pool
    for name in ("A", "B"):
        assert after[name].pool == before[name].pool and after[name].compounds == before[name].compounds
    assert legacy_after != legacy_before  # the v2 pool counted held-out labels


def test_l1000_pools_ignore_held_out_detection_and_labels():
    from research.protocol_v2 import tasks_v21 as V
    from research.protocol_v2 import design as DS
    try:
        data = K.T.LP.load()
        design = DS.load("l1000")
    except (FileNotFoundError, OSError) as exc:
        pytest.skip(f"prepared L1000 data unavailable: {exc}")
    detected = data.conditions.detected.to_numpy(bool)
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    fold = 3
    heldout = set(comp.index[comp.fold == fold])
    before = V._l1000_tier(data, design, fold, "LT", detected)
    rows = np.flatnonzero(data.conditions.compound.isin(heldout).to_numpy())
    flipped = detected.copy()
    flipped[rows] = False
    saved = data.compounds.copy()
    changed = saved.copy()
    changed.loc[changed.compound.isin(heldout), "klass"] = changed.klass.dropna().iloc[0]
    data.compounds = changed
    try:
        after = V._l1000_tier(data, design, fold, "LT", flipped)
    finally:
        data.compounds = saved
    assert after.pool == before.pool and after.compounds == before.compounds
    # the protocol-v2 rule over every compound moves when held-out detection flips
    keys = tuple(K.T.LP.TIERS["LT"]["keys"])
    complete = {c for c in comp.index if set(keys) <= design.get(c, frozenset())}

    def legacy(flags):
        detected_at = {c: {k for k in keys if (r := data.index.get(k, {}).get(c)) is not None and flags[r]}
                       for c in comp.index}
        return K.fold_pools(comp.klass.to_dict(), comp.identity.astype(str).to_dict(), list(comp.index), complete,
                            detected_at, min_identities=K.T.LP.POOL_MIN_IDENTITIES,
                            min_detected=K.T.LP.POOL_MIN_DETECTED_IDENTITIES)
    assert legacy(detected) != legacy(flipped)
