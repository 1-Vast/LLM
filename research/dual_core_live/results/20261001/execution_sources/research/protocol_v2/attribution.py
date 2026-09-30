"""Decision gates for the virtual cell and for feedback: action change is not decision value.

File summary
- Path: research/protocol_v2/attribution.py
- Purpose: decide, from matched records, whether the virtual-cell channel or the real-reading
  feedback channel earns a place in a default planner. Both must pass the whole chain:
  action change, then terminal decision change, then an independent terminal correctness gain,
  with no increase in wrong decisions or measurement cost.
- Core points:
  - Virtual cell (`vc_gate`): the current planner (`belief`) against the same planner with the
    structural kernel masked (`belief_vc_masked`) and with another compound's structure
    (`belief_vc_permuted`). Reported overall, by structural applicability (nearest training
    Tanimoto), and by scaffold overlap with the fold's training compounds. L1000 folds are
    identity/scaffold components, so every L1000 tier is scaffold-held-out by construction.
  - Feedback (`feedback_gate`): real readings against withheld readings (the agent knows only
    that a measurement ran and removed nothing) and against another compound's compatible real
    reading. The first-measurement-matched subset (same first action, both took a second) is
    reported, and flagged as descriptive: "the second action changed" is a post-treatment
    selection, not a causal contrast. Horizon: two-step against one-step lookahead.
  - A three-step horizon, a study-held-out virtual cell and stochastic-logging off-policy
    estimates need data or tasks this repository does not have; `BLOCKED` names them.
  - Verdicts (pre-registered in `protocol.json`):
    - `KEEP`: action change > 0, decision change > 0, correct gain >= MPIE with a lower 95%
      bound above 0 against every control, wrong difference upper bound <= 0.005, measurement
      difference upper bound <= 0.10.
    - `REJECT_AS_DEFAULT`: correct-gain upper bound below the MPIE against the main control.
    - `INCONCLUSIVE` otherwise. Anything short of `KEEP` stays an audit or research feature.
- Run: python -m research.protocol_v2.attribution --out FILE
- Interfaces: `chain`, `vc_gate`, `feedback_gate`, `verdict`, `BLOCKED`
- Depends on: records.py, research/external_validation/statistics.py, research/belief_planning/tasks.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.external_validation import statistics as S

from . import records as RC

MPIE, WRONG_NI, COST_NI = 0.02, 0.005, 0.10
VC_ARMS = ("belief", "belief_vc_masked", "belief_vc_permuted")
FEEDBACK_ARMS = ("belief", "belief_feedback_withheld", "belief_feedback_permuted", "belief_h1")
DEV = Path("outputs/belief_planning_20260927/registered/dev")
EXTERNAL = Path("outputs/belief_planning_20260927/external/records.jsonl.gz")
BLOCKED = {
    "three_step_horizon": "every registered task allows at most two measurements and ends at the first elimination; "
                          "a confirmation step needs a new task definition (protocol v2 section 8)",
    "study_held_out_virtual_cell": "a Phase I reference library for a Phase II task yields 96 development episodes "
                                   "(belief_planning phase1_line_task_feasibility), too few to estimate a gain",
    "stochastic_logging_ope": "every registered policy is deterministic, so no alternative action has a positive "
                              "logging propensity; the full condition tables allow exact counterfactual replay "
                              "instead, which this package uses",
}


def _paired(frame, left, right, metric):
    sub = frame[frame.arm.isin((left, right))].copy()
    sub["policy"] = sub.arm
    sub["compound"] = sub.fold.astype(str) + ":" + sub.compound
    return S.paired(sub, left, right, metric, "unit")


def chain(frame: pd.DataFrame, real: str, control: str) -> dict:
    """Action change -> decision change -> correct, wrong and cost differences, on identical episodes."""
    a = frame[frame.arm == real].set_index("episode")
    b = frame[frame.arm == control].set_index("episode").reindex(a.index)
    action = a.sequence != b.sequence
    decision = a.final != b.final
    out = {"episodes": int(len(a)), "units": int(a.unit.nunique()),
           "action_change_rate": float(action.mean()), "decision_change_rate": float(decision.mean()),
           "decision_change_given_action_change": float(decision[action].mean()) if action.any() else 0.0,
           "correct_on_changed_real": float(a.correct[action].mean()) if action.any() else None,
           "correct_on_changed_control": float(b.correct[action].mean()) if action.any() else None}
    for metric in ("correct", "wrong", "measurements", "days"):
        out[metric] = _paired(frame, real, control, metric)
    return out


def verdict(main: dict, others: list[dict]) -> str:
    def passes(c):
        return (c["action_change_rate"] > 0 and c["decision_change_rate"] > 0
                and c["correct"]["difference"] >= MPIE and c["correct"]["ci"][0] > 0
                and c["wrong"]["ci"][1] <= WRONG_NI and c["measurements"]["ci"][1] <= COST_NI)
    if passes(main) and all(o["correct"]["ci"][0] > 0 for o in others):
        return "KEEP"
    if main["correct"]["ci"][1] < MPIE:
        return "REJECT_AS_DEFAULT"
    return "INCONCLUSIVE"


def _applicability(t) -> str:
    if t is None or (isinstance(t, float) and np.isnan(t)):
        return "no_structure"
    return "<0.30" if t < 0.30 else "0.30-0.40" if t < 0.40 else "0.40-0.60" if t < 0.60 else ">=0.60"


def attach_features(frame: pd.DataFrame, features: pd.DataFrame, scaffolds: dict) -> pd.DataFrame:
    """Nearest-training Tanimoto per (tier, compound), and scaffold overlap with the fold's training set."""
    sim = {(str(r.tier), str(r.compound)): float(r.max_train_tanimoto) for r in features.itertuples()}
    frame = frame.copy()
    frame["max_train_tanimoto"] = [sim.get((str(t), str(c)), float("nan")) for t, c in zip(frame.tier, frame.compound)]
    frame["applicability"] = frame.max_train_tanimoto.map(_applicability)
    overlap = []
    for (tier, fold), g in frame.groupby(["tier", "fold"]):
        train = {scaffolds.get(c) for c in frame[(frame.tier == tier) & (frame.fold != fold)].compound.unique()}
        train.discard(None)
        for idx, c in zip(g.index, g.compound):
            s = scaffolds.get(c)
            overlap.append((idx, "no_scaffold" if not s else ("scaffold_seen" if s in train else "scaffold_held_out")))
    frame["scaffold_overlap"] = pd.Series(dict(overlap))
    return frame


