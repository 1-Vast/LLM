"""Unified scoring of the frozen e_data1 replay under one scorer, four rules, with coverage bounds.

File summary
- Path: research/identifiability_audit/unified_score.py
- Purpose: recompute the frozen protocol-v2.1 SciPlex3 B and L1000 LT replay diagnostics with one
  legal menu, one decoy rule, one QC semantics, one endpoint and one cost, and to separate the two
  components the original headroom number mixed: action choice and abstention.
- Core points:
  - Four conditions: `fixed` and the diagnostic `oracle`, each under `must_act` and `may_abstain`.
    The original `table_oracle` already starts from the empty sequence, so the registered
    oracle-minus-fixed number is oracle-may-abstain minus fixed-must-act.
  - The fixed abstention rule uses only decision-time information: the fold's training-fold
    reference tables and the episode's hypothesis pair. It abstains when the first condition of the
    fixed sequence has no detected reference template for one of the two hypotheses.
  - A missing biological result is never skipped silently and never filled by a model. Every
    assignment of the missing readings is enumerated and the policy difference is reported as a
    joint lower and upper bound over those assignments.
  - Abstention is decomposed rather than characterised in one sentence: the report records each
    arm's own utility change under abstention (not only the change in the gap), because a widening
    gap can come from abstention damaging `fixed` rather than from extra action-choice headroom.
  - The historical +0.0702, +0.0473 and -0.192 numbers are copied into the output as
    `original_protocol_replay` and are never recomputed or overwritten.
- Run: python -m research.identifiability_audit.unified_score [--out DIR]
- Interfaces: `UTILITY`, `simulate`, `oracle_sequence`, `task_report`, `main`
- Depends on: research/protocol_v2/{e_data1,tasks_v21,contracts,design}.py, numpy, pandas
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "identifiability_audit_20260930" / "unified_score"
E_DATA1 = ROOT / "outputs" / "protocol_v2_1_20260927" / "e_data1"
CASE_MEMORY = ROOT / "outputs" / "case_memory_integration" / "results.json"

UTILITY = {"correct": 1.0, "wrong": -2.0, "exhausted": -2.0, "undetermined": 0.0, "deferred": 0.0}
TASKS = (("sciplex3", "B"), ("l1000", "LT"))


# --------------------------------------------------------------------------------- frozen replay data
def _tables(dataset_tier: str) -> list:
    rows = []
    for path in sorted((E_DATA1 / "tables").glob(f"{dataset_tier}_*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle)
    return rows


def _action_id(key) -> str:
    """The frozen protocol's action identifier: `line|024h|00010nM`."""
    from research.protocol_v2.contracts import C

    return key if isinstance(key, str) else C.action_id(tuple(key))


def simulate(row: dict, sequence, outcome_of: dict | None = None) -> dict:
    """Terminal decision of following `sequence` on one episode's outcome table.

    A QC failure or a non-eliminating reading continues to the next key, as the frozen runner does.
    `outcome_of` overrides named action readings when enumerating missing-result assignments.
    """
    h1, h2, truth = row["h1"], row["h2"], row["truth"]
    steps, eliminated = 0, None
    for key in sequence:
        entry = row["outcomes"].get(_action_id(key))
        if entry is None:
            continue
        steps += 1
        outcome = (outcome_of or {}).get(_action_id(key), entry["outcome"])
        if outcome in ("eliminate_a", "eliminate_b") and (
                outcome_of is not None or entry["lifecycle"] == "measured_valid"):
            eliminated = h1 if outcome == "eliminate_a" else h2
            break
    if not steps:
        final = "deferred"
    elif eliminated is None:
        final = "undetermined"
    else:
        final = "correct" if eliminated != truth else "wrong"
    return {"final": final, "measurements": steps}


