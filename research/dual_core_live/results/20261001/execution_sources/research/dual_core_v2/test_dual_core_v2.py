"""Tests for the dual-core v2 corrections (risk control, lineage, honest errors, contracts, policies).

File summary
- Path: research/dual_core_v2/test_dual_core_v2.py
- Purpose: regression tests for the defects confirmed on 2026-09-28 and the behaviour of their repairs.
- Core points:
  - P3: block 7's fixed-sequence Learn-then-Test returns the threshold-0 fallback even when the
    unconstrained policy is safe by a wide margin; the repaired procedure certifies it, names its
    outcome, never certifies abstain-all and never reports a zero conditional risk for zero decisions.
  - Both p-values are valid (simulated type-I error) and Holm keeps the family-wise error rate.
- Interfaces: pytest tests
- Depends on: research/dual_core (block 7, unchanged), research/dual_core_v2
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from research.dual_core_v2 import risk_control as RC  # noqa: E402

GRID = [0.0, 0.0025, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0]


def _synthetic_traces(n_units=400, *, risky_share=0.0, seed=0):
    """One-step episodes. Safe steps (risk 0.005-0.02) are wrong 1% of the time; risky steps
    (risk 0.2-0.4) are wrong 40% of the time. Every episode decides."""
    rng = np.random.default_rng(seed)
    traces = []
    for u in range(n_units):
        risky = rng.random() < risky_share
        risk = rng.uniform(0.2, 0.4) if risky else rng.uniform(0.005, 0.02)
        wrong = rng.random() < (0.4 if risky else 0.01)
        for arm in ("reference", "incontext"):
            traces.append({"arm": arm, "dataset": "syn", "tier": "X", "fold": u % 5, "unit": f"u{u}",
                           "compound": f"c{u}", "h1": "A", "h2": "B", "truth": "A",
                           "steps": [{"key": ["L", 24.0, 1.0], "note": {"risk_forecast": risk},
                                      "eliminated": ["A"] if wrong else ["B"]}]})
    return traces


def _episode_table(traces, threshold):
    from research.dual_core import agent as AG
    rows = []
    for t in traces:
        if t["arm"] != "reference":
            continue
        o = AG.truncate(t, t["truth"], threshold)
        rows.append({"fold": t["fold"], "unit": t["unit"], "wrong": o["wrong"], "decided": o["decided"]})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------ P3 regression
def test_block7_p3_falls_back_to_zero_even_when_p0_is_safe():
    """The confirmed defect: the loop starts at threshold 0, whose zero-decision loss is on the null
    boundary, so the first test fails, the loop breaks and P3 becomes 0 in every fold."""
    from research.dual_core import e2
    from research.dual_core import splits as SP
    traces = _synthetic_traces()
    spec = {"alpha": 0.05, "delta": 0.1, "threshold_grid": GRID}
    out = e2.policies(traces, SP.crossfit_roles(), spec)["syn|reference"]
    assert {v["P3"] for v in out["thresholds"].values()} == {0.0}
    # ... and it is reported as a zero conditional error at zero coverage, not as undefined
    assert out["policies"]["P3"]["coverage"] == 0.0
    assert out["policies"]["P3"]["wrong_among_decided"] == 0.0
    # while the unconstrained policy is far inside the target on the same traces
    full = _episode_table(traces, 1.0)
    assert RC.conditional_risk(full.wrong, full.decided) < 0.03


@pytest.mark.parametrize("method", ["hb", "betting"])
def test_repaired_ltt_certifies_safe_unconstrained_policy(method):
    traces = _synthetic_traces()
    cal = {lam: _episode_table(traces, lam).query("fold != 0") for lam in GRID}
    units = sorted(cal[1.0].unit.unique())
    losses = {lam: RC.unit_losses(cal[lam], units) for lam in GRID if lam > 0}
    cert = RC.certify(losses, losses[1.0], alpha=0.05, delta=0.1, rho=0.5, method=method, reference_key=1.0)
    assert cert.status == "certified" and cert.policy == 1.0 and not cert.abstains


def test_repaired_ltt_certifies_an_abstaining_threshold_when_p0_is_unsafe():
    traces = _synthetic_traces(n_units=1500, risky_share=0.2, seed=1)
    cal = {lam: _episode_table(traces, lam).query("fold != 0") for lam in GRID}
    units = sorted(cal[1.0].unit.unique())
    losses = {lam: RC.unit_losses(cal[lam], units) for lam in GRID if lam > 0}
    assert losses[1.0].risk() > 0.05                              # P0 violates the target
    cert = RC.certify(losses, losses[1.0], alpha=0.05, delta=0.1, rho=0.5, reference_key=1.0)
    assert cert.status == "certified" and cert.abstains
    assert 0.02 <= cert.policy <= 0.2                             # abstains on every risky step (risk > 0.2)
    assert 0.3 not in cert.certified and 1.0 not in cert.certified
    assert cert.candidates[1.0]["p"] > 0.1                        # P0 itself is not certified


def test_abstain_all_is_explicit_and_never_a_candidate():
    traces = _synthetic_traces()
    tab = _episode_table(traces, 1.0)
    losses = RC.unit_losses(tab)
    with pytest.raises(ValueError):
        RC.certify({RC.ABSTAIN_ALL: losses}, losses, alpha=0.05, delta=0.1, rho=0.5)
    applied = RC.apply_policy({1.0: tab}, RC.ABSTAIN_ALL)
    assert not applied.decided.any() and (applied.measurements == 0).all()
    assert math.isnan(RC.conditional_risk(applied.wrong, applied.decided))


def test_structural_abstain_when_p0_never_decides():
    losses = RC.UnitLosses(("a", "b", "c"), np.zeros(3), np.zeros(3))
    cert = RC.certify({1.0: losses}, losses, alpha=0.05, delta=0.1, rho=0.5)
    assert cert.status == "structural_abstain" and cert.policy == RC.ABSTAIN_ALL
    assert math.isnan(losses.risk())


def test_zero_threshold_is_not_abstain_all():
    """A step whose recorded risk is exactly 0 is still bought at threshold 0."""
    from research.dual_core import agent as AG
    trace = {"steps": [{"key": ["L", 24.0, 1.0], "note": {"risk_forecast": 0.0}, "eliminated": ["B"]}]}
    assert AG.truncate(trace, "A", 0.0)["decided"]


def test_coverage_requirement_blocks_a_low_risk_low_coverage_policy():
    rng = np.random.default_rng(3)
    n = 3000
    ref = RC.UnitLosses(tuple(map(str, range(n))), (rng.random(n) < 0.06).astype(float), np.ones(n))
    decided = (rng.random(n) < 0.2).astype(float)                  # keeps 20% of P0's decisions
    tiny = RC.UnitLosses(ref.units, np.zeros(n), decided)
    cert = RC.certify({0.01: tiny, 1.0: ref}, ref, alpha=0.05, delta=0.1, rho=0.5, reference_key=1.0)
    assert cert.candidates[0.01]["p_risk"] < 1e-6 and cert.candidates[0.01]["p_cov"] > 0.5
    assert cert.status == "no_candidate_certified"


# ------------------------------------------------------------------------------------ validity
def test_hb_matches_block7():
    from research.dual_core import e2
    for mean in (0.0, 0.01, 0.03, 0.0476, 0.2):
        for n in (10, 84, 400):
            assert RC.hb_pvalue(mean, n, 0.05 / 1.05) == pytest.approx(e2._hb_pvalue(mean, n, 0.05 / 1.05))


@pytest.mark.parametrize("method", ["hb", "betting"])
def test_pvalues_hold_type_one_error_at_the_boundary(method):
    """X in [0, 1] with E[X] = t exactly (the least favourable null): rejection rate <= delta."""
    rng = np.random.default_rng(11)
    t, delta, reps, n = 0.05 / 1.05, 0.1, 1500, 120
    rejections = 0
    for _ in range(reps):
        # a skewed bounded variable with mean t: mostly near t, occasionally 1
        spike = rng.random(n) < 0.02
        x = np.where(spike, 1.0, (t - 0.02) / 0.98 * rng.uniform(0.0, 2.0, n))
        p = RC.hb_pvalue(float(x.mean()), n, t) if method == "hb" else RC.betting_pvalue(x, t, delta=delta)
        rejections += p <= delta
    se = math.sqrt(delta * (1 - delta) / reps)
    assert rejections / reps <= delta + 3 * se


def test_betting_is_more_powerful_than_hb_for_low_variance_losses():
    rng = np.random.default_rng(5)
    t = 0.05 / 1.05
    x = np.clip(rng.normal(t - 0.012, 0.03, 600), 0, 1)
    assert RC.betting_pvalue(x, t) < RC.hb_pvalue(float(x.mean()), len(x), t)


def test_holm_keeps_family_wise_error_when_every_candidate_is_unsafe():
    rng = np.random.default_rng(7)
    reps, false = 400, 0
    for _ in range(reps):
        n = 150
        ref = RC.UnitLosses(tuple(map(str, range(n))), (rng.random(n) < 0.055).astype(float), np.ones(n))
        cands = {lam: RC.UnitLosses(ref.units, (rng.random(n) < 0.055).astype(float), np.ones(n))
                 for lam in (0.01, 0.02, 0.05, 0.1, 0.5)}
        cands[1.0] = ref
        cert = RC.certify(cands, ref, alpha=0.05, delta=0.1, rho=0.5, reference_key=1.0)
        false += cert.status == "certified"
    assert false / reps <= 0.1 + 3 * math.sqrt(0.09 / reps)


def test_plugin_select_has_an_explicit_fallback():
    losses = RC.UnitLosses(("a", "b"), np.ones(2), np.ones(2))
    assert RC.plugin_select({1.0: losses}, losses, alpha=0.05, rho=0.5) == (RC.ABSTAIN_ALL, "no_candidate_meets_target")


# ------------------------------------------------------------------------------------ lineage
@pytest.fixture(scope="module")
def nested_a01():
    """SciPlex3 tier A with folds 0 and 1 held out, the reference world and the v2 world."""
    from research.belief_planning import arms as BA
    from research.belief_planning import tasks as T
    from research.protocol_v2 import contracts as K
    from research.dual_core_v2 import nested as NS
    from research.dual_core_v2 import world3 as W3
    data, ctx, setting, design, original = NS.load("sciplex3", "A", (0, 1))
    lineage = NS.lineage_of("sciplex3", "A", (0, 1), ctx, original)
    heldout = {c for c, f in original.items() if f in (0, 1)}
    view = K.public_view(ctx, heldout, training_compounds=lineage.training_compounds, design=design)
    reference = BA.world_for(view, "on", "true")
    quality = np.clip(np.nan_to_num(np.asarray(data.agreement, float), nan=0.0), 0.0, 1.0)
    ref_quality = {}
    for k, t in view.ft.tables.items():
        for n in t.names:
            ref_quality.setdefault(n, {})[k] = float(quality[data.index[k][n]])
    fp, pos = view.extra["fingerprints"]
    public = view.data.compounds.drop_duplicates("compound").set_index("compound")
    groups = {c: g for c, g in public["skeleton"].items() if isinstance(g, str)}
    kwargs = dict(reference_quality=ref_quality, fingerprints=fp, positions=pos, vc="on", feedback="true",
                  hyperparameters=reference.hyperparameters, groups=groups, heldout=heldout)
    world = W3.WorldV2(view.ft, view.params, lineage.training_compounds, dataset="sciplex3",
                       assay="sci-RNA-seq3 pseudobulk shift", **kwargs)
    unit_of = T.units("sciplex3")[T.UNIT["sciplex3"]].astype(str).to_dict()
    return dict(data=data, ctx=ctx, setting=setting, original=original, lineage=lineage, view=view,
                reference=reference, world=world, kwargs=kwargs, unit_of=unit_of, quality=quality)


def test_block7_calibration_models_were_fitted_on_the_test_fold():
    """The confirmed defect: the model that produced fold g's calibration traces saw fold f."""
    from research.belief_planning import tasks as T
    from research.protocol_v2 import tasks_v21 as TV
    from research.dual_core_v2 import nested as NS
    data, ctx_g, _, _ = TV.load("sciplex3", "A", 1)            # block 7's model for calibration fold 1
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    fold0 = [c for c in comp.index if comp.fold[c] == 0]         # test fold 0
    seen = set().union(*[set(t.names) for t in ctx_g.ft.tables.values()])
    assert seen & set(fold0), "block 7's fold-1 model should contain fold-0 references"
    unit_of = T.units("sciplex3")[T.UNIT["sciplex3"]].astype(str).to_dict()
    lin = NS.Lineage("sciplex3", "A", (1,), (), tuple(TV.training_compounds(ctx_g, 1)), "", tuple(sorted(seen)), (), {})
    with pytest.raises(NS.LineageError):
        NS.check_independent(lin, fold0, unit_of)


