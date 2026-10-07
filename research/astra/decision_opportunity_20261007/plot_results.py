"""Standalone scientific figures from existing results; no outcomes are generated."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent


def main():
    rows = list(csv.DictReader((HERE / "budget_frontier1/FRONTIER.csv").open(encoding="utf-8")))
    contexts = ["PANC-1", "HepG2/C3A"]
    arms = [("M0", "fixed_top_prior", "Empirical prior, fixed", "#999999", "--"),
            ("M0", "knowledge_gradient", "Empirical prior, KG", "#333333", "-"),
            ("M2", "fixed_top_prior", "STATE correction, fixed", "#0072B2", "--"),
            ("M2", "knowledge_gradient", "STATE correction, KG", "#D55E00", "-")]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=False, constrained_layout=True)
    for ax, context in zip(axes, contexts):
        for model, policy, label, color, style in arms:
            points = sorted((r for r in rows if r["context"] == context and r["model"] == model
                             and r["policy"] == policy), key=lambda r: int(r["screens"]))
            ax.plot([int(r["counterfactual_credits"]) for r in points],
                    [float(r["utility"]) for r in points], color=color, linestyle=style, marker="o",
                    markersize=3, label=label)
        ax.set(title=context, xlabel="Counterfactual profile credits (K + 5)", xticks=range(5,14))
        ax.grid(alpha=.2)
        ax.set_ylabel("Sum of five independent well-B RNA projections")
    axes[1].legend(fontsize=8, loc="lower right")
    fig.suptitle("Exploratory development frontier — all prefixes, no new purchases", fontsize=11)
    for suffix in ("png", "pdf"):
        fig.savefig(HERE / ("budget_frontier1/FRONTIER." + suffix), dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
