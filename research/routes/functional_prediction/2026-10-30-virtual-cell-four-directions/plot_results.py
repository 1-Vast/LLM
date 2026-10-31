"""Plot saved source-grouped metrics and an observed technical dose example."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[3]
RESULTS=PROJECT/"data/processed/virtual_cell_four_directions_20261030/pilot_b_maestro"


def main():
    figures=ROOT/"figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    scores=pd.read_csv(RESULTS/"summary.csv")
    rare=scores[scores.subset=="rare"].set_index("method").precision
    panel=rare.sort_values(ascending=False).head(5).index.tolist()
    for name in ["conditional_residual","source_balanced_global","permuted_context"]:
        if name not in panel:panel.append(name)
    panel=sorted(panel,key=lambda name:rare[name])
    labels={"full_rank_ridge":"Full-rank ridge","balanced_rationale":"Source-balanced rationale",
            "nonlinear_tree":"Nonlinear tree","balanced_screen_type":"Source-balanced screen type",
            "balanced_coarse_phenotype":"Source-balanced phenotype","official_style_knn":"Official-style text neighbor",
            "conditional_residual":"Candidate conditional residual","source_balanced_global":"Source-balanced gene prior",
            "permuted_context":"Candidate with permuted context"}
    fig,ax=plt.subplots(figsize=(9,5.1))
    colors=["#2878a5" if name=="conditional_residual" else "#c49a6c" if name=="permuted_context" else "#909a9e" for name in panel]
    ax.barh(range(len(panel)),[100*rare[name] for name in panel],color=colors,height=.65)
    ax.set_yticks(range(len(panel)),[labels.get(name,name) for name in panel])
    for i,name in enumerate(panel):ax.text(100*rare[name]+.12,i,f"{100*rare[name]:.2f}%",va="center",fontsize=9)
    ax.set_xlabel("Rare-gene P@50 (%) · equal weight per source group")
    ax.set_title("B: conditional residual learning versus ordinary predictors",loc="left",weight="bold",pad=12)
    ax.set_xlim(0,100*max(rare)*1.2)
    ax.grid(axis="x",alpha=.15);ax.set_axisbelow(True)
    fig.text(.02,.015,"Historical training tasks only; five source-grouped holdouts. Retrospective binary hits; no independent biological validation.",fontsize=8,color="#555555")
    fig.tight_layout(rect=(0,.05,1,1))
    fig.savefig(figures/"b_model_comparison.png",dpi=180,bbox_inches="tight")
    fig.savefig(figures/"b_model_comparison.svg",bbox_inches="tight")
    plt.close(fig)
    wells=pd.read_csv(ROOT/"census_c_wells.csv")
    first,second="bortezomib","paclitaxel"
    fig,ax=plt.subplots(figsize=(8.2,5.1))
    for cell,group in wells.groupby("cell.line"):
        a=group[group.drug1==first].groupby("drug1.conc").relative_growth.mean()
        b=group[group.drug1==second].groupby("drug1.conc").relative_growth.mean()
        common=sorted(set(a.index)&set(b.index))
        ax.plot(np.array(common)*1e6,[a[x]-b[x] for x in common],"o-",markersize=4,label=cell,lw=1.5)
    ax.axhline(0,color="#333333",lw=1)
    for y in [-.25,.25]:ax.axhline(y,color="#aaaaaa",ls="--",lw=.8)
    ax.set_xscale("log");ax.set_xlabel("Matched measured concentration (µM)")
    ax.set_ylabel("Relative log2 growth: bortezomib − paclitaxel")
    ax.set_title("C: observed dose-dependent rank reversal",loc="left",weight="bold",pad=12)
    ax.legend(title="Background",ncol=3,fontsize=9,frameon=False)
    ax.grid(alpha=.15)
    fig.text(.02,.015,"24–60 h endpoint; two technical wells per dose, one plate per background. Example selected for illustration; no held-out prediction.",fontsize=8,color="#555555")
    fig.tight_layout(rect=(0,.05,1,1))
    fig.savefig(figures/"c_observed_dose_switch.png",dpi=180,bbox_inches="tight")
    fig.savefig(figures/"c_observed_dose_switch.svg",bbox_inches="tight")
    plt.close(fig)
    print(figures)


if __name__=="__main__":
    main()
