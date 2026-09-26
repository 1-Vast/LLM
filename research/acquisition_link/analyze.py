"""Score the prediction-to-measurement evaluation and apply the frozen classification rule.

File summary
- Path: research/acquisition_link/analyze.py
- Purpose: turn `episodes.jsonl` and `menu_audit.csv` into the tables `protocol.json` names:
  the code-path consistency checks first, then per-arm decision metrics, the primary and
  secondary paired contrasts, action distributions by time, dose and line, per-class robustness,
  forecast calibration by support stratum, and the SHADOW / REJECT / INCONCLUSIVE verdict.
- Core points:
  - A failed consistency check stops the report: it is a defect, not a result.
  - Intervals are block 2's: skeleton-clustered bootstrap, 2,000 draws, seed 20260926, paired
    on the same episodes (`research/dynamic_world_model/analyze.py`).
  - The verdict is computed by the rule frozen in `protocol.json`; nothing here chooses it.
- Run: python research/acquisition_link/analyze.py
- Depends on: evaluate.py, research/dynamic_world_model (analyze, common, card_audit), numpy, pandas
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evaluate as V  # noqa: E402  (puts the block-2 directory and src on the path)

import common as C  # noqa: E402

BLOCK2 = C.OUTPUTS / "episodes" / "episodes.jsonl"
EPISODES = V.OUT / "episodes" / "episodes.jsonl"
AUDIT = V.OUT / "episodes" / "menu_audit.csv"
KEYS = ["tier", "compound", "truth", "decoy"]
ORDER = ("oracle", "da", "da_dynamic", "da_2ref", "da_permuted", "ec_cards_1ref", "ec_cards_2ref", "magnitude",
         "production_after", "production_before", "cost_only", "fixed")


def _block2():
    """Block 2's scoring module, loaded by path so this file's own name does not shadow it."""

    import importlib.util
    spec = importlib.util.spec_from_file_location("block2_analyze", C.HERE / "analyze.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _sequence(record: dict) -> tuple:
    return tuple(tuple(step["key"]) for step in record.get("steps", []))


def consistency(records: list[dict]) -> dict:
    ours = {(r["tier"], r["compound"], r["truth"], r["decoy"], r["policy"]): r for r in records}
    theirs = {}
    with BLOCK2.open(encoding="utf-8") as stream:
        for line in stream:
            r = json.loads(line)
            if r["policy"] in ("separation", "fixed", "oracle", "magnitude", "cost_only"):
                theirs[(r["tier"], r["compound"], r["truth"], r["decoy"], r["policy"])] = r
    checks = {}

    def compare(name, a_policy, b_policy, source):
        pairs = [(key, rec) for key, rec in ours.items() if key[4] == a_policy]
        mismatched = 0
        for key, rec in pairs:
            other = source.get(key[:4] + (b_policy,))
            if other is None or other["final"] != rec["final"] or _sequence(other) != _sequence(rec):
                mismatched += 1
        checks[name] = {"compared": len(pairs), "mismatched": mismatched, "passed": bool(pairs) and mismatched == 0}

    compare("production_before_equals_cost_only", "production_before", "cost_only", ours)
    compare("production_after_equals_magnitude", "production_after", "magnitude", ours)
    compare("ec_cards_2ref_equals_block2_separation", "ec_cards_2ref", "separation", theirs)
    compare("fixed_equals_block2_fixed", "fixed", "fixed", theirs)
    compare("oracle_equals_block2_oracle", "oracle", "oracle", theirs)
    compare("magnitude_equals_block2_magnitude", "magnitude", "magnitude", theirs)
    compare("cost_only_equals_block2_cost_only", "cost_only", "cost_only", theirs)
    return checks


def distributions(records: list[dict]) -> dict:
    out: dict = {}
    for r in records:
        steps = r.get("steps", [])
        slot = out.setdefault(r["tier"], {}).setdefault(r["policy"], {"episodes": 0, "step1": {}, "step2": {}, "deferred": 0,
                                                                    "step2_after_unresolved": 0, "step2_72h_after_undetected_24h": 0,
                                                                    "undetected_24h_first": 0})
        slot["episodes"] += 1
        slot["deferred"] += r["final"] == "deferred"
        for index, name in ((0, "step1"), (1, "step2")):
            if len(steps) > index:
                line, hours, dose = steps[index]["key"]
                for label in (f"time:{hours:g}h", f"dose:{dose:g}nM", f"line:{line}"):
                    slot[name][label] = slot[name].get(label, 0) + 1
        if steps and steps[0]["key"][1] == 24.0 and steps[0]["outcome"] == "undetected":
            slot["undetected_24h_first"] += 1
            slot["step2_72h_after_undetected_24h"] += len(steps) > 1 and steps[1]["key"][1] == 72.0
    return out


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    """Block 2's ECE (card_audit.ece), equal-width bins."""

    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= edges[i + 1])
        if m.any():
            total += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(total)


