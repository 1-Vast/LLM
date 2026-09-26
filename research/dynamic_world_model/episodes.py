"""Run every deterministic measurement-choice policy over the pre-registered decision episodes.

File summary
- Path: research/dynamic_world_model/episodes.py
- Purpose: for each fold and tier, calibrate the validator on training compounds, then for each
  held-out compound of a pool class and each other pool class, let each policy choose up to two
  measurements one at a time, execute them against the compound's real measured data, and read
  them only through the validator and the repository's `EvidenceState`.
- Core points:
  - Selection goes through the repository's own selectors: `BudgetedEvidenceSelector` for
    cost_only and magnitude (the current virtual-cell tie-break), `select_expected_coverage` for
    the card-based policies, with detection power taken from the scenario card.
  - A missing or QC-failed measurement is charged and returns `quality_failed`.
  - The permuted-label control changes only the cards the planner sees; the validator that reads
    the measurement is the real one.
  - `dyn_model` is added by `transition.py` once the transition arms are evaluated; this module
    exposes the hooks it needs.
- Run: python research/dynamic_world_model/episodes.py
- Depends on: common.py, maestro.selection, maestro.acquisition, maestro.models, maestro.outcome, rdkit
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

import common as C

from maestro.acquisition import select_expected_coverage  # noqa: E402
from maestro.models import (DevelopmentAction, EvidenceAction, EvidenceActionKind, BiologicalQuantity,  # noqa: E402
                            FunctionalInterventionProfile, MechanismContrast, MechanismHypothesis)
from maestro.outcome import EvidenceState  # noqa: E402
from maestro.selection import BudgetedEvidenceSelector  # noqa: E402

STEP_BUDGET_DAYS = 8.0
PROFILE = FunctionalInterventionProfile(mode="small_molecule")


def days(key) -> float:
    return {24.0: 1.0, 72.0: 3.0}[key[1]] + 5.0


def lab_cost(keys) -> tuple[float, int]:
    total_days = sum(days(k) for k in keys)
    seen, wells = set(), 0
    for k in keys:
        wells += 2
        if (k[0], k[1]) not in seen:
            seen.add((k[0], k[1]))
            wells += 4
    return total_days, wells


def make_action(key, h1, h2, *, detection_power=None, distinguishes=True) -> EvidenceAction:
    line, t, dose = key
    return EvidenceAction(
        identifier=C.action_id(key), description=f"sci-RNA-seq3 transcriptome, {line}, {dose:g} nM, {t:g} h",
        cost=days(key), distinguishes=(h1, h2) if distinguishes else (),
        kind=EvidenceActionKind.RNA_ABUNDANCE_MEASUREMENT, readout="transcriptome_shift", time_hours=t,
        expected_conditions={"dose_nM": f"{dose:g}"}, execution_context=line,
        quantity=BiologicalQuantity.RNA_ABUNDANCE, detection_power=detection_power)


# ------------------------------------------------------------------------------ magnitude predictor
class Magnitude:
    """The served rung's rule restricted to training compounds: 5 nearest by Tanimoto, weighted mean, norm."""

    def __init__(self, data: C.Data, detected: np.ndarray):
        from rdkit import Chem, RDLogger
        from rdkit.Chem import rdFingerprintGenerator
        RDLogger.DisableLog("rdApp.*")
        gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
        comp = data.compounds.drop_duplicates("compound")
        self.names = list(comp.compound)
        self.fold = dict(zip(comp.compound, comp.fold))
        self.fp = np.asarray([gen.GetFingerprintAsNumPy(Chem.MolFromSmiles(s)).astype(np.float32) for s in comp.smiles])
        self.pos = {c: i for i, c in enumerate(self.names)}
        self.data = data

    def predict(self, compound: str, key) -> float | None:
        if key[1] != 24.0:
            return None                                   # the served rung refuses time_not_supported
        x = self.fp[self.pos[compound]]
        inter = self.fp @ x
        union = self.fp.sum(1) + x.sum() - inter
        sim = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
        fold = self.fold[compound]
        vectors, weights = [], []
        for j in np.argsort(-sim):
            other = self.names[j]
            if self.fold[other] == fold:
                continue
            row = self.data.index.get(key, {}).get(other)
            if row is None or not C.qc_passed(self.data, row):
                continue
            vectors.append(self.data.shift[row])
            weights.append(max(float(sim[j]), 1e-6))
            if len(vectors) == 5:
                break
        if not vectors:
            return None
        w = np.asarray(weights) / np.sum(weights)
        return float(np.linalg.norm(np.tensordot(w, np.asarray(vectors), axes=1)))


