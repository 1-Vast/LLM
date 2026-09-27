"""Contract tests for the belief-planning world model, arms, external manifest and vault.

Run: python -m pytest research/belief_planning -q
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from research.external_validation import firewall as F

from . import arms as BA
from . import tasks as T
from . import world as W

ROOT = T.ROOT
HERE = Path(__file__).resolve().parent
P, C, E = T.P, T.C, T.E
SCIPLEX3 = ROOT / "outputs/dynamic_world_model_20260926/prepared"


def _fold(dataset="sciplex3", tier="B", fold=0, *, sealed=True):
    data, ctx, setting = T.load(dataset, tier, fold)
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    heldout = set(comp.index[comp.fold == fold])
    view = F.seal(ctx, heldout) if sealed else ctx
    episodes = T.prepare(view, fold, tier, real_ctx=ctx)
    return data, ctx, view, setting, episodes, heldout


needs_data = pytest.mark.skipif(not SCIPLEX3.exists(), reason="prepared SciPlex3 data not present")


@needs_data
def test_world_model_reads_training_folds_only_and_the_sealed_view_changes_nothing():
    data, ctx, sealed, setting, episodes, heldout = _fold()
    real_world = BA.world_for(ctx if "training_compounds" in ctx.extra else _prepared(ctx, sealed), "on", "true")
    sealed_world = BA.world_for(sealed, "on", "true")
    for entry in sealed_world.keys.values():
        assert not heldout & set(entry["names"])
    assert real_world.hyperparameters["s"] == sealed_world.hyperparameters["s"]
    for compound, truth, decoy, h1, h2 in episodes[:20]:
        for key in setting.keys[:4]:
            a = real_world.forecast(key, h1, h2, compound)
            b = sealed_world.forecast(key, h1, h2, compound)
            assert [dict(x.probabilities) for x in a.branches] == [dict(x.probabilities) for x in b.branches]


def _prepared(ctx, sealed):
    ctx.extra.update({k: sealed.extra[k] for k in ("training_compounds", "vc_partner", "feedback_partner_reading")})
    return ctx


@needs_data
def test_masked_world_is_compound_blind_and_the_kernel_abstains_outside_its_domain():
    _, _, sealed, setting, episodes, _ = _fold()
    masked = BA.world_for(sealed, "masked", "true")
    (c1, _, _, h1, h2), others = episodes[0], [e for e in episodes if e[3:] == episodes[0][3:] and e[0] != episodes[0][0]]
    key = setting.keys[0]
    base = [dict(b.probabilities) for b in masked.forecast(key, h1, h2, c1).branches]
    for c2, *_ in others[:5]:
        assert [dict(b.probabilities) for b in masked.forecast(key, h1, h2, c2).branches] == base
    on = BA.world_for(sealed, "on", "true")
    far = np.zeros_like(on.fp[0])
    on.fp = np.vstack([on.fp, far])
    on.pos = {**on.pos, "__no_structure__": len(on.fp) - 1}
    if on.hyperparameters["k"] > 0:
        assert "vc_abstained" in on.forecast(key, h1, h2, "__no_structure__").basis


@needs_data
def test_feedback_conditions_the_next_forecast_and_a_qc_failure_conditions_nothing():
    _, _, sealed, setting, episodes, _ = _fold()
    world = BA.world_for(sealed, "masked", "true")
    compound, _, _, h1, h2 = episodes[0]
    first, second = setting.keys[3], setting.keys[7]
    plain = [dict(b.probabilities) for b in world.forecast(second, h1, h2, compound).branches]
    qc = [dict(b.probabilities) for b in world.forecast(second, h1, h2, compound, ((first, W.QC_FAILED),)).branches]
    absent = [dict(b.probabilities) for b in world.forecast(second, h1, h2, compound, ((first, W.ABSENT),)).branches]
    assert qc == plain
    if world.hyperparameters["e"] < 1.0:
        assert absent != plain


@needs_data
def test_agent_menus_match_the_runner_and_forecasts_never_become_evidence():
    data, ctx, sealed, setting, episodes, _ = _fold()
    arm = BA.belief_arm()
    for compound, truth, decoy, h1, h2 in episodes[:12]:
        row = P.run_matched("belief", arm, sealed, compound, truth, h1, h2, setting,
                            execute=lambda _c, cpd, key, a, b: E.execute(ctx, cpd, key, a, b))
        assert P.audit_record(row, setting) == []
        for step in row["steps"]:
            real = E.execute(ctx, compound, tuple(step["key"]), h1, h2)["outcome"]
            assert step["outcome"] == (real if step["qc"] else "quality_failed")
            assert step["note"]["evidence_kind"] == "model_prediction"
        eliminated = set(row["steps"][-1]["eliminated"]) if row["steps"] else set()
        readings = {s["outcome"] for s in row["steps"]}
        assert bool(eliminated) == bool(readings & {"eliminate_a", "eliminate_b"})


@needs_data
def test_changing_heldout_outcomes_cannot_change_the_agents_first_choice():
    data, ctx, sealed, setting, episodes, heldout = _fold()
    compound, truth, decoy, h1, h2 = episodes[0]
    arm = BA.belief_arm()
    first = arm(sealed, compound, h1, h2, [], list(setting.keys), setting.budget_days, setting, None)[0]
    for rows in (r for key in setting.keys for c, r in ctx.data.index.get(key, {}).items() if c in heldout):
        ctx.data.shift[rows] = -ctx.data.shift[rows]
    ctx.data.compounds.loc[ctx.data.compounds.compound == compound, "klass"] = decoy
    fresh = F.seal(ctx, heldout)
    T.prepare(fresh, 0, "B", real_ctx=ctx)
    again = arm(fresh, compound, h1, h2, [], list(setting.keys), setting.budget_days, setting, None)[0]
    assert again == first


@needs_data
def test_permuted_feedback_substitutes_a_compatible_real_reading():
    _, _, sealed, setting, episodes, _ = _fold()
    other = sealed.extra["feedback_partner_reading"]
    for compound, _, _, h1, h2 in episodes[:10]:
        for key in setting.keys[:3]:
            assert other(compound, key, h1, h2) in (W.UNRESOLVED, W.ABSENT, W.NONTERMINAL)


@needs_data
def test_unit_left_out_readings_equal_single_loo_when_every_unit_is_one_compound():
    _, ctx, *_ = _fold()
    key = ctx.tier.keys[0]
    singles = {n: n for n in ctx.ft.tables[key].names}
    grouped = W.group_out_outcomes(ctx.ft, key, ctx.params["floor"], ctx.params["margin"], singles)
    assert grouped == C.loo_outcomes(ctx.ft, key, ctx.params["floor"], ctx.params["margin"])


def test_external_manifest_carries_no_label_or_outcome_and_no_development_identity():
    path = HERE / "manifests" / "gse70138_p2ld.json"
    if not path.exists():
        pytest.skip("external manifest not written")
    man = json.loads(path.read_text(encoding="utf-8"))
    text = json.dumps(man).lower()
    for forbidden in ('"klass"', '"moa"', '"truth"', '"cc_q75"', '"detected"', '"distil'):
        assert forbidden not in text
    assert man["audit"]["test_identity_in_development"] == 0
    assert man["audit"]["test_batches_in_GSE92742"] == []
    tests = {t["compound"] for t in man["test_compounds"]}
    assert not tests & set(man["reference_compounds"])
    assert len(man["keys"]) == 12 and len(man["fixed_order"]) == 2


def test_vault_refuses_an_unregistered_manifest_and_a_second_replay(tmp_path, monkeypatch):
    from . import locked as L
    freeze = {"sha256": {}, "external_study": {"manifest_sha256": "0" * 64}}
    monkeypatch.setattr(L, "ACCESS_LOG", tmp_path / "vault_access.jsonl")
    with pytest.raises(F.FreezeMismatch):
        L._open_vault(freeze)
    freeze["external_study"]["manifest_sha256"] = F.sha256_file(L.MANIFEST) if L.MANIFEST.exists() else "x"
    if not L.MANIFEST.exists():
        pytest.skip("external manifest not written")
    (tmp_path / "vault_access.jsonl").write_text(json.dumps({"event": "replay_started"}) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="vault_already_opened"):
        L._open_vault(freeze)


def _synthetic_study(monkeypatch):
    """A study with the external schema but invented measurements and labels (no GSE70138 value is read)."""
    import pandas as pd
    from . import external_phase2 as X
    from . import l1000_level5 as L5
    rng = np.random.default_rng(7)
    smiles = [s for s in T.C.load().compounds.drop_duplicates("compound").smiles if isinstance(s, str)][:80]
    classes = ("class_a", "class_b", "class_c", "class_d")
    lines = ("MCF7", "HT29", "PC3")
    keys = [(line, 24.0, dose) for line in lines for dose in X.DOSES_NM]
    refs = [f"REF{i:03d}" for i in range(64)]
    tests = [f"NEW{i:03d}" for i in range(16)]
    label = {c: classes[i % 4] for i, c in enumerate(refs + tests)}
    centre = {k: rng.normal(size=978) for k in classes}
    rows, shifts = [], []
    for c in refs + tests:
        for line, t, dose in keys:
            strength = {40.0: 0.1, 120.0: 0.3, 1110.0: 0.8, 10000.0: 1.5}[dose]
            vec = strength * centre[label[c]] + rng.normal(size=978)
            detected = bool(strength > 0.5 and rng.random() < 0.8)
            rows.append({"compound": c, "cell_line": line, "time": 24.0, "dose": dose, "signatures": 1, "batch": "SYN",
                         "cc_q75": 0.5 if detected else 0.05, "signature_strength": 1.0, "qc": True,
                         "detected": detected, "replicates": 2, "n_cells_rep1": 20, "n_cells_rep2": 20})
            shifts.append(vec.astype(np.float32))
    conditions = pd.DataFrame(rows)
    monkeypatch.setattr(L5, "build_conditions", lambda study, k, cpds: (conditions, np.asarray(shifts), {"MCF7": {}}))
    monkeypatch.setattr(L5, "annotations", lambda study, cpds: {c: {"klass": label.get(c), "route": "synthetic",
                                                                      "multi_moa": False} for c in cpds})
    man = {"keys": [list(k) for k in keys], "fixed_order": [["MCF7", 24.0, 10000.0], ["HT29", 24.0, 10000.0]],
           "reference_compounds": refs,
           "test_compounds": [{"compound": c, "identity": c, "unit": f"u{i // 2}", "scaffold": None, "smiles": smiles[i]}
                              for i, c in enumerate(tests)]}
    return man, dict(zip(refs + tests, smiles))


@needs_data
def test_external_pipeline_runs_end_to_end_on_a_synthetic_study(monkeypatch):
    from . import external_phase2 as X
    from . import replay as R
    man, smiles = _synthetic_study(monkeypatch)
    data, ctx, setting, summary = X.open_study(man)
    data.compounds["smiles"] = data.compounds.compound.map(smiles)
    assert summary["pool"] and summary["eligible_test_compounds"] > 0
    unit = {t["compound"]: t["unit"] for t in man["test_compounds"]}
    names = list(R.LADDER) + list(R.AGENT)
    result = R.run({"dataset": "synthetic"}, ctx, X.TEST_FOLD, "P2LD", setting, names, unit, limit=4)
    assert result["problems"] == []
    assert {r["arm"] for r in result["records"]} == set(names)
    assert all(r["unit"].startswith("u") for r in result["records"])
