"""Plot every registered development prefix; no fitted summary or interval."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("Use a new figure directory")
    args.out.mkdir(parents=True)
    source = Path(__file__).resolve().parent / "budget_frontier1" / "FRONTIER.csv"
    with source.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    colors = {"M0": "#515151", "M1": "#d99b12", "M2": "#1768ac", "M21": "#9b4b9f"}
    names = {"M0": "Empirical", "M1": "Gene-gated", "M2": "STATE", "M21": "Both"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.3))
    for ax, context in zip(axes, ("PANC-1", "HepG2/C3A")):
        for model, color in colors.items():
            for policy, linestyle in (("fixed_top_prior", "-"), ("knowledge_gradient", "--")):
                values = sorted((r for r in rows if r["context"] == context
                                 and r["model"] == model and r["policy"] == policy),
                                key=lambda r: int(r["screens"]))
                ax.plot([int(r["counterfactual_credits"]) for r in values],
                        [float(r["utility"]) for r in values], color=color,
                        linestyle=linestyle, marker=".", linewidth=1.6,
                        label=f"{names[model]} / {'fixed' if linestyle == '-' else 'KG'}")
        ax.set(title=context, xlabel="Replay profiles: A acquisitions + 5 B confirmations",
               ylabel="Sum of 5 B transcript projections", xticks=range(5, 14))
        ax.grid(alpha=0.18)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.045),
               ncol=4, frameon=False, fontsize=9)
    fig.suptitle("Development budget frontier — two previously exposed cells", fontsize=13)
    fig.text(0.5, 0.012, "All 144 prefixes shown. Posthoc replay; no new measurements or population inference.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.18, 1, 0.94))
    for suffix in ("png", "svg"):
        fig.savefig(args.out / f"budget_frontier.{suffix}", dpi=180)
    plt.close(fig)
    receipt = {"input": str(source.relative_to(Path.cwd())),
               "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "points": len(rows), "interpretation": "Descriptive posthoc development frontier"}
    (args.out / "FIGURE_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