def _strata(frame, real, control, column) -> dict:
    out = {}
    for value, g in frame.groupby(column):
        if g[g.arm == real].unit.nunique() < 5:
            out[value] = {"units": int(g[g.arm == real].unit.nunique()), "status": "too_few_units"}
            continue
        c = chain(g, real, control)
        out[value] = {"units": c["units"], "episodes": c["episodes"], "action_change_rate": c["action_change_rate"],
                      "decision_change_rate": c["decision_change_rate"], "correct": c["correct"],
                      "wrong": c["wrong"], "descriptive_only": c["units"] < 50}
    return out


def vc_gate(frame: pd.DataFrame) -> dict:
    out = {}
    for (dataset, tier), g in frame.groupby(["dataset", "tier"]):
        if not set(VC_ARMS) <= set(g.arm):
            continue
        masked, permuted = chain(g, "belief", "belief_vc_masked"), chain(g, "belief", "belief_vc_permuted")
        out[f"{dataset}:{tier}"] = {
            "vs_masked": masked, "vs_permuted": permuted,
            "permuted_vs_masked": chain(g, "belief_vc_permuted", "belief_vc_masked")["correct"],
            "by_applicability": _strata(g, "belief", "belief_vc_masked", "applicability"),
            "by_scaffold_overlap": _strata(g, "belief", "belief_vc_masked", "scaffold_overlap"),
            "verdict": verdict(masked, [permuted])}
    return out


