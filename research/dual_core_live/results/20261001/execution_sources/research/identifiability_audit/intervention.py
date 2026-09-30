"""Round-2 minimal interventions: forecast swap and policy swap on frozen episodes.

File summary
- Path: research/identifiability_audit/intervention.py
- Purpose: hold the episode list, legal menu, budget, maximum measurements, QC rule, endpoint, cost
  rule and seed fixed, and vary one thing at a time: (A) the forecast a fixed policy receives, and
  (B) the policy that receives one fixed forecast. Every cell runs through the frozen
  `research.protocol_v2.runner.run_episode`, so legality, real measurement, QC and evidence update
  are the code the registered replay executed.
- Core points:
  - Backends are never merged. `none`/`reference`/`permuted`/`constant` are adapters over the
    repository's `SparseReferenceModel`; `world_ref` is an adapter over the belief-planning
    `ReferenceWorld`; the production STATE endpoint and the case-memory outcome forecaster are
    recorded as separate objects and are not run here (see `NOT_RUN`).
  - A cell that ignores its assigned forecast is reported as such rather than silently counted: the
    `fixed` policy never reads a forecast, so its five forecast rows are a negative control.
  - Ranking is probed, not assumed: for every episode the unconditioned expected utility of every
    menu action is recomputed under the cell's own forecast, so "the ranking changed" is a
    measurement rather than an inference from the chosen action.
  - Nothing here trains a model, develops a readout or optimises a planner. The oracle cell reads
    hidden outcomes and is diagnostic only.
- Run: python -m research.identifiability_audit.intervention [--folds 0] [--out DIR]
- Interfaces: `FORECASTS`, `POLICIES`, `build_bundle`, `run_task`, `main`
- Depends on: research/protocol_v2/{tasks_v21,contracts,runner}.py, research/sparse_value,
  research/belief_planning, research/external_validation
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "identifiability_audit_20260930" / "intervention"
TASKS = (("sciplex3", "B"), ("l1000", "LT"))
SEED = 20260930

FORECASTS = ("none", "reference", "world_ref", "permuted", "constant")
POLICIES = ("fixed", "baseline", "risk_select", "decision_sensitive")

# The cell list is explicit and deliberately small. `choose_injected` is the only policy that reads
# the injected forecast, so the forecast main effect is estimated on it alone. Every other policy
# builds its own model internally, so it is run under the reference forecast only. The two `fixed`
# cells are the negative control for the World x Policy interaction: `fixed` never reads a forecast,
# so any forecast effect must vanish there.
CELLS = (
    ("none", "choose_injected"), ("reference", "choose_injected"), ("world_ref", "choose_injected"),
    ("permuted", "choose_injected"), ("constant", "choose_injected"),
    ("none", "fixed"), ("reference", "fixed"),
    ("reference", "baseline"), ("reference", "risk_select"), ("reference", "decision_sensitive"),
)

NOT_RUN = {
    "world_v2": {"backend": "research/dual_core_v2/world3.py:WorldV2",
                 "reason": "one WorldV2 fit for SciPlex3 B fold 0 exceeded 7.75 minutes of wall clock "
                           "before completing, so the two tasks' fold grids do not fit this run",
                 "measured": "probe script tmp/wv2_probe.py, sciplex3 B fold 0, >465 s and still fitting",
                 "unblocks_when": "a dedicated run with a multi-hour budget, or a cached fitted world"},
    "discrimination": {"backend": "research/sequence_audit/policies.py:discrimination",
                       "reason": "it reads ctx.magnitude, which the whitelist PublicContext deliberately "
                                 "does not expose; running it would require weakening the evidence firewall",
                       "measured": "AttributeError: 'PublicContext' object has no attribute 'magnitude'",
                       "unblocks_when": "a public-view-compliant variant of the arm"},
    "production_state": {"backend": "src/virtual_cell/state_adapter.py (STATE condition-level shift)",
                         "reason": "no registered context matches SciPlex3 B or L1000 LT, and its query "
                                   "requires the target's own post-treatment rows, which is not a "
                                   "decision-time input",
                         "measured": "log/20260930 Round 1, section R1.6",
                         "unblocks_when": "a registered context for these tasks plus a decision-time state"},
    "case_memory_forecaster": {"backend": "research/case_memory_integration/external_replay.py:forecast",
                               "reason": "its population is LINCS 2020 unseen blocks, not the protocol-v2 "
                                         "SciPlex3 B or L1000 LT episodes frozen here",
                               "measured": "26 test units; 25 of them with a single legal action",
                               "unblocks_when": "a shared episode set between the two studies"},
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------------- bundle
@dataclass
class Bundle:
    dataset: str
    tier: str
    fold: int
    data: object
    ctx: object
    setting: object
    design: object
    view: object
    training: tuple
    heldout: set
    episodes: list
    quality: np.ndarray
    groups: dict
    ft_perm: object = None
    reference_world: object = None
    meta: dict = field(default_factory=dict)


def build_bundle(dataset: str, tier: str, fold: int) -> Bundle:
    from research.belief_planning import arms as BA
    from research.belief_planning import tasks as T
    from research.protocol_v2 import contracts as K
    from research.protocol_v2 import tasks_v21 as V

    data, ctx, setting, design = V.load(dataset, tier, fold)
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    heldout = {c for c in ctx.tier.compounds if comp.fold.get(c) == fold}
    training = V.training_compounds(ctx, fold)
    view = K.public_view(ctx, heldout, training_compounds=training, design=design)
    episodes = V.episode_list(ctx, fold)
    quality = np.clip(np.nan_to_num(np.asarray(data.agreement, dtype=np.float64), nan=0.0), 0.0, 1.0)
    units = T.units(dataset)
    groups = {c: str(u) for c, u in units[T.UNIT[dataset]].items() if isinstance(u, str)}
    unit_col = T.UNIT[dataset]
    unit_of = {c: str(u) for c, u in units[unit_col].items()}
    quality_of = {}
    for key, table in view.ft.tables.items():
        for name in table.names:
            quality_of.setdefault(name, {})[key] = float(quality[data.index[key][name]])
    from research.dynamic_world_model import common as C

    ft_perm = C.build_fold_tables(data, ctx.tier, fold, ctx.detected,
                                 label_map=_permuted_labels(data, ctx.tier, fold, dataset, tier))
    reference_world = BA.world_for(view, "on", "true")
    return Bundle(dataset=dataset, tier=tier, fold=fold, data=data, ctx=ctx, setting=setting, design=design,
                  view=view, training=training, heldout=heldout, episodes=episodes, quality=quality,
                  groups=groups, ft_perm=ft_perm, reference_world=reference_world,
                  meta={"unit_of": unit_of, "quality_of": quality_of, "unit_column": unit_col})


def _permuted_labels(data, tier, fold, dataset, tier_name):
    """The protocol's own within-fold label permutation (same seed path as tasks_v21._context)."""
    from research.protocol_v2.contracts import C, T

    E = T.E
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    seed_name = E.stable(tier.name) if dataset == "l1000" else ord(tier_name)
    rng = np.random.default_rng([C.SEED, int(fold), seed_name])
    train = [c for c in comp.index if comp.fold.get(c) != fold and comp.klass.get(c) in tier.pool]
    permuted_values = rng.permutation([comp.klass[c] for c in train])
    return dict(zip(train, permuted_values))