def calibration(audit: pd.DataFrame) -> dict:
    out = {}
    for tier, sub in audit.groupby("tier"):
        refused = sub[~sub.served]
        served = sub[sub.served & sub.realised.notna()].copy()
        y = (served.realised == "correct").to_numpy(dtype=float)
        realised_d = y - (served.realised == "wrong").to_numpy(dtype=float)
        p = served.p_correct.to_numpy(dtype=float)
        pt = served.p_correct_truth_branch.to_numpy(dtype=float)
        strata = pd.cut(served.support, bins=[0, 1, 3, 8, 10_000], labels=["1", "2-3", "4-8", ">8"])
        by_support = []
        for label, part in served.groupby(strata, observed=True):
            yy = (part.realised == "correct").to_numpy(dtype=float)
            dd = yy - (part.realised == "wrong").to_numpy(dtype=float)
            by_support.append({"support": str(label), "n": int(len(part)), "mean_p_correct": float(part.p_correct.mean()),
                               "realised_correct": float(yy.mean()), "mean_discrimination": float(part.discrimination.mean()),
                               "realised_discrimination": float(dd.mean()),
                               "mean_lower_bound": float(part.discrimination_lower.mean()),
                               "bound_holds_on_average": bool(dd.mean() >= part.discrimination_lower.mean())})
        reasons = sub.reason.value_counts().to_dict()
        refused_real = refused[refused.realised.notna()]
        out[tier] = {
            "menu_rows": int(len(sub)), "served_fraction": float(sub.served.mean()),
            "served_scored": int(len(served)), "ece_pooled": ece(p, y), "brier_pooled": float(np.mean((p - y) ** 2)),
            "ece_truth_branch": ece(pt, y), "mean_p_correct": float(p.mean()), "realised_correct": float(y.mean()),
            "mean_total_variation": float(served.total_variation.mean()),
            "mean_discrimination": float(served.discrimination.mean()), "realised_discrimination": float(realised_d.mean()),
            "by_support": by_support, "menu_reasons": {str(k): int(v) for k, v in reasons.items()},
            "refused_realised_correct": float((refused_real.realised == "correct").mean()) if len(refused_real) else None,
            "admissible_fraction_of_served": float(sub[sub.served].admissible.mean()),
        }
    return out


def per_class(frame: pd.DataFrame) -> dict:
    out = {}
    for tier in sorted(frame.tier.unique()):
        a = frame[(frame.tier == tier) & (frame.policy == "da")].set_index(KEYS).correct
        b = frame[(frame.tier == tier) & (frame.policy == "magnitude")].set_index(KEYS).correct
        joined = pd.concat([a.rename("da"), b.rename("magnitude")], axis=1, join="inner").reset_index()
        rows = []
        for truth, part in joined.groupby("truth"):
            rows.append({"class": truth, "episodes": int(len(part)), "compounds": int(part.compound.nunique()),
                         "da": float(part.da.mean()), "magnitude": float(part.magnitude.mean()),
                         "difference": float((part.da - part.magnitude).mean())})
        out[tier] = sorted(rows, key=lambda r: r["difference"])
    return out


def classify(contrasts: dict, rates: dict, audit: dict, protocol: dict) -> dict:
    tiers = ("B", "A")
    pa = {t: contrasts[f"{t}|da-magnitude|correct"] for t in tiers}
    utility = {t: contrasts[f"{t}|da-magnitude|utility"] for t in tiers}
    permuted = {t: contrasts[f"{t}|da_permuted-magnitude|correct"] for t in tiers}
    wrong = {t: rates[t]["da"]["wrong_elimination"] - rates[t]["magnitude"]["wrong_elimination"] for t in tiers}
    ece_served = {t: audit[t]["ece_pooled"] for t in tiers}
    criteria = {
        "pa_interval_excludes_zero_in_a_tier": any(pa[t]["low"] > 0 for t in tiers),
        "pa_lower_bound_above_minus_0.02_in_every_tier": all(pa[t]["low"] > -0.02 for t in tiers),
        "wrong_elimination_within_0.02_in_every_tier": all(wrong[t] <= 0.02 for t in tiers),
        "no_utility_interval_entirely_below_zero": not any(utility[t]["high"] < 0 for t in tiers),
        "permuted_control_short_of_da_where_da_gains": all(permuted[t]["mean"] < pa[t]["mean"] for t in tiers if pa[t]["mean"] > 0),
        "served_forecast_ece_at_most_0.10": all(ece_served[t] <= 0.10 for t in tiers),
    }
    reject = any(pa[t]["high"] < 0 for t in tiers) or any(wrong[t] > 0.02 for t in tiers)
    verdict = "REJECT" if reject else "SHADOW" if all(criteria.values()) else "INCONCLUSIVE"
    s1 = {t: contrasts[f"{t}|production_after-production_before|utility"] for t in tiers}
    return {"verdict": verdict, "promote_available": False, "criteria": criteria, "pa": pa, "utility": utility,
            "permuted": permuted, "wrong_elimination_difference": wrong, "ece_served": ece_served,
            "reject_triggers": {"pa_interval_entirely_below_zero": {t: pa[t]["high"] < 0 for t in tiers},
                                "wrong_elimination_above_0.02": {t: wrong[t] > 0.02 for t in tiers}},
            "wiring_repair": {"keep": all(s1[t]["low"] > 0 for t in tiers), "utility": s1,
                              "rule": protocol["wiring_repair_rule"]}}


