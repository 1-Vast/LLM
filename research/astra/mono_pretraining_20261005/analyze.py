"""Registered analysis of the S2 records: contrasts, null distributions, swap analysis and the gates.

File summary
- Path: research/astra/mono_pretraining_20261005/analyze.py
- Purpose: turn `s2_{dev,eval}_records.pkl` into line-level paired contrasts with the registered
  tissue-stratified line bootstrap (10,000 resamples, contract seed), the permutation and scratch-vs-scratch
  reference distributions, the swap analysis, and (dev only) the gates that decide whether E may be read.
- Core points: units are lines (draws, roles and family members averaged inside a line); concordance =
  within-line Spearman of the screen score vs the two-orientation mean label (information estimand);
  yield = measured confirmed discoveries under P2 (decision estimand); verdict classes follow the frozen
  contract function with tau = 5% and the EXPLORATORY_ prefix.
- Interfaces: `summarize`, `gates`, `main`.
- Depends on: `common`, the frozen campaign engine.
"""
from __future__ import annotations

import argparse
import json
import pickle
import re

import numpy as np

from research.astra.confirmation_campaign_20261004.design import campaign as c

from . import common as cm

def members(arms, family):
    pre = {"scr_h6": "scr", "dperm_h6": "dperm", "cperm_h6": "cperm"}[family]
    return sorted(x for x in arms if re.fullmatch(rf"{pre}\d+_h6", x))


def resolve(arms, name, base):
    if name == "S1":
        return [base]
    if name in ("scr_h6", "dperm_h6", "cperm_h6"):
        return members(arms, name)
    return [name]


def _rho_lines(conc, names, cfg_for):
    by = {}
    for r in conc:
        if r["arm"] in names and np.isfinite(r["rho"]) and (r["cfg"] == -1 or r["cfg"] == cfg_for.get(r["arm"], r["cfg"])):
            by.setdefault((r["tissue"], r["line"]), []).append(r["rho"])
    return {k: float(np.mean(v)) for k, v in by.items()}


def _auc_lines(conc, names, cfg_for):
    by = {}
    for r in conc:
        if r["arm"] in names and r["auc"] is not None and (r["cfg"] == -1 or r["cfg"] == cfg_for.get(r["arm"], r["cfg"])):
            by.setdefault((r["tissue"], r["line"]), []).append(r["auc"])
    return {k: float(np.mean(v)) for k, v in by.items()}


def _yield_lines(camp, names):
    by = {}
    for r in camp:
        if r["arm"] in names:
            by.setdefault((r["tissue"], r["line"]), []).append(r["confirmed"])
    return {k: float(np.mean(v)) for k, v in by.items()}


def _boot_mean_diff(d: np.ndarray, idx):
    m = np.array([d[i].mean() for i in idx])
    return dict(mean=float(d.mean()), ci=[float(v) for v in np.percentile(m, [2.5, 97.5])], n=int(d.size),
                better=int((d > 0).sum()), worse=int((d < 0).sum()))


def swap_analysis(camp, a, b):
    """Purchased-screen swap rate and net confirmed discoveries of arm a against arm b (same line, role, draw)."""
    A = {(r["tissue"], r["line"], r["role"], r["draw"], r["fold"]): r for r in camp if r["arm"] == a}
    B = {(r["tissue"], r["line"], r["role"], r["draw"], r["fold"]): r for r in camp if r["arm"] == b}
    n_screens = n_diff = gained = lost = 0
    per_line = {}
    for k, ra in A.items():
        rb = B[k]
        sa, sb = set(ra["screens"]), set(rb["screens"])
        ca = set(ra["verification_hits"]) & set(ra["screen_hits"])
        cb = set(rb["verification_hits"]) & set(rb["screen_hits"])
        n_screens += len(sa); n_diff += len(sa - sb); gained += len(ca - cb); lost += len(cb - ca)
        per_line.setdefault(k[:2], []).append(len(ca) - len(cb))
    pl = np.array([np.mean(v) for v in per_line.values()])
    return dict(swap_rate=n_diff / max(n_screens, 1), screens_swapped_in=int(n_diff), confirmed_gained=int(gained),
                confirmed_lost=int(lost), net=int(gained - lost), lines_better=int((pl > 0).sum()),
                lines_worse=int((pl < 0).sum()), lines_tied=int((pl == 0).sum()))


class _T:
    def __init__(self, pid):
        self.pid = pid


def _matrices(camp, names, pids, keys):
    """Line x pair matrices of confirmed pairs averaged over draws and members (as the registered two-way scheme)."""
    mats = []
    for d in sorted({r["draw"] for r in camp}):
        for n in names:
            rs = [r for r in camp if r["arm"] == n and r["draw"] == d]
            mats.append(c.pair_matrices(rs, {k: _T(v) for k, v in pids.items()}, keys))
    return {t: sum(m[t] for m in mats) / len(mats) for t in mats[0]}


