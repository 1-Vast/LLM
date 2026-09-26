"""Run the registered arms of the prediction-to-measurement evaluation over the block-2 episodes.

File summary
- Path: research/acquisition_link/evaluate.py
- Purpose: for each fold and tier, rebuild block 2's fold tables and calibration, then run every
  arm of `protocol.json` on the same episodes, the same validator and the same evidence path, and
  score every served step-1 forecast over the whole menu for calibration.
- Core points:
  - `ReferenceCardForecaster` is the SciPlex3 forecaster: each hypothesis's branch is the
    leave-one-out validator reading of its measured training references at the condition, mapped
    to the registered outcome labels. It satisfies `maestro.acquisition.OutcomeForecaster`, so the
    orchestrator can use it unchanged; here the arms call the src selectors directly, as block 2 did.
  - What a reading eliminates comes from the same `OutcomeRule` objects `common.evidence_update`
    applies to a real result (`registered_rules`), checked by `test_acquisition_link.py`.
  - Block-2 code is imported, never edited: `common.py`, `episodes.py`.
- Run: python research/acquisition_link/evaluate.py
- Depends on: research/dynamic_world_model (common, episodes), maestro.acquisition, maestro.outcome
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "dynamic_world_model"))
sys.path.insert(0, str(ROOT / "src"))

import common as C  # noqa: E402
import episodes as E  # noqa: E402

from maestro.acquisition import (  # noqa: E402
    OutcomeBranch,
    OutcomeForecast,
    outcome_consequences,
    select_discriminating_action,
    select_expected_coverage,
)
from maestro.models import EvidenceScope  # noqa: E402
from maestro.outcome import OutcomeRule  # noqa: E402
from maestro.outcome import OutcomeClass  # noqa: E402

OUT = ROOT / "outputs" / "acquisition_link_20260926"
MATCH = {True: "profile_matches_h1", False: "profile_matches_h2"}
UNRESOLVED, ABSENT = "profile_unresolved", "no_detectable_response"
ARMS = ("cost_only", "production_before", "production_after", "magnitude", "ec_cards_2ref", "ec_cards_1ref",
        "da_2ref", "da", "da_permuted", "da_dynamic", "fixed")


def load_protocol() -> dict:
    return json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))


def frozen_hashes() -> dict[str, str]:
    return {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in ("PROTOCOL.md", "protocol.json")}


def registered_rules(h1: str, h2: str) -> tuple[OutcomeRule, ...]:
    """The rules `common.evidence_update` reads a real result with, restated so acquisition can value readings."""

    return (
        OutcomeRule("matches_h1", "profile_matches_h1", frozenset({"response_detected", "profile_matches:H1"}),
                    eliminates=frozenset({h2}), scope=EvidenceScope.MECHANISM_CONTRAST, requires_time_match=True,
                    minimum_independent_units=2),
        OutcomeRule("matches_h2", "profile_matches_h2", frozenset({"response_detected", "profile_matches:H2"}),
                    eliminates=frozenset({h1}), scope=EvidenceScope.MECHANISM_CONTRAST, requires_time_match=True,
                    minimum_independent_units=2),
        OutcomeRule("unresolved", "profile_unresolved", frozenset({"response_detected", "profile_unresolved"}),
                    scope=EvidenceScope.MEASUREMENT_FEASIBILITY),
        OutcomeRule("no_response", "no_detectable_response", frozenset({"no_detectable_response"}),
                    scope=EvidenceScope.INTERVENTION_IMPLEMENTATION),
    )


class ReferenceCardForecaster:
    """Per-hypothesis readings of measured references at each condition, read by the frozen validator."""

    name = "sciplex3_reference_cards"

    def __init__(self, ft: C.FoldTables, params: dict, *, minimum_references: int = 1, step1: tuple | None = None,
                 label: str = "v2"):
        self.ft, self.params, self.minimum, self.step1, self.label = ft, params, minimum_references, step1, label

    def forecast_key(self, key: tuple, h1: str, h2: str) -> OutcomeForecast:
        identifier = C.action_id(key)
        basis = (f"leave-one-out validator readings of measured training references, fold {self.ft.fold}, "
                 f"tier {self.ft.tier}, forecast {self.label}")
        if key not in self.ft.tables:
            return OutcomeForecast(identifier, (), basis, refusal=f"condition_not_in_reference_data:{identifier}")
        floor, margin, eliminates = self.params["floor"], self.params["margin"], self.params["eliminates"]
        outcomes = C.loo_outcomes(self.ft, key, floor, margin) if eliminates else None
        first = (C.loo_outcomes(self.ft, self.step1[0], floor, margin)
                 if self.step1 is not None and eliminates and self.step1[0] in self.ft.tables else None)
        table = self.ft.tables[key]
        branches = []
        conditioned = []
        for own, other in ((h1, h2), (h2, h1)):
            refs = [c for c, k in zip(table.names, table.klass) if k == own]
            if self.step1 is not None:
                kept = ([c for c in refs if C.STEP1_CATEGORY.get(first.get((c, other), "")) == self.step1[1]]
                        if first is not None else [])
                conditioned.append(len(kept) >= self.minimum)
                if len(kept) >= self.minimum:
                    refs = kept
            if not refs:
                return OutcomeForecast(identifier, (), basis, refusal=f"no_reference_for_hypothesis:{own}")
            if len(refs) < self.minimum:
                return OutcomeForecast(identifier, (), basis,
                                       refusal=f"too_few_references_at_condition:{own}:{len(refs)}")
            readings = [outcomes[(c, other)] for c in refs] if outcomes is not None else ["undetected"] * len(refs)
            own_label, other_label = MATCH[own == h1], MATCH[own != h1]
            counts = {own_label: readings.count("eliminate_b"), other_label: readings.count("eliminate_a"),
                      UNRESOLVED: readings.count("ambiguous"), ABSENT: readings.count("undetected")}
            branches.append(OutcomeBranch(own, {k: v / len(refs) for k, v in counts.items()}, len(refs)))
        if self.step1 is not None:
            basis += "; step-2 references conditioned on the step-1 reading" + ("" if all(conditioned) else " (fallback used)")
        return OutcomeForecast(identifier, tuple(branches), basis, model_version=f"sciplex3_reference_cards_{self.label}")

    def forecast(self, contrast, actions, evidence):
        """The `OutcomeForecaster` protocol: action identifiers are block-2 condition labels."""

        h1, h2 = (hypothesis.identifier for hypothesis in contrast.hypotheses)
        keys = {C.action_id(key): key for key in self.ft.tables}
        forecaster = self
        if self.step1 is None and evidence is not None:
            categories = {ABSENT: "undetected", UNRESOLVED: "detected_unresolved"}
            for update in reversed(evidence.updates):
                if (update.outcome_class is OutcomeClass.PREDICTED
                        and frozenset(update.candidate_hypotheses) == contrast.identifiers()
                        and update.outcome_label in categories and update.action_identifier in keys):
                    forecaster = ReferenceCardForecaster(
                        self.ft, self.params, minimum_references=self.minimum,
                        step1=(keys[update.action_identifier], categories[update.outcome_label]), label=self.label,
                    )
                    break
        return {action.identifier: (forecaster.forecast_key(keys[action.identifier], h1, h2) if action.identifier in keys else
                                    OutcomeForecast(action.identifier, (), "", refusal="condition_not_in_reference_data"))
                for action in actions}


def magnitude_priorities(ctx: E.FoldContext, compound: str, menu) -> dict[str, float]:
    out = {}
    for key in menu:
        value = ctx.magnitude.predict(compound, key)
        if value is not None:
            out[C.action_id(key)] = value
    return out


def choose_discriminating(ctx: E.FoldContext, compound, h1, h2, executed, menu, *, minimum: int, permuted: bool = False,
                          dynamic: bool = False) -> tuple:
    step1 = None
    if dynamic and executed and executed[0]["outcome"] in ("undetected", "ambiguous"):
        step1 = (executed[0]["key"], C.STEP1_CATEGORY[executed[0]["outcome"]])
    forecaster = ReferenceCardForecaster(ctx.ft_perm if permuted else ctx.ft, ctx.params, minimum_references=minimum,
                                         step1=step1)
    forecasts = {C.action_id(key): forecaster.forecast_key(key, h1, h2) for key in menu}
    actions = [E.make_action(key, h1, h2) for key in menu]
    plan = select_discriminating_action(frozenset({h1, h2}), actions, E.PROFILE, E.STEP_BUDGET_DAYS, forecasts,
                                        outcome_consequences(registered_rules(h1, h2)),
                                        action_priorities=magnitude_priorities(ctx, compound, menu))
    reasons = {}
    for item in plan.evaluations:
        reasons[item.reason] = reasons.get(item.reason, 0) + 1
    chosen = plan.chosen
    note = {"status": plan.status, "menu_reasons": reasons,
            "chosen": None if chosen is None else {k: v for k, v in chosen.payload().items() if k != "reason"},
            "low_support_menu": sum(1 for item in plan.evaluations if item.low_support)}
    if chosen is None:
        return None, {**note, "reason": "no_admissible_action"}
    return next(key for key in menu if C.action_id(key) == chosen.action_identifier), note


def choose_coverage(ctx: E.FoldContext, compound, h1, h2, executed, menu, *, with_priorities: bool) -> tuple:
    actions = [E.make_action(key, h1, h2) for key in menu]
    priorities = magnitude_priorities(ctx, compound, menu) if with_priorities else None
    plan = select_expected_coverage(frozenset({h1, h2}), actions, E.PROFILE, E.STEP_BUDGET_DAYS, action_priorities=priorities)
    if not plan.plan.actions:
        return None, {"reason": plan.status}
    chosen = plan.plan.actions[0].identifier
    return next(key for key in menu if C.action_id(key) == chosen), {"priority": (priorities or {}).get(chosen)}


def choose_cards(ctx: E.FoldContext, compound, h1, h2, executed, menu, *, minimum: int) -> tuple:
    cards = {key: C.card(ctx.ft, key, h1, h2, ctx.params, minimum_references=minimum) for key in menu}
    return E.select_by_cards(menu, cards, h1, h2)


def policies() -> dict:
    return {
        "production_before": lambda ctx, c, h1, h2, ex, menu: choose_coverage(ctx, c, h1, h2, ex, menu, with_priorities=False),
        "production_after": lambda ctx, c, h1, h2, ex, menu: choose_coverage(ctx, c, h1, h2, ex, menu, with_priorities=True),
        "ec_cards_2ref": lambda ctx, c, h1, h2, ex, menu: E.choose("separation", ctx, c, h1, h2, ex, None),
        "ec_cards_1ref": lambda ctx, c, h1, h2, ex, menu: choose_cards(ctx, c, h1, h2, ex, menu, minimum=1),
        "da_2ref": lambda ctx, c, h1, h2, ex, menu: choose_discriminating(ctx, c, h1, h2, ex, menu, minimum=2),
        "da": lambda ctx, c, h1, h2, ex, menu: choose_discriminating(ctx, c, h1, h2, ex, menu, minimum=1),
        "da_permuted": lambda ctx, c, h1, h2, ex, menu: choose_discriminating(ctx, c, h1, h2, ex, menu, minimum=1, permuted=True),
        "da_dynamic": lambda ctx, c, h1, h2, ex, menu: choose_discriminating(ctx, c, h1, h2, ex, menu, minimum=1, dynamic=True),
    }


def menu_audit(ctx: E.FoldContext, compound, truth, h1, h2) -> list[dict]:
    """Every step-1 menu action's v2 forecast against what this compound's measurement would read."""

    forecaster = ReferenceCardForecaster(ctx.ft, ctx.params, minimum_references=1)
    menu = list(ctx.tier.keys)
    forecasts = {C.action_id(key): forecaster.forecast_key(key, h1, h2) for key in menu}
    consequences = outcome_consequences(registered_rules(h1, h2))
    plan = select_discriminating_action(frozenset({h1, h2}), [E.make_action(k, h1, h2) for k in menu], E.PROFILE,
                                        1e9, forecasts, consequences)
    labels = sorted(consequences)
    rows = []
    for key in menu:
        identifier = C.action_id(key)
        evaluation = next(item for item in plan.evaluations if item.action_identifier == identifier)
        result = E.execute(ctx, compound, key, h1, h2)
        outcome = result["outcome"]
        if outcome == "quality_failed":
            realised = None
        elif outcome in ("undetected", "ambiguous"):
            realised = outcome
        else:
            eliminated = h2 if outcome == "eliminate_b" else h1
            realised = "wrong" if eliminated == truth else "correct"
        forecast = forecasts[identifier]
        truth_branch = forecast.branch_for(truth)
        p_truth = None
        if truth_branch is not None and forecast.refusal is None:
            alpha = {label: truth_branch.probabilities.get(label, 0.0) * truth_branch.support + 0.5 for label in labels}
            p_truth = alpha[MATCH[truth == h1]] / sum(alpha.values())
        rows.append({"tier": ctx.tier.name, "fold": ctx.ft.fold, "compound": compound, "truth": truth, "h1": h1, "h2": h2,
                     "action": identifier, "time": key[1], "dose": key[2], "line": key[0],
                     "served": forecast.refusal is None, "refusal": forecast.refusal,
                     "reason": evaluation.reason, "admissible": evaluation.admissible,
                     "p_correct": evaluation.p_correct, "p_wrong": evaluation.p_wrong,
                     "discrimination": evaluation.discrimination, "discrimination_lower": evaluation.discrimination_lower,
                     "total_variation": evaluation.total_variation, "support": evaluation.support,
                     "p_correct_truth_branch": p_truth, "realised": realised})
    return rows


def run_fold(task) -> tuple[list, list, dict]:
    tier_name, fold = task
    protocol = C.load_protocol()
    data = C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    magnitude = E.Magnitude(data, detected)
    records, audit, calibration = [], [], {}
    for ctx, f in E.contexts(data, protocol, detected, magnitude, tier_names=(tier_name,), folds=(fold,)):
        ctx.extra["policies"] = policies()
        calibration[f"{ctx.tier.name}|{f}"] = {k: v for k, v in ctx.params.items() if k != "grid"}
        for compound, truth, decoy, h1, h2 in E.episode_list(ctx, f):
            base = {"tier": ctx.tier.name, "fold": f, "decoy": decoy}
            for arm in ARMS:
                records.append(base | E.run_episode(arm, ctx, compound, truth, h1, h2, None))
            records.append(base | E.oracle(ctx, compound, truth, h1, h2))
            audit.extend(menu_audit(ctx, compound, truth, h1, h2))
    return records, audit, calibration


def main() -> None:
    from concurrent.futures import ProcessPoolExecutor
    import pandas as pd

    started = time.time()
    protocol = load_protocol()
    data = C.load()
    folds = sorted(int(f) for f in data.compounds.fold.unique())
    tasks = [(tier, fold) for tier in ("B", "A") for fold in folds]
    records, audit, calibration = [], [], {}
    with ProcessPoolExecutor(max_workers=min(len(tasks), 10)) as pool:
        for (tier, fold), (recs, rows, cal) in zip(tasks, pool.map(run_fold, tasks)):
            records += recs
            audit += rows
            calibration.update(cal)
            print(f"{tier} fold {fold}: {len(recs)} records, {time.time() - started:.0f}s", flush=True)
    out = OUT / "episodes"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "episodes.jsonl").open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(C.clean(record), default=C._default) + chr(10))
    pd.DataFrame(audit).to_csv(out / "menu_audit.csv", index=False)
    C.write_json(out / "manifest.json", C.clean({
        "protocol_hashes": frozen_hashes(), "protocol_version": protocol["version"], "episodes": len(records),
        "menu_rows": len(audit), "calibration": calibration, "seconds": round(time.time() - started, 1),
        "runner_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in (
            ("evaluate.py", HERE / "evaluate.py"), ("common.py", C.HERE / "common.py"),
            ("episodes.py", C.HERE / "episodes.py"), ("acquisition.py", ROOT / "src" / "maestro" / "acquisition.py"))}}))
    print(f"episodes {len(records)}, menu rows {len(audit)}, {time.time() - started:.0f}s", flush=True)


if __name__ == "__main__":
    main()
