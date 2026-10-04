"""Frozen decision rules for the feedback-validation study.

File summary
- Path: research/astra/feedback_validation_20261003/verdict.py
- Purpose: turn per-line campaign receipts (`lines.jsonl`) into the registered primary verdict and
  the secondary estimates.
- Core points:
  - A unit is a target cell line; its value for an arm is the mean over replicates (SV, VS) and,
    for multi-seed arms, over seeds.
  - Primary: validated discoveries (screen call AND independent validation call) of `feedback`
    against static* = the static arm with the most validated discoveries. static* is re-selected
    inside every bootstrap resample (percentile bootstrap over lines stratified by stratum,
    10,000 resamples, seed 20261003). G = relative gain (ratio of sums).
  - Categories on G: MEANINGFUL_GAIN (lower bound > 0, point >= 0.10), SMALL_GAIN (lower bound > 0,
    point < 0.10), INCONCLUSIVE (lower bound <= 0, upper >= 0.10), NO_MEANINGFUL_GAIN (lower bound
    <= 0, 0 < upper < 0.10), HARM (upper <= 0). A stop category (NO_MEANINGFUL_GAIN or HARM) also
    requires the same category, or HARM, against the pre-specified comparator history_rate;
    otherwise the verdict is INCONCLUSIVE.
  - Sensitivity: two-way bootstrap over lines and drug pairs (pairs recur in every line).
- Interfaces: `python -m research.astra.feedback_validation_20261003.verdict RUN_DIR`.
- Depends on: numpy.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

STATIC_ARMS = ("history_mean", "history_rate", "ridge_static", "gbm_static")
FIXED_COMPARATOR = "history_rate"
MEANINGFUL = 0.10
RESAMPLES = 10_000
SEED = 20261003
FIELDS = ("screen_hits", "screen_hits_nonmissing", "validated", "validated_strict", "valid_calls",
          "validated_efficacious", "valid_missing", "wells")
STOP = ("NO_MEANINGFUL_GAIN", "HARM")


def load(run_dir: Path) -> list[dict]:
    with open(run_dir / "lines.jsonl", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def _value(runs: list[dict], field: str) -> float:
    vals = [r[field] for r in runs if r.get(field) is not None]
    return float(np.mean(vals)) if vals else np.nan


def table(lines: list[dict], budget: str) -> tuple[dict, np.ndarray, list[tuple[str, str]]]:
    """arm -> field -> per-unit array (mean over replicates and seeds); unit strata; unit keys."""
    units: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in lines:
        units[(record["stratum"], record["line"])].append(record)
    keys = sorted(units)
    arms = sorted(lines[0]["budgets"][budget]["arms"])
    out = {arm: {f: np.full(len(keys), np.nan) for f in FIELDS + ("valid_y_mean",)} for arm in arms}
    for u, key in enumerate(keys):
        for arm in arms:
            per_rep = {f: [] for f in FIELDS + ("valid_y_mean",)}
            for record in units[key]:
                value = record["budgets"][budget]["arms"][arm]
                runs = value if isinstance(value, list) else [value]
                for f in FIELDS:
                    per_rep[f].append(_value(runs, f))
                ym = [r["valid_y_sum"] / r["valid_y_n"] for r in runs if r["valid_y_n"]]
                per_rep["valid_y_mean"].append(float(np.mean(ym)) if ym else np.nan)
            for f, vals in per_rep.items():
                vals = [v for v in vals if np.isfinite(v)]
                out[arm][f][u] = float(np.mean(vals)) if vals else np.nan
    strata = np.array([k[0] for k in keys])
    return out, strata, keys


def _resample(strata: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    parts = []
    for s in np.unique(strata):
        members = np.flatnonzero(strata == s)
        parts.append(rng.choice(members, size=members.size, replace=True))
    return np.concatenate(parts)


def _summary(d: np.ndarray, base: np.ndarray, means: np.ndarray, ratios: np.ndarray, x: np.ndarray) -> dict:
    total = base.sum()
    return {"lines": int(d.size), "sum_x": float(x.sum()), "sum_y": float(total), "mean_diff": float(d.mean()),
            "mean_diff_ci": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
            "relative_gain": float(d.sum() / total) if total else None,
            "relative_gain_ci": [float(np.nanpercentile(ratios, 2.5)), float(np.nanpercentile(ratios, 97.5))],
            "better": int((d > 0).sum()), "worse": int((d < 0).sum())}


def contrast(x: np.ndarray, y: np.ndarray, strata: np.ndarray) -> dict:
    """Paired per-unit contrast x - y (fixed comparator), stratified bootstrap."""
    keep = np.isfinite(x) & np.isfinite(y)
    x, y, strata = x[keep], y[keep], strata[keep]
    d = x - y
    rng = np.random.default_rng(SEED)
    means, ratios = np.empty(RESAMPLES), np.empty(RESAMPLES)
    for i in range(RESAMPLES):
        idx = _resample(strata, rng)
        means[i] = d[idx].mean()
        base = y[idx].sum()
        ratios[i] = d[idx].sum() / base if base else np.nan
    return _summary(d, y, means, ratios, x)


def contrast_vs_best(x: np.ndarray, statics: dict[str, np.ndarray], strata: np.ndarray) -> dict:
    """x minus the best static arm, re-selecting the best arm inside every resample."""
    names = sorted(statics)
    S = np.vstack([statics[n] for n in names])
    best = int(np.argmax(S.sum(axis=1)))
    y = S[best]
    d = x - y
    rng = np.random.default_rng(SEED)
    means, ratios, chosen = np.empty(RESAMPLES), np.empty(RESAMPLES), np.zeros(len(names), int)
    for i in range(RESAMPLES):
        idx = _resample(strata, rng)
        sums = S[:, idx].sum(axis=1)
        j = int(np.argmax(sums))
        chosen[j] += 1
        di = x[idx] - S[j, idx]
        means[i] = di.mean()
        ratios[i] = di.sum() / sums[j] if sums[j] else np.nan
    out = _summary(d, y, means, ratios, x)
    out["static_star"] = names[best]
    out["static_star_bootstrap_share"] = {n: float(c / RESAMPLES) for n, c in zip(names, chosen)}
    return out


def two_way(lines: list[dict], budget: str, keys: list[tuple[str, str]], strata: np.ndarray) -> dict:
    """Sensitivity: resample lines (within stratum) and drug pairs (within stratum) jointly."""
    arms = ("feedback",) + STATIC_ARMS
    pair_index: dict[str, dict[int, int]] = defaultdict(dict)
    for record in lines:
        for p in record["pair_ids"]:
            pair_index[record["stratum"]].setdefault(int(p), len(pair_index[record["stratum"]]))
    unit_of = {k: u for u, k in enumerate(keys)}
    mats = {arm: {s: np.zeros((len(keys), len(pair_index[s]))) for s in pair_index} for arm in arms}
    reps: dict[tuple[str, str], int] = defaultdict(int)
    for record in lines:
        reps[(record["stratum"], record["line"])] += 1
    for record in lines:
        u = unit_of[(record["stratum"], record["line"])]
        s = record["stratum"]
        for arm in arms:
            value = record["budgets"][budget]["arms"][arm]
            runs = value if isinstance(value, list) else [value]
            for run in runs:
                for p in run["validated_pairs"]:
                    mats[arm][s][u, pair_index[s][int(p)]] += 1.0 / (len(runs) * reps[(s, record["line"])])
    rng = np.random.default_rng(SEED + 1)
    ratios = np.empty(RESAMPLES)
    for i in range(RESAMPLES):
        idx = _resample(strata, rng)
        totals = {arm: 0.0 for arm in arms}
        for s, n in ((s, len(pair_index[s])) for s in pair_index):
            w = np.bincount(rng.integers(0, n, n), minlength=n).astype(float)
            members = idx[strata[idx] == s]
            for arm in arms:
                totals[arm] += float((mats[arm][s][members] @ w).sum())
        best = max(STATIC_ARMS, key=lambda a: totals[a])
        ratios[i] = (totals["feedback"] - totals[best]) / totals[best] if totals[best] else np.nan
    return {"relative_gain_ci": [float(np.nanpercentile(ratios, 2.5)), float(np.nanpercentile(ratios, 97.5))],
            "resamples": RESAMPLES}


def category(c: dict) -> str:
    g = c.get("relative_gain")
    if g is None:
        return "UNDEFINED"
    lo, hi = c["relative_gain_ci"]
    if hi <= 0:
        return "HARM"
    if lo > 0:
        return "MEANINGFUL_GAIN" if g >= MEANINGFUL else "SMALL_GAIN"
    return "INCONCLUSIVE" if hi >= MEANINGFUL else "NO_MEANINGFUL_GAIN"


def evaluate(lines: list[dict], budget: str, *, primary: bool) -> dict:
    t, strata, keys = table(lines, budget)
    totals = {arm: {f: float(np.nansum(v[f])) for f in FIELDS} for arm, v in t.items()}
    fb = t["feedback"]
    statics = {a: t[a]["validated"] for a in STATIC_ARMS}
    out: dict = {"budget": budget, "units": len(keys), "records": len(lines), "totals": totals,
                 "unit_screen_hits_mean": float(np.mean([r["line_screen_hits"] for r in lines])),
                 "unit_validated_available_mean": float(np.mean([r["line_validated"] for r in lines]))}
    main = out["primary_contrast"] = contrast_vs_best(fb["validated"], statics, strata)
    fixed = out["fixed_comparator_contrast"] = contrast(fb["validated"], t[FIXED_COMPARATOR]["validated"], strata)
    if primary:
        cat, cat_fixed = category(main), category(fixed)
        verdict = cat
        if cat in STOP and cat_fixed not in STOP:
            verdict = "INCONCLUSIVE"
        out["verdict"] = verdict
        out["category_vs_best_static"] = cat
        out["category_vs_history_rate"] = cat_fixed
    sec = out["secondary"] = {}
    sec["S1_screen_hits_vs_best_static"] = contrast_vs_best(fb["screen_hits"], {a: t[a]["screen_hits"] for a in STATIC_ARMS},
                                                            strata)
    for arm in STATIC_ARMS:
        sec[f"S1b_validated_vs_{arm}"] = contrast(fb["validated"], t[arm]["validated"], strata)
    star = main["static_star"]
    rate = {}
    for arm in ("feedback", star, "rate_feedback", "shuffle", "wrong_line", "random", "oracle_screen"):
        s, v = np.nansum(t[arm]["screen_hits_nonmissing"]), np.nansum(t[arm]["validated"])
        rate[arm] = float(v / s) if s else None
    sec["S2_validation_rate_among_screen_hits_with_validation"] = rate
    sec["S3_mean_validation_label_of_purchases"] = contrast(fb["valid_y_mean"], t[star]["valid_y_mean"], strata)
    sec["S4_feedback_minus_shuffle"] = contrast(fb["validated"], t["shuffle"]["validated"], strata)
    sec["S4b_shuffle_minus_static_star"] = contrast(t["shuffle"]["validated"], t[star]["validated"], strata)
    sec["S4c_feedback_minus_wrong_line"] = contrast(fb["validated"], t["wrong_line"]["validated"], strata)
    sec["S6_validated_efficacious"] = contrast_vs_best(fb["validated_efficacious"],
                                                       {a: t[a]["validated_efficacious"] for a in STATIC_ARMS}, strata)
    sec["S9_history_feedback_minus_history_mean"] = contrast(t["history_feedback"]["validated"],
                                                              t["history_mean"]["validated"], strata)
    sec["S9b_gbm_feedback_minus_gbm_static"] = contrast(t["gbm_feedback"]["validated"], t["gbm_static"]["validated"],
                                                         strata)
    sec["S12_rate_feedback_minus_history_rate"] = contrast(t["rate_feedback"]["validated"],
                                                            t["history_rate"]["validated"], strata)
    if np.isfinite(fb["validated_strict"]).any():
        sec["S14_strict_majority_calls"] = contrast_vs_best(
            fb["validated_strict"], {a: t[a]["validated_strict"] for a in STATIC_ARMS}, strata)
    same = 0
    for r in lines:
        arms = r["budgets"][budget]["arms"]
        same += sorted(sum(arms["offset_only"]["purchases"], [])) == sorted(sum(arms["ridge_static"]["purchases"], []))
    sec["S5_offset_only_identical_to_static_records"] = f"{same}/{len(lines)}"
    per = {}
    for s in np.unique(strata):
        m = strata == s
        per[str(s)] = contrast_vs_best(fb["validated"][m], {a: t[a]["validated"][m] for a in STATIC_ARMS}, strata[m])
    sec["S7_per_stratum"] = per
    rounds = lines[0]["budgets"][budget]["rounds"]
    sec["S10_elapsed_and_wells"] = {"feedback_rounds": rounds, "static_minimum_rounds": 1,
                                    "wells_feedback": totals["feedback"]["wells"], "wells_static_star": totals[star]["wells"]}
    if primary:
        sec["S13_two_way_bootstrap_lines_x_pairs"] = two_way(lines, budget, keys, strata)
    return out


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    run_dir = Path(argv[0])
    lines = load(run_dir)
    budgets = list(lines[0]["budgets"])
    result = {name: evaluate(lines, name, primary=(name == "primary")) for name in budgets}
    (run_dir / "verdict.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    head = result.get("primary", result[budgets[0]])
    print(json.dumps({"verdict": head.get("verdict"), "primary_contrast": head["primary_contrast"],
                      "fixed": head["fixed_comparator_contrast"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