# --------------------------------------------------------------------------------- forecast adapters
class ForecastAdapter:
    """Common shape: `forecast(target, h1, h2, *, source=None, observed_label=None)` -> SV.Forecast."""

    backend = "unknown"
    version = "unknown"

    def bind(self, compound: str) -> None:
        self.compound = compound

    def input_digest(self, target, h1, h2, source, observed_label) -> str:
        return _sha256(f"{self.backend}|{self.compound}|{target}|{h1}|{h2}|{source}|{observed_label}")


class NoneForecast(ForecastAdapter):
    backend = "none"
    version = "audit-stub"

    def forecast(self, target, h1, h2, *, source=None, observed_label=None):
        from research.sparse_value.model import Forecast

        return Forecast({}, "forecast_disabled_by_audit")


class ConstantForecast(ForecastAdapter):
    """Content-free: one fixed label distribution, the pooled training marginal, for every query."""

    backend = "constant"
    version = "audit-stub"

    def __init__(self, ft, params):
        self.ft, self.params = ft, params

    def forecast(self, target, h1, h2, *, source=None, observed_label=None):
        from research.sparse_value.model import Branch, Forecast, LABELS

        alpha = np.full(len(LABELS), 1.0)
        probs = alpha / alpha.sum()
        branches = {}
        for own, other in ((h1, h2), (h2, h1)):
            correct, wrong = (0, 1) if own == h1 else (1, 0)
            value = float(probs[correct] - 2 * probs[wrong])
            branches[own] = Branch(own, dict(zip(LABELS, probs.tolist())), dict(zip(LABELS, alpha.tolist())),
                                   float(probs[correct]), float(probs[wrong]), value,
                                   float((probs @ np.array([1.0, 4.0, 0.0, 0.0]) - value ** 2) / 5.0),
                                   0.95, (), (), (), (), 0, 0, "constant_prior", 1.0)
        return Forecast(branches)