def test_nested_model_never_fits_on_either_held_out_fold(nested_a01, monkeypatch):
    """Spy on the fitting inputs: reference tables, pool, validator calibration and transfer fits."""
    from research.dual_core import transfer as TF
    from research.dual_core_v2 import nested as NS
    from research.dual_core_v2 import world3 as W3
    s = nested_a01
    held = {c for c, f in s["original"].items() if f in (0, 1)}
    held_units = {s["unit_of"].get(c, c) for c in held}
    for fold in (0, 1):
        NS.check_independent(s["lineage"], [c for c, f in s["original"].items() if f == fold], s["unit_of"])
    assert set(s["lineage"].training_folds) == {2, 3, 4}
    for table in s["ctx"].ft.tables.values():
        assert not set(table.names) & held
    seen_units = []
    original = TF.fit_pair

    def spy(prompt, target, X, Y, q, units, **kw):
        seen_units.extend(units)
        return original(prompt, target, X, Y, q, units, **kw)

    monkeypatch.setattr(TF, "fit_pair", spy)
    W3.WorldV2(s["view"].ft, s["view"].params, s["lineage"].training_compounds, dataset="sciplex3",
               assay="sci-RNA-seq3 pseudobulk shift", **s["kwargs"])
    assert seen_units and not set(map(str, seen_units)) & {str(u) for u in held_units}


