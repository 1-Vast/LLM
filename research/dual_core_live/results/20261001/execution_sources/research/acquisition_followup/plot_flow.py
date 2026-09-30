"""Render recorded held-out LINCS metrics and measured population endpoints."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

OUT = Path(__file__).resolve().parents[2] / "outputs/acquisition_followup/lincs"


def main():
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    trace = json.loads((OUT / "flow_traces.json").read_text(encoding="utf-8"))[0]
    arms = ["persistence", "training_target_mean", "global_scaled_persistence", "ridge_residual", "ridge_shuffled_test_source"]
    labels = ["Keep 6 h state", "Training 24 h mean", "Scalar calibration", "Learned transition", "Shuffled early state"]
    colors = ["#7b8794", "#7b8794", "#7b8794", "#086b83", "#ba7037"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.titleweight": "bold"})
    fig = plt.figure(figsize=(13, 8.6), facecolor="white")
    grid = fig.add_gridspec(2, 2, height_ratios=[1.1, 1], left=.18, right=.95, top=.83, bottom=.17,
                          hspace=.64, wspace=.46)
    for column, (metric, title) in enumerate((("cosine", "Profile direction: cosine (higher is better)"),
                                              ("mse", "Profile error: MSE (lower is better)"))):
        ax = fig.add_subplot(grid[0, column])
        for index, arm in enumerate(arms):
            record = summary["metrics"][arm][metric]
            mean, bounds = record["mean"], record["ci95"]
            ax.errorbar(mean, index, xerr=np.array([[mean - bounds[0]], [bounds[1] - mean]]),
                        fmt="o", color=colors[index], markersize=6, capsize=4, linewidth=1.8)
        ax.set_yticks(range(len(arms)), labels if column == 0 else [""] * len(arms))
        ax.invert_yaxis()
        ax.set_ylim(4.6, -.6)
        ax.set_title(title, loc="left", fontsize=11, pad=12)
        ax.grid(axis="x", alpha=.18)
        ax.set_axisbelow(True)
        ax.set_xlabel("Mean and 95% compound-bootstrap interval")

    ax = fig.add_subplot(grid[1, :])
    palette = ["#086b83", "#b65d28", "#6d5597", "#4d7c39"]
    for gene, color in zip(trace["largest_measured_changes"][:4], palette):
        ax.plot([6, 24], [gene["source"], gene["target"]], linestyle="--", linewidth=1.2,
                color=color, alpha=.65)
        ax.scatter([6, 24], [gene["source"], gene["target"]], color=color, s=42, zorder=3)
        ax.scatter(24, gene["prediction"], color=color, marker="x", s=85, linewidths=2, zorder=4)
    ax.axhline(0, color="#adb5bd", linewidth=.8)
    ax.set_xticks([6, 24], ["6 h: measured source", "24 h: measured target + predicted target"])
    ax.set_xlim(4, 27)
    ax.set_ylabel("Cached plate-normalized RNA shift")
    ax.set_title(f"First predetermined held-out case: {trace['annotation']['name']} ({trace['pert_id']})",
                 loc="left", fontsize=11, pad=12)
    handles = [Line2D([0], [0], color=color, linewidth=2, label=gene["symbol"])
               for gene, color in zip(trace["largest_measured_changes"][:4], palette)]
    handles += [Line2D([0], [0], color="#343a40", marker="o", linestyle="none", label="Measured endpoint"),
                Line2D([0], [0], color="#343a40", marker="x", linestyle="none", markersize=8, label="Model prediction")]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0, -.22), frameon=False, ncol=6,
              fontsize=9, handletextpad=.45, columnspacing=1.2)
    fig.text(.08, .955, "Real-data dynamics: early state informs later direction", fontsize=20, weight="bold", color="#163640")
    fig.text(.08, .913, "LINCS L1000 | A549 | 10 uM | 6 h to 24 h | 244 held-out conditions, 243 chemical identities", fontsize=11)
    fig.text(.08, .881, "Learned transition improves direction; its MSE does not clearly beat the training mean. No selector promotion.", fontsize=10, color="#5c6770")
    fig.text(.08, .055, "Dashed lines connect two separate measured populations; they are not observed cell trajectories or intermediate states.\n"
             "Case genes are the four largest observed endpoint changes (descriptive only). Predictions remain planning inputs, never evidence.",
             fontsize=9, color="#5c6770", linespacing=1.5)
    target = OUT / "flow_analysis.png"
    fig.savefig(target, dpi=180)
    plt.close(fig)
    print(target)


if __name__ == "__main__":
    main()
