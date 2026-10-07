"""Headroom, tie, dispersion and power numbers from EXISTING aggregated campaign receipts (agent C, phase 1).

File summary
- Path: research/astra/mono_pretraining_20261005/decisions/headroom_from_receipts.py
- Purpose: reproduce every number quoted in DECISION_SPACE.md / AGENT_ROLE.md / EVALUATION_DESIGN.md that comes
  from the confirmation-campaign receipts. Reads ONLY per-campaign scalar fields (confirmed, n_menu, M,
  menu_joint_hits) of the frozen design/resources result files and the resources summary. It never imports the
  builder, never opens the raw Jaaks CSV and never opens a vault ticket (no access_log entry is needed).
- Output: headroom_from_receipts.json next to this file (refuses to overwrite).
- Run: PYTHONPATH='src;.' D:/anaconda/envs/maestro/python.exe research/astra/mono_pretraining_20261005/decisions/headroom_from_receipts.py
"""
from __future__ import annotations

import collections
import gzip
import json
from math import sqrt
from pathlib import Path

import numpy as np
from scipy.stats import chi2, norm

HERE = Path(__file__).resolve().parent
CC = HERE.parents[1] / "confirmation_campaign_20261004"
OUT = HERE / "headroom_from_receipts.json"
TAU = 0.05
INFL_TWO_WAY = 33.6 / 15.0   # width ratio two-way (line x pair) / line bootstrap, R - C_mean on E (REPORT 4.2): [-22.84,+10.73] vs [-13.36,+1.67]


def load_scalar(path: Path, keep=lambda r: True):
    rows = []
    with gzip.open(path, "rt") as handle:
        for line in handle:
            r = json.loads(line)
            if keep(r):
                rows.append({k: v for k, v in r.items() if not isinstance(v, (list, dict))})
    return rows


def per_line(rows):
    values = collections.defaultdict(lambda: collections.defaultdict(list))
    meta = {}
    for r in rows:
        key = (r["tissue"], r["line"])
        values[r["arm"]][key].append(r["confirmed"])
        meta.setdefault(key, {})[r["role"]] = (r["n_menu"], r["M"], r["menu_joint_hits"])
    lines = sorted(meta)
    V = {a: np.array([np.mean(values[a][k]) for k in lines]) for a in values}
    menu = np.array([np.mean([x[0] for x in meta[k].values()]) for k in lines])
    M = np.array([np.mean([x[1] for x in meta[k].values()]) for k in lines])
    jh = np.array([np.mean([x[2] for x in meta[k].values()]) for k in lines])
    tissue = np.array([k[0] for k in lines])
    return lines, V, menu, M, jh, tissue