def main() -> None:
    A = _block2()
    protocol = V.load_protocol()
    records = [json.loads(line) for line in EPISODES.open(encoding="utf-8")]
    checks = consistency(records)
    failed = [name for name, check in checks.items() if not check["passed"]]
    out = V.OUT / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    if failed:
        C.write_json(out / "consistency_failed.json", checks)
        raise SystemExit(f"consistency checks failed, no results reported: {failed}")
    frame = A.load_episodes([EPISODES])
    skeleton = A.skeleton_map()
    rows = A.table(frame, skeleton)
    rates = {}
    for row in rows:
        rates.setdefault(row["tier"], {})[row["policy"]] = {
            "correct": row["correct"]["mean"], "wrong_elimination": row["wrong_elimination"]["mean"],
            "utility": row["utility"]["mean"], "regret": row["regret"]["mean"], "deferred": row["deferred"]}
    specs = []
    for tier in ("B", "A"):
        for metric in ("correct", "wrong_any", "utility"):
            specs += [(tier, "da", "magnitude", metric), (tier, "production_after", "production_before", metric)]
        specs += [(tier, "da", "ec_cards_1ref", "correct"), (tier, "da", "da_2ref", "correct"),
                  (tier, "da", "ec_cards_2ref", "correct"), (tier, "da", "ec_cards_2ref", "utility"),
                  (tier, "da_permuted", "magnitude", "correct"), (tier, "da", "da_permuted", "correct"),
                  (tier, "da_dynamic", "da", "correct"), (tier, "da", "cost_only", "correct"),
                  (tier, "ec_cards_1ref", "ec_cards_2ref", "correct"), (tier, "da_2ref", "ec_cards_2ref", "correct")]
    specs += [("A", "da", "fixed", "correct"), ("A", "da", "fixed", "utility"), ("A", "da_dynamic", "fixed", "correct")]
    contrasts = {f"{t}|{a}-{b}|{m}": A.paired(frame, t, a, b, m, skeleton) for t, a, b, m in specs}
    audit = calibration(pd.read_csv(AUDIT))
    verdict = classify(contrasts, rates, audit, protocol)
    summary = {"protocol_hashes": V.frozen_hashes(), "consistency": checks, "rows": rows, "contrasts": contrasts,
               "distributions": distributions(records), "per_class": per_class(frame), "calibration": audit,
               "classification": verdict}
    C.write_json(out / "summary.json", C.clean(summary))
    report = render(summary)
    (out / "report.md").write_text(report, encoding="utf-8", newline=chr(10))
    print(report)


def _ci(d: dict) -> str:
    return "n/a" if d.get("mean") is None else f"{d['mean']:+.3f} [{d['low']:+.3f}, {d['high']:+.3f}]"


