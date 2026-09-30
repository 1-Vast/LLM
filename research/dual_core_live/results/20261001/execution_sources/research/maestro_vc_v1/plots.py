"""Figures for visual verification: data quality, splits, adaptation, calibration, decisions and trajectories.

File summary
- Path: research/maestro_vc_v1/plots.py
- Purpose: draw every diagnostic the design asks to be inspected by eye, from files the pipeline wrote,
  so a reader can see a problem (a batch effect, a leaky split, a miscalibrated forecast) that a summary
  number would hide.
- Core points:
  - Style follows the data-visualisation method used in this repository's tooling: categorical hues in a
    fixed order and validated (light mode: blue, orange, aqua, yellow, magenta, green), color follows the
    entity and never its rank, thin marks, a recessive grid, text in ink tokens, direct labels beside
    markers, and marker shape as a second channel because three of the hues sit below 3:1 contrast.
    Diverging plots use blue and red around a gray midpoint; magnitude uses one blue ramp.
  - One axis per plot: no dual-axis chart. Small multiples separate tiers.
  - Every figure function returns the path it wrote; `make_all` writes them all to
    `outputs/maestro_vc_v1/figures/` and returns a manifest with the source files.
  - Figures: measurement status and missingness; replicate agreement; control matching; dose-response and
    time-course; Hallmark pathway direction by class; split overlap and structural novelty; adaptation
    cost against realised error; calibration curves and the selected-action under-forecast; uncertainty
    against error by reference support; terminal-decision differences against the fixed order; replay
    decision trajectories; case embedding; a hypothesis graph.
- Interfaces: `make_all`, `INK`, `PALETTE`, one `fig_*` function per figure
- Depends on: matplotlib, numpy, pandas, the pipeline's outputs
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "outputs/maestro_vc_v1/figures"
ANALYSIS = ROOT / "outputs/maestro_vc_v1/analysis"
REPLAY = ROOT / "outputs/maestro_vc_v1/replay"
PROCESSED = ROOT / "data/processed/maestro_vc_v1"
SURFACE, GRID, AXIS = "#fcfcfb", "#e1e0d9", "#c3c2b7"
INK = {"primary": "#0b0b0b", "secondary": "#52514e", "muted": "#898781"}
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
BLUE_RAMP = ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIVERGING = LinearSegmentedColormap.from_list("bwr_gray", ["#2a78d6", "#f0efec", "#e34948"])
SEQUENTIAL = LinearSegmentedColormap.from_list("blue_seq", BLUE_RAMP)
MARKERS = ["o", "s", "^", "D", "v", "P"]
ARM_STYLE = {  # color follows the entity, never its rank
    "fixed": (INK["secondary"], "o"), "belief_similarity": (PALETTE[0], "s"), "cm_full": (PALETTE[1], "^"),
    "cm_full_prior": (PALETTE[2], "D"), "cm_full_prior_anchored": (PALETTE[3], "v"), "vc_incontext": (PALETTE[4], "P"),
    "scalar_vc": (PALETTE[5], "X"), "cm_nofail": (INK["muted"], "x"), "coverage": (INK["muted"], "+"),
    "random_legal": (INK["muted"], "1"), "belief_class": (PALETTE[5], "o"), "prior_only": (PALETTE[2], "o"),
    "oracle": (INK["primary"], "*"),
}
WORLD_STYLE = {"class": (PALETTE[5], "o"), "similarity": (PALETTE[0], "s"), "cm_full": (PALETTE[1], "^"), "scalar": (INK["muted"], "x")}
TIER_LABEL = {"A": "SciPlex3 A", "B": "SciPlex3 B", "LT": "L1000 LT", "T": "L1000 T"}


def _style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "axes.edgecolor": AXIS,
        "axes.labelcolor": INK["secondary"], "xtick.color": INK["muted"], "ytick.color": INK["muted"],
        "text.color": INK["primary"], "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False, "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans"], "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
        "axes.titlecolor": INK["primary"], "legend.frameon": False, "lines.linewidth": 1.6, "figure.dpi": 130})


def _save(fig, name: str) -> str:
    FIG.mkdir(parents=True, exist_ok=True)
    path = FIG / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(path.relative_to(ROOT).as_posix())


def _load_scored(arms=None):
    from research.scientific_case_memory import evaluate_decision_policy as D

    return D.load_scored(REPLAY / "scored", arms)


# ---------------------------------------------------------------------------------------- data quality
def fig_status():
    _style()
    frames = []
    for ds in ("sciplex3", "l1000"):
        f = pd.read_csv(PROCESSED / f"state_table_{ds}.csv")
        f["dataset"] = ds
        frames.append(f)
    df = pd.concat(frames)
    order = ["qualified", "undetected", "qc_failed", "planned_missing"]
    colors = {"qualified": PALETTE[0], "undetected": PALETTE[1], "qc_failed": PALETTE[4], "planned_missing": INK["muted"]}
    groups = df.groupby(["dataset", "cell_line"]).measurement_status.value_counts(normalize=True).unstack(fill_value=0)
    groups = groups.reindex(columns=order, fill_value=0)
    counts = df.groupby(["dataset", "cell_line"]).size()
    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    y = np.arange(len(groups))
    left = np.zeros(len(groups))
    for status in order:
        ax.barh(y, groups[status].to_numpy(), left=left, height=0.62, color=colors[status], edgecolor=SURFACE, linewidth=2,
                label=status.replace("_", " "))
        for i, (v, l) in enumerate(zip(groups[status], left)):
            if v > 0.09:
                ax.text(l + v / 2, i, f"{v:.0%}", ha="center", va="center", color="white" if status == "qualified" else INK["primary"], fontsize=8)
        left += groups[status].to_numpy()
    ax.set_yticks(y, [f"{a} {b} (n={counts[(a, b)]})" for a, b in groups.index])
    ax.set_xlim(0, 1)
    ax.set_xlabel("share of planned conditions")
    ax.set_title("Measurement status of every planned condition\n(a missing or failed condition is a status, never a zero)")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    ax.grid(axis="y", visible=False)
    return _save(fig, "01_measurement_status.png")


def fig_replicates():
    _style()
    from research.dynamic_world_model import common as C

    data = C.load()
    l1 = pd.read_csv(ROOT / "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv")
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    ag = data.agreement[np.isfinite(data.agreement)]
    axes[0].hist(ag, bins=40, color=PALETTE[0], edgecolor=SURFACE)
    axes[0].axvline(np.median(ag), color=INK["secondary"], linewidth=1)
    axes[0].text(np.median(ag), axes[0].get_ylim()[1] * 0.92, f" median {np.median(ag):.2f}", color=INK["secondary"], fontsize=8)
    axes[0].set(title="SciPlex3: replicate agreement", xlabel="Pearson r between the two replicate groups", ylabel="conditions")
    q = l1["cc_q75"].dropna()
    axes[1].hist(q, bins=40, color=PALETTE[1], edgecolor=SURFACE)
    axes[1].axvline(q.median(), color=INK["secondary"], linewidth=1)
    axes[1].text(q.median(), axes[1].get_ylim()[1] * 0.92, f" median {q.median():.2f}", color=INK["secondary"], fontsize=8)
    axes[1].set(title="L1000: replicate correlation (cc_q75)", xlabel="75th percentile replicate correlation", ylabel="conditions")
    i = int(np.nanargmax(np.abs(data.rep1).sum(1)))
    x, y = data.rep1[i], data.rep2[i]
    axes[2].scatter(x, y, s=4, color=PALETTE[0], alpha=0.5, linewidths=0)
    lim = np.nanpercentile(np.abs(np.r_[x, y]), 99.5)
    axes[2].plot([-lim, lim], [-lim, lim], color=INK["muted"], linewidth=0.8)
    axes[2].set(xlim=(-lim, lim), ylim=(-lim, lim), title="Example: the two replicate profiles of one condition",
                xlabel="replicate 1 shift", ylabel="replicate 2 shift")
    return _save(fig, "02_replicate_agreement.png")


def fig_controls():
    _style()
    base = ROOT / "outputs/dynamic_world_model_20260926/prepared"
    wells = pd.read_csv(base / "wells.csv")
    cond = pd.read_csv(base / "conditions.csv")
    ctrl = wells[wells.is_control].groupby(["cell_line", "time"]).size()
    treated = cond.groupby(["cell_line", "time"]).size()
    idx = sorted(set(ctrl.index) | set(treated.index))
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    x = np.arange(len(idx))
    ax.bar(x - 0.2, [treated.get(i, 0) for i in idx], 0.38, color=PALETTE[0], label="treated conditions", edgecolor=SURFACE)
    ax.bar(x + 0.2, [ctrl.get(i, 0) for i in idx], 0.38, color=PALETTE[1], label="vehicle control wells", edgecolor=SURFACE)
    for xi, i in zip(x, idx):
        ax.text(xi + 0.2, ctrl.get(i, 0) + 8, str(int(ctrl.get(i, 0))), ha="center", fontsize=8, color=INK["secondary"])
        ax.text(xi - 0.2, treated.get(i, 0) + 8, str(int(treated.get(i, 0))), ha="center", fontsize=8, color=INK["secondary"])
    ax.set_xticks(x, [f"{c} {int(t)} h" for c, t in idx])
    ax.set_ylabel("count")
    ax.set_title("Control matching: every treated (cell line, time) group has vehicle wells")
    ax.set_ylim(0, 900)
    ax.legend(loc="upper center", ncol=2)
    ax.grid(axis="x", visible=False)
    return _save(fig, "03_control_matching.png")


def fig_dose_time():
    _style()
    from research.dynamic_world_model import common as C

    data = C.load()
    cond = data.conditions.copy()
    cond["norm"] = np.linalg.norm(data.shift, axis=1)
    ok = [C.qc_passed(data, i) for i in range(len(cond))]
    cond = cond[ok]
    l1 = pd.read_csv(ROOT / "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv")
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.5))
    for k, cell in enumerate(sorted(cond.cell_line.unique())):
        for t, ls in ((24.0, "-"), (72.0, "--")):
            g = cond[(cond.cell_line == cell) & (cond.time == t)].groupby("dose").norm
            if g.ngroups == 0:
                continue
            m, s = g.mean(), g.std() / np.sqrt(g.size())
            axes[0].errorbar(m.index, m.values, yerr=1.96 * s.values, color=PALETTE[k], marker=MARKERS[k], linestyle=ls, capsize=2,
                             markersize=4)
        last = cond[(cond.cell_line == cell)].groupby("dose").norm.mean()
        axes[0].text(last.index.max() * 1.15, last.iloc[-1], cell, color=INK["primary"], fontsize=8, va="center")
    axes[0].set(xscale="log", title="SciPlex3: response size against dose", xlabel="dose (nM)", ylabel="mean shift norm (solid 24 h, dashed 72 h)")
    axes[0].set_xlim(7, 30000)
    l1 = l1[l1.qc]
    for j, tt in enumerate((6.0, 24.0)):
        g = l1[l1.time == tt]
        axes[1].scatter(np.full(len(g), j) + np.random.default_rng(1).normal(0, 0.06, len(g)), g.signature_strength, s=4,
                        color=PALETTE[j], alpha=0.35, linewidths=0)
        axes[1].plot([j - 0.25, j + 0.25], [g.signature_strength.median()] * 2, color=INK["primary"], linewidth=1.6)
    axes[1].set_xticks([0, 1], ["6 h", "24 h"])
    axes[1].set(title="L1000: signature strength by time", ylabel="signature strength (median bar)")
    det = l1.groupby(["cell_line", "time"]).detected.mean().unstack()
    for j, cell in enumerate(det.index):
        axes[2].plot(det.columns, det.loc[cell], color=PALETTE[j % 6], marker=MARKERS[j % 6], markersize=5)
        nudge = {"A549": 0.004, "PC3": -0.004}.get(cell, 0.0)
        axes[2].text(24.6, det.loc[cell].iloc[-1] + nudge, cell, fontsize=8, va="center", color=INK["primary"])
    axes[2].set(title="L1000: share detected, 6 h to 24 h", xlabel="hours", ylabel="detected fraction", xlim=(5, 29), xticks=[6, 24])
    return _save(fig, "04_dose_response_time_course.png")


def fig_pathway_heatmap():
    _style()
    from research.dynamic_world_model import common as C

    data = C.load()
    sets = json.loads((ROOT / "outputs/biological_depth_20260926/prepared/gene_sets.json").read_text(encoding="utf-8"))
    genes = pd.read_csv(ROOT / "outputs/biological_depth_20260926/prepared/genes.csv")
    sym = {s: i for i, s in enumerate(genes.symbol)}
    key = ("A549", 24.0, 10000.0)
    rows = data.index[key]
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    classes = {}
    for c, r in rows.items():
        k = comp.klass.get(c)
        if isinstance(k, str) and C.qc_passed(data, r):
            classes.setdefault(k, []).append(r)
    classes = {k: v for k, v in classes.items() if len(v) >= 3}
    names = sorted(sets)
    idx = {n: [sym[g] for g in sets[n] if g in sym] for n in names}
    idx = {n: v for n, v in idx.items() if len(v) >= 10}
    M = np.array([[data.shift[np.array(r)][:, idx[n]].mean() for n in idx] for r in classes.values()])
    top = np.argsort(-M.std(0))[:16]
    M = M[:, top]
    labels = [list(idx)[i].replace("HALLMARK_", "").replace("_", " ").title() for i in top]
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    v = np.abs(M).max()
    im = ax.imshow(M, cmap=DIVERGING, vmin=-v, vmax=v, aspect="auto")
    ax.set_xticks(range(len(labels)), labels, rotation=55, ha="right", fontsize=8)
    ax.set_yticks(range(len(classes)), [f"{k} (n={len(vv)})" for k, vv in classes.items()], fontsize=8)
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("mean signed shift in the gene set (blue down, red up)")
    ax.set_title("Pathway direction by mechanism class: SciPlex3 A549, 24 h, 10 uM (Hallmark sets)")
    return _save(fig, "05_pathway_direction_heatmap.png")


# ---------------------------------------------------------------------------------------- splits
def fig_splits():
    _style()
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), gridspec_kw={"wspace": 0.28})
    for ax, (ds, unit) in zip(axes[:2], (("sciplex3", "skeleton"), ("l1000", "component"))):
        path = ROOT / ("outputs/biological_depth_20260926/prepared/compounds.csv" if ds == "sciplex3" else
                       "outputs/sequence_audit_20260926/l1000/prepared/compounds.csv")
        c = pd.read_csv(path).dropna(subset=["fold"])
        u = {f: set(c[c.fold == f][unit]) for f in sorted(c.fold.unique())}
        M = np.array([[len(u[a] & u[b]) for b in u] for a in u])
        ax.imshow(np.where(np.eye(len(u)) > 0, M, np.nan), cmap=SEQUENTIAL, aspect="equal")
        for i in range(len(u)):
            for j in range(len(u)):
                ax.text(j, i, str(M[i, j]), ha="center", va="center", fontsize=9, color=INK["primary"])
        ax.set_xticks(range(len(u)), [f"fold {int(k)}" for k in u], fontsize=8)
        ax.set_yticks(range(len(u)), [f"fold {int(k)}" for k in u], fontsize=8)
        ax.grid(False)
        ax.set_title(f"{ds}: units shared between folds\n(diagonal = units per fold; off-diagonal must be 0)", fontsize=9)
    sc = _load_scored(["fixed"])
    for k, (tier, g) in enumerate(sc.groupby("tier")):
        s = g.drop_duplicates("compound").nn_similarity.dropna()
        axes[2].hist(s, bins=np.linspace(0, 1, 26), histtype="step", color=PALETTE[k], linewidth=1.6, label=TIER_LABEL[tier])
    axes[2].axvline(0.40, color=INK["secondary"], linestyle="--", linewidth=1)
    axes[2].text(0.415, axes[2].get_ylim()[1] * 0.52, "applicability\nfloor 0.40", fontsize=8, color=INK["secondary"])
    axes[2].set_title("Held-out compounds: nearest\ntraining neighbour", fontsize=9)
    axes[2].set(xlabel="Tanimoto similarity", ylabel="compounds")
    axes[2].legend(loc="upper right", fontsize=8)
    return _save(fig, "06_split_overlap_and_novelty.png")


# ---------------------------------------------------------------------------------------- adaptation
def fig_adaptation():
    _style()
    st = json.loads((ANALYSIS / "stress.json").read_text(encoding="utf-8"))
    cr = pd.DataFrame(st["cost_rows"])
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.4), gridspec_kw={"wspace": 0.85, "width_ratios": [1, 1.15, 1.1]})
    axes[0].hist(cr.cost, bins=np.linspace(0, 1, 26), color=PALETTE[0], edgecolor=SURFACE)
    axes[0].set_title("Priced adaptation cost of every\nsource condition", fontsize=9)
    axes[0].set(xlabel="cost (0 = as good as a same-condition class-mate)", ylabel="(fold, target, source) triples")
    sigs = sorted(cr.signature.unique())

    def short(sig):
        cell = "cell line changes" if "cell_line_change=True" in sig else "same cell line"
        time = {"same": "same time", "near": "time near", "far": "time far"}[sig.split("time=")[1].split(";")[0]]
        dose = {"same": "same dose", "near": "dose near", "far": "dose far"}[sig.split("dose=")[1].split(";")[0]]
        return f"{cell}, {time}, {dose}"

    for j, s_ in enumerate(sigs):
        g = cr[cr.signature == s_]
        axes[1].scatter(g.cost, g.nll, s=10, color=PALETTE[j % 6], marker=MARKERS[j % 6], alpha=0.65, linewidths=0, label=short(s_))
    rho, ci = st["cost_vs_nll"]["spearman"], st["cost_vs_nll"]["ci"]
    axes[1].set_title(f"Dearer transfer, worse forecast\nSpearman {rho:.2f} [{ci[0]:.2f}, {ci[1]:.2f}]", fontsize=9)
    axes[1].set(xlabel="priced cost of borrowing from the source", ylabel="NLL of the borrowed forecast")
    axes[1].legend(fontsize=6.5, loc="upper left", markerscale=1.3)
    t = pd.DataFrame(st["adaptation_table_heldout"])
    y = np.arange(len(t))[::-1]
    axes[2].hlines(y, t.realised, t.table_success, color=AXIS, linewidth=1.2)
    axes[2].scatter(t.table_success, y, color=PALETTE[0], marker="o", s=30, label="predicted by the table (training pairs)", zorder=3)
    axes[2].scatter(t.realised, y, color=PALETTE[1], marker="s", s=30, label="realised on held-out compounds", zorder=3)
    axes[2].set_yticks(y, [short(s_) for s_ in t.signature], fontsize=6.8)
    axes[2].set_title("Adaptation table against held-out reality", fontsize=9)
    axes[2].set(xlabel="probability the transfer reproduces the target's reading", xlim=(0.2, 1.0))
    axes[2].legend(fontsize=7, loc="lower left", bbox_to_anchor=(0.0, -0.32))
    return _save(fig, "07_adaptation_cost.png")


# ---------------------------------------------------------------------------------------- calibration
def fig_calibration():
    _style()
    r = json.loads((ANALYSIS / "results.json").read_text(encoding="utf-8"))
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.4), gridspec_kw={"wspace": 0.55, "width_ratios": [1, 1.1, 1.1]})
    ax = axes[0]
    ax.plot([0, 0.6], [0, 0.6], color=INK["muted"], linewidth=0.8)
    for w, (col, mk) in ((k, WORLD_STYLE[k]) for k in ("class", "similarity", "cm_full")):
        c = pd.DataFrame(r["calibration_curves"][w])
        c = c[c.n >= 20]
        ax.plot(c.forecast, c.observed, color=col, marker=mk, markersize=5, label=w)
    first = pd.DataFrame(r["calibration_curves"]["class"]).iloc[0]
    ax.annotate(f"first bin: {int(first.n):,} items\nforecast {first.forecast:.4f}, observed {first.observed:.4f}", (first.forecast, first.observed),
                xytext=(0.12, 0.05), fontsize=7, color=INK["secondary"], arrowprops=dict(arrowstyle="-", color=AXIS))
    ax.set(xlim=(0, 0.6), ylim=(0, 0.6), xlabel="forecast probability of a wrong elimination", ylabel="observed frequency")
    ax.set_title("Reliability over all held-out conditions\n(bins with fewer than 20 items omitted)", fontsize=9)
    ax.legend(loc="upper left", fontsize=8)
    sel = pd.DataFrame(r["selected_calibration"])
    sel = sel[sel.world == "cm_full"]
    ax = axes[1]
    y = np.arange(len(sel))[::-1]
    for yi, (_, s_) in zip(y, sel.iterrows()):
        col, mk = ARM_STYLE.get(s_.arm, (INK["muted"], "o"))
        lo, hi = (s_.ratio_ci if s_.ratio_ci else (np.nan, np.nan))
        ax.hlines(yi, lo, hi, color=col, linewidth=1.4)
        ax.scatter([s_.ratio], [yi], color=col, marker=mk, s=40, zorder=3)
        ax.text(hi + 0.1, yi, f"{s_.ratio:.2f}", va="center", fontsize=8, color=INK["secondary"])
    ax.axvline(1.0, color=INK["secondary"], linestyle="--", linewidth=1)
    ax.set_yticks(y, list(sel.arm), fontsize=8)
    ax.set_title("On the action each arm chose:\nobserved / forecast (1 = calibrated)", fontsize=9)
    ax.set(xlabel="ratio with 95% interval; above 1 = risk under-forecast", xlim=(0, 4.4))
    ax = axes[2]
    m = pd.DataFrame(r["world_metrics_pooled"])
    m = m[m.world.isin(["class", "similarity", "cm_full", "scalar"])].reset_index(drop=True)
    cols = {k: v[0] for k, v in WORLD_STYLE.items()}
    ax.barh(np.arange(len(m))[::-1], m.discrimination, color=[cols[w] for w in m.world], height=0.55, edgecolor=SURFACE)
    for i, (_, x_) in zip(np.arange(len(m))[::-1], m.iterrows()):
        ax.text(x_.discrimination + 0.02, i, f"{x_.discrimination:.2f} nats (NLL {x_.nll:.3f})", va="center", fontsize=8, color=INK["secondary"])
    ax.set_yticks(np.arange(len(m))[::-1], list(m.world))
    ax.set_title("Hypothesis discrimination of the forecast\n(scalar is 0 by construction)", fontsize=9)
    ax.set(xlabel="mean log p(y | true) - log p(y | other), nats", xlim=(0, 1.15))
    ax.grid(axis="y", visible=False)
    return _save(fig, "08_calibration.png")


def fig_uncertainty():
    _style()
    from research.scientific_case_memory import evaluate_case_retrieval as F

    rows = F.load_items(REPLAY / "forecasts")
    df = F.item_frame(rows, ["similarity"])
    bins = [(0, 2), (2, 6), (6, 12), (12, 25), (25, 60), (60, 10 ** 6)]
    labels = ["<2", "2-5", "6-11", "12-24", "25-59", "60+"]
    df["bin"] = pd.cut(df.support_truth, [b[0] - 0.5 for b in bins] + [10 ** 7], labels=labels)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    tiers = sorted(df.tier.unique())
    for k, tier in enumerate(tiers):
        g = df[df.tier == tier].groupby("bin", observed=True).agg(nll=("nll", "mean"), n=("nll", "size"), pw=("p_wrong", "mean"), yw=("y_wrong", "mean"))
        axes[0].plot(g.index.astype(str), g.nll, color=PALETTE[k], marker=MARKERS[k], markersize=5, label=f"{TIER_LABEL[tier]} (n={int(g.n.sum()):,})")
        axes[1].plot(g.index.astype(str), g.pw, color=PALETTE[k], marker=MARKERS[k], markersize=5)
        axes[2].plot(g.index.astype(str), g.yw, color=PALETTE[k], marker=MARKERS[k], markersize=5)
    axes[0].set(title="Forecast error by reference support", xlabel="independent reference units behind the forecast", ylabel="mean NLL")
    axes[1].set(title="Forecast wrong-elimination probability", xlabel="reference units", ylabel="mean forecast")
    axes[2].set(title="Observed wrong-elimination frequency", xlabel="reference units", ylabel="observed frequency")
    axes[0].legend(fontsize=7.5, loc="upper right")
    fig.suptitle("Uncertainty against error: the forecast wrong-elimination probability against what happened, by the number of reference units behind it", fontsize=9, y=1.03)
    for a in axes:
        a.tick_params(axis="x", labelsize=8)
    return _save(fig, "09_uncertainty_vs_error.png")


# ---------------------------------------------------------------------------------------- decisions
def fig_decisions():
    _style()
    r = json.loads((ANALYSIS / "results.json").read_text(encoding="utf-8"))
    p = pd.DataFrame(r["paired"])
    p = p[(p.comparator == "fixed") & (p.metric == "correct")]
    arms = ["belief_similarity", "cm_full", "cm_full_prior", "cm_full_prior_anchored", "vc_incontext", "scalar_vc", "cm_nofail"]
    head = {h["tier"]: h for h in r["headroom"]}
    fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.6), sharey=True)
    for ax, tier in zip(axes, ["A", "B", "LT", "T"]):
        sub = p[p.tier == tier].set_index("arm")
        ax.axvspan(-0.01, 0.02, color=GRID, alpha=0.5, linewidth=0)
        ax.axvline(0, color=INK["secondary"], linewidth=1)
        for i, arm in enumerate(arms):
            if arm not in sub.index:
                continue
            s = sub.loc[arm]
            col, mk = ARM_STYLE[arm]
            ax.hlines(len(arms) - 1 - i, s.lo, s.hi, color=col, linewidth=1.4)
            ax.scatter([s.difference], [len(arms) - 1 - i], color=col, marker=mk, s=34, zorder=3)
        h = head.get(tier)
        ax.set_title(f"{TIER_LABEL[tier]}  (headroom {h['headroom']:.3f}{'' if h['eligible'] else ', below gate'})", fontsize=9)
        ax.set_xlabel("correct decisions, arm minus fixed")
        ax.set_yticks(range(len(arms)), arms[::-1] if False else [a for a in reversed(arms)], fontsize=8)
        ax.set_xlim(-0.36, 0.09)
    fig.suptitle("Terminal decisions against the fixed expert order (95% unit-cluster interval; shaded: -0.01 to +0.02, the pre-registered non-inferiority and gain thresholds)", fontsize=9, y=1.02)
    return _save(fig, "10_action_value_vs_fixed.png")


def fig_efficiency():
    _style()
    r = json.loads((ANALYSIS / "results.json").read_text(encoding="utf-8"))
    s = pd.DataFrame(r["summary"])
    arms = ["fixed", "belief_similarity", "cm_full", "cm_full_prior", "cm_full_prior_anchored", "vc_incontext", "scalar_vc", "oracle"]
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.6))
    for ax, tier in zip(axes, ["A", "B", "LT", "T"]):
        g = s[s.tier == tier].set_index("arm")
        for arm in arms:
            col, mk = ARM_STYLE[arm]
            ax.scatter(g.loc[arm, "measurements"], g.loc[arm, "correct"], color=col, marker=mk, s=46, zorder=3, label=arm)
        ax.set(title=TIER_LABEL[tier], xlabel="measurements per episode", ylabel="correct decisions" if tier == "A" else "")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=8, fontsize=8, bbox_to_anchor=(0.5, -0.1))
    fig.suptitle("Cost against correctness: fewer measurements at the same correct rate is licensed delay; fewer correct is a trade", fontsize=9, y=1.03)
    return _save(fig, "11_efficiency.png")


def fig_trajectories():
    _style()
    sc = _load_scored(["fixed", "belief_similarity", "cm_full_prior", "oracle"])
    tf = sc[(sc.tier == "B") & (sc.fold == 0)]
    eps = tf.groupby(["compound", "h1", "h2"]).size().index
    rng = np.random.default_rng(3)
    pick = [eps[i] for i in rng.choice(len(eps), 18, replace=False)]
    arms = ["fixed", "belief_similarity", "cm_full_prior", "oracle"]
    cmap = {"correct": PALETTE[2], "wrong": "#d03b3b", "undetermined": INK["muted"], "deferred": AXIS, "exhausted": "#d03b3b"}
    fig, ax = plt.subplots(figsize=(11.5, 7))
    for r_i, (c, h1, h2) in enumerate(pick):
        for a_i, arm in enumerate(arms):
            row = tf[(tf.arm == arm) & (tf.compound == c) & (tf.h1 == h1) & (tf.h2 == h2)].iloc[0]
            ax.add_patch(plt.Rectangle((a_i * 3.1, -r_i - 0.42), 2.9, 0.84, facecolor=cmap[row.final], edgecolor=SURFACE, linewidth=1, alpha=0.18))
            for s_i, s in enumerate(row.steps):
                st = s["state"]
                mk = {"measured_eliminating": "s", "measured_ambiguous": "o", "measured_undetected": "v", "quality_failed": "x"}.get(st, "o")
                col = cmap[row.final] if st == "measured_eliminating" else INK["secondary"]
                ax.scatter([a_i * 3.1 + 0.5 + s_i * 1.0], [-r_i], marker=mk, s=44, color=col, zorder=3)
                ax.text(a_i * 3.1 + 0.5 + s_i * 1.0, -r_i + 0.24, s["action"][:4] + s["action"][5:9], fontsize=5.5, ha="center", color=INK["muted"])
            ax.text(a_i * 3.1 + 2.75, -r_i, row.final, fontsize=7, ha="right", va="center", color=INK["primary"])
        ax.text(-0.3, -r_i, f"{c[:14]}", fontsize=7, ha="right", va="center", color=INK["secondary"])
    ax.set_xticks([a_i * 3.1 + 1.45 for a_i in range(len(arms))], arms)
    ax.set_yticks([])
    ax.set_xlim(-0.2, 12.4)
    ax.grid(False)
    ax.spines["left"].set_visible(False)
    ax.xaxis.tick_top()
    ax.set_title("Replay trajectories, SciPlex3 B fold 0: each row one episode; square = qualified elimination, circle = ambiguous, triangle = undetected, x = QC failure", pad=22, fontsize=9)
    return _save(fig, "12_replay_trajectories.png")


# ---------------------------------------------------------------------------------------- cases
def fig_case_embedding():
    _style()
    from research.scientific_case_memory import case_index as CI
    from research.scientific_case_memory import case_schema as S
    from research.scientific_case_memory import case_store as CS

    store = CS.CaseStore(ROOT / "outputs/scientific_case_memory/library_sciplex3_B.jsonl.gz")
    cases = [c for c in store.latest() if c.case_kind is not S.CaseKind.ADAPTATION]
    X = []
    for c in cases:
        codes = np.stack([CI.decode_codes(u.codes) for u in c.hypothesis_updates]) if c.hypothesis_updates else np.zeros((1, 1), int)
        row = []
        for k in range(4):
            row.append(float(((codes == k).sum()) / max((codes >= 0).sum(), 1)))
        row.append(float(len(c.hypothesis_updates)))
        X.append(row)
    X = np.array(X)
    X = (X - X.mean(0)) / np.maximum(X.std(0), 1e-9)
    U, s, Vt = np.linalg.svd(X, full_matrices=False)
    Z = U[:, :2] * s[:2]
    kinds = [c.case_kind.value for c in cases]
    klass = [c.context_fingerprint["hypothesis_class"] for c in cases]
    top = pd.Series(klass).value_counts().index[:5]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
    kstyle = {"canonical": (PALETTE[0], "o"), "contrastive": (PALETTE[1], "^"), "failure": (PALETTE[4], "s")}
    for k, (col, mk) in kstyle.items():
        m = np.array([x == k for x in kinds])
        if m.any():
            axes[0].scatter(Z[m, 0], Z[m, 1], color=col, marker=mk, s=26, alpha=0.8, linewidths=0, label=f"{k} ({int(m.sum())})")
    axes[0].set(title="Case memory: reading-profile embedding coloured by case kind", xlabel="component 1", ylabel="component 2")
    axes[0].legend(loc="best")
    for j, t in enumerate(top):
        m = np.array([x == t for x in klass])
        axes[1].scatter(Z[m, 0], Z[m, 1], color=PALETTE[j], marker=MARKERS[j], s=26, alpha=0.85, linewidths=0, label=f"{t} ({int(m.sum())})")
    other = np.array([x not in set(top) for x in klass])
    axes[1].scatter(Z[other, 0], Z[other, 1], color=AXIS, s=14, linewidths=0, label="other classes")
    axes[1].set(title="Same embedding coloured by mechanism class (five largest)", xlabel="component 1", ylabel="component 2")
    axes[1].legend(loc="best", fontsize=7)
    return _save(fig, "13_case_embedding.png")


def fig_graph():
    _style()
    from research.scientific_case_memory import case_store as CS

    store = CS.CaseStore(ROOT / "outputs/scientific_case_memory/cases_genetic_pharmacological_and_engagement.jsonl.gz")
    case = next(c for c in store.latest() if c.case_id == "mc-alk-lorlatinib-ach000804")
    graph = case.provenance["graph"]
    layers = ["intervention", "target_engagement", "proximal_function", "pathway_state", "cellular_state", "phenotype", "observed_assay"]
    fig, ax = plt.subplots(figsize=(11.5, 4.6))
    pos = {n["node_id"]: (layers.index(n["layer"]), 0) for n in graph["nodes"]}
    for n in graph["nodes"]:
        x, y = pos[n["node_id"]]
        measured = n["status"] in ("qualified", "ambiguous", "undetected")
        ax.add_patch(plt.Rectangle((x - 0.42, y - 0.18), 0.84, 0.36, facecolor=PALETTE[0] if measured else SURFACE,
                                   edgecolor=PALETTE[0] if measured else INK["muted"], linewidth=1.2,
                                   linestyle="-" if measured else "--", alpha=0.25 if measured else 1.0))
        ax.text(x, y + 0.03, n["layer"].replace("_", "\n"), ha="center", va="center", fontsize=7.5, color=INK["primary"])
        ax.text(x, y - 0.13, n["status"].replace("_", " "), ha="center", va="center", fontsize=6.5, color=INK["secondary"])
    for e in graph["edges"]:
        (x1, _), (x2, _) = pos[e["source"]], pos[e["target"]]
        ax.annotate("", xy=(x2 - 0.43, 0), xytext=(x1 + 0.43, 0), arrowprops=dict(arrowstyle="->", color=INK["muted"] if e["evidence_strength"] in ("predicted", "speculative") else PALETTE[0],
                                                                                    linestyle="--" if e["evidence_strength"] in ("predicted", "speculative") else "-", linewidth=1.2))
        ax.text((x1 + x2) / 2, 0.24, e["evidence_strength"], ha="center", fontsize=6.5, color=INK["muted"])
    for j, h in enumerate(graph["hypotheses"]):
        y = -0.55 - 0.32 * j
        ax.text(-0.45, y, f"{h['hypothesis_id']}{' (advisory)' if h['advisory'] else ' (registered)'}: {h['claim'][:118]}", fontsize=7.2,
                color=INK["primary"] if not h["advisory"] else INK["secondary"], va="center")
    ax.set_xlim(-0.55, 6.6)
    ax.set_ylim(-2.3, 0.5)
    ax.axis("off")
    ax.set_title(f"Hypothesis graph of {case.case_id}: solid = measured layer, dashed = not measured; edges into unmeasured layers are predictions", fontsize=9)
    return _save(fig, "14_hypothesis_graph.png")


def make_all() -> dict:
    out = {}
    for fn in (fig_status, fig_replicates, fig_controls, fig_dose_time, fig_pathway_heatmap, fig_splits, fig_adaptation,
               fig_calibration, fig_uncertainty, fig_decisions, fig_efficiency, fig_trajectories, fig_case_embedding, fig_graph):
        try:
            out[fn.__name__] = fn()
        except Exception as exc:  # a failed figure is reported, never skipped silently
            out[fn.__name__] = f"FAILED: {type(exc).__name__}: {exc}"
    (FIG / "figures_manifest.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    for k, v in make_all().items():
        print(k, v)