# ------------------------------------------------------------------------------ fold context
@dataclass
class FoldContext:
    data: C.Data
    tier: C.Tier
    ft: C.FoldTables
    ft_perm: C.FoldTables
    params: dict
    detected: np.ndarray
    magnitude: Magnitude
    card_cache: dict
    extra: dict


def card_for(ctx: FoldContext, key, h1, h2, *, permuted=False, step1=None):
    cache_key = (key, h1, h2, permuted, step1)
    if cache_key not in ctx.card_cache:
        ft = ctx.ft_perm if permuted else ctx.ft
        ctx.card_cache[cache_key] = C.card(ft, key, h1, h2, ctx.params, step1=step1)
    return ctx.card_cache[cache_key]


def execute(ctx: FoldContext, compound, key, h1, h2) -> dict:
    row = ctx.data.index.get(key, {}).get(compound)
    if row is None or not C.qc_passed(ctx.data, row):
        return {"qc": False, "outcome": "quality_failed", "row": row, "agreement": float("nan")}
    reading = C.read_profile(ctx.ft, key, ctx.data.shift[row], bool(ctx.detected[row]), h1, h2, ctx.params) \
        if ctx.params["eliminates"] else {"outcome": "undetected" if not ctx.detected[row] else "ambiguous"}
    return {"qc": True, "row": row, "agreement": float(ctx.data.agreement[row]), **reading}


# ------------------------------------------------------------------------------ policies
def choose(policy: str, ctx: FoldContext, compound, h1, h2, executed: list, rng) -> tuple:
    """Return (key or None, note dict)."""
    menu = [k for k in ctx.tier.keys if k not in [e["key"] for e in executed]]
    if not menu:
        return None, {"reason": "menu_exhausted"}
    if policy == "random":
        return menu[rng.integers(len(menu))], {}
    if policy == "fixed":
        if ctx.tier.name == "B":
            order = [("A549", 24.0, 10000.0), ("MCF7", 24.0, 10000.0)]
        else:
            order = [("A549", 24.0, 10000.0), ("A549", 72.0, 10000.0)]
        for k in order:
            if k in menu:
                return k, {}
        return None, {"reason": "fixed_sequence_exhausted"}
    if policy in ("cost_only", "magnitude"):
        actions = [make_action(k, h1, h2) for k in menu]
        priorities = {}
        if policy == "magnitude":
            for k in menu:
                value = ctx.magnitude.predict(compound, k)
                if value is not None:
                    priorities[C.action_id(k)] = value
        plan = BudgetedEvidenceSelector().select(frozenset({h1, h2}), actions, PROFILE, STEP_BUDGET_DAYS,
                                                  action_priorities=priorities)
        if not plan.actions:
            return None, {"reason": "selector_returned_empty"}
        chosen = plan.actions[0].identifier
        return next(k for k in menu if C.action_id(k) == chosen), {"priority": priorities.get(chosen)}
    if policy in ("separation", "separation_permuted", "dyn_ref"):
        step1 = None
        if policy == "dyn_ref" and executed:
            first = executed[0]
            if first["outcome"] in ("undetected", "ambiguous"):
                step1 = (first["key"], C.STEP1_CATEGORY[first["outcome"]])
        cards = {k: card_for(ctx, k, h1, h2, permuted=(policy == "separation_permuted"), step1=step1) for k in menu}
        return select_by_cards(menu, cards, h1, h2)
    if policy in ctx.extra.get("policies", {}):
        return ctx.extra["policies"][policy](ctx, compound, h1, h2, executed, menu)
    raise ValueError(policy)


def select_by_cards(menu, cards, h1, h2):
    actions = []
    for k in menu:
        c = cards[k]
        p = c.get("p_correct", 0.0) if c.get("served") else 0.0
        actions.append(make_action(k, h1, h2, detection_power=min(p, 1.0) if p > 0 else None, distinguishes=p > 0))
    plan = select_expected_coverage(frozenset({h1, h2}), actions, PROFILE, STEP_BUDGET_DAYS)
    note = {"cards": {C.action_id(k): {"served": cards[k].get("served"), "p_correct": cards[k].get("p_correct"),
                                        "p_wrong": cards[k].get("p_wrong"), "reason": cards[k].get("reason")}
                      for k in menu}, "expected_coverage": plan.expected_coverage, "assumptions": list(plan.assumptions)}
    if not plan.plan.actions:
        return None, {**note, "reason": "no_action_distinguishes_the_contrast"}
    chosen = plan.plan.actions[0].identifier
    return next(k for k in menu if C.action_id(k) == chosen), note


