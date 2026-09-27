"""Descriptive figures for the report: key arms across development tiers and the external study.

File summary
- Path: research/belief_planning/figures.py
- Purpose: read the frozen analysis summaries and draw two panels per setting. Panel 1: correct
  decisions against measurements, for the key arms with 95% intervals. Panel 2: the paired
  difference from the fixed order for the agent and its controls. Registered after the runs;
  it adds no endpoint, only a legible view of `summary.json`.
- Run: python -m research.belief_planning.figures
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "belief_planning_20260927"
KEY = ("fixed", "belief", "anchored", "belief_vc_masked", "belief_feedback_withheld", "belief_h1", "myopic_edv",
       "retrieval", "marginal_only", "maestro_vc", "oracle")
COLOURS = {"belief": "#b2182b", "anchored": "#ef8a62", "fixed": "#2166ac", "oracle": "#999999"}


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    settings = {}
    for path in (OUT / "registered" / "dev_analysis" / "summary.json", OUT / "external" / "analysis" / "summary.json"):
        if path.exists():
            settings.update(json.loads(path.read_text(encoding="utf-8")))
    names = list(settings)
    fig, axes = plt.subplots(2, len(names), figsize=(3.6 * len(names), 7.2), squeeze=False)
    for j, name in enumerate(names):
        arms = settings[name]["arms"]
        ax = axes[0][j]
        for arm in KEY:
            if arm not in arms:
                continue
            v = arms[arm]
            c = v["correct"]
            ax.errorbar(v["measurements"]["estimate"], c["estimate"], yerr=[[c["estimate"] - c["ci"][0]], [c["ci"][1] - c["estimate"]]],
                        fmt="o", ms=4, lw=0.8, color=COLOURS.get(arm, "#4d4d4d"))
            ax.annotate(arm, (v["measurements"]["estimate"], c["estimate"]), fontsize=6, xytext=(3, 2), textcoords="offset points")
        ax.set_title(name, fontsize=9)
        ax.set_xlabel("measurements per episode", fontsize=8)
        if j == 0:
            ax.set_ylabel("correct terminal decisions", fontsize=8)
        ax = axes[1][j]
        gates = settings[name]["gates"].get("belief", {}).get("fixed")
        rows = []
        if gates:
            rows.append(("belief - fixed", gates["differences"]["correct"]))
        anchored = settings[name]["gates"].get("anchored", {}).get("fixed")
        if anchored:
            rows.append(("anchored - fixed", anchored["differences"]["correct"]))
        for what in ("virtual_cell", "feedback", "lookahead"):
            for control, v in (settings[name]["attribution"].get(what) or {}).get("controls", {}).items():
                rows.append((f"belief - {control.replace('belief_', '')}", v["overall"]["correct"]))
        for i, (label, d) in enumerate(rows):
            ax.errorbar(d["difference"], i, xerr=[[d["difference"] - d["ci"][0]], [d["ci"][1] - d["difference"]]],
                        fmt="o", ms=4, color="#b2182b" if i == 0 else "#4d4d4d")
        ax.axvline(0, color="k", lw=0.5)
        ax.axvline(0.02, color="k", lw=0.5, ls=":")
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([r[0] for r in rows], fontsize=6)
        ax.invert_yaxis()
        ax.set_xlabel("paired correct difference (95% CI); dotted = MPIE", fontsize=7)
    fig.tight_layout()
    target = OUT / "figures" / "belief_planning_overview.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=150)
    print(target)


if __name__ == "__main__":
    main()
