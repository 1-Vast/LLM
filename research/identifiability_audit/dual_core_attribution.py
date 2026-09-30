"""Forecast/policy attribution on the frozen e_data1 traces, without a new model or planner.

File summary
- Path: research/identifiability_audit/dual_core_attribution.py
- Purpose: on the frozen protocol-v2.1 episodes, hold the task, menu, budget, stopping rule and
  scorer fixed and attribute every difference from `fixed` to (i) a changed first action,
  (ii) a changed later action, (iii) abstention, or (iv) terminal luck. No model is trained, no
  readout is developed and no planner is changed: every arm is the code the frozen run executed.
- Core points:
  - The frozen arms split by whether they consult a forecast: `fixed` and `random_legal` do not;
    `myopic_edv`, `belief` and `safe` consult a model built only from the fold's *training*
    compounds; `oracle` reads the held-out outcome and is diagnostic only.
  - No frozen arm receives a decision-time measurement of the held-out compound. The protocol-v2
    world model is a reference-similarity model over training compounds, so these traces cannot
    support a state-informed versus state-free contrast.
  - Abstention is reported separately from action choice: an arm's stop reasons are counted and the
    utility of the episodes it abstained on is compared with what `fixed` obtained there.
- Run: python -m research.identifiability_audit.dual_core_attribution [--out DIR]
- Interfaces: `BACKENDS`, `task_report`, `main`
- Depends on: the frozen outputs/protocol_v2_1_20260927/e_data1/scored/*.jsonl.gz, numpy, pandas
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCORED = ROOT / "outputs" / "protocol_v2_1_20260927" / "e_data1" / "scored"
OUT = ROOT / "outputs" / "identifiability_audit_20260930" / "dual_core"
TASKS = ("sciplex3_B", "l1000_LT")

BACKENDS = {
    "fixed": {"module": "research/external_validation/arms.py:fixed", "uses_forecast": False,
              "forecast_source": None},
    "random_legal": {"module": "research/external_validation/arms.py:random_legal", "uses_forecast": False,
                     "forecast_source": None},
    "myopic_edv": {"module": "research/external_validation/arms.py:myopic_edv", "uses_forecast": True,
                   "forecast_source": "SparseReferenceModel over the fold's training compounds "
                                      "(leave-one-out outcomes)"},
    "belief": {"module": "research/belief_planning/arms.py:belief_arm", "uses_forecast": True,
               "forecast_source": "belief_planning.world.ReferenceWorld over training compounds "
                                  "(scenario cards)"},
    "safe": {"module": "research/protocol_v2/safe.py:safe_arm", "uses_forecast": True,
             "forecast_source": "belief_planning ReferenceWorld plus a novelty gate on training similarity"},
    "oracle": {"module": "research/external_validation/arms.py:make_oracle", "uses_forecast": True,
               "forecast_source": "the held-out outcome itself; diagnostic only"},
}
ABSTAIN_STOPS = ("estimated_net_non_positive", "value_unknown", "oracle_defers", "selector_returned_empty",
                 "registered_validator_cannot_eliminate", "defer_floor")


def _load(prefix: str) -> pd.DataFrame:
    rows = []
    for path in sorted(SCORED.glob(f"{prefix}_*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                r = json.loads(line)
                rows.append({"arm": r["arm"], "episode": f"{r['fold']}|{r['compound']}|{r['h1']}|{r['h2']}",
                             "unit": str(r["unit"]), "fold": int(r["fold"]),
                             "final": r["score"]["final"], "utility": float(r["score"]["utility"]),
                             "correct": float(r["score"]["correct"]),
                             "wrong": float(r["score"]["wrong"]),
                             "measurements": int(r["measurements"]), "days": float(r["days"]),
                             "stop": r["stop"],
                             "first_action": (r["steps"][0]["action"] if r["steps"] else ""),
                             "sequence": "|".join(s["action"] for s in r["steps"]),
                             "qc_failed_steps": sum(s.get("lifecycle") == "measured_qc_failed"
                                                    for s in r["steps"])})
    return pd.DataFrame(rows)


def _paired(frame: pd.DataFrame, left: str, right: str, metric: str = "utility") -> dict:
    a = frame[frame.arm == left].set_index("episode")
    b = frame[frame.arm == right].set_index("episode").reindex(a.index)
    diff = (a[metric] - b[metric]).groupby(a.unit).mean()
    values = diff.to_numpy()
    rng = np.random.default_rng(20260930)
    boot = np.array([values[rng.integers(0, len(values), len(values))].mean() for _ in range(2000)])
    return {"difference": float(values.mean()),
            "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            "metric": metric, "units": int(len(values))}


def task_report(prefix: str) -> dict:
    frame = _load(prefix)
    fixed = frame[frame.arm == "fixed"].set_index("episode")
    out = {"task": prefix, "episodes": int(len(fixed)), "units": int(fixed.unit.nunique()), "arms": {}}
    for arm in sorted(frame.arm.unique()):
        sub = frame[frame.arm == arm]
        joined = sub.set_index("episode").reindex(fixed.index)
        abstained = joined.stop.isin(ABSTAIN_STOPS)
        on_abstained = joined[abstained]
        fixed_on_abstained = fixed[abstained]
        out["arms"][arm] = {
            **BACKENDS.get(arm, {"module": "unknown", "uses_forecast": None}),
            "first_action_changed_vs_fixed": float((joined.first_action != fixed.first_action).mean()),
            "sequence_changed_vs_fixed": float((joined.sequence != fixed.sequence).mean()),
            "terminal_changed_vs_fixed": float((joined.final != fixed.final).mean()),
            "correct": float(joined.correct.mean()),
            "wrong": float(joined.wrong.mean()),
            "utility_episode_mean": float(joined.utility.mean()),
            "measurements": float(joined.measurements.mean()),
            "days": float(joined.days.mean()),
            "qc_failed_steps": int(joined.qc_failed_steps.fillna(0).sum()),
            "abstention_rate": float(abstained.mean()),
            "stop_reasons": joined.stop.value_counts().to_dict(),
            "utility_on_abstained_episodes": (float(on_abstained.utility.mean()) if len(on_abstained) else None),
            "fixed_utility_on_those_episodes": (float(fixed_on_abstained.utility.mean())
                                                if len(on_abstained) else None),
            "abstention_utility_contribution": (float((on_abstained.utility
                                                       - fixed_on_abstained.utility).mean())
                                                if len(on_abstained) else 0.0),
            "utility_vs_fixed": _paired(frame, arm, "fixed"),
            "correct_vs_fixed": _paired(frame, arm, "fixed", "correct"),
            "measurements_vs_fixed": _paired(frame, arm, "fixed", "measurements"),
        }
    out["notes"] = [
        "every arm ran on the same episodes, menu, budget, stopping rule and terminal scorer",
        "no arm receives a decision-time measurement of the held-out compound; the protocol-v2 world "
        "model is a reference-similarity model over training compounds",
        "oracle reads the held-out outcome and is a diagnostic ceiling, not a policy",
    ]
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {"tasks": {name: task_report(name) for name in TASKS}}
    (out / "dual_core_attribution.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    print(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main()
