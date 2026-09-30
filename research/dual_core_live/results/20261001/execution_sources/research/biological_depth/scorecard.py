"""Render audit.json (and optional calibration and agent-probe results) as Markdown tables.

File summary
- Path: research/biological_depth/scorecard.py
- Purpose: produce the tables quoted in the day record directly from the result files, so no
  number in the record is copied by hand.
- Run: python research/biological_depth/scorecard.py --audit <audit.json> [--calibration <json> ...]
       [--probe <summary.json>] --output <scorecard.md>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ORDER = ("zero", "systematic", "ridge_chem", "knn_chem", "mlp_existing", "latent_pca", "latent_mae",
         "latent_jepa", "latent_jepa_moa", "latent_jepa_moa_shuffled")


def ci(value: dict | None) -> str:
    if not value or value.get("mean") is None:
        return "n/a"
    low, high = value["ci95"]
    return f"{value['mean']:.3f} [{low:.3f}, {high:.3f}]"


def num(value) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, nargs="*", default=[])
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    r = json.loads(args.audit.read_text(encoding="utf-8"))
    arms = [a for a in ORDER if a in r["B1"]]
    out = [f"Population: {r['population']['conditions']} conditions, {r['population']['responsive']} responsive "
           f"(by line {r['population']['responsive_by_line']}; by dose {r['population']['responsive_by_dose']}).", ""]
    out += ["Replicate ceiling (rep 1 vs rep 2, centered): responsive " + ci(r["ceiling"]["responsive"]) +
            "; all " + ci(r["ceiling"]["all"]), ""]
    out += ["| Arm | B1 responsive | B1 all | B1 scrambled | MSE skill | MSE skill scrambled |", "|---|---|---|---|---|---|"]
    for a in arms:
        b2 = r["B2"][a]
        out.append(f"| `{a}` | {ci(r['B1'][a]['responsive'])} | {ci(r['B1'][a]['all'])} | "
                   f"{ci(b2['b1_scrambled_responsive'])} | {ci(b2['mse_skill_responsive'])} | "
                   f"{ci(b2['mse_skill_scrambled_responsive'])} |")
    b3 = r["B3"]
    out += ["", f"B3 mechanism retrieval, {b3['scored_compounds']} compounds in {b3['classes']} classes: observed-profile "
            f"ceiling {ci(b3['observed_ceiling'])}; chemistry nearest neighbour {ci(b3['chemistry_nearest_neighbour'])}; "
            f"chance {ci(b3['chance'])}.", "", "| Arm | B3 accuracy | B4 potency A549 / K562 / MCF7 | B5 context r | "
            "B5 interaction r | B5 top-line accuracy (majority rate) |", "|---|---|---|---|---|---|"]
    for a in arms:
        b4 = r["B4"][a]
        b5, b5i = r["B5"][a], r["B5_interaction"][a]
        out.append(f"| `{a}` | {ci(b3['arms'].get(a))} | {num(b4['A549'])} / {num(b4['K562'])} / {num(b4['MCF7'])} | "
                   f"{ci(b5['correlation'])} | {ci(b5i['correlation'])} | {ci(b5['top_line_accuracy'])} "
                   f"({num(b5['majority_line_rate'])}) |")
    observed = r["B6"]["observed"]
    held = [k for k, v in observed.items() if v["passed"]]
    out += ["", "Anchors holding in the observed data: " + (", ".join(f"`{k}`" for k in held) or "none") +
            f" ({len(held)} of {len(observed)}); not holding: " +
            (", ".join(f"`{k}`" for k, v in observed.items() if not v["passed"]) or "none") + ".", "",
            "| Arm | Anchors reproduced out of fold | Passed although absent in data |", "|---|---|---|"]
    for a in arms:
        b6 = r["B6"][a]
        out.append(f"| `{a}` | {len(b6['reproduced'])} of {len(held)}: {', '.join(b6['reproduced']) or '-'} | "
                   f"{', '.join(b6['passed_but_absent_in_data']) or '-'} |")
    out += ["", "| Arm | B7 spread vs RMSE (registered) | B7 scale-free | B1 confident half | B8 PRISM |",
            "|---|---|---|---|---|"]
    for a in arms:
        b7 = r["B7"].get(a) or {}
        reg, free = b7.get("registered_spread_vs_rmse"), b7.get("scale_free_relative_spread_vs_centered_error")
        fmt = (lambda v: "n/a" if not v else f"{v['spearman']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]")
        out.append(f"| `{a}` | {fmt(reg)} | {fmt(free)} | {ci(b7.get('b1_confident_half'))} | "
                   f"{num(r['B8'].get('arms', {}).get(a))} |")
    out += ["", f"B8 observed: Spearman(shift norm, -PRISM AUC) = {num(r['B8'].get('observed'))} over "
            f"{r['B8'].get('matched_compound_lines')} compound-lines.", ""]
    p = r["primary"]
    out += [f"P1 `latent_jepa` - `knn_chem` (B1 responsive): {ci(p['P1_jepa_minus_knn'])}",
            f"P2 `latent_jepa` - `latent_pca`: {ci(p['P2_jepa_minus_pca'])}",
            f"P3 anchors: `latent_jepa` {p['P3_anchors']['latent_jepa']}, `mlp_existing` {p['P3_anchors']['mlp_existing']}, "
            f"held in data {p['P3_anchors']['held_in_data']}", ""]
    keys = ("specific_signal", "beyond_retrieval", "near_ceiling", "anchor_depth", "knows_what_it_does_not_know",
            "sufficient_for_advisory_ranking")
    out += ["| Arm | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
    for a in arms:
        v = r["verdicts"].get(a)
        if v:
            out.append(f"| `{a}` | " + " | ".join("yes" if v[k] else "no" for k in keys) + " |")
    for path in args.calibration:
        c = json.loads(path.read_text(encoding="utf-8"))
        out += ["", f"Calibration `{c['arm']}` at {c['level']}: mean coverage {c['mean_coverage']:.3f}; readouts at or "
                f"above 0.70: {c['share_readouts_at_or_above_0.70']:.2f}; in distribution {c['coverage_in_distribution']:.3f}, "
                f"novel {c['coverage_novel']:.3f}; passed: {c['passed']}."]
    if args.probe:
        s = json.loads(args.probe.read_text(encoding="utf-8"))
        out += ["", f"Agent probe, {s['items']} compounds, {len(s['options'])} classes (chance {s['chance']:.3f}):", "",
                "| Arm | Accuracy |", "|---|---|"]
        out += [f"| `{k}` | {ci(v)} |" for k, v in s["accuracy"].items()]
        out += ["", f"DeepSeek card minus signature: {ci(s['primary_deepseek_card_minus_signature'])}; "
                f"Jev card minus signature: {ci(s['jev_card_minus_signature'])}; DeepSeek card minus tool: "
                f"{ci(s['deepseek_card_minus_tool'])}; Jev agreement over repeats: {num(s['jev_pairwise_agreement_first10'])}; "
                f"spend DeepSeek ${s['spend']['deepseek_usd']:.4f} over {s['spend']['deepseek_calls']} calls, "
                f"Jev about ${s['spend']['jev_usd_estimate']:.4f}."]
    args.output.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