# ------------------------------------------------------------------------------------ world v2
def test_v1_variant_reproduces_block7_world(nested_a01):
    from research.dual_core import world2 as W2
    s = nested_a01
    old = W2.StrictInContextWorld(s["view"].ft, s["view"].params, s["lineage"].training_compounds,
                                  transfer_arm="rrt_q", source="auto", **s["kwargs"])
    new = s["world"]
    for src in ("prompt", "transfer"):
        assert np.allclose(old.incontext["loglik"][src], new.fitted["loglik"][src])
    v1 = new.variant("v1")
    assert (v1.incontext["source"], v1.incontext["kappa"], v1.incontext["tau"]) == \
        (old.incontext["source"], old.incontext["kappa"], old.incontext["tau"])


def _prompt_set(s, compound, key_prompt, *, decision_point=1, quality=None, step=0, dataset="sciplex3"):
    import hashlib
    from research.dual_core.ledger import Prompt
    from research.dual_core_v2 import world3 as W3
    row = s["data"].index[key_prompt][compound]
    shift = np.asarray(s["data"].shift[row], float)
    q = float(s["quality"][row]) if quality is None else quality
    p = Prompt(compound, dataset, "sci-RNA-seq3 pseudobulk shift", key_prompt, step, 6.0, int(row), "b", q, True,
               hashlib.sha256(shift.tobytes()).hexdigest(), shift)
    return W3.PromptSet(compound, dataset, "sci-RNA-seq3 pseudobulk shift", decision_point, (p,), "test")