def oracle_sequence(row: dict, sequences, days: dict, allow_abstain: bool):
    """Best utility, then fewest days, then fewest measurements, over full-menu sequences."""
    best = ((0.0, 0.0, 0.0), ()) if allow_abstain else ((-np.inf, -np.inf, -np.inf), None)
    for seq in sequences:
        result = simulate(row, seq)
        if result["measurements"] != len(seq):
            continue
        spent = sum(days[_action_id(k)] for k in seq)
        candidate = (UTILITY[result["final"]], -spent, -len(seq))
        if candidate > best[0]:
            best = (candidate, seq)
    return best[1] if best[1] is not None else ()


# --------------------------------------------------------------------------------- decision-time evidence
def template_counts(fold_tables, key: tuple, classes) -> dict:
    """Detected training reference templates per class at one condition (decision-time information)."""
    table = fold_tables.tables.get(tuple(key))
    if table is None:
        return {k: 0 for k in classes}
    detected = np.asarray(table.detected, dtype=bool)
    klass = np.asarray(table.klass, dtype=object)
    return {k: int(((klass == k) & detected).sum()) for k in classes}


# --------------------------------------------------------------------------------- per-task report
def task_report(dataset: str, tier: str) -> dict:
    from research.protocol_v2 import contracts as K
    from research.protocol_v2 import e_data1 as ED
    from research.protocol_v2 import tasks_v21 as V

    name = f"{dataset}_{tier}"
    rows = _tables(name)
    settings = json.loads((E_DATA1 / "manifest.json").read_text(encoding="utf-8"))["settings"][name]
    keys = [tuple(k) for k in settings["keys"]]
    days = {_action_id(k): float(v) for k, v in settings["days"].items()}
    budget = float(settings["budget_days"])
    max_measurements = int(settings["max_measurements"])
    sequences = ED.legal_sequences(keys, days, budget, max_measurements)

    # decision-time reference availability, one pass per fold
    contexts = {}
    for fold in sorted({int(r["fold"]) for r in rows}):
        _data, ctx, _setting, _design = V.load(dataset, tier, fold)
        contexts[fold] = ctx

    def abstains(row, sequence) -> bool:
        if not sequence:
            return True
        ctx = contexts[int(row["fold"])]
        counts = template_counts(ctx.ft, sequence[0], (row["h1"], row["h2"]))
        return min(counts.values()) == 0

    sequences_by_episode = {}
    for row in rows:
        key = (row["compound"], row["h1"], row["h2"], row["fold"])
        sequences_by_episode[key] = ED.table_oracle(row, sequences, days)  # original, abstain-allowed

    fixed_choice = ED.fixed_star(rows, sequences)  # cross-fitted, as in the frozen protocol

    def fixed_sequence(row):
        return fixed_choice[int(row["fold"])]

    records = []
    for row in rows:
        episode = f"{tier}|{row['fold']}|{row['compound']}|{row['h1']}|{row['h2']}"
        seq_fixed = fixed_sequence(row)
        seq_oracle_abs = sequences_by_episode[(row["compound"], row["h1"], row["h2"], row["fold"])]
        seq_oracle = oracle_sequence(row, sequences, days, allow_abstain=False)
        fixed_abstains = abstains(row, seq_fixed)
        chosen = {
            "fixed_must_act": seq_fixed,
            "fixed_may_abstain": () if fixed_abstains else seq_fixed,
            "oracle_must_act": seq_oracle,
            "oracle_may_abstain": seq_oracle_abs,
        }
        for arm, seq in chosen.items():
            result = simulate(row, seq)
            records.append({"arm": arm, "episode": episode, "unit": str(row["unit"]),
                            "fold": int(row["fold"]), "compound": row["compound"],
                            "final": result["final"], "utility": UTILITY[result["final"]],
                            "correct": float(result["final"] == "correct"),
                            "wrong": float(result["final"] in ("wrong", "exhausted")),
                            "undetermined": float(result["final"] == "undetermined"),
                            "deferred": float(result["final"] == "deferred"),
                            "measurements": result["measurements"],
                            "days": sum(days[_action_id(k)] for k in seq)})
    frame = pd.DataFrame(records)
    arms = {arm: _rate(frame[frame.arm == arm]) for arm in sorted(frame.arm.unique())}

    # ------------------------------------------------------------------ coverage and missing-result bounds
    missing = {}
    for row in rows:
        cells = [a for a, v in row["outcomes"].items() if v["lifecycle"] != "measured_valid"]
        if cells:
            missing[(row["compound"], row["h1"], row["h2"], row["fold"])] = cells
    coverage = {
        "episodes": int(len(rows)),
        "menu_actions": int(len(keys)),
        "episode_action_cells": int(len(rows) * len(keys)),
        "actions_absent_from_table": 0,
        "results_unusable": int(sum(len(v) for v in missing.values())),
        "episodes_with_unusable_result": int(len(missing)),
        "policy_reachable_branches": {"fixed": "the cross-fitted fixed sequence (1-2 keys)",
                                      "oracle": "every ordered sequence of <= "
                                                f"{max_measurements} keys within the {budget:g}-day budget"},
    }
    bounds = _missing_bounds(rows, missing, fixed_sequence, sequences_by_episode, sequences, days, abstains)

    must, allow = _paired(frame, "oracle_must_act", "fixed_must_act"), \
        _paired(frame, "oracle_may_abstain", "fixed_may_abstain")
    abstention = {
        "oracle_own_utility_change": _paired(frame, "oracle_may_abstain", "oracle_must_act"),
        "fixed_own_utility_change": _paired(frame, "fixed_may_abstain", "fixed_must_act"),
        "oracle_own_correct_change": _paired(frame, "oracle_may_abstain", "oracle_must_act", "correct"),
        "fixed_own_correct_change": _paired(frame, "fixed_may_abstain", "fixed_must_act", "correct"),
        "gap_change_must_act_to_abstain_allowed": float(allow["difference"] - must["difference"]),
    }
    cost = {
        "oracle_measurements_change": _paired(frame, "oracle_may_abstain", "oracle_must_act", "measurements"),
        "fixed_measurements_change": _paired(frame, "fixed_may_abstain", "fixed_must_act", "measurements"),
        "oracle_days_change": _paired(frame, "oracle_may_abstain", "oracle_must_act", "days"),
        "fixed_days_change": _paired(frame, "fixed_may_abstain", "fixed_must_act", "days"),
    }

    report = {
        "task": f"{dataset}:{tier}",
        "menu": [_action_id(k) for k in keys],
        "budget_days": budget,
        "max_measurements": max_measurements,
        "cost_model": "days per condition key (SciPlex3: 6 days; L1000: time_h/24 + 5 days)",
        "endpoint": "utility correct +1, wrong/exhausted -2, undetermined/deferred 0",
        "arms": arms,
        "within_rule_action_gap": must,
        "within_rule_action_gap_abstain_allowed": allow,
        "within_policy_abstention_gap_fixed": abstention["fixed_own_utility_change"],
        "within_policy_abstention_gap_oracle": abstention["oracle_own_utility_change"],
        "within_rule_action_gap_correct_rate": _paired(frame, "oracle_must_act", "fixed_must_act", "correct"),
        "within_rule_action_gap_correct_rate_abstain_allowed":
            _paired(frame, "oracle_may_abstain", "fixed_may_abstain", "correct"),
        "abstention_decomposition": abstention,
        "abstention_cost_change": cost,
        "abstention_cost_change_fixed": _paired(frame, "fixed_may_abstain", "fixed_must_act", "measurements"),
        "abstention_cost_change_oracle": _paired(frame, "oracle_may_abstain", "oracle_must_act", "measurements"),
        "coverage": coverage,
        "missing_result_bounds": bounds,
        "units": int(frame.unit.nunique()),
    }
    return report