def contrast(V, a, b):
    d = V[a] - V[b]
    n = d.size
    return {"mean_diff": float(d.mean()), "sd": float(d.std(ddof=1)), "sd_rel_of_mean_b": float(d.std(ddof=1) / V[b].mean()),
            "rel_gain": float(V[a].sum() / V[b].sum() - 1), "better": int((d > 0).sum()), "worse": int((d < 0).sum()),
            "tied": int((d == 0).sum()), "n": int(n)}


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"REFUSED: {OUT} exists")
    E_rows = load_scalar(CC / "design/results/eval_20261004_130452/campaigns_primary.jsonl.gz")
    HD_rows = load_scalar(CC / "design/results/dev_20261004_130123/campaigns_p2_grid.jsonl.gz", lambda r: r["fp"] == 30)
    result: dict = {"source": "scalar fields of design/results/{eval_20261004_130452/campaigns_primary,dev_20261004_130123/campaigns_p2_grid(fp=30)}.jsonl.gz",
                    "unit": "line value = mean over SV/VS role assignments of confirmed discoveries (P2, fp 30, cap M=ceil(menu/5))"}
    pooled_jh, pooled_t = [], []
    for name, rows in (("E", E_rows), ("HD", HD_rows)):
        lines, V, menu, M, jh, tissue = per_line(rows)
        n = len(lines)
        base, orc = V["C_mean"], V["oracle"]
        gap = orc - base
        sec = {"n_lines": n, "totals": {a: float(v.sum()) for a, v in V.items()},
               "menu_mean": float(menu.mean()), "M_mean": float(M.mean()),
               "mean_value_C_mean": float(base.mean()),
               "joint_hits_per_line": {"mean": float(jh.mean()), "median": float(np.median(jh)), "sum": float(jh.sum()),
                                       "zero_lines": int((jh == 0).sum()), "ge5_lines": int((jh >= 5).sum())},
               "oracle_rel_gain_over_C_mean": float(orc.sum() / base.sum() - 1),
               "lines_with_oracle_headroom_vs_C_mean": int((orc > base + 1e-9).sum()),
               "lines_at_oracle_ceiling_with_hits": int((np.isclose(orc, base) & (jh > 0)).sum()),
               "share_of_gap_in_top5_lines": float(np.sort(gap)[::-1][:5].sum() / gap.sum()),
               "share_of_gap_in_top10_lines": float(np.sort(gap)[::-1][:10].sum() / gap.sum()),
               "gap_closure_needed_for_tau_5pct": float(TAU * base.sum() / gap.sum()),
               "contrasts": {f"{a}-{b}": contrast(V, a, b) for a, b in
                             (("R", "C_mean"), ("S_both", "S"), ("C_mean", "C_s"), ("C_mean", "C_v"), ("C_mean", "S_both"),
                              ("C_prod", "C_mean"), ("L_v", "C_mean"), ("oracle", "C_mean"))},
               "hindsight_best_of_two_gain_vs_C_mean": {a: float(np.maximum(V[a], base).sum() / base.sum() - 1)
                                                        for a in ("R", "S_both", "C_s", "C_v", "C_prod", "L_v", "S")},
               "hindsight_best_of_all_simple6_gain": float(np.max(np.stack([V[a] for a in ("S_both", "L_v", "C_s", "C_v", "C_mean", "C_prod")]), axis=0).sum() / base.sum() - 1),
               "per_tissue": {t: {"lines": int((tissue == t).sum()), "C_mean": float(base[tissue == t].sum()),
                                  "oracle": float(orc[tissue == t].sum()), "R": float(V["R"][tissue == t].sum()),
                                  "S_both": float(V["S_both"][tissue == t].sum()), "joint_hits": float(jh[tissue == t].sum())}
                              for t in ("Breast", "Colon", "Pancreas")}}
        result[name] = sec
        pooled_jh.append(jh)
        pooled_t.append(tissue)
    jh, tissue = np.concatenate(pooled_jh), np.concatenate(pooled_t)
    disp = {}
    for t in ("Breast", "Colon", "Pancreas"):
        x = jh[tissue == t]
        m = float(x.mean())
        stat = float(((x - m) ** 2).sum() / m)
        disp[t] = {"lines": int(x.size), "mean": m, "var_over_mean": float(x.var(ddof=1) / m), "zero_lines": int((x == 0).sum()),
                   "poisson_dispersion_chi2": stat, "df": int(x.size - 1), "p": float(1 - chi2.cdf(stat, x.size - 1))}
    srt = np.sort(jh)[::-1]
    cum = np.cumsum(srt) / srt.sum()
    result["line_level_hit_concentration_125_lines"] = {
        "zero_hit_lines": int((jh == 0).sum()), "zero_hit_fraction": float((jh == 0).mean()),
        "share_in_top10pct_lines": float(cum[int(0.1 * jh.size) - 1]), "share_in_top20pct_lines": float(cum[int(0.2 * jh.size) - 1]),
        "per_tissue_dispersion": disp,
        "note": "menu composition differs by line (QC-conditioned), so overdispersion is an upper bound on a pure line effect"}

    # barren-line reallocation bound from the cap curves of the resources summary (C_mean, P2 fp30)
    summ = json.loads((CC / "resources/results/summary_20261004_130800/summary.json").read_text(encoding="utf-8"))
    realloc = {}
    for label, block, zero_frac in (("E", summ["eval_E_lines"], result["E"]["joint_hits_per_line"]["zero_lines"] / result["E"]["n_lines"]),
                                    ("HD", summ["development_HD_lines"], result["HD"]["joint_hits_per_line"]["zero_lines"] / result["HD"]["n_lines"])):
        curve = {int(k): v["P2_fp30"]["confirmed"] for k, v in block["custom"]["cap_percent"]["C_mean"].items()}
        target = 20.0 / (1.0 - zero_frac)
        lo = max(k for k in curve if k <= target)
        hi = min(k for k in curve if k >= target)
        interp = curve[lo] + (target - lo) / (hi - lo) * (curve[hi] - curve[lo]) if hi != lo else curve[lo]
        realloc[label] = {"zero_hit_fraction": zero_frac, "equivalent_cap_percent": target, "C_mean_cap_curve": curve,
                          "chord_yield_at_equivalent_cap": interp, "relative_to_20pct": interp / curve[20] - 1,
                          "meaning": "perfect foresight of barren lines + uniform reallocation of their cap; chord of a concave curve is a lower bound of that ideal"}
    result["barren_line_reallocation_bound"] = realloc

    # native plate-set decisions
    native = collections.defaultdict(lambda: collections.defaultdict(list))
    with open(CC / "resources/results/eval_20261004_130438/campaigns_native.jsonl", encoding="utf-8") as handle:
        for line in handle:
            r = json.loads(line)
            if r["rounds"] == 2 and r["fp"] == 30 and r["pct"] in (20, 30, 50):
                native[(r["pct"], r["pred"])][(r["tissue"], r["line"])].append(r["confirmed"])
    nat = {}
    for pct in (20, 30, 50):
        keys = sorted(native[(pct, "C_mean")])
        a = np.array([np.mean(native[(pct, "R")][k]) for k in keys])
        b = np.array([np.mean(native[(pct, "C_mean")][k]) for k in keys])
        d = a - b
        nat[str(pct)] = {"n": len(keys), "R": float(a.sum()), "C_mean": float(b.sum()), "mean_per_line_C_mean": float(b.mean()),
                         "sd_diff": float(d.std(ddof=1)), "halfwidth_rel": float(1.96 * d.std(ddof=1) / sqrt(len(keys)) / b.mean()),
                         "lines_rule_out_tau_50pct": float((1.96 * d.std(ddof=1) / (TAU * b.mean())) ** 2)}
    result["native_plate_set_N2_fp30"] = nat

    # power grid
    grid = []
    for sd in (0.09, 0.15, 0.22, 0.28):
        for n in (61, 64, 125):
            for infl in (1.0, INFL_TWO_WAY):
                se = infl * sd / sqrt(n)
                grid.append({"sd_rel": sd, "n_lines": n, "inflation": round(infl, 2), "halfwidth95": 1.96 * se,
                             "mde_L_gt_0_at_80pct": 2.8 * se, "effect_for_L_gt_tau_at_80pct": TAU + 2.8 * se,
                             "p_U_lt_tau_if_true_effect_0": float(norm.cdf((TAU - 1.96 * se) / se))})
    result["power_grid"] = grid
    result["lines_to_rule_out_tau"] = {f"sd_rel_{sd}": {"at_50pct": (1.96 * sd / TAU) ** 2, "at_80pct": (2.8 * sd / TAU) ** 2,
                                                        "at_80pct_two_way": (2.8 * sd * INFL_TWO_WAY / TAU) ** 2}
                                       for sd in (0.09, 0.15, 0.22, 0.28)}
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
