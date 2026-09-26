"""Summarise matched sequence replays: rates, paired contrasts with grouped intervals, and sensitivity.

File summary
- Path: research/sequence_audit/analyze.py
- Purpose: turn a replay's episode records into per-arm decision rates and paired differences,
  with percentile intervals from a bootstrap over independent units, and the sensitivity of each
  interval to the choice of unit (compound, chemical scaffold, assay plate).
- Core points:
  - Differences are paired on (compound, h1, h2) and resampled by cluster, so every episode of a
    unit moves together; the estimate is the ratio of summed differences to summed episodes.
  - SciPlex3 units: the primary unit is the InChIKey skeleton group used for the folds. Sensitivity
    units are the compound, the Bemis-Murcko ring scaffold, and the plate cohort, which is the
    rep1 plate of the compound's A549 24 h 10 uM well. A leave-one-plate-cohort-out range is also
    reported, because eight or nine plate clusters are too few for a percentile interval.
  - `check_reproduction` confirms that the matched replay reproduces the original follow-up
    records wherever the original rules were already the matched ones.
- Run: python research/sequence_audit/analyze.py phase2_matched_replay
- Depends on: numpy, pandas, rdkit, policies.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import policies as P  # noqa: E402

C = P.C
OUT = P.ROOT / "outputs" / "sequence_audit_20260926"
SEED = 20260926
DRAWS = 2000
METRICS = ("correct", "wrong", "utility", "undetermined", "deferred", "measurements", "days")


def load(label: str) -> pd.DataFrame:
    rows = [json.loads(line) for line in (OUT / label / "episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    frame = pd.DataFrame(rows)
    frame["correct"] = (frame.final == "correct").astype(float)
    frame["wrong"] = frame.final.isin(("wrong", "exhausted")).astype(float)
    frame["undetermined"] = (frame.final == "undetermined").astype(float)
    frame["deferred"] = (frame.final == "deferred").astype(float)
    frame["qc_failures"] = [sum(not s["qc"] for s in steps) for steps in frame.steps]
    frame["fallbacks"] = [sum("fallback" in (s.get("note") or {}) for s in steps) for steps in frame.steps]
    return frame


def sciplex3_units() -> pd.DataFrame:
    """Independent-unit labels per SciPlex3 compound."""
    from rdkit import Chem, RDLogger
    from rdkit.Chem.Scaffolds import MurckoScaffold
    RDLogger.DisableLog("rdApp.*")
    data = C.load()
    comp = data.compounds.drop_duplicates("compound").set_index("compound")

    def scaffold(smiles, compound):
        mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
        text = Chem.MolToSmiles(MurckoScaffold.GetScaffoldForMol(mol)) if mol is not None else ""
        return text or f"acyclic:{compound}"

    conditions = data.conditions
    a549 = conditions[(conditions.cell_line == "A549") & (conditions.time == 24.0)]
    anchor = {}
    for compound, group in a549.groupby("compound"):
        preferred = group[group.dose == 10000.0]
        anchor[compound] = str((preferred if len(preferred) else group.sort_values("dose", ascending=False)).plate_rep1.iloc[0])
    return pd.DataFrame({"compound": comp.index, "skeleton": comp.skeleton.values,
                         "scaffold": [scaffold(s, c) for c, s in zip(comp.index, comp.smiles)],
                         "plate_cohort": [anchor.get(c, f"none:{c}") for c in comp.index]}).set_index("compound")


def paired(frame: pd.DataFrame, left: str, right: str, metric: str, unit: pd.Series) -> dict:
    """Mean paired difference left - right and a cluster-bootstrap 95% interval over `unit`."""
    key = ["compound", "h1", "h2"]
    a = frame[frame.policy == left].set_index(key)[metric]
    b = frame[frame.policy == right].set_index(key)[metric]
    if not a.index.sort_values().equals(b.index.sort_values()):
        raise ValueError(f"{left} and {right} were not run on the same episodes")
    difference = (a - b.reindex(a.index)).rename("d").reset_index()
    difference["unit"] = difference.compound.map(unit)
    blocks = difference.groupby("unit").d.agg(["sum", "size"]).to_numpy()
    rng = np.random.default_rng(SEED)
    ix = rng.integers(len(blocks), size=(DRAWS, len(blocks)))
    boot = blocks[ix, 0].sum(axis=1) / blocks[ix, 1].sum(axis=1)
    return {"left": left, "right": right, "metric": metric, "difference": float(difference.d.mean()),
            "ci95": [float(x) for x in np.quantile(boot, [0.025, 0.975])], "units": int(len(blocks)),
            "episodes": int(len(difference))}


def leave_one_out(frame: pd.DataFrame, left: str, right: str, metric: str, unit: pd.Series) -> list[float]:
    key = ["compound", "h1", "h2"]
    a = frame[frame.policy == left].set_index(key)[metric]
    b = frame[frame.policy == right].set_index(key)[metric]
    difference = (a - b.reindex(a.index)).rename("d").reset_index()
    difference["unit"] = difference.compound.map(unit)
    return [float(difference[difference.unit != u].d.mean()) for u in sorted(difference.unit.unique())]


def summary_table(frame: pd.DataFrame) -> list[dict]:
    rows = []
    for (tier, qc_rule, policy), group in frame.groupby(["tier", "qc_rule", "policy"]):
        rows.append({"tier": tier, "qc_rule": qc_rule, "policy": policy, "episodes": int(len(group)),
                     **{m: float(group[m].mean()) for m in METRICS},
                     "qc_failures": int(group.qc_failures.sum()), "fallbacks": int(group.fallbacks.sum()),
                     "second_measurement_after_neutral": int(sum(
                         len(s) > 1 and s[0]["qc"] and not s[0]["eliminated"] for s in group.steps)),
                     "neutral_first": int(sum(bool(s) and s[0]["qc"] and not s[0]["eliminated"] for s in group.steps)),
                     "stops": dict(Counter(str(x).split(":")[0] for x in group.stop))})
    return rows


def check_reproduction(frame: pd.DataFrame) -> dict:
    """Arms whose original rules already matched must reproduce the follow-up record exactly."""
    original = [json.loads(line) for line in
                (P.ROOT / "outputs/acquisition_followup/sequences/episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    index = {(r["tier"], r["policy"], r["compound"], r["h1"], r["h2"]): r for r in original}
    pairs = {("fixed", "continue"): "fixed", ("da_unconditioned", "continue"): "da", ("two_step", "stop"): "two_step",
             ("one_step_utility", "stop"): "one_step_utility", ("two_step_permuted", "stop"): "two_step_permuted"}
    result = {}
    for (arm, rule), name in pairs.items():
        mine = frame[(frame.policy == arm) & (frame.qc_rule == rule)]
        if mine.empty:
            continue
        same = sum((r.final, [s["action"] for s in r.steps]) ==
                   (index[(r.tier, name, r.compound, r.h1, r.h2)]["final"],
                    [s["action"] for s in index[(r.tier, name, r.compound, r.h1, r.h2)]["steps"]])
                   for r in mine.itertuples())
        result[f"{arm}|{rule} vs original {name}"] = {"episodes": int(len(mine)), "identical": int(same)}
    return result


def fixed_gap_by_path(frame: pd.DataFrame, tier: str, qc_rule: str, arm: str = "two_step") -> dict:
    """Net correct-decision gap fixed - arm, split by the arm's path in discordant pairs."""
    sub = frame[(frame.tier == tier) & (frame.qc_rule == qc_rule)]
    key = ["compound", "h1", "h2"]
    left = sub[sub.policy == arm].set_index(key)
    right = sub[sub.policy == "fixed"].set_index(key)
    out = Counter()
    for index, row in left.iterrows():
        a, b = row.final == "correct", right.loc[index].final == "correct"
        if a == b:
            continue
        steps = row.steps
        if not steps:
            path = "deferred_before_first"
        elif not steps[0]["qc"]:
            path = "first_qc_failed_" + ("continued" if len(steps) > 1 else "stopped")
        elif steps[0]["eliminated"]:
            path = "first_eliminated"
        else:
            path = "first_neutral_" + ("continued" if len(steps) > 1 else "stopped")
        out[path] += 1 if b else -1
    n = len(left)
    return {path: count / n for path, count in sorted(out.items())}


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "phase2_matched_replay"
    frame = load(label)
    units = sciplex3_units()
    table = summary_table(frame)
    contrasts, sensitivity = [], []
    baselines = ("one_step_utility", "da", "da_unconditioned", "fixed", "production", "magnitude", "two_step_permuted")
    focus = "two_step_fallback" if "two_step_fallback" in set(frame.policy) else "two_step"
    others = [b for b in (("two_step",) if focus != "two_step" else ()) + baselines if b in set(frame.policy)]
    for tier in ("A", "B"):
        for qc_rule in ("continue", "stop"):
            sub = frame[(frame.tier == tier) & (frame.qc_rule == qc_rule)]
            for baseline in others:
                for metric in ("correct", "wrong", "utility", "measurements"):
                    contrasts.append({"tier": tier, "qc_rule": qc_rule,
                                      **paired(sub, focus, baseline, metric, units.skeleton)})
                if qc_rule == "continue" and baseline in ("fixed", "two_step", "one_step_utility"):
                    for metric in ("correct", "wrong", "utility"):
                        for name in ("compound", "scaffold", "plate_cohort"):
                            unit = pd.Series(units.index, index=units.index) if name == "compound" else units[name]
                            sensitivity.append({"tier": tier, "unit": name, **paired(sub, focus, baseline, metric, unit)})
                        loo = leave_one_out(sub, focus, baseline, metric, units.plate_cohort)
                        sensitivity.append({"tier": tier, "unit": "leave_one_plate_cohort_out", "left": focus,
                                            "right": baseline, "metric": metric, "range": [min(loo), max(loo)]})
    gaps = {f"{tier}|{rule}": fixed_gap_by_path(frame, tier, rule) for tier in ("A", "B") for rule in ("continue", "stop")}
    summary = {"label": label, "focus": focus, "reproduction": check_reproduction(frame), "means": table,
               "contrasts": contrasts, "unit_sensitivity": sensitivity, "fixed_gap_by_path": gaps,
               "units": {"skeleton": int(units.skeleton.nunique()), "scaffold": int(units.scaffold.nunique()),
                         "plate_cohort": int(units.plate_cohort.nunique()), "compound": int(len(units))}}
    (OUT / label / "summary.json").write_bytes(json.dumps(summary, indent=1).encode("utf-8"))
    lines = [f"# Matched replay: {label}", "",
             "SciPlex3 episodes already analysed by blocks 2 and 3 and the follow-up: exploratory, never confirmatory.",
             "Every arm ran under the same menu, time order, two-measurement and 16-day budget, QC rule, stops and "
             "utility (+1 correct, -2 wrong, 0 otherwise).", "",
             "## Rates", "", "|Tier|QC rule|Arm|Correct|Wrong|Undetermined|Deferred|Utility|Measurements|Days|"
             "Neutral first|Second after neutral|Fallbacks|", "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in sorted(table, key=lambda r: (r["tier"], r["qc_rule"], -r["utility"])):
        lines.append(f"|{r['tier']}|{r['qc_rule']}|{r['policy']}|{r['correct']:.3f}|{r['wrong']:.3f}|"
                     f"{r['undetermined']:.3f}|{r['deferred']:.3f}|{r['utility']:.3f}|{r['measurements']:.2f}|"
                     f"{r['days']:.2f}|{r['neutral_first']}|{r['second_measurement_after_neutral']}|{r['fallbacks']}|")
    lines += ["", f"## Paired {focus} minus baseline (95% interval, skeleton-clustered bootstrap)", "",
              "|Tier|QC rule|Baseline|Metric|Difference|95% CI|", "|---|---|---|---|---:|---|"]
    for r in contrasts:
        lines.append(f"|{r['tier']}|{r['qc_rule']}|{r['right']}|{r['metric']}|{r['difference']:+.3f}|"
                     f"[{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]|")
    lines += ["", "## Unit sensitivity (QC rule `continue`)", "", "|Tier|Baseline|Metric|Unit|Units|95% CI or range|",
              "|---|---|---|---|---:|---|"]
    for r in sensitivity:
        span = r.get("ci95") or r["range"]
        lines.append(f"|{r['tier']}|{r['right']}|{r['metric']}|{r['unit']}|{r.get('units', '')}|"
                     f"[{span[0]:+.3f}, {span[1]:+.3f}]|")
    lines += ["", "## Fixed minus two-step correct rate, by the two-step path in discordant pairs", ""]
    for key, value in gaps.items():
        lines.append(f"- {key}: " + ", ".join(f"{k} {v:+.3f}" for k, v in value.items()))
    lines += ["", "## Reproduction of the original follow-up records", ""]
    for key, value in summary["reproduction"].items():
        lines.append(f"- {key}: {value['identical']}/{value['episodes']} identical")
    (OUT / label / "report.md").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