class ReferenceForecast(ForecastAdapter):
    backend = "sparse_value.SparseReferenceModel"
    version = "repository"

    def __init__(self, ft, params, group_map, permuted=False):
        from research.sparse_value.model import SparseReferenceModel

        self.model = SparseReferenceModel(ft, params, group_map)

    def forecast(self, target, h1, h2, *, source=None, observed_label=None):
        return self.model.forecast(target, h1, h2, source=source, observed_label=observed_label)


class PermutedForecast(ReferenceForecast):
    backend = "sparse_value.SparseReferenceModel:label_permuted_fold_tables"
    version = "repository"


class WorldRefForecast(ForecastAdapter):
    """Adapter over the belief-planning ReferenceWorld (a research reading-forecast backend).

    This is NOT WorldV2. WorldV2 (`research/dual_core_v2/world3.py`) could not be fitted within this
    run; see `NOT_RUN`.
    """

    backend = "belief_planning.world.ReferenceWorld"
    version = "repository"

    def __init__(self, world):
        self.world = world
        self.compound = None

    def forecast(self, target, h1, h2, *, source=None, observed_label=None):
        from research.sparse_value.model import Branch, Forecast, LABELS

        history = ()
        if source is not None and observed_label is not None:
            history = ((tuple(source), observed_label),)
        out = self.world.forecast(tuple(target), h1, h2, self.compound, history)
        if getattr(out, "refusal", None):
            return Forecast({}, f"world_ref:{out.refusal}")
        branches = {}
        for branch in out.branches:
            own = branch.hypothesis
            probabilities = dict(branch.probabilities)
            probs = np.array([float(probabilities.get(name, 0.0)) for name in LABELS], dtype=float)
            total = probs.sum()
            if total <= 0:
                return Forecast({}, f"world_ref:empty_distribution:{own}")
            probs = probs / total
            correct, wrong = (0, 1) if own == h1 else (1, 0)
            weights = np.zeros(len(LABELS))
            weights[correct], weights[wrong] = 1.0, -2.0
            value = float(probs @ weights)
            variance = float((probs @ (weights ** 2) - value ** 2) / (len(out.branches) + 1.0))
            branches[own] = Branch(own, dict(zip(LABELS, probs.tolist())),
                                   dict(zip(LABELS, (probs * 4.0).tolist())),
                                   float(probs[correct]), float(probs[wrong]), value, variance,
                                   float(min(1.0, probs[wrong] + 1.96 * max(variance, 0.0) ** 0.5)),
                                   (), (), (), (), 0, 0, "belief_planning_reference_world", 1.0)
        missing = [h for h in (h1, h2) if h not in branches]
        if missing:
            return Forecast({}, f"world_ref:missing_branch:{','.join(missing)}")
        return Forecast(branches)


def forecast_adapter(name: str, bundle: Bundle) -> ForecastAdapter:
    params = bundle.view.params
    group_map = {c: bundle.meta["unit_of"].get(c, c) for c in bundle.meta["unit_of"]}
    if name == "none":
        return NoneForecast()
    if name == "constant":
        return ConstantForecast(bundle.view.ft, params)
    if name == "reference":
        return ReferenceForecast(bundle.view.ft, params, group_map)
    if name == "permuted":
        return PermutedForecast(bundle.ft_perm, params, group_map)
    if name == "world_ref":
        return WorldRefForecast(bundle.reference_world)
    raise KeyError(name)


