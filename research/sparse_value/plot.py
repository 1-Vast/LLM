"""Plot all recorded acquisition-price assumptions; no fitting or rerunning."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

OUT = Path(__file__).resolve().parents[2] / "outputs/sparse_value/evaluation"
TIERS = (("sciplex3", "A"), ("sciplex3", "B"), ("l1000", "LT"), ("l1000", "T"))
BASELINES = {"fixed_fallback": ("Repaired fallback", "#b37428", "s"),
             "fixed": ("Fixed sequence", "#74808c", "D"),
             "da_unconditioned": ("Single-step discrimination", "#73598e", "^")}


def main():
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.titleweight": "bold"})
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), layout="constrained")
    price_colors = plt.colormaps["viridis"](np.linspace(.12, .9, 7))
    for ax, (dataset, tier) in zip(axes.flat, TIERS):
        rows = [r for r in summary["cost_curves"] if r["dataset"] == dataset and r["tier"] == tier]
        sparse = sorted([r for r in rows if r["policy"].startswith("sparse_")], key=lambda r: r["cost_per_measurement"])
        prices = [r["cost_per_measurement"] for r in sparse]
        positions = np.arange(len(prices))
        ax.plot(positions, [r["net"] for r in sparse], "o-", color="#086b83", linewidth=2, label="Sparse conditional value")
        for policy, (label, color, marker) in BASELINES.items():
            values = sorted([r for r in rows if r["policy"] == policy], key=lambda r: r["cost_per_measurement"])
            ax.plot(positions, [r["net"] for r in values], marker=marker, linestyle="--", color=color, label=label, markersize=4)
        ax.axhline(0, color="#adb5bd", linewidth=.8)
        ax.set_xticks(positions, [f"{price:g}" for price in prices])
        ax.set_title(f"{dataset.upper()} / {tier}", loc="left")
        ax.set_xlabel("Price per assay (utility units; displayed as ordered scenarios)")
        ax.set_ylabel("Net = correct - 2 x wrong - price x assays")
        ax.grid(alpha=.18)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Decision value across every stated assay price\nExploratory grouped holdout replay; each comparator uses the same price", fontsize=16)
    fig.savefig(OUT / "cost_curves.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(13, 9), layout="constrained")
    for ax, (dataset, tier) in zip(axes.flat, TIERS):
        rows = [r for r in summary["cost_curves"] if r["dataset"] == dataset and r["tier"] == tier and r["policy"].startswith("sparse_")]
        rows.sort(key=lambda r: r["cost_per_measurement"])
        ax.plot([r["measurements"] for r in rows], [r["correct"] for r in rows], color="#086b83", linewidth=1, alpha=.5)
        ax.scatter([r["measurements"] for r in rows], [r["correct"] for r in rows], s=50, c=price_colors,
                   edgecolors="white", linewidths=.45, zorder=4, label="Sparse value (price colors below)")
        for policy, (label, color, marker) in BASELINES.items():
            row = next(r for r in summary["rates"] if (r["dataset"], r["tier"], r["policy"]) == (dataset, tier, policy))
            ax.scatter(row["measurements"], row["correct"], s=65, marker=marker, color=color, label=label)
        wrong = [r["wrong"] for r in rows]
        ax.set_title(f"{dataset.upper()} / {tier} | sparse wrong: {min(wrong):.3f}-{max(wrong):.3f}", loc="left", fontsize=11)
        ax.set_xlabel("Mean real assays purchased")
        ax.set_ylabel("Correct decision rate")
        ax.margins(x=.2, y=.25)
        ax.grid(alpha=.18)
        ax.legend(frameon=False, fontsize=8, loc="best")
    price_handles = [Line2D([0], [0], marker="o", linestyle="none", color=color, label=f"Price {price:g}")
                     for color, price in zip(price_colors, (0, .005, .01, .02, .05, .1, .2))]
    fig.legend(handles=price_handles, loc="outside lower center", ncol=7, frameon=False)
    fig.suptitle("Assay use versus correct decisions\nAll seven assay prices shown; connecting lines link policies, not biological trajectories", fontsize=16)
    fig.savefig(OUT / "decision_frontier.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5), layout="constrained")
    for ax, (dataset, tier) in zip(axes.flat, TIERS):
        rows = [r for r in summary["cost_curves"] if r["dataset"] == dataset and r["tier"] == tier and r["policy"].startswith("sparse_")]
        rows.sort(key=lambda r: r["cost_per_measurement"])
        positions = np.arange(len(rows))
        ax.plot(positions, [r["wrong"] for r in rows], "o-", color="#086b83", label="Sparse conditional value")
        for policy, (label, color, _) in BASELINES.items():
            row = next(r for r in summary["rates"] if (r["dataset"], r["tier"], r["policy"]) == (dataset, tier, policy))
            ax.axhline(row["wrong"], color=color, linestyle="--", label=label)
        ax.set_xticks(positions, [f"{r['cost_per_measurement']:g}" for r in rows])
        ax.set_title(f"{dataset.upper()} / {tier}", loc="left")
        ax.set_xlabel("Price per assay (ordered scenarios)")
        ax.set_ylabel("Wrong decision rate per episode")
        ax.set_ylim(bottom=0)
        ax.grid(alpha=.18)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Wrong-decision risk across assay prices\nPoint estimates; paired grouped confidence intervals are in summary.json", fontsize=16)
    fig.savefig(OUT / "wrong_risk.png", dpi=180)
    plt.close(fig)
    print("Saved cost_curves.png, decision_frontier.png and wrong_risk.png")


if __name__ == "__main__":
    main()