def render(summary: dict) -> str:
    lines = ["# Prediction-to-measurement link: results", "",
             "Generated by `research/acquisition_link/analyze.py` from `outputs/acquisition_link_20260926/`. "
             "Protocol hashes: " + ", ".join(f"`{k}` {v[:12]}" for k, v in summary["protocol_hashes"].items()) + ".", "",
             "## Consistency checks (code-path equalities)", "", "| Check | Compared | Mismatched | Passed |", "|---|---:|---:|---|"]
    for name, check in summary["consistency"].items():
        lines.append(f"| {name} | {check['compared']} | {check['mismatched']} | {check['passed']} |")
    lines += ["", "## Decision metrics per arm", "",
              "| Tier | Arm | Episodes | Correct | Wrong elim. | Undetermined | Deferred | Utility | Regret | Measurements | Days | Wells | Days to elim. |",
              "|---|---|---:|---|---|---:|---:|---|---|---:|---:|---:|---:|"]
    for row in sorted(summary["rows"], key=lambda r: (r["tier"], ORDER.index(r["policy"]) if r["policy"] in ORDER else 99)):
        def ci(d):
            return f"{d['mean']:.3f} [{d['low']:.3f}, {d['high']:.3f}]"
        to_elim = row["days_to_elimination_when_reached"]
        lines.append(f"| {row['tier']} | {row['policy']} | {row['episodes']} | {ci(row['correct'])} | {ci(row['wrong_elimination'])} | "
                     f"{row['undetermined']:.3f} | {row['deferred']:.3f} | {ci(row['utility'])} | {ci(row['regret'])} | "
                     f"{row['mean_measurements']:.2f} | {row['mean_days']:.1f} | {row['mean_wells']:.1f} | "
                     f"{'' if to_elim is None else f'{to_elim:.1f}'} |")
    lines += ["", "## Paired contrasts (skeleton-clustered 95% intervals)", "", "| Tier | Contrast | Metric | Difference | Episodes | Clusters |",
              "|---|---|---|---|---:|---:|"]
    for key, c in summary["contrasts"].items():
        tier, name, metric = key.split("|")
        lines.append(f"| {tier} | {name} | {metric} | {_ci(c)} | {c['n']} | {c['clusters']} |")
    v = summary["classification"]
    lines += ["", "## Classification (rule frozen in protocol.json)", "", f"**{v['verdict']}** (PROMOTE unavailable from these data).", "",
              "| Criterion | Holds |", "|---|---|"]
    lines += [f"| {k} | {val} |" for k, val in v["criteria"].items()]
    lines += ["", f"Wrong-elimination difference da - magnitude: " + ", ".join(f"{t} {d:+.3f}" for t, d in v["wrong_elimination_difference"].items()),
              f"Served-forecast ECE: " + ", ".join(f"{t} {d:.3f}" for t, d in v["ece_served"].items()),
              f"Wiring repair kept: {v['wiring_repair']['keep']} (utility production_after - production_before: "
              + ", ".join(f"{t} {_ci(d)}" for t, d in v["wiring_repair"]["utility"].items()) + ")"]
    lines += ["", "## Forecast calibration over the step-1 menu (v2 forecasts)", ""]
    for tier, cal in summary["calibration"].items():
        lines.append(f"Tier {tier}: served {cal['served_fraction']:.3f} of {cal['menu_rows']} menu rows; ECE {cal['ece_pooled']:.3f} "
                     f"(truth branch {cal['ece_truth_branch']:.3f}), Brier {cal['brier_pooled']:.3f}; mean predicted P(correct) "
                     f"{cal['mean_p_correct']:.3f} against realised {cal['realised_correct']:.3f}; mean total variation "
                     f"{cal['mean_total_variation']:.3f} against mean rule-conditioned discrimination {cal['mean_discrimination']:.3f}.")
        lines += ["", "| Support | n | Mean P(correct) | Realised correct | Mean D | Realised D | Mean lower bound | Bound holds |",
                  "|---|---:|---:|---:|---:|---:|---:|---|"]
        for s in cal["by_support"]:
            lines.append(f"| {s['support']} | {s['n']} | {s['mean_p_correct']:.3f} | {s['realised_correct']:.3f} | {s['mean_discrimination']:.3f} | "
                         f"{s['realised_discrimination']:.3f} | {s['mean_lower_bound']:.3f} | {s['bound_holds_on_average']} |")
        lines.append("")
    lines += ["## Action distribution (counts of chosen conditions)", ""]
    for tier, arms in summary["distributions"].items():
        for arm in ORDER:
            if arm in arms and arm != "oracle":
                d = arms[arm]
                s1 = ", ".join(f"{k} {n}" for k, n in sorted(d["step1"].items()))
                s2 = ", ".join(f"{k} {n}" for k, n in sorted(d["step2"].items()))
                lines.append(f"- {tier} {arm}: step 1 [{s1}]; step 2 [{s2}]; deferred {d['deferred']}; "
                             f"72 h after an undetected 24 h first step {d['step2_72h_after_undetected_24h']} of {d['undetected_24h_first']}")
    lines += ["", "## Per-class correct-rate difference, da - magnitude", ""]
    for tier, rows in summary["per_class"].items():
        lines.append(f"- Tier {tier}: " + "; ".join(f"{r['class']} {r['difference']:+.3f} (n={r['episodes']}, {r['compounds']} cpd)" for r in rows))
    return chr(10).join(lines) + chr(10)


if __name__ == "__main__":
    main()
