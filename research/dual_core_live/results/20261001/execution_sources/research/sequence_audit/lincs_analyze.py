"""Analyse the frozen L1000 evaluation and apply the pre-registered decision rule.

File summary
- Path: research/sequence_audit/lincs_analyze.py
- Purpose: per-arm decision rates, the primary and secondary paired contrasts with intervals over
  the held-out compound's fold component, unit sensitivity (identity group, batch cohort, leave one
  batch out), step-1 forecast calibration, contrast-support strata, the plate diagnostic, and the
  classification `protocol.json` fixes.
- Core points:
  - The classification reads only the tier-LT contrasts named in the protocol, plus the tier-T
    point estimates PROMOTE requires. Everything else is reported, not decided on.
  - Refuses to run unless the episode manifest's frozen hashes match the protocol files.
- Run: python research/sequence_audit/lincs_analyze.py
- Depends on: analyze.py, lincs_prepare.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import analyze as A  # noqa: E402
import lincs_prepare as LP  # noqa: E402

OUT = A.OUT / "l1000"
TOLERANCE = 0.02


def load() -> pd.DataFrame:
    rows = [json.loads(line) for line in (OUT / "episodes" / "episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    frame = pd.DataFrame(rows)
    frame["correct"] = (frame.final == "correct").astype(float)
    frame["wrong"] = frame.final.isin(("wrong", "exhausted")).astype(float)
    frame["undetermined"] = (frame.final == "undetermined").astype(float)
    frame["deferred"] = (frame.final == "deferred").astype(float)
    frame["qc_failures"] = [sum(not s["qc"] for s in steps) for steps in frame.steps]
    frame["fallbacks"] = [sum("fallback" in (s.get("note") or {}) for s in steps) for steps in frame.steps]
    frame["qc_rule"] = "continue"
    return frame


def units() -> dict[str, pd.Series]:
    compounds = pd.read_csv(LP.OUT / "compounds.csv").set_index("compound")
    conditions = pd.read_csv(LP.OUT / "conditions.csv")
    first = conditions[(conditions.cell_line == "A549") & (conditions.time == 6.0)].set_index("compound").batch
    return {"component": compounds.component, "identity": compounds.identity,
            "batch_cohort": first.reindex(compounds.index).fillna("none")}


def calibration(audit: pd.DataFrame) -> dict:
    served = audit[audit.served & audit.realised.isin(("correct", "wrong", "neutral"))].copy()
    served["y"] = (served.realised == "correct").astype(float)
    out = {}
    for name, group in [("all", served)] + [(f"tier_{t}", g) for t, g in served.groupby("tier")] + \
            [(f"support_{s}", g) for s, g in served.groupby(pd.cut(served.support, [0, 1, 4, 1e9],
                                                                        labels=["1", "2-4", ">=5"]), observed=True)]:
        p, y = group.p_correct_truth_branch.to_numpy(float), group.y.to_numpy()
        bins = np.minimum((p * 10).astype(int), 9)
        ece = sum(abs(p[bins == b].mean() - y[bins == b].mean()) * np.mean(bins == b) for b in range(10) if np.any(bins == b))
        out[name] = {"rows": int(len(group)), "mean_forecast": float(p.mean()), "realised": float(y.mean()),
                     "ece": float(ece), "brier": float(np.mean((p - y) ** 2))}
    out["refused_share"] = float((~audit.served).mean())
    return out


def plate_diagnostic(audit: pd.DataFrame) -> dict:
    elim = audit[audit.realised.isin(("correct", "wrong"))]
    out = {}
    for name, group in [("all", elim)] + list(elim.groupby("realised")):
        out[name] = {"eliminating_readings": int(len(group)),
                     "nearest_template_same_batch": float(group.nearest_same_batch.astype(float).mean()),
                     "templates_same_batch_share": float(group.template_same_batch_share.mean())}
    return out


def classify(contrasts: list[dict]) -> dict:
    def get(tier, right, metric):
        return next(c for c in contrasts if c["tier"] == tier and c["right"] == right and c["metric"] == metric)

    u2, w2 = get("LT", "two_step", "utility"), get("LT", "two_step", "wrong")
    uf, wf = get("LT", "fixed", "utility"), get("LT", "fixed", "wrong")
    t2, tf = get("T", "two_step", "utility"), get("T", "fixed", "utility")
    checks = {
        "reject_utility": u2["ci95"][1] < 0, "reject_wrong": w2["ci95"][0] > TOLERANCE,
        "gain_over_two_step": u2["ci95"][0] > 0, "wrong_vs_two_step_ok": w2["ci95"][1] <= TOLERANCE,
        "gain_over_fixed": uf["ci95"][0] > 0, "wrong_vs_fixed_ok": wf["ci95"][1] <= TOLERANCE,
        "tier_T_consistent": t2["difference"] >= 0 and tf["difference"] >= 0,
    }
    if checks["reject_utility"] or checks["reject_wrong"]:
        verdict = "REJECT"
    elif all(checks[k] for k in ("gain_over_two_step", "wrong_vs_two_step_ok", "gain_over_fixed", "wrong_vs_fixed_ok",
                                 "tier_T_consistent")):
        verdict = "PROMOTE"
    elif checks["gain_over_two_step"] and checks["wrong_vs_two_step_ok"]:
        verdict = "SHADOW"
    else:
        verdict = "INCONCLUSIVE"
    return {"verdict": verdict, "checks": checks}


def main() -> None:
    manifest = json.loads((OUT / "episodes" / "manifest.json").read_text(encoding="utf-8"))
    for name in ("PROTOCOL.md", "protocol.json"):
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != manifest["freeze"]["sha256"][name]:
            raise SystemExit(f"{name} changed after the run")
    frame = load()
    audit = pd.DataFrame([json.loads(line) for line in
                          (OUT / "episodes" / "menu_audit.jsonl").read_text(encoding="utf-8").splitlines()])
    unit = units()
    table = A.summary_table(frame)
    focus = "two_step_fallback"
    baselines = ("two_step", "fixed", "da", "da_unconditioned", "production", "one_step_utility", "two_step_permuted")
    contrasts, sensitivity = [], []
    for tier in ("LT", "T"):
        sub = frame[frame.tier == tier]
        for baseline in baselines:
            for metric in ("utility", "wrong", "correct", "measurements", "days"):
                contrasts.append({"tier": tier, **A.paired(sub, focus, baseline, metric, unit["component"])})
        for metric in ("utility", "wrong", "correct"):
            contrasts.append({"tier": tier, "note": "forecast signal", **A.paired(sub, "two_step", "two_step_permuted",
                                                                                 metric, unit["component"])})
            contrasts.append({"tier": tier, "note": "planner versus fixed", **A.paired(sub, "two_step", "fixed", metric,
                                                                                      unit["component"])})
        for baseline in ("two_step", "fixed"):
            for metric in ("utility", "wrong"):
                for name in ("identity", "batch_cohort"):
                    sensitivity.append({"tier": tier, "unit": name, **A.paired(sub, focus, baseline, metric, unit[name])})
                loo = A.leave_one_out(sub, focus, baseline, metric, unit["batch_cohort"])
                sensitivity.append({"tier": tier, "unit": "leave_one_batch_out", "left": focus, "right": baseline,
                                    "metric": metric, "range": [min(loo), max(loo)]})
    strata = []
    frame["stratum"] = pd.cut(frame.contrast_support, [-1, 3, 7, 1e9], labels=["<=3", "4-7", ">=8"])
    for (tier, stratum, policy), group in frame.groupby(["tier", "stratum", "policy"], observed=True):
        strata.append({"tier": tier, "stratum": str(stratum), "policy": policy, "episodes": int(len(group)),
                       **{m: float(group[m].mean()) for m in ("correct", "wrong", "utility", "measurements")}})
    decision = classify(contrasts)
    summary = {"manifest_freeze": manifest["freeze"], "gates": manifest["gates"], "means": table, "contrasts": contrasts,
               "unit_sensitivity": sensitivity, "support_strata": strata, "calibration": calibration(audit),
               "plate_diagnostic": plate_diagnostic(audit), "decision": decision,
               "units": {k: int(v.nunique()) for k, v in unit.items()}}
    (OUT / "summary.json").write_bytes(json.dumps(summary, indent=1, default=str).encode("utf-8"))
    lines = ["# L1000 independent decision validation", "",
             f"Protocol frozen {manifest['freeze']['frozen_at_local']} before any L1000 validator reading or decision. "
             f"Gates: {manifest['gates']}. Decision (tier LT): **{decision['verdict']}**.", "",
             "## Rates", "", "|Tier|Arm|Episodes|Correct|Wrong|Undetermined|Deferred|Utility|Measurements|Days|"
             "Neutral first|Second after neutral|Fallbacks|", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in sorted(table, key=lambda r: (r["tier"], -r["utility"])):
        lines.append(f"|{r['tier']}|{r['policy']}|{r['episodes']}|{r['correct']:.3f}|{r['wrong']:.3f}|{r['undetermined']:.3f}|"
                     f"{r['deferred']:.3f}|{r['utility']:.3f}|{r['measurements']:.2f}|{r['days']:.2f}|{r['neutral_first']}|"
                     f"{r['second_measurement_after_neutral']}|{r['fallbacks']}|")
    lines += ["", "## Paired contrasts (95% interval, component-clustered bootstrap)", "",
              "|Tier|Left|Right|Metric|Difference|95% CI|Units|", "|---|---|---|---|---:|---|---:|"]
    for r in contrasts:
        lines.append(f"|{r['tier']}|{r['left']}|{r['right']}|{r['metric']}|{r['difference']:+.3f}|"
                     f"[{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]|{r['units']}|")
    lines += ["", "## Unit sensitivity", "", "|Tier|Right|Metric|Unit|Units|95% CI or range|", "|---|---|---|---|---:|---|"]
    for r in sensitivity:
        span = r.get("ci95") or r["range"]
        lines.append(f"|{r['tier']}|{r['right']}|{r['metric']}|{r['unit']}|{r.get('units', '')}|[{span[0]:+.3f}, {span[1]:+.3f}]|")
    lines += ["", "## Contrast-support strata", "", "|Tier|Stratum|Arm|Episodes|Correct|Wrong|Utility|Measurements|",
              "|---|---|---|---:|---:|---:|---:|---:|"]
    for r in strata:
        if r["policy"] in ("two_step_fallback", "two_step", "fixed", "da"):
            lines.append(f"|{r['tier']}|{r['stratum']}|{r['policy']}|{r['episodes']}|{r['correct']:.3f}|{r['wrong']:.3f}|"
                         f"{r['utility']:.3f}|{r['measurements']:.2f}|")
    lines += ["", "## Step-1 forecast calibration (truth-branch correct-elimination probability)", ""]
    for k, v in summary["calibration"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Plate diagnostic (eliminating step-1 readings)", ""]
    for k, v in summary["plate_diagnostic"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Decision checks", "", f"- {decision['checks']}"]
    (OUT / "report.md").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
