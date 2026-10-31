"""Render the fixed C2 comparisons; no fitting or selection changes."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
RUN = ROOT.parents[3] / "data/processed/virtual_cell_dose_transfer_20261030/c2_hts001"
summary = json.loads((RUN/"summary.json").read_text())
methods = [m for m in summary["methods"] if m != "wrong_shape"]
methods.sort(key=lambda m:summary["methods"][m]["primary"]["aggregate"])
labels = {"source_mean":"Source mean (no anchors)","linear":"Two-anchor interpolation",
    "additive_shape":"Additive anchored shape","candidate":"Candidate scaled shape",
    "pooled_shape":"Pooled normalized shape","full_anchored_ridge":"Full anchored ridge",
    "joint_covariance":"Joint covariance update","smooth_gp":"Smooth GP",
    "hill_map":"Regularized Hill","profile_neighbor":"Profile neighbor","profile_tree":"Profile tree"}
colors = ["#bd684b" if m=="candidate" else "#527c8a" if m in ["joint_covariance","additive_shape"] else "#a7aaa9" for m in methods]
fig, axes = plt.subplots(1,2,figsize=(12,6.2),sharey=True)
for ax,key,title in zip(axes,["primary","best_drug"],["Pairwise choice regret (primary)","Whole-menu best-drug regret (secondary)"]):
    values = [summary["methods"][m][key]["aggregate"] for m in methods]
    positions = np.arange(len(methods))
    ax.barh(positions,values,color=colors,height=.67)
    ax.set_yticks(positions,labels=[labels[m] for m in methods])
    ax.set_xlim(0,max(values)*1.25)
    for pos,value in zip(positions,values):
        ax.text(value+max(values)*.018,pos,f"{value:.5f}",va="center",fontsize=8.5)
    ax.set_title(title,fontsize=11,pad=12)
    ax.set_xlabel("Mean regret in log2 interval-growth units; lower is better",fontsize=9)
    ax.tick_params(axis="y",length=0,labelsize=9)
    ax.spines[["top","right","left"]].set_visible(False)
    ax.grid(axis="x",alpha=.12)
    ax.set_axisbelow(True)
axes[0].invert_yaxis()
fig.suptitle("HTS001: held-out backgrounds with two measured doses per compound",fontsize=13,y=.97)
fig.text(.02,.035,"Six related PC9 backgrounds; exposed development data. Historical full curves are available to every model.\nThe wrong-drug diagnostic is omitted from this plot. Interval growth does not identify cell death or clinical benefit.",fontsize=8.5,color="#555555")
fig.tight_layout(rect=[0,.1,1,.92])
(ROOT/"figures").mkdir(exist_ok=True)
fig.savefig(ROOT/"figures/selection_regret.png",dpi=180)
fig.savefig(ROOT/"figures/selection_regret.svg")
plt.close(fig)
print(str(ROOT/"figures/selection_regret.png"))
