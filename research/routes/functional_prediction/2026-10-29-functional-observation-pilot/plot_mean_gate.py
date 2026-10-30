"""Render saved original-fit summaries only; no raw data or model refitting."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
result = json.loads((root / "primary_result.json").read_text(encoding="utf-8"))
receipt = json.loads((root / "execution_receipt.json").read_text(encoding="utf-8"))
outer = json.loads((root / "primary_outer_execution.json").read_text(encoding="utf-8"))
assert receipt["state"] == "complete" and outer["returncode"] == 0
plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.facecolor": "white"})
fig, axes = plt.subplots(2, 4, figsize=(15, 7), layout="constrained")
for ax, (cell, point) in zip(axes.flat, result["point"].items()):
    times = point["times_hours"]
    ax.plot(times, point["train_mean"], "o", ms=4, color="#a0a0a0", label="Training mean")
    ax.plot(times, point["validation_mean"], "s", ms=4, color="#252525", label="Validation mean")
    ax.plot(times, point["predictions"][0], "-", lw=1.8, color="#376b96", label="Exponential fit")
    ax.plot(times, point["predictions"][1], "--", lw=1.8, color="#ba633f", label="Curvature fit")
    ax.set_title(f"{cell}   D = {point['D']:.3g}", loc="left", fontsize=11)
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Arithmetic mean live count")
    ax.grid(axis="y", alpha=0.15)
text_ax = axes.flat[-1]
text_ax.axis("off")
q05, q95 = result["stability_q05_q95"]
text_ax.text(0.02, 0.98,
             "Fixed seven-plate comparison\n\n"
             f"Mean D = {result['Delta']:.6g}\n"
             f"Row-block 5th/95th percentiles:\n{q05:.6g}, {q95:.6g}\n\n"
             "500 prechosen resamples\n"
             "Not a biological confidence interval\n"
             "No latent-rate or drug validation\n\n"
             "Each plate has its own count axis.\n"
             "Lines connect predictions at observed frames.",
             va="top", fontsize=11, linespacing=1.5)
handles, labels = axes.flat[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="outside lower center", ncol=4, frameon=False)
fig.suptitle("Control trajectories: a conditional mean-prediction prerequisite", fontsize=16)
fig.savefig(root / "mean_gate.png", dpi=170)