def _held_case(s):
    """A held-out compound measured at two conditions, and a contrast of its pool."""
    keys = list(s["ctx"].ft.tables)
    pool = s["ctx"].tier.pool
    comp = s["data"].compounds.drop_duplicates("compound").set_index("compound")
    for c, f in sorted(s["original"].items()):
        if f != 0 or comp.klass.get(c) not in pool:
            continue
        measured = [k for k in keys if c in s["data"].index.get(k, {})]
        if len(measured) >= 2:
            h1 = comp.klass[c]
            h2 = next(h for h in pool if h != h1)
            return c, measured[0], measured[1], h1, h2
    raise AssertionError("no held-out compound measured twice")


def test_prompt_contract_refusals(nested_a01):
    from research.dual_core_v2 import world3 as W3
    s = nested_a01
    world = s["world"].variant("transfer")
    c, kp, kt, h1, h2 = _held_case(s)
    ok = _prompt_set(s, c, kp)
    world.forecast(kt, h1, h2, c, (), prompts=ok)
    cases = {
        "not_a_prompt_set": dict(prompts={kp: ok.prompts[0]}),
        "identity_mismatch": dict(prompts=ok, compound="another"),
        "future_measurement": dict(prompts=_prompt_set(s, c, kp, decision_point=0)),
        "target_outcome_leakage": dict(prompts=_prompt_set(s, c, kt), key=kt),
        "dataset_mismatch": dict(prompts=_prompt_set(s, c, kp, dataset="l1000")),
        "invalid_quality": dict(prompts=_prompt_set(s, c, kp, quality=float("nan"))),
    }
    for reason, case in cases.items():
        with pytest.raises(W3.PromptRefused) as err:
            world.forecast(case.get("key", kt), h1, h2, case.get("compound", c), (), prompts=case["prompts"])
        assert err.value.reason == reason