def contrast_for(h1, h2, actions) -> MechanismContrast:
    hyps = (MechanismHypothesis(h1, f"The compound acts by {h1}.", DevelopmentAction.CONTINUE, causal_factor=h1),
            MechanismHypothesis(h2, f"The compound acts by {h2}.", DevelopmentAction.REVISE_ATTRIBUTION, causal_factor=h2))
    return MechanismContrast(f"{h1}__vs__{h2}", hyps, ("mechanism class",), plan=actions[0] if actions else None,
                             additional_plans=tuple(actions[1:]))


def run_episode(policy: str, ctx: FoldContext, compound, truth, h1, h2, rng, budget: int = 2) -> dict:
    hypotheses = (h1, h2)
    menu_actions = [make_action(k, h1, h2) for k in ctx.tier.keys]
    contrast = contrast_for(h1, h2, menu_actions)
    state = EvidenceState.open(contrast.hypotheses)
    executed = []
    status = None
    for step in range(budget):
        key, note = choose(policy, ctx, compound, h1, h2, executed, rng)
        if key is None:
            status = "deferred" if not executed else None
            break
        result = execute(ctx, compound, key, h1, h2)
        action = next(a for a in menu_actions if a.identifier == C.action_id(key))
        state, interpretation, outcome = C.evidence_update(
            state, contrast, action, key, result, h1, h2, qc=result["qc"], agreement=result["agreement"],
            source=f"sciplex3:{compound}")
        executed.append({"key": key, "action": C.action_id(key), "outcome": outcome, "qc": result["qc"],
                         "score_h1": result.get("score_a"), "score_h2": result.get("score_b"),
                         "agreement": result["agreement"], "outcome_class": interpretation.outcome_class.value,
                         "scope": interpretation.scope.value, "eliminated": sorted(state.eliminated),
                         "note": {k: v for k, v in note.items() if k != "cards"},
                         "card": (note.get("cards") or {}).get(C.action_id(key))})
        if state.eliminated:
            break
    return finish(policy, compound, truth, h1, h2, state, executed, status)


def finish(policy, compound, truth, h1, h2, state, executed, status=None) -> dict:
    other = h2 if truth == h1 else h1
    remaining = state.candidates
    if status == "deferred":
        final = "deferred"
    elif remaining == frozenset({truth}):
        final = "correct"
    elif remaining == frozenset({other}):
        final = "wrong"
    elif not remaining:
        final = "exhausted"
    else:
        final = "undetermined"
    keys = [e["key"] for e in executed]
    total_days, wells = lab_cost(keys)
    first = next((i for i, e in enumerate(executed) if e["eliminated"]), None)
    to_first = lab_cost(keys[:first + 1]) if first is not None else (None, None)
    utility = {"correct": 1, "wrong": -2, "exhausted": -2}.get(final, 0)
    return {"policy": policy, "compound": compound, "truth": truth, "h1": h1, "h2": h2, "final": final,
            "utility": utility, "measurements": len(executed), "days": total_days, "wells": wells,
            "days_to_elimination": to_first[0], "wells_to_elimination": to_first[1],
            "steps": [{k: (list(v) if k == "key" else v) for k, v in e.items()} for e in executed]}


def oracle(ctx: FoldContext, compound, truth, h1, h2, budget: int = 2) -> dict:
    menu = list(ctx.tier.keys)
    results = {k: execute(ctx, compound, k, h1, h2) for k in menu}
    other = h2 if truth == h1 else h1

    def value(outcome):
        if outcome == "eliminate_b":   # h2 eliminated
            return 1 if h2 == other else -2
        if outcome == "eliminate_a":
            return 1 if h1 == other else -2
        return 0

    best = (0, 0.0, 0, ())
    for k1 in menu:
        v1 = value(results[k1]["outcome"])
        if v1 != 0:
            candidate = (v1, -lab_cost([k1])[0], -lab_cost([k1])[1], (k1,))
            best = max(best, candidate, key=lambda x: (x[0], x[1], x[2]))
            continue
        for k2 in menu:
            if k2 == k1:
                continue
            v2 = value(results[k2]["outcome"])
            candidate = (v2, -lab_cost([k1, k2])[0], -lab_cost([k1, k2])[1], (k1, k2))
            best = max(best, candidate, key=lambda x: (x[0], x[1], x[2]))
    keys = list(best[3])
    menu_actions = [make_action(k, h1, h2) for k in ctx.tier.keys]
    contrast = contrast_for(h1, h2, menu_actions)
    state = EvidenceState.open(contrast.hypotheses)
    executed = []
    for key in keys:
        r = results[key]
        action = next(a for a in menu_actions if a.identifier == C.action_id(key))
        state, interpretation, outcome = C.evidence_update(state, contrast, action, key, r, h1, h2, qc=r["qc"],
                                                           agreement=r["agreement"], source=f"sciplex3:{compound}")
        executed.append({"key": key, "action": C.action_id(key), "outcome": outcome, "qc": r["qc"],
                         "eliminated": sorted(state.eliminated), "agreement": r["agreement"]})
    return finish("oracle", compound, truth, h1, h2, state, executed, "deferred" if not keys else None)