# --------------------------------------------------------------------------------- policies
def policy_callable(name: str, model: ForecastAdapter, bundle: Bundle):
    """The arm for one cell. `model` is only consulted by the policies that read a forecast."""
    from research.external_validation import arms as A
    from research.sparse_value import policy as SV

    if name == "fixed":
        return A.fixed
    if name == "baseline":
        return A.myopic_edv()
    if name == "risk_select":
        return A.sparse_two_step()
    if name == "decision_sensitive":
        return A.decision_sensitive_edv
    if name == "choose_injected":
        price = A.PRICE

        def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
            if not ctx.params["eliminates"]:
                return None, {"reason": "registered_validator_cannot_eliminate"}
            model.bind(compound)
            action, note = SV.choose(model, menu, h1, h2, executed, remaining, setting, price)
            return action, note
        return arm
    raise KeyError(name)


def _ranking(model: ForecastAdapter, compound, menu, h1, h2, setting):
    """Unconditioned expected utility of every menu action under one forecast (decision-time only)."""
    from research.sparse_value import policy as SV

    model.bind(compound)
    weights = {h1: 0.5, h2: 0.5}
    rows = []
    for key in menu:
        forecast = model.forecast(key, h1, h2)
        estimate = SV.value(forecast, weights)
        rows.append((str(key), None if estimate is None else float(estimate["utility"]),
                     None if forecast.refusal else "ok", forecast.refusal))
    ranked = sorted((r for r in rows if r[1] is not None), key=lambda r: (-r[1], r[0]))
    return {"order": [r[0] for r in ranked], "utilities": {r[0]: r[1] for r in rows},
            "refusals": {r[0]: r[3] for r in rows if r[3]},
            "refused_fraction": float(sum(1 for r in rows if r[3]) / max(len(rows), 1))}


# --------------------------------------------------------------------------------- run
def run_task(dataset: str, tier: str, folds, out: Path) -> dict:
    from research.protocol_v2 import contracts as K
    from research.protocol_v2 import runner as RN

    cells = {}
    rows = []
    for fold in folds:
        bundle = build_bundle(dataset, tier, fold)
        unit_of = bundle.meta["unit_of"]
        menu_ids = [K.C.action_id(k) for k in bundle.setting.keys]
        for forecast_name, policy_name in CELLS:
            adapter = forecast_adapter(forecast_name, bundle)
            arm = policy_callable(policy_name, adapter, bundle)
            cell = f"{forecast_name}|{policy_name}"
            for compound, truth, decoy, h1, h2 in bundle.episodes:
                adapter.bind(compound)
                trace = RN.run_episode(cell, arm, bundle.view, bundle.ctx, compound, h1, h2,
                                       bundle.setting, design_menu=True)
                score = K.score(trace, truth)
                rank = _ranking(adapter, compound, bundle.setting.keys, h1, h2, bundle.setting)
                steps = trace["steps"]
                reads_forecast = policy_name == "choose_injected" or any(
                    s.get("note", {}).get("evidence_kind") == "model_prediction" for s in steps)
                rows.append({
                    "fold": fold, "compound": compound, "unit": str(unit_of.get(compound, compound)),
                    "h1": h1, "h2": h2, "truth": truth, "forecast": forecast_name, "policy": policy_name,
                    "cell": cell, "forecast_backend": adapter.backend, "forecast_version": adapter.version,
                    "forecast_refused_fraction": rank["refused_fraction"],
                    "forecast_available": bool(rank["order"]),
                    "ranking_top1": (rank["order"][0] if rank["order"] else None),
                    "ranking_digest": _sha256(">".join(rank["order"])),
                    "first_action": (steps[0]["action"] if steps else None),
                    "second_action": (steps[1]["action"] if len(steps) > 1 else None),
                    "sequence": "|".join(s["action"] for s in steps),
                    "reads_forecast": bool(reads_forecast),
                    "prediction_entered_selector": bool(reads_forecast),
                    "prediction_entered_evidence_update": any(
                        s.get("outcome_class") == "predicted" for s in steps),
                    "realized_readings": "|".join(str(s.get("readout")) for s in steps),
                    "qc_flags": "|".join(str(bool(s.get("qc"))) for s in steps),
                    "final": score["final"], "utility": score["utility"],
                    "correct": score["correct"], "wrong": score["wrong"],
                    "measurements": trace["measurements"], "days": trace["days"],
                    "stop": trace["stop"],
                })
            print(f"{dataset}:{tier} fold {fold} {cell} done", flush=True)
    frame = pd.DataFrame(rows)
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out / "episodes.csv", index=False)
    return {"frame": frame, "menu": menu_ids}