def summarize(records: dict, base: str, selected: dict, specs_family: dict, resamples=10000) -> dict:
    conc, camp = records["conc"], records["campaigns"]
    arms = {r["arm"] for r in camp}
    cfg_for = {n: selected[f] for n, f in specs_family.items()}
    keys = c.sort_keys({(r["tissue"], r["line"]) for r in camp})
    idx = c.boot_indices(keys, resamples)

    def lines(kind, name):
        names = resolve(arms, name, base)
        d = {"rho": _rho_lines, "auc": _auc_lines}.get(kind)
        return d(conc, names, cfg_for) if d else _yield_lines(camp, names)

    contrasts = [("pre_h6", "S1"), ("pre_h6", "scr_h6"), ("pre_h6", "dperm_h6"), ("pre_h6", "cperm_h6"),
                 ("pre_h6", "pot_p3"), ("pre_h6", "pre_h3"), ("pre_h3", "S1"), ("pot_p3", "S1"), ("preX_h6", "S1"),
                 ("own_h6", "S1"), ("scr_h6", "S1"), ("D_add", "S1"), ("pre_h6", "preX_h6"), ("own_h6", "pre_h6")]
    out = {"base": base, "n_lines": len(keys), "contrasts": {}}
    for a, b in contrasts:
        if not resolve(arms, a, base) or not resolve(arms, b, base) or a == b:
            continue
        row = {}
        ra, rb = lines("rho", a), lines("rho", b)
        ks = [k for k in keys if k in ra and k in rb]
        row["concordance"] = _boot_mean_diff(np.array([ra[k] - rb[k] for k in ks]), c.boot_indices(ks, resamples))
        aa, ab = lines("auc", a), lines("auc", b)
        ks = [k for k in keys if k in aa and k in ab]
        if ks:
            row["auc_joint_call"] = _boot_mean_diff(np.array([aa[k] - ab[k] for k in ks]), c.boot_indices(ks, resamples))
        ya, yb = lines("yield", a), lines("yield", b)
        x, y = np.array([ya[k] for k in keys]), np.array([yb[k] for k in keys])
        yc = c.boot_contrast(x, y, keys, idx)
        row["yield"] = dict(yc, decision=c.decision(yc))
        if "pids" in records and (a, b) in (("pre_h6", "S1"), ("pre_h6", "scr_h6"), ("own_h6", "S1")):
            mx = _matrices(camp, resolve(arms, a, base), records["pids"], keys)
            my = _matrices(camp, resolve(arms, b, base), records["pids"], keys)
            row["yield"]["line_pair_sensitivity"] = c.two_way(mx, my, keys, resamples=min(resamples, 5000))
        out["contrasts"][f"{a} - {b}"] = row
    # reference distributions: permutation members and scratch-vs-scratch noise floor (concordance gain over base)
    base_rho = lines("rho", "S1")
    ref = {}
    for fam in ("pre_h6", "scr_h6", "dperm_h6", "cperm_h6"):
        vals = []
        for m in resolve(arms, fam, base):
            rm = _rho_lines(conc, [m], cfg_for)
            vals.append(float(np.mean([rm[k] - base_rho[k] for k in keys if k in rm and k in base_rho])))
        ref[fam] = vals
    scr = ref["scr_h6"]
    ref["scratch_vs_scratch_pairwise_diff"] = [abs(scr[i] - scr[j]) for i in range(len(scr)) for j in range(i + 1, len(scr))]
    totals = {}
    for fam in ("scr_h6", "dperm_h6", "cperm_h6"):
        totals[fam] = [float(sum(_yield_lines(camp, [m]).values())) for m in resolve(arms, fam, base)]
    totals["pre_h6"] = float(sum(_yield_lines(camp, ["pre_h6"]).values()))
    totals["S1"] = float(sum(_yield_lines(camp, [base]).values()))
    out["reference_concordance_gain_over_base"] = ref
    out["reference_yield_totals"] = totals
    out["swap"] = {f"{a} vs S1": swap_analysis(camp, a, base) for a in ("pre_h6", "pot_p3", "own_h6", "scr0_h6")
                   if a in arms}
    return out


def gates(dev: dict, g1: dict) -> dict:
    cc = dev["contrasts"]
    ref = dev["reference_concordance_gain_over_base"]
    pre_gain = cc["pre_h6 - S1"]["concordance"]["mean"]
    g2 = cc["own_h6 - S1"]["concordance"]["ci"][0] > 0
    g3_parts = dict(
        pre_over_base=cc["pre_h6 - S1"]["concordance"]["ci"][0] > 0,
        pre_over_scratch=cc["pre_h6 - scr_h6"]["concordance"]["ci"][0] > 0,
        above_all_drug_permutations=pre_gain > max(ref["dperm_h6"]),
        above_all_cell_permutations=pre_gain > max(ref["cperm_h6"]))
    g1p = bool(g1["G1"]["passed"])
    g3 = all(g3_parts.values())
    return dict(G1_mono_preflight=g1p, G2_own_mono_ceiling=bool(g2), G3_development=bool(g3), G3_parts=g3_parts,
                open_E=bool(g1p and g2 and g3),
                rule="E is read only if G1 (held-out mono skill), G2 (own-mono ceiling concordance gain, CI>0) and G3 "
                     "(pretrained concordance gain over base and scratch with CI>0 and above all drug/cell permutations) all pass")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["dev", "eval"])
    a = ap.parse_args(argv)
    from .run_s2 import arm_specs
    fam = {n: sp["family"] for n, sp in arm_specs(65).items()}
    sel = json.loads((cm.RESULTS / f"s2_dev_selection_{cm.RUN}.json").read_text())
    rec = pickle.load(open(cm.RESULTS / f"s2_{a.stage}_records_{cm.RUN}.pkl", "rb"))
    summary = summarize(rec, sel["base"], sel["selected"], fam)
    cm.dump(cm.RESULTS / f"s2_{a.stage}_summary_{cm.RUN}.json", summary)
    if a.stage == "dev":
        g1 = json.loads((cm.RESULTS / "s1_g1.json").read_text())
        g = gates(summary, g1)
        cm.dump(cm.RESULTS / f"s2_gates_{cm.RUN}.json", g)
        print(json.dumps(g, indent=1))
    for k, v in summary["contrasts"].items():
        print(k, "concordance", v["concordance"]["mean"], v["concordance"]["ci"], "| yield", v["yield"]["sum_x"],
              v["yield"]["sum_y"], v["yield"]["relative_gain_ci"], v["yield"]["decision"]["verdict"])


if __name__ == "__main__":
    main()
