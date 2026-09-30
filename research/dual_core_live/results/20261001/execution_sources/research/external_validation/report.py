"""Apply the registered gates to the locked replay and write the decision, risk and ablation reports.

File summary
- Path: research/external_validation/report.py
- Purpose: one entry point that verifies the freeze, reads the replay once, applies
  `promotion.py` per tier, and writes `summary.json`, `report.md`, the figures and
  `baseline_selection.json` (the comparator frozen for an external study).
- Core points:
  - Integrity (G1) is recomputed here: freeze digests, the replay's recorded rule violations and
    fold-boundary problems, and identical episode sets across arms.
  - Every number in the report comes from `statistics.py`; the report code decides nothing itself.
- Run: python -m research.external_validation.report
- Depends on: firewall, promotion, statistics, risk_audit, calibration_audit, paired_ablation
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import calibration_audit as CA
from . import firewall as F
from . import paired_ablation as PA
from . import promotion as PR
from . import risk_audit as RA
from . import statistics as S

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = RA.OUT
KEY = ["compound", "h1", "h2"]


def integrity(frame: pd.DataFrame, manifest: dict, freeze_problems: list, dataset: str, tier: str) -> list[str]:
    problems = [f"freeze:{p}" for p in freeze_problems]
    for name, found in manifest["problems"].items():
        if name.startswith(f"{dataset}_{tier}_"):
            problems += [f"{name}:{p}" for p in found]
    reference = None
    for policy, group in frame.groupby("policy"):
        episodes = set(map(tuple, group[KEY].to_numpy()))
        reference = reference or episodes
        if episodes != reference:
            problems.append(f"episode_set_differs:{policy}")
    return problems


def fmt(d: dict, digits=3) -> str:
    return f"{d['difference']:+.{digits}f} [{d['ci'][0]:+.{digits}f}, {d['ci'][1]:+.{digits}f}]"


def rate_fmt(d: dict, digits=3) -> str:
    return f"{d['estimate']:.{digits}f} [{d['ci'][0]:.{digits}f}, {d['ci'][1]:.{digits}f}]"


def main() -> None:
    spec = PR.protocol()
    freeze = json.loads((HERE / "freeze.json").read_text(encoding="utf-8"))
    freeze_problems = F.verify_freeze(freeze)
    manifest = json.loads((OUT / "replay_manifest.json").read_text(encoding="utf-8"))
    frame, steps = RA.collect()
    features = pd.read_csv(OUT / "compound_features.csv")
    diagnostics = pd.read_csv(OUT / "prediction_diagnostics.csv")

    risk = RA.summarize(frame, spec)
    figures = RA.figures(frame, spec, OUT / "figures")
    calibration_rows = CA.rows(steps, features, diagnostics)
    calibration = CA.audit(calibration_rows)
    predictions = PA.prediction_diagnostics(diagnostics)

    tiers, statuses, selected = {}, {}, {}
    for dataset, tier in RA.TIERS:
        sub = frame[(frame.dataset == dataset) & (frame.tier == tier)]
        unit = RA.UNIT[dataset]
        problems = integrity(sub, manifest, freeze_problems, dataset, tier)
        comparator = PR.strongest_baseline(sub, spec)
        selected[f"{dataset}|{tier}"] = comparator
        primary = PR.gates(sub, "maestro_vc", comparator, unit, spec, integrity=problems)
        vc = PR.vc_gate(sub, unit, spec)
        secondary = {c: PR.gates(sub, c, comparator, unit, spec, integrity=problems, level=0.9875)
                     for c in ("production_default", "maestro_masked", "sparse_two_step")}
        sensitivity = {cluster: {m: S.paired(sub, "maestro_vc", comparator, m, cluster) for m in ("correct", "wrong")}
                       for cluster in RA.SENSITIVITY[dataset]}
        ladder = {p: {m: S.paired(sub, p, comparator, m, unit) for m in ("correct", "wrong", "measurements")}
                  for p in sorted(sub.policy.unique()) if p != comparator and "@" not in p}
        tiers[f"{dataset}|{tier}"] = {
            "integrity_problems": problems, "comparator": comparator,
            "primary": primary, "primary_status": PR.status(primary, vc), "virtual_cell_gate": vc,
            "secondary": {c: {"gates": g, "status": PR.status(g)} for c, g in secondary.items()},
            "sensitivity": sensitivity, "ladder_vs_comparator": ladder,
            "ablation": PA.ablation(sub, unit)}
        statuses[f"{dataset}|{tier}"] = tiers[f"{dataset}|{tier}"]["primary_status"]

    votes = pd.Series(list(selected.values())).value_counts()
    top = votes[votes == votes.max()].index.tolist()
    pooled = frame[frame.policy.isin(top)].groupby("policy").correct.mean()
    external_comparator = sorted(top, key=lambda p: (-pooled[p], p))[0]
    baseline_selection = {"rule": spec["strongest_baseline_rule"], "selected_per_development_tier": selected,
                          "external_comparator": external_comparator,
                          "selected_on": "the 2026-09-27 locked development replay (outputs/external_validation_20260927/replay)",
                          "freeze_components": freeze["components"]}
    (HERE / "baseline_selection.json").write_bytes(json.dumps(baseline_selection, indent=1).encode("utf-8"))

    summary = {"status": "internal replay on development data; not external validation",
               "freeze_verified": not freeze_problems, "freeze_problems": freeze_problems,
               "records": manifest["records"], "overall_status": PR.overall(statuses.values()),
               "status_by_tier": statuses, "tiers": tiers, "risk": risk, "calibration": calibration,
               "calibration_worst_strata": CA.worst_strata(calibration), "prediction_diagnostics": predictions,
               "figures": figures, "baseline_selection": baseline_selection,
               "not_executed": manifest.get("not_executed", {})}
    (OUT / "summary.json").write_bytes(json.dumps(summary, indent=1, default=float).encode("utf-8"))
    (OUT / "report.md").write_bytes(render(summary).encode("utf-8"))
    print(json.dumps({"overall": summary["overall_status"], "by_tier": statuses, "external_comparator": external_comparator,
                      "freeze_verified": summary["freeze_verified"]}, indent=1))


def render(summary: dict) -> str:
    lines = ["# Locked development replay: decision, risk and ablation report", "",
             f"Status: {summary['status']}. Records: {summary['records']:,}. "
             f"Freeze verified: {summary['freeze_verified']}. Overall status of `maestro_vc`: "
             f"**{summary['overall_status']}**.", ""]
    for name, t in summary["tiers"].items():
        arms = summary["risk"][name]["arms"]
        lines += [f"## {name}", "", f"Comparator (strongest baseline): `{t['comparator']}`. "
                  f"Integrity problems: {len(t['integrity_problems'])}. Primary status: **{t['primary_status']}**.", "",
                  "| Arm | Correct | Wrong | Decided | Selective risk | Measurements | Assay-days |",
                  "|---|---:|---:|---:|---:|---:|---:|"]
        for arm, a in sorted(arms.items(), key=lambda kv: -kv[1]["correct"]["estimate"]):
            if "@" in arm:
                continue
            sel = a["selective_risk"]["estimate"]
            lines.append(f"| `{arm}` | {rate_fmt(a['correct'])} | {rate_fmt(a['wrong'])} | {a['decided']['estimate']:.3f} | "
                         f"{'n/a' if sel is None else f'{sel:.3f}'} | {a['measurements']['estimate']:.2f} | {a['days']['estimate']:.2f} |")
        p = t["primary"]
        lines += ["", "Primary comparison, `maestro_vc` minus the comparator (95%, clustered by the unit):", "",
                  f"- correct {fmt(p['differences']['correct'])}; wrong {fmt(p['differences']['wrong'])}; "
                  f"measurements {fmt(p['differences']['measurements'], 2)}; assay-days {fmt(p['differences']['days'], 2)}",
                  f"- `maestro_vc` wrong-risk {rate_fmt(p['wrong_rate'])}",
                  f"- gates: G1 {p['G1_integrity']['pass']}, G2 pass {p['G2_safety']['pass']} / reject {p['G2_safety']['reject']}, "
                  f"G3 non-inferior {p['G3_effectiveness']['pass']} / superior {p['G3_effectiveness']['superior']} / reject "
                  f"{p['G3_effectiveness']['reject']}, G4 {p['G4_benefit']['pass']}, G5 available {p['G5_external_replication']['available']}, "
                  f"G6 {t['virtual_cell_gate']['pass']}", ""]
        lines += ["Secondary candidates (Bonferroni 98.75%):", ""]
        for c, s in t["secondary"].items():
            d = s["gates"]["differences"]
            lines.append(f"- `{c}`: correct {fmt(d['correct'])}, wrong {fmt(d['wrong'])}, measurements "
                         f"{fmt(d['measurements'], 2)} -> **{s['status']}**")
        lines += ["", "Virtual-cell ablation:", ""]
        for pair, a in t["ablation"].items():
            lines.append(f"- {pair}: first-step switch {a['first_step_switch_rate']:.3f}, any-step switch "
                         f"{a['any_step_switch_rate']:.3f}; correct {fmt(a['overall']['correct'])}, wrong "
                         f"{fmt(a['overall']['wrong'])}; {a['acquisition_value']}")
        lines.append("")
    lines += ["## Prediction diagnostics (secondary)", "",
              "| Tier | Rows (detected) | VC cosine | Ridge cosine | Training-mean cosine | VC - mean | Ridge - mean |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for name, d in summary["prediction_diagnostics"].items():
        x = d["detected"]
        lines.append(f"| {name} | {x['rows']} | {x.get('mean_cosine_vc', float('nan')):.3f} | "
                     f"{x.get('mean_cosine_ridge', float('nan')):.3f} | {x.get('mean_cosine_train_mean', float('nan')):.3f} | "
                     f"{fmt(x['vc_minus_train_mean']) if 'vc_minus_train_mean' in x else 'n/a'} | "
                     f"{fmt(x['ridge_minus_train_mean']) if 'ridge_minus_train_mean' in x else 'n/a'} |")
    lines += ["", "## Calibration of chosen-action forecasts (diagnostic)", "",
              "| Arm | n | P(correct) mean | observed | ECE | intercept | slope | P(wrong) mean | observed wrong |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, c in summary["calibration"].items():
        a, w = c["all"]["correct"], c["all"]["wrong"]
        lines.append(f"| {name} | {a['n']} | {a['mean_forecast']:.3f} | {a['observed']:.3f} | {a['ece']:.3f} | "
                     f"{a['intercept'] if a['intercept'] is None else round(a['intercept'], 2)} | "
                     f"{a['slope'] if a['slope'] is None else round(a['slope'], 2)} | {w['mean_forecast']:.3f} | {w['observed']:.3f} |")
    lines += ["", "Largest stratum miscalibration (correct-reading forecasts, strata with 50 or more):", ""]
    for r in summary["calibration_worst_strata"][:8]:
        lines.append(f"- {r['arm']} / {r['stratum']}={r['level']}: n {r['n']}, forecast {r['mean_forecast']:.3f}, "
                     f"observed {r['observed']:.3f}, ECE {r['ece']:.3f}")
    lines += ["", "## Pareto sets", ""]
    for name, r in summary["risk"].items():
        lines.append(f"- {name}: all arms {', '.join(f'`{a}`' for a in r['pareto_all'])}; under the wrong-risk cap "
                     f"{', '.join(f'`{a}`' for a in r['pareto_under_cap'])}")
    lines += ["", "## Figures", ""] + [f"- [{k}](figures/{Path(v).name})" for k, v in summary["figures"].items()]
    lines += ["", f"External comparator frozen for a future study: `{summary['baseline_selection']['external_comparator']}`.",
              f"Not executed: {summary['not_executed']}.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