def matched_second_step(frame: pd.DataFrame, real: str, control: str) -> dict:
    a = frame[frame.arm == real].set_index("episode")
    b = frame[frame.arm == control].set_index("episode").reindex(a.index)
    both = (a.first_action == b.first_action) & a.second_action.notna() & b.second_action.notna()
    switched = both & (a.second_action != b.second_action)
    return {"matched_first_both_second": int(both.sum()), "second_action_switched": int(switched.sum()),
            "switch_rate": float(switched.sum() / max(both.sum(), 1)),
            "correct_switched_real": float(a.correct[switched].mean()) if switched.any() else None,
            "correct_switched_control": float(b.correct[switched].mean()) if switched.any() else None,
            "correct_matched_real": float(a.correct[both].mean()) if both.any() else None,
            "correct_matched_control": float(b.correct[both].mean()) if both.any() else None,
            "status": "descriptive: the switch is a post-treatment selection"}


def feedback_gate(frame: pd.DataFrame) -> dict:
    out = {}
    for (dataset, tier), g in frame.groupby(["dataset", "tier"]):
        if not set(FEEDBACK_ARMS) <= set(g.arm):
            continue
        withheld = chain(g, "belief", "belief_feedback_withheld")
        permuted = chain(g, "belief", "belief_feedback_permuted")
        out[f"{dataset}:{tier}"] = {
            "vs_withheld": withheld, "vs_permuted": permuted,
            "first_measurement_matched": matched_second_step(g, "belief", "belief_feedback_withheld"),
            "two_step_vs_one_step": chain(g, "belief", "belief_h1"),
            "verdict": verdict(withheld, [permuted])}
    return out


def load_frame(path: Path, features_path: Path, dataset: str | None = None) -> pd.DataFrame:
    from research.belief_planning import tasks as T
    frame = RC.load(path, tuple(set(VC_ARMS) | set(FEEDBACK_ARMS)))
    features = pd.read_csv(features_path) if features_path.is_file() else pd.DataFrame(
        columns=["tier", "compound", "max_train_tanimoto"])
    scaffolds = {}
    for ds in sorted(set(frame.dataset.dropna())):
        if ds in ("sciplex3", "l1000"):
            units = T.units(ds)
            scaffolds.update({str(c): (s if isinstance(s, str) and s else None)
                              for c, s in units["murcko_scaffold"].items()})
    return attach_features(frame, features, scaffolds)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    results = {"blocked": BLOCKED, "vc": {}, "feedback": {}}
    for path, feats in ((DEV, DEV / "compound_features.csv"), (EXTERNAL, EXTERNAL.parent / "compound_features.csv")):
        if not path.exists():
            continue
        frame = load_frame(path, feats)
        results["vc"].update(vc_gate(frame))
        results["feedback"].update(feedback_gate(frame))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_bytes(json.dumps(results, indent=1, default=float).encode("utf-8"))
    for name, r in results["vc"].items():
        m = r["vs_masked"]
        print("VC", name, f"action {m['action_change_rate']:.3f} decision {m['decision_change_rate']:.3f} "
              f"correct {m['correct']['difference']:+.3f} [{m['correct']['ci'][0]:+.3f},{m['correct']['ci'][1]:+.3f}] "
              f"-> {r['verdict']}")
    for name, r in results["feedback"].items():
        m = r["vs_withheld"]
        h = r["two_step_vs_one_step"]["correct"]
        print("FB", name, f"action {m['action_change_rate']:.3f} decision {m['decision_change_rate']:.3f} "
              f"correct {m['correct']['difference']:+.3f} [{m['correct']['ci'][0]:+.3f},{m['correct']['ci'][1]:+.3f}] "
              f"2v1 {h['difference']:+.3f} [{h['ci'][0]:+.3f},{h['ci'][1]:+.3f}] -> {r['verdict']}")


if __name__ == "__main__":
    main()