def _rate(frame: pd.DataFrame) -> dict:
    def unit_mean(metric):
        return float(frame.groupby("unit")[metric].mean().mean())
    return {"correct_unit_mean": unit_mean("correct"), "correct_episode_mean": float(frame.correct.mean()),
            "wrong_unit_mean": unit_mean("wrong"), "wrong_episode_mean": float(frame.wrong.mean()),
            "undetermined_unit_mean": unit_mean("undetermined"),
            "undetermined_episode_mean": float(frame.undetermined.mean()),
            "deferred_unit_mean": unit_mean("deferred"),
            "deferred_episode_mean": float(frame.deferred.mean()),
            "utility_unit_mean": unit_mean("utility"),
            "utility_episode_mean": float(frame.utility.mean()),
            "measurements_episode_mean": float(frame.measurements.mean()),
            "days_episode_mean": float(frame.days.mean()),
            "episodes": int(len(frame))}


def _paired(frame: pd.DataFrame, left: str, right: str, metric: str = "utility") -> dict:
    """Unit-paired difference of `metric`, with a unit-cluster bootstrap interval."""
    a = frame[frame.arm == left].set_index("episode")
    b = frame[frame.arm == right].set_index("episode").reindex(a.index)
    diff = (a[metric] - b[metric]).groupby(a.unit).mean()
    values = diff.to_numpy()
    rng = np.random.default_rng(20260930)
    boot = np.array([values[rng.integers(0, len(values), len(values))].mean() for _ in range(2000)])
    return {"left": left, "right": right, "metric": metric, "weighting": "unit_mean",
            "difference": float(values.mean()),
            "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            "units": int(len(values))}


def _missing_bounds(rows, missing, fixed_sequence, oracle_by_episode, sequences, days, abstains) -> dict:
    """Joint lower/upper bound on oracle-minus-fixed utility over every assignment of missing readings.

    The assignment is shared by both policies: the missing reading is one fact about the world, not
    two independent unknowns. Each missing cell may resolve to eliminate_a, eliminate_b, or to a
    non-eliminating reading (which continues the sequence).
    """
    if not missing:
        return {"episodes_with_unusable_result": 0, "assignments": 0,
                "difference_lower_bound": None, "difference_upper_bound": None,
                "note": "no unusable result on any policy-reachable branch"}

    def difference(row, assignment):
        episode_key = (row["compound"], row["h1"], row["h2"], row["fold"])
        override = dict(zip(missing.get(episode_key, ()), assignment))
        oracle = UTILITY[simulate(row, oracle_by_episode[episode_key], override)["final"]]
        fixed = UTILITY[simulate(row, fixed_sequence(row), override)["final"]]
        return oracle - fixed

    lows, highs = [], []
    for row in rows:
        episode_key = (row["compound"], row["h1"], row["h2"], row["fold"])
        cells = missing.get(episode_key)
        if not cells:
            lows.append(difference(row, ()))
            highs.append(difference(row, ()))
            continue
        options = [("eliminate_a", "eliminate_b", "undetected")] * len(cells)
        values = [difference(row, assignment) for assignment in itertools.product(*options)]
        lows.append(float(min(values)))
        highs.append(float(max(values)))
    lows, highs = np.array(lows), np.array(highs)
    unit = [str(r["unit"]) for r in rows]
    series = pd.DataFrame({"unit": unit, "lo": lows, "hi": highs})
    lo = series.groupby("unit").lo.mean().mean()
    hi = series.groupby("unit").hi.mean().mean()
    return {"episodes_with_unusable_result": int(len(missing)),
            "unusable_result_cells": int(sum(len(v) for v in missing.values())),
            "assignments_per_episode": 3,
            "difference_lower_bound": float(lo), "difference_upper_bound": float(hi),
            "crosses_zero": bool(lo < 0 < hi),
            "note": "worst and best resolution of every unusable reading, shared by both policies"}


# --------------------------------------------------------------------------------- case memory
def case_memory_report() -> dict:
    """Coverage and a decoy-unified recomputation of the frozen case-memory decision level.

    The frozen replay scores `fixed` against the first sorted decoy while its `oracle` requires the
    condition to beat every decoy; that asymmetry alone can produce a negative oracle-minus-fixed
    number. Both decoy aggregations are recomputed here, on the same readings and the same endpoint.
    """
    from research.case_memory_integration import external_replay as ER

    pack, arrays = ER.load_pack()
    pool = pack["pool"]
    units = pack["units"]
    test = sorted(b for b, u in units.items() if u["unseen"])

    thresholds = {}
    reference = sorted(b for b, u in units.items() if not u["unseen"])
    for cell in ER.CORE_CELL_LINES:
        norms = [float(np.linalg.norm(arrays[f"vec::{b}::{cell}"])) for b in reference
                 if f"vec::{b}::{cell}" in arrays]
        thresholds[cell] = float(np.percentile(norms, ER.DETECTION_PERCENTILE)) if norms else 0.0

    def centroid(klass, cell, exclude=None):
        members = [b for b, u in units.items() if not u["unseen"] and u["moa"] == klass and b != exclude
                   and f"vec::{b}::{cell}" in arrays]
        return np.mean([arrays[f"vec::{b}::{cell}"] for b in members], axis=0) if members else None

    CODES = {0: "correct", 1: "wrong", 2: "undetermined", 3: "deferred"}

    def reading(unit, cell, own, decoy):
        co, cd = centroid(own, cell), centroid(decoy, cell)
        if co is None or cd is None:
            return "undetermined"
        return CODES[ER._reading(arrays[f"vec::{unit}::{cell}"], co, cd, thresholds[cell])]

    # reference readings: the decision-time evidence a policy may use (reference blocks only)
    ref_codes: list[int] = []
    for block in reference:
        own = units[block]["moa"]
        for cell in units[block]["conditions"]:
            co = centroid(own, cell, exclude=block)
            if co is None:
                continue
            for decoy in pool:
                if decoy == own:
                    continue
                cd = centroid(decoy, cell)
                if cd is None:
                    continue
                ref_codes.append(ER._reading(arrays[f"vec::{block}::{cell}"], co, cd, thresholds[cell]))

    def pooled(codes):
        counts = np.full(4, 0.5)
        for code in codes:
            counts[code] += 1.0
        return counts / counts.sum()

    def resolve(cell, decoy_set) -> str:
        """Terminal of one measurement: correct only if own beats every decoy in the set."""
        outcomes = [reading(unit_of_cell, cell, own_of_cell, d) for d in decoy_set]
        if "wrong" in outcomes:
            return "wrong"
        if all(o == "correct" for o in outcomes):
            return "correct"
        return "undetermined"

    rows = []
    for unit in test:
        own_of_cell = units[unit]["moa"]
        unit_of_cell = unit
        menu = list(units[unit]["conditions"])
        decoys = sorted(d for d in pool if d != own_of_cell)
        for aggregation in ("first_decoy", "all_decoys"):
            decoy_set = decoys[:1] if aggregation == "first_decoy" else decoys
            if not menu:
                for arm in ("fixed_must_act", "fixed_may_abstain", "oracle_must_act", "oracle_may_abstain"):
                    rows.append({"arm": f"{arm}|{aggregation}", "unit": unit, "final": "deferred"})
                continue
            fixed_cell = next((c for c in ER.CORE_CELL_LINES if c in menu), menu[0])
            rows.append({"arm": f"fixed_must_act|{aggregation}", "unit": unit,
                         "final": resolve(fixed_cell, decoy_set)})
            # fixed abstention rule: decision-time mechanism-prior forecast of the pooled reference
            # readings at the fixed cell; abstain when the expected utility is not positive.
            prior = pooled(ref_codes)
            expected = float(prior[0]) - 2.0 * float(prior[1])
            rows.append({"arm": f"fixed_may_abstain|{aggregation}", "unit": unit,
                         "final": ("deferred" if expected <= 0 else resolve(fixed_cell, decoy_set))})
            outcomes = [resolve(cell, decoy_set) for cell in menu]
            forced = ("correct" if "correct" in outcomes else
                      "undetermined" if "undetermined" in outcomes else "wrong")
            rows.append({"arm": f"oracle_must_act|{aggregation}", "unit": unit, "final": forced})
            rows.append({"arm": f"oracle_may_abstain|{aggregation}", "unit": unit,
                         "final": ("correct" if "correct" in outcomes else "deferred")})
    frame = pd.DataFrame(rows)
    frame["utility"] = frame["final"].map(UTILITY)
    out = {}
    for arm, group in frame.groupby("arm"):
        out[arm] = {"correct": float((group.final == "correct").mean()),
                    "wrong": float((group.final == "wrong").mean()),
                    "deferred": float((group.final == "deferred").mean()),
                    "undetermined": float((group.final == "undetermined").mean()),
                    "utility_mean": float(group.utility.mean()), "episodes": int(len(group))}
    gaps = {}
    for aggregation in ("first_decoy", "all_decoys"):
        def series(arm):
            return frame[frame.arm == f"{arm}|{aggregation}"].set_index("unit").utility
        fixed, oracle_abs, oracle_act, fixed_abs = (series(a) for a in
                                                    ("fixed_must_act", "oracle_may_abstain",
                                                     "oracle_must_act", "fixed_may_abstain"))
        index = fixed.index
        gaps[f"oracle_must_act_minus_fixed_must_act|{aggregation}"] = \
            float((oracle_act.reindex(index) - fixed).mean())
        gaps[f"oracle_may_abstain_minus_fixed_may_abstain|{aggregation}"] = \
            float((oracle_abs.reindex(index) - fixed_abs.reindex(index)).mean())
        gaps[f"abstention_gap_oracle|{aggregation}"] = float((oracle_abs - oracle_act.reindex(index)).mean())
        gaps[f"abstention_gap_fixed|{aggregation}"] = float((fixed_abs.reindex(index) - fixed).mean())
        gaps[f"decoy_aggregation_gap_at_frozen_rules|{aggregation}"] = \
            float((oracle_abs.reindex(index) - fixed).mean())
    menu_sizes = sorted({len(units[b]["conditions"]) for b in test})
    return {
        "task": "case_memory:lincs2020_unseen",
        "menu_sizes_per_unit": menu_sizes,
        "menu_cells_total": int(sum(len(units[b]["conditions"]) for b in test)),
        "menu_size_histogram": {str(size): int(sum(1 for b in test if len(units[b]["conditions"]) == size))
                                for size in menu_sizes},
        "units_with_one_action": int(sum(1 for b in test if len(units[b]["conditions"]) == 1)),
        "test_units": int(len(test)),
        "coverage": {"menu_is_per_unit": True,
                     "max_measurements": 1,
                     "note": "the frozen replay allows one measurement per unit; the menu is the "
                             "unit's available cell lines, so most units have no action choice at all"},
        "arms": out,
        "gaps": gaps,
        "decoy_aggregation_note": ("the frozen fixed arm scores the first sorted decoy while its oracle "
                                   "requires every decoy to be beaten; recomputing both under one "
                                   "aggregation removes that asymmetry"),
    }


# --------------------------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    analysis = json.loads((E_DATA1 / "analysis.json").read_text(encoding="utf-8"))
    case_results = json.loads(CASE_MEMORY.read_text(encoding="utf-8"))
    original = {
        "sciplex3:B": {"oracle_minus_fixed_star_correct": analysis["tiers"]["sciplex3:B"]["headroom_vs_fixed_star"],
                       "rule": "oracle may abstain minus fixed forced to act (protocol v2.1 as registered)"},
        "l1000:LT": {"oracle_minus_fixed_star_correct": analysis["tiers"]["l1000:LT"]["headroom_vs_fixed_star"],
                     "rule": "oracle may abstain minus fixed forced to act (protocol v2.1 as registered)"},
        "case_memory:lincs2020_unseen": {
            "oracle_minus_fixed_correct": case_results["oracle_headroom_correct"],
            "rule": "frozen replay: oracle requires every decoy beaten; fixed scores the first sorted decoy"},
    }

    reports = {"original_protocol_replay": original, "tasks": {}}
    for dataset, tier in TASKS:
        reports["tasks"][f"{dataset}:{tier}"] = task_report(dataset, tier)
        print(f"{dataset}:{tier} done", flush=True)
    reports["tasks"]["case_memory:lincs2020_unseen"] = case_memory_report()
    (out / "unified_score.json").write_text(json.dumps(reports, indent=1, default=str), encoding="utf-8")
    print(json.dumps(reports["tasks"], indent=1, default=str))


if __name__ == "__main__":
    main()