def test_quality_change_cannot_reuse_a_cached_forecast(nested_a01):
    s = nested_a01
    world = s["world"].variant("transfer")
    if world.incontext["kappa"] <= 0:
        pytest.skip("transfer source not active in this fold")
    c, kp, kt, h1, h2 = _held_case(s)
    high = world.forecast(kt, h1, h2, c, (), prompts=_prompt_set(s, c, kp, quality=0.9))
    low = world.forecast(kt, h1, h2, c, (), prompts=_prompt_set(s, c, kp, quality=0.0))
    diff = max(abs(high.branches[i].probabilities[k] - low.branches[i].probabilities[k])
               for i in range(2) for k in high.branches[i].probabilities)
    assert diff > 1e-9, "rrt_q uses the prompt quality, so the forecast must change with it"


def test_block7_world_reuses_a_stale_kernel_when_only_quality_changes(nested_a01):
    """The contract weakness in block 7: its kernel cache key holds the shift digest, not the quality."""
    from research.dual_core import world2 as W2
    from research.incontext_world import world as IW
    s = nested_a01
    old = W2.StrictInContextWorld(s["view"].ft, s["view"].params, s["lineage"].training_compounds,
                                  transfer_arm="rrt_q", source="transfer", **s["kwargs"])
    if old.incontext["kappa"] <= 0:
        pytest.skip("transfer source not active in this fold")
    c, kp, kt, h1, h2 = _held_case(s)
    a = _prompt_set(s, c, kp, quality=0.9).prompts[0]
    b = _prompt_set(s, c, kp, quality=0.0).prompts[0]
    first = old.context_logkernel(kt, {kp: a}, "transfer")
    second = old.context_logkernel(kt, {kp: b}, "transfer")
    fresh = W2.StrictInContextWorld(s["view"].ft, s["view"].params, s["lineage"].training_compounds,
                                    transfer_arm="rrt_q", source="transfer", incontext=old.incontext,
                                    **s["kwargs"]).context_logkernel(kt, {kp: b}, "transfer")
    assert np.array_equal(first, second) and not np.allclose(second, fresh)


def test_no_prompt_forecast_equals_reference_world(nested_a01):
    from research.dual_core_v2 import world3 as W3
    s = nested_a01
    c, kp, kt, h1, h2 = _held_case(s)
    empty = W3.PromptSet(c, "sciplex3", "sci-RNA-seq3 pseudobulk shift", 0, (), "test")
    for which in ("auto", "v1", "off"):
        got = s["world"].variant(which).forecast(kt, h1, h2, c, (), prompts=empty)
        ref = s["reference"].forecast(kt, h1, h2, c, ())
        assert [dict(b.probabilities) for b in got.branches] == [dict(b.probabilities) for b in ref.branches]


def test_prediction_records_cannot_eliminate_hypotheses(nested_a01):
    """A v2 forecast turned into a record keeps its prediction kind, and a prediction eliminates nothing
    even when it claims the reading that a real measurement would use to eliminate."""
    from agent.memory import MeasurementResult
    from maestro.models import EvidenceKind, EvidenceScope, FunctionalInterventionProfile
    from maestro.outcome import EvidenceState, InterpretationTable, OutcomeRule
    from research.dual_core_v2 import world3 as W3
    s = nested_a01
    c, kp, kt, h1, h2 = _held_case(s)
    f = s["world"].variant("auto").forecast(kt, h1, h2, c, (), prompts=_prompt_set(s, c, kp))
    assert f.evidence_kind is EvidenceKind.MODEL_PREDICTION and f.model_version == W3.MODEL_VERSION
    rule = OutcomeRule("matches_h1", "profile_matches_h1", frozenset({"response_detected", "profile_matches:H1"}),
                       eliminates=frozenset({"H2"}), scope=EvidenceScope.MECHANISM_CONTRAST)
    base = dict(action_identifier="a", statement=f.basis, source_id="world3", context_identifier="A549",
                time_hours=72.0, independent_units=2, quality_passed=True, conditions={}, metrics={},
                interpretation_fields=("response_detected", "profile_matches:H1"), result_id="r")
    table = InterpretationTable((rule,))
    profile = FunctionalInterventionProfile(mode="small_molecule", nominal_dose=1.0, time_hours=72.0)
    state = EvidenceState(candidates=frozenset({"H1", "H2"}))
    predicted = MeasurementResult(**base, evidence_kind=f.evidence_kind)
    interpretation = table.interpret(predicted, None, profile)
    assert interpretation.eliminates == frozenset() and not interpretation.can_update_mechanism
    assert state.apply(interpretation, predicted).candidates == frozenset({"H1", "H2"})