# --------------------------------------------------------------------------------- analysis
def analyse(frame, out: Path) -> dict:
    import pandas as pd

    reference = frame[(frame.forecast == "reference")]
    anchor = reference[reference.policy == "choose_injected"].set_index(
        ["fold", "compound", "h1", "h2"])
    rows = []
    for cell, group in frame.groupby(["forecast", "policy"]):
        joined = group.set_index(["fold", "compound", "h1", "h2"])
        common = joined.index.intersection(anchor.index)
        sub, anc = joined.loc[common], anchor.loc[common]
        paired = (sub.utility - anc.utility).groupby(sub.unit).mean()
        values = paired.to_numpy()
        rng = np.random.default_rng(SEED)
        boot = np.array([values[rng.integers(0, len(values), len(values))].mean() for _ in range(2000)])
        changed_first = float((sub.first_action != anc.first_action).mean())
        changed_seq = float((sub.sequence != anc.sequence).mean())
        changed_terminal = float((sub.final != anc.final).mean())
        rows.append({
            "cell": f"{cell[0]}|{cell[1]}", "forecast": cell[0], "policy": cell[1],
            "forecast_backend": group.forecast_backend.iloc[0],
            "reads_forecast": bool(group.reads_forecast.iloc[0]),
            "forecast_available_rate": float(sub.forecast_available.mean()),
            "ranking_changed_rate": float((sub.ranking_digest != anc.ranking_digest).mean()),
            "ranking_top1_changed_rate": float((sub.ranking_top1 != anc.ranking_top1).mean()),
            "first_action_changed_rate": changed_first,
            "sequence_changed_rate": changed_seq,
            "terminal_changed_rate": changed_terminal,
            "action_changed_but_terminal_same_rate": float(
            ((sub.sequence != anc.sequence) & (sub.final == anc.final)).mean()),
            "correct": float(sub.correct.mean()), "wrong": float(sub.wrong.mean()),
            "abstention_rate": float((sub.final == "deferred").mean()),
            "measurements": float(sub.measurements.mean()), "days": float(sub.days.mean()),
            "utility": float(sub.utility.mean()),
            "paired_utility_vs_reference_cell": float(values.mean()),
            "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            "units": int(len(values)), "episodes": int(len(sub)),
        })
    cells = pd.DataFrame(rows)
    cells.to_csv(out / "cells.csv", index=False)

    # World x Policy interaction on the terminal, among cells that actually read their forecast
    usable = cells[cells.reads_forecast]
    interaction = {}
    for policy in sorted(usable.policy.unique()):
        part = usable[usable.policy == policy].set_index("forecast")
        if "reference" in part.index and "none" in part.index:
            interaction[policy] = {
            "world_effect_reference_minus_none": float(part.loc["reference", "utility"]
                                                           - part.loc["none", "utility"])}
    for forecast in sorted(usable.forecast.unique()):
        part = usable[usable.forecast == forecast].set_index("policy")
        if "baseline" in part.index and "risk_select" in part.index:
            interaction.setdefault(f"policy@forecast={forecast}", {})["risk_select_minus_baseline"] = \
            float(part.loc["risk_select", "utility"] - part.loc["baseline", "utility"])
    summary = {"cells": cells.to_dict("records"), "interaction": interaction, "not_run": NOT_RUN}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    return summary


def main() -> None:
    import pandas as pd

    parser = argparse.ArgumentParser()
    parser.add_argument("--folds", default="0")
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    folds = [int(x) for x in args.folds.split(",") if x]
    out = Path(args.out)
    for dataset, tier in TASKS:
        task_out = out / f"{dataset}_{tier}"
        result = run_task(dataset, tier, folds, task_out)
        summary = analyse(result["frame"], task_out)
        print(f"{dataset}:{tier}", json.dumps(summary["interaction"], indent=1, default=str), flush=True)


if __name__ == "__main__":
    main()
