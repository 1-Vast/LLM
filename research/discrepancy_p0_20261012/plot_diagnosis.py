"""Plot descriptive archived diagnostics from the retained summary only."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "runs/archive/RESULTS.json").read_text())
arms = result["arms"]
prior, conditional = arms["zero_purchase"], arms["conditional"]
reductions = [100 * (1 - conditional["mean_mse"][band] / prior["mean_mse"][band])
              for band in ("all", "selected_prior", "boundary")]
reductions.append(100 * (1 - conditional["mean_pairwise_difference_mse"]
                        / prior["mean_pairwise_difference_mse"]))

plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "svg.fonttype": "none"})
fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.5))
axes[0].bar(np.arange(4), reductions, color=["#517da5"] * 3 + ["#bb7744"], width=.62)
axes[0].set_xticks(np.arange(4), ["All drugs", "Prior top 10", "Prior 11-30", "Top 10 vs\nnext 10 pairs"])
axes[0].set_ylim(0, 27)
axes[0].set_ylabel("MSE reduction vs prior (%)")
axes[0].set_title("Conditional update: prediction and ranking", loc="left", fontsize=11)
for position, value in enumerate(reductions):
    axes[0].text(position, value + .7, f"{value:.2f}%", ha="center")
axes[0].text(.02, .95, "106 exposed contexts; same observed mask per arm",
             transform=axes[0].transAxes, fontsize=8, va="top")

names = ["lowrank", "conditional"]
x = np.arange(len(names))
positive = [arms[name]["mean_positive_contribution"] for name in names]
negative = [arms[name]["mean_negative_contribution"] for name in names]
axes[1].bar(x, positive, color="#517da5", width=.45, label="Improving-context contribution")
axes[1].bar(x, negative, color="#bb7744", width=.45, label="Harming-context contribution")
axes[1].scatter(x, [arms[name]["mean_utility_increment"] for name in names],
                color="#202934", s=40, zorder=3, label="Mean utility increment")
axes[1].scatter(x, [arms[name]["scenario_net_increment"]["0.001"] for name in names],
                color="#202934", marker="x", s=55, zorder=3, label="After declared 0.01 cost")
axes[1].axhline(0, color="#555555", linewidth=.8)
axes[1].set_xticks(x, ["Low rank", "Conditional"])
axes[1].set_ylim(-.078, .079)
axes[1].set_ylabel("Mean top-10 utility increment")
axes[1].set_title("Selection: losses outweigh gains", loc="left", fontsize=11)
axes[1].text(.02, .95, "101 complete paired contexts; contributions divided by 101",
             transform=axes[1].transAxes, fontsize=8, va="top")
axes[1].legend(loc="lower left", fontsize=7, frameon=False)
fig.text(.07, .035, "Exposed retrospective diagnosis. No new policy, inferential intervals, or independent biological confirmation.", fontsize=8)
fig.subplots_adjust(left=.08, right=.98, top=.87, bottom=.2, wspace=.38)
output = HERE / "figures"
output.mkdir(exist_ok=True)
for extension in ("png", "svg"):
    fig.savefig(output / f"decision_diagnosis.{extension}", dpi=180)
plt.close(fig)
print(str(output / "decision_diagnosis.png"))