# ------------------------------------------------------------------------------------ honest transfer errors
def _pair_data(n=60, d=40, residual=0.0, seed=0):
    rng = np.random.default_rng(seed)
    B = rng.normal(size=(3, d))
    Z = rng.normal(size=(n, 3))
    X = Z @ B + 0.3 * rng.normal(size=(n, d))
    specific = rng.normal(size=(n, d))
    X = X + specific
    Y = Z @ B * 0.8 + residual * specific + 0.3 * rng.normal(size=(n, d))
    return X, Y, np.ones(n), [f"u{i}" for i in range(n)]


def test_block7_inner_mse_of_rrt_q_can_never_exceed_ridge_st():
    """The confirmed optimism: gamma is scored on the residuals it was fitted to, and gamma = 0 is feasible."""
    from research.dual_core import transfer as TF
    for seed in range(5):
        X, Y, q, units = _pair_data(residual=0.0, seed=seed)
        pm = TF.fit_pair(("p",), ("c",), X, Y, q, units)
        assert pm.inner_mse["rrt_q"] <= pm.inner_mse["ridge_st"] + 1e-15


def test_honest_error_removes_the_optimism_on_noise():
    from research.dual_core_v2 import transfer_honest as TH
    gaps = []
    for seed in range(6):
        X, Y, q, units = _pair_data(residual=0.0, seed=seed)
        r = TH.honest_errors(("p",), ("c",), X, Y, q, units)
        gaps.append(r["honest"]["rrt_q"] - r["in_sample"]["rrt_q"])
    assert np.mean(gaps) > 0


def test_honest_error_still_finds_a_real_residual():
    from research.dual_core_v2 import transfer_honest as TH
    X, Y, q, units = _pair_data(residual=0.8, seed=1)
    r = TH.honest_errors(("p",), ("c",), X, Y, q, units)
    assert r["honest"]["rrt_q"] < r["honest"]["ridge_st"]


def test_honest_error_fits_never_see_their_held_out_inner_fold(monkeypatch):
    from research.dual_core import transfer as TF
    from research.dual_core_v2 import transfer_honest as TH
    X, Y, q, units = _pair_data(seed=2)
    folds = TF.inner_folds(units)
    calls = []
    original = TF.fit_pair

    def spy(prompt, target, Xs, Ys, qs, us, **kw):
        calls.append(set(map(str, us)))
        return original(prompt, target, Xs, Ys, qs, us, **kw)

    monkeypatch.setattr(TF, "fit_pair", spy)
    TH.honest_errors(("p",), ("c",), X, Y, q, units)
    held = [{u for u, f in zip(units, folds) if f == k} for k in range(TF.INNER)]
    assert len(calls) == 1 + TF.INNER
    for k, used in enumerate(calls[1:]):
        assert not used & held[k] and used | held[k] == set(units)


# ------------------------------------------------------------------------------------ analysis designs
def test_split_design_calibrates_and_tests_one_model_that_never_saw_either_fold():
    from research.dual_core_v2 import analysis as A
    for f in A.FOLDS:
        cal, test = A.design_roles("split", f)
        assert len(cal) == 1 and len(test) == 1 and cal[0][0] == test[0][0]
        model_folds = {int(x) for x in cal[0][0][1:]}
        assert model_folds == {f, cal[0][1]} and test[0][1] == f and cal[0][1] != f


def test_nested_crossfit_never_uses_a_model_trained_on_the_test_fold():
    from research.dual_core_v2 import analysis as A
    for f in A.FOLDS:
        cal, test = A.design_roles("nested_crossfit", f)
        assert {g for _, g in cal} == set(A.FOLDS) - {f}
        for model, g in cal + test:
            assert f in {int(x) for x in model[1:]}          # f is excluded from every model's fit
        cal7, _ = A.design_roles("block7_crossfit", f)
        assert all(m == f"block7_f{g}" for m, g in cal7)      # block 7: models trained on all folds but g


def test_summarise_reports_undefined_risk_for_zero_decisions():
    from research.dual_core_v2 import analysis as A
    frame = pd.DataFrame({"unit": ["a", "b"], "wrong": [False, False], "decided": [False, False],
                          "correct": [False, False], "abstained": [True, True], "measurements": [0, 0]})
    s = A.summarise(frame, draws=50)
    assert s["wrong_among_decided"] is None and s["wrong_among_decided_ci"] is None and s["undefined_draws"] == 50
