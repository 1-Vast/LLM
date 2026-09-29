"""Tests for the dual-core iteration: split integrity, strict nesting and the transfer models.

File summary
- Path: research/dual_core/test_dual_core.py
- Purpose: pin the properties the E1/E2 claims rest on, on synthetic data where the truth is known.
- Core points:
  - Split checks reject unregistered folds (block 6's 1-5 error), units that span folds, incomplete or
    double coverage, empty tasks, duplicated records and overlapping calibration/test roles.
  - Inner folds never split an independent unit.
  - `rrt` recovers a compound-specific residual when one exists (gamma near 1) and ignores it when it
    is noise (gamma near 0). With q = 0, `rrt_q` is exactly `ridge_st`.
  - The chemical models fall back to the context mean without a structure. Aggregation weights are
    a probability vector.
- Interfaces: pytest tests
- Depends on: splits.py, transfer.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from research.dual_core import splits as SP  # noqa: E402
from research.dual_core import transfer as TF  # noqa: E402


def test_split_checks_reject_known_failures():
    with pytest.raises(SP.SplitError):
        SP.check_folds([1, 2, 3, 4, 5])                         # block 6's first run
    assert SP.check_folds([0, 1, 2, 3, 4]) == (0, 1, 2, 3, 4)
    folds = pd.Series({"a": 0, "b": 1, "c": 1})
    with pytest.raises(SP.SplitError):
        SP.check_units(folds, pd.Series({"a": "u1", "b": "u1", "c": "u2"}))
    SP.check_units(folds, pd.Series({"a": "u1", "b": "u2", "c": "u2"}))
    with pytest.raises(SP.SplitError):
        SP.check_coverage({0: ["a"], 1: ["b"]}, {"a", "b", "c"})
    with pytest.raises(SP.SplitError):
        SP.check_coverage({0: ["a", "b"], 1: ["b", "c"]}, {"a", "b", "c"})
    SP.check_coverage({0: ["a"], 1: ["b", "c"]}, {"a", "b", "c"})
    with pytest.raises(SP.SplitError):
        SP.check_tasks({"sciplex3_B_5": 0, "sciplex3_B_0": 12})
    with pytest.raises(SP.SplitError):
        SP.duplicated_records(pd.DataFrame({"k": [1, 1], "arm": ["x", "x"]}), ["k", "arm"])
    roles = SP.crossfit_roles()
    assert all(f not in cal and len(cal) == 4 for f, cal in roles.items())


def test_inner_folds_never_split_a_unit():
    units = [f"u{i // 3}" for i in range(60)]
    folds = TF.inner_folds(units)
    frame = pd.DataFrame({"u": units, "f": folds})
    assert (frame.groupby("u").f.nunique() == 1).all()
    assert set(folds) == set(range(TF.INNER))


def _pairs(residual: bool, seed=0, n=90, d=80):
    rng = np.random.default_rng(seed)
    A, B = rng.normal(size=(2, d)), rng.normal(size=(2, d))
    Z = rng.normal(size=(n, 2))
    own = rng.normal(size=(n, d)) * 0.6                  # compound-specific component, identical at p and c
    X = Z @ A + own + 0.02 * rng.normal(size=(n, d))
    Y = Z @ B + (own if residual else rng.normal(size=(n, d)) * 0.6) + 0.02 * rng.normal(size=(n, d))
    units = [f"u{i}" for i in range(n)]
    return X, Y, units


def test_rrt_recovers_a_compound_specific_residual_only_when_it_exists():
    X, Y, units = _pairs(residual=True)
    pm = TF.fit_pair("p", "c", X, Y, np.ones(len(X)), units)
    assert pm.gamma_const > 0.7 and pm.gamma0 > 0.7
    X, Y, units = _pairs(residual=False)
    pm = TF.fit_pair("p", "c", X, Y, np.ones(len(X)), units)
    assert pm.gamma_const < 0.2
    x = X[0]
    assert np.allclose(pm.predict(x, 0.0, "rrt_q"), pm.predict(x, 0.0, "ridge_st"))


def test_rrt_improves_discrimination_on_synthetic_residuals():
    from research.incontext_world import metrics as M
    # 400 genes: the compound-specific component cannot be absorbed by a low-rank map of 90 references
    X, Y, units = _pairs(residual=True, n=120, d=400)
    pm = TF.fit_pair("p", "c", X[:90], Y[:90], np.ones(90), units[:90])
    ridge = np.stack([pm.predict(x, 1.0, "ridge_st") for x in X[90:]])
    rrt = np.stack([pm.predict(x, 1.0, "rrt_q") for x in X[90:]])
    assert M.discrimination(rrt, Y[90:]).mean() >= M.discrimination(ridge, Y[90:]).mean()   # both saturate here
    assert np.mean((rrt - Y[90:]) ** 2) < np.mean((ridge - Y[90:]) ** 2)


def test_chemical_models_fall_back_without_structure_and_aggregation_is_a_distribution():
    rng = np.random.default_rng(3)
    fp = (rng.random((20, 64)) < 0.2).astype(float)
    Y = rng.normal(size=(20, 10))
    tm = TF.fit_target("c", fp, Y, [f"u{i}" for i in range(20)], np.zeros(10))
    assert np.allclose(tm.predict(None, "chem_ridge"), Y.mean(0))
    assert np.allclose(tm.predict(np.zeros(64), "chem_knn"), Y.mean(0))
    preds = [np.ones(3), 3 * np.ones(3)]
    for arm in ("rrt_mean", "rrt_best_single", "rrt_precision"):
        value, w = TF.aggregate(preds, [1.0, 3.0], arm)
        assert abs(w.sum() - 1.0) < 1e-12 and (w >= 0).all()
    value, w = TF.aggregate(preds, [1.0, 3.0], "rrt_best_single")
    assert np.allclose(value, 1.0)
    value, w = TF.aggregate(preds, [1.0, 3.0], "rrt_precision")
    assert np.allclose(w, [0.75, 0.25])


# ---------------------------------------------------------------------------------------- agent side
@pytest.fixture(scope="module")
def l1000_t1():
    from research.belief_planning import arms as BA
    from research.protocol_v2 import contracts as K
    from research.protocol_v2 import tasks_v21 as TV
    from research.dual_core import agent as AG
    from research.dual_core import world2 as W2
    data, real_ctx, setting, design = TV.load("l1000", "T", 1)
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    heldout = set(comp.index[comp.fold == 1])
    training = TV.training_compounds(real_ctx, 1)
    view = K.public_view(real_ctx, heldout, training_compounds=training, design=design)
    reference = BA.world_for(view, "on", "true")
    fp, pos = view.extra["fingerprints"]
    public = view.data.compounds.drop_duplicates("compound").set_index("compound")
    groups = {c: g for c, g in public["component"].items() if isinstance(g, str)}
    quality = np.clip(np.nan_to_num(np.asarray(data.agreement, float)), 0, 1)
    ref_quality = {}
    for k, t in view.ft.tables.items():
        for n in t.names:
            ref_quality.setdefault(n, {})[k] = float(quality[data.index[k][n]])
    common = dict(fingerprints=fp, positions=pos, vc="on", feedback="true", hyperparameters=reference.hyperparameters,
                  groups=groups, heldout=heldout, reference_quality=ref_quality)
    executor = AG.LedgerExecutor(real_ctx, dataset="l1000", assay="L1000 Level 5 MODZ", quality=quality,
                                 batch=data.conditions.batch.astype(str).to_numpy(), detected=real_ctx.detected,
                                 cost_days=setting.days)
    return {"data": data, "real": real_ctx, "setting": setting, "view": view, "reference": reference, "common": common,
            "training": training, "heldout": heldout, "episodes": TV.episode_list(real_ctx, 1), "executor": executor,
            "W2": W2, "AG": AG, "K": K}


def _bought(fx):
    """An episode with a QC-passed, non-eliminating first purchase, bought through the ledger executor."""
    from research.belief_planning import world as W
    for compound, truth, decoy, h1, h2 in fx["episodes"]:
        keys = sorted(fx["view"].data.availability[compound])
        if len(keys) < 2:
            continue
        ledger = fx["executor"].open(compound, h1, h2)
        result = fx["executor"](fx["real"], compound, keys[0], h1, h2)
        label = W.label_of(result["outcome"])
        if result["qc"] and label in (W.UNRESOLVED, W.ABSENT):
            step = {"key": list(keys[0]), "qc": True, "outcome": result["outcome"], "eliminated": []}
            return compound, h1, h2, keys[0], keys[1], label, ledger, step
    pytest.skip("no episode with a non-eliminating first purchase")


def test_ledger_serves_only_purchased_past_matching_prompts(l1000_t1):
    from research.dual_core.ledger import LedgerRefusal
    fx = l1000_t1
    compound, h1, h2, p, target, label, ledger, step = _bought(fx)
    prompts = ledger.prompts(target=target, executed=[step])
    assert list(prompts) == [p]
    prompt = prompts[p]
    assert prompt.compound == compound and prompt.step == 0 and prompt.cost_days == fx["setting"].days(p)
    assert np.allclose(prompt.shift, fx["data"].shift[fx["data"].index[p][compound]])
    # the target itself is never a prompt
    assert ledger.prompts(target=p, executed=[step]) == {}
    assert ledger.refusals[-1][2] == "target_outcome_leakage"
    # nothing bought yet at decision point 0; future and unpurchased requests are refused
    assert ledger.prompts(target=target, executed=[]) == {}
    with pytest.raises(LedgerRefusal):
        ledger.get(p, decision_point=0)
    with pytest.raises(LedgerRefusal):
        ledger.get(target, decision_point=1)
    # a result whose row belongs to another compound is refused
    other = next(c for c in fx["data"].index[p] if c != compound)
    bad = {"row": fx["data"].index[p][other], "qc": True}
    assert ledger.record(target, bad) is None and ledger.refusals[-1][2] == "identity_mismatch"
    assert ledger.record(target, {"row": None, "qc": False}) is None and ledger.refusals[-1][2] == "no_row"
    # an executed step that does not match the ledger's purchase at that position is an error
    with pytest.raises(LedgerRefusal):
        ledger.prompts(target=target, executed=[{"key": list(target), "qc": True}])


def test_world2_refuses_heldout_qualities_and_bare_arrays_and_nests_exactly(l1000_t1):
    fx = l1000_t1
    W2 = fx["W2"]
    common = dict(fx["common"])
    off_layer = {"source": "off", "kappa": 0.0, "tau": 0.0}
    bad = dict(common, reference_quality={**common["reference_quality"], next(iter(fx["heldout"])): {}})
    with pytest.raises(ValueError):
        W2.StrictInContextWorld(fx["view"].ft, fx["view"].params, fx["training"], incontext=off_layer, **bad)
    compound, h1, h2, p, target, label, ledger, step = _bought(fx)
    prompts = ledger.prompts(target=target, executed=[step])
    history = ((p, label),)
    on = W2.StrictInContextWorld(fx["view"].ft, fx["view"].params, fx["training"],
                                 incontext={"source": "transfer", "kappa": 8.0, "tau": 4.0}, **common)
    off = W2.StrictInContextWorld(fx["view"].ft, fx["view"].params, fx["training"],
                                  incontext={"source": "transfer", "kappa": 0.0, "tau": 4.0}, **common)
    ref = fx["reference"].forecast(target, h1, h2, compound, history)

    def probs(f):
        return [f.branch_for(h).probabilities for h in (h1, h2)]

    assert probs(off.forecast(target, h1, h2, compound, history, profiles=prompts)) == probs(ref)
    assert probs(on.forecast(target, h1, h2, compound, history)) == probs(ref)
    with pytest.raises(TypeError):
        on.forecast(target, h1, h2, compound, history, profiles={p: np.asarray(prompts[p].shift)})
    moved = on.forecast(target, h1, h2, compound, history, profiles=prompts)
    assert moved.model_version == W2.MODEL_VERSION and moved.evidence_kind.value == "model_prediction"
    for b in moved.branches:
        assert abs(sum(b.probabilities.values()) - 1) < 1e-9 and min(b.probabilities.values()) >= 0


def test_world2_empirical_bayes_is_strictly_nested(l1000_t1, monkeypatch):
    from research.dual_core import transfer as TF
    fx = l1000_t1
    W2 = fx["W2"]
    seen = []
    original = W2.StrictInContextWorld.pair

    def spy(self, p_key, c_key, names=None):
        seen.append(None if names is None else frozenset(names))
        return original(self, p_key, c_key, names)

    monkeypatch.setattr(W2.StrictInContextWorld, "pair", spy)
    world = W2.StrictInContextWorld(fx["view"].ft, fx["view"].params, fx["training"], source="auto", **fx["common"])
    everyone = sorted(set().union(*[set(t.names) for t in fx["view"].ft.tables.values()]))
    inner = dict(zip(everyone, TF.inner_folds([fx["common"]["groups"].get(n, n) for n in everyone])))
    inner_sets = [s for s in seen if s is not None]
    assert inner_sets, "the transfer source was never fitted on inner folds"
    for names in inner_sets:
        assert len({inner[n] for n in names}) == TF.INNER - 1      # exactly the inner-training folds
    assert world.incontext["nesting"] == "strict_inner_group"


def test_predictions_cannot_eliminate_a_hypothesis():
    from agent.memory import MeasurementResult
    from maestro.models import EvidenceKind, EvidenceScope, FunctionalInterventionProfile
    from maestro.outcome import EvidenceState, InterpretationTable, OutcomeRule
    rule = OutcomeRule("matches_h1", "profile_matches_h1", frozenset({"response_detected", "profile_matches:H1"}),
                       eliminates=frozenset({"H2"}), scope=EvidenceScope.MECHANISM_CONTRAST)
    base = dict(action_identifier="a", statement="shift", source_id="s", context_identifier="A549", time_hours=24.0,
                independent_units=2, quality_passed=True, conditions={}, metrics={},
                interpretation_fields=("response_detected", "profile_matches:H1"), result_id="r")
    table = InterpretationTable((rule,))
    profile = FunctionalInterventionProfile(mode="small_molecule", nominal_dose=1.0, time_hours=24.0)
    predicted = MeasurementResult(**base, evidence_kind=EvidenceKind.MODEL_PREDICTION)
    state = EvidenceState(candidates=frozenset({"H1", "H2"}))
    interpretation = table.interpret(predicted, None, profile)
    assert interpretation.eliminates == frozenset() and not interpretation.can_update_mechanism
    assert state.apply(interpretation, predicted).candidates == frozenset({"H1", "H2"})


def test_truncation_matches_the_abstention_rule():
    from research.dual_core import agent as AG
    trace = {"steps": [
        {"key": ["A", 6.0, 1.0], "eliminated": [], "note": {"risk_forecast": 0.01}},
        {"key": ["A", 24.0, 1.0], "eliminated": ["H2"], "note": {"risk_forecast": 0.08}}]}
    full = AG.truncate(trace, "H1", 1.0)
    assert full["decided"] and full["correct"] and not full["abstained"] and full["measurements"] == 2
    stopped = AG.truncate(trace, "H1", 0.05)
    assert stopped["abstained"] and not stopped["decided"] and stopped["measurements"] == 1
    assert AG.truncate(trace, "H2", 1.0)["wrong"] is True
    assert AG.truncate(trace, "H1", 0.0)["measurements"] == 0