# ------------------------------------------------------------------------------ driver
def contexts(data, protocol, detected, magnitude, tier_names=("B", "A"), folds=None):
    all_tiers = C.tiers(data, protocol)
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    for name in tier_names:
        tier = all_tiers[name]
        for fold in (folds if folds is not None else sorted(data.compounds.fold.unique())):
            ft = C.build_fold_tables(data, tier, int(fold), detected)
            params = C.calibrate(ft, protocol)
            rng = np.random.default_rng([C.SEED, int(fold), ord(name)])
            train = [c for c in comp.index if comp.fold[c] != fold and comp.klass.get(c) in tier.pool]
            labels = [comp.klass[c] for c in train]
            permuted = dict(zip(train, rng.permutation(labels)))
            ft_perm = C.build_fold_tables(data, tier, int(fold), detected, label_map=permuted)
            yield FoldContext(data, tier, ft, ft_perm, params, detected, magnitude, {}, {}), int(fold)


def stable(*parts) -> int:
    """A process-independent integer for seeding (Python's str hash is salted per process)."""
    return int(hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()[:8], 16)


POLICIES = ("fixed", "cost_only", "magnitude", "separation", "separation_permuted", "dyn_ref")


def episode_list(ctx: FoldContext, fold: int):
    comp = ctx.data.compounds.drop_duplicates("compound").set_index("compound")
    out = []
    for compound in ctx.tier.compounds:
        if comp.fold[compound] != fold:
            continue
        truth = comp.klass[compound]
        for decoy in ctx.tier.pool:
            if decoy == truth:
                continue
            rng = np.random.default_rng([C.SEED, stable(compound, decoy)])
            h1, h2 = (truth, decoy) if rng.random() < 0.5 else (decoy, truth)
            out.append((compound, truth, decoy, h1, h2))
    return out


def run_fold(task) -> tuple[list, dict]:
    """One (tier, fold): build the tables, calibrate, and run every policy on its episodes."""
    tier_name, fold = task
    protocol = C.load_protocol()
    data = C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    magnitude = Magnitude(data, detected)
    records, calibration = [], {}
    for ctx, f in contexts(data, protocol, detected, magnitude, tier_names=(tier_name,), folds=(fold,)):
        calibration[f"{ctx.tier.name}|{f}"] = ctx.params
        for compound, truth, decoy, h1, h2 in episode_list(ctx, f):
            base = {"tier": ctx.tier.name, "fold": f, "decoy": decoy}
            for policy in POLICIES:
                records.append(base | run_episode(policy, ctx, compound, truth, h1, h2, None))
            for seed in range(20):
                rng = np.random.default_rng([C.SEED, seed, stable(compound, decoy)])
                records.append(base | {"seed": seed} | run_episode("random", ctx, compound, truth, h1, h2, rng))
            records.append(base | oracle(ctx, compound, truth, h1, h2))
    return records, calibration


def main() -> None:
    from concurrent.futures import ProcessPoolExecutor
    started = time.time()
    protocol = C.load_protocol()
    data = C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    out_dir = C.OUTPUTS / "episodes"
    out_dir.mkdir(parents=True, exist_ok=True)
    folds = sorted(int(f) for f in data.compounds.fold.unique())
    tasks = [(t, f) for t in ("B", "A") for f in folds]
    records, calibration = [], {}
    with ProcessPoolExecutor(max_workers=min(len(tasks), 10)) as pool:
        for (t, f), (recs, cal) in zip(tasks, pool.map(run_fold, tasks)):
            records += recs
            calibration.update(cal)
            print(f"{t} fold {f}: {len(recs)} records, {time.time() - started:.0f}s", flush=True)
    with (out_dir / "episodes.jsonl").open("w", encoding="utf-8") as stream:
        for r in records:
            stream.write(json.dumps(C.clean(r), default=C._default) + chr(10))
    C.write_json(out_dir / "calibration.json", C.clean({
        "detection_null": null, "folds": calibration, "detected_conditions": int(detected.sum()),
        "qc_passed_conditions": int(sum(C.qc_passed(data, i) for i in range(len(data.conditions)))),
        "protocol_hashes": C.frozen_hashes(),
        "runner_sha256": {name: hashlib.sha256((C.HERE / name).read_bytes()).hexdigest()
                          for name in ("episodes.py", "common.py")}}))
    print(f"episodes {len(records)} in {time.time() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
