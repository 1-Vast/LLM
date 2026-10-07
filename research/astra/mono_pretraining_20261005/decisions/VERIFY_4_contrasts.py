"""Check 4: recompute the dev contrasts and the G1-G3 logic from s2_dev_records.pkl without analyze.py.

Reads only the study's records (no outcome file). Run:
PYTHONPATH='src;.' D:/anaconda/envs/maestro/python.exe research/astra/mono_pretraining_20261005/decisions/VERIFY_4_contrasts.py
Writes decisions/VERIFY_4_contrasts.json (refuses to overwrite).
"""
from __future__ import annotations

import json
import pickle
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import VERIFY_lib as L  # noqa: E402

OUT = L.HERE / "VERIFY_4_contrasts.json"
rec = pickle.load(open(L.STUDY / "results/s2_dev_records.pkl", "rb"))
sel = json.loads((L.STUDY / "results/s2_dev_selection.json").read_text())
summ = json.loads((L.STUDY / "results/s2_dev_summary.json").read_text())
gates = json.loads((L.STUDY / "results/s2_gates.json").read_text())
cfg_of_family = sel["selected"]
fam = lambda a: ("scr_h6" if re.fullmatch(r"scr\d+_h6", a) else "dperm_h6" if re.fullmatch(r"dperm\d+_h6", a)
                 else "cperm_h6" if re.fullmatch(r"cperm\d+_h6", a) else a)
arms = sorted({r["arm"] for r in rec["campaigns"]})
members = {f: sorted(a for a in arms if fam(a) == f) for f in ("scr_h6", "dperm_h6", "cperm_h6")}
tissue_of = {}


def line_rho(names):
    by = {}
    for r in rec["conc"]:
        a = r["arm"]
        if a in names and np.isfinite(r["rho"]) and (r["cfg"] == -1 or r["cfg"] == cfg_of_family.get(fam(a), -2)):
            by.setdefault((r["tissue"], r["line"]), []).append(r["rho"])
            tissue_of[(r["tissue"], r["line"])] = r["tissue"]
    return {k: float(np.mean(v)) for k, v in by.items()}


def line_yield(names):
    by = {}
    for r in rec["campaigns"]:
        if r["arm"] in names:
            by.setdefault((r["tissue"], r["line"]), []).append(r["confirmed"])
    return {k: float(np.mean(v)) for k, v in by.items()}


def resolve(name):
    if name == "S1":
        return [sel["base"]]
    return members.get(name, [name])


def contrast(a, b):
    ra, rb = line_rho(resolve(a)), line_rho(resolve(b))
    ks = sorted(set(ra) & set(rb))
    conc = L.line_bootstrap({k: ra[k] - rb[k] for k in ks}, {k: k[0] for k in ks})
    ya, yb = line_yield(resolve(a)), line_yield(resolve(b))
    ks = sorted(ya)
    y = L.line_bootstrap({k: ya[k] - yb[k] for k in ks}, {k: k[0] for k in ks}, base_by_line={k: yb[k] for k in ks})
    y.update(sum_a=float(sum(ya.values())), sum_b=float(sum(yb.values())), rel=float(sum(ya.values()) / sum(yb.values()) - 1))
    return dict(concordance=conc, yield_=y)


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"REFUSED: {OUT} exists")
    names = [("pre_h6", "S1"), ("pre_h6", "scr_h6"), ("pre_h6", "dperm_h6"), ("pre_h6", "cperm_h6"), ("own_h6", "S1"),
             ("pre_h6", "pot_p3"), ("pot_p3", "S1"), ("D_add", "S1")]
    mine = {f"{a} - {b}": contrast(a, b) for a, b in names}
    cmp = {}
    for k, v in mine.items():
        t = summ["contrasts"].get(k)
        if t is None:
            continue
        cmp[k] = dict(conc_mean=(v["concordance"]["mean"], t["concordance"]["mean"]),
                      conc_ci=(v["concordance"]["ci"], t["concordance"]["ci"]),
                      yield_rel=(v["yield_"]["rel"], t["yield"]["relative_gain"]),
                      yield_rel_ci=(v["yield_"]["rel_ci"], t["yield"]["relative_gain_ci"]),
                      max_abs_diff=max(abs(v["concordance"]["mean"] - t["concordance"]["mean"]),
                                       abs(v["concordance"]["ci"][0] - t["concordance"]["ci"][0]),
                                       abs(v["concordance"]["ci"][1] - t["concordance"]["ci"][1]),
                                       abs(v["yield_"]["rel"] - t["yield"]["relative_gain"]),
                                       abs(v["yield_"]["rel_ci"][0] - t["yield"]["relative_gain_ci"][0]),
                                       abs(v["yield_"]["rel_ci"][1] - t["yield"]["relative_gain_ci"][1])))
    # reference distributions of concordance gain over base per member
    base = line_rho(resolve("S1"))
    ref = {}
    for f in ("scr_h6", "dperm_h6", "cperm_h6"):
        ref[f] = [float(np.mean([line_rho([m])[k] - base[k] for k in base if k in line_rho([m])])) for m in members[f]]
    pre = line_rho(["pre_h6"])
    pre_gain = float(np.mean([pre[k] - base[k] for k in base]))
    # gate recomputation per PROTOCOL_V1 section 7
    own = mine["own_h6 - S1"]["concordance"]
    g2 = own["ci"][0] > 0
    g3 = dict(pre_over_base=mine["pre_h6 - S1"]["concordance"]["ci"][0] > 0,
              pre_over_scratch=mine["pre_h6 - scr_h6"]["concordance"]["ci"][0] > 0,
              above_all_drug_perm=pre_gain > max(ref["dperm_h6"]), above_all_cell_perm=pre_gain > max(ref["cperm_h6"]))
    # per-member paired contrasts pre vs each permutation member (line level), fraction of members that beat pre
    beat = {f: int(sum(g > pre_gain for g in ref[f])) for f in ref}
    # scratch-vs-scratch noise floor
    scr = ref["scr_h6"]
    nf = [abs(scr[i] - scr[j]) for i in range(len(scr)) for j in range(i + 1, len(scr))]
    # swap analysis of pre_h6 vs base, independent
    A = {(r["tissue"], r["line"], r["role"], r["draw"]): r for r in rec["campaigns"] if r["arm"] == "pre_h6"}
    B = {(r["tissue"], r["line"], r["role"], r["draw"]): r for r in rec["campaigns"] if r["arm"] == sel["base"]}
    sw = dict(screens=0, swapped=0, gained=0, lost=0)
    for k, ra in A.items():
        rb = B[k]
        sa, sb = set(ra["screens"]), set(rb["screens"])
        ca = set(ra["verification_hits"]); cb = set(rb["verification_hits"])
        sw["screens"] += len(sa); sw["swapped"] += len(sa - sb); sw["gained"] += len(ca - cb); sw["lost"] += len(cb - ca)
    res = dict(mine=mine, comparison_with_analyze=cmp, max_abs_diff_overall=max(v["max_abs_diff"] for v in cmp.values()),
               pre_concordance_gain_over_base=pre_gain, reference_gain_members={f: [round(x, 6) for x in v] for f, v in ref.items()},
               members_with_gain_above_pre=beat, scratch_vs_scratch_noise_floor_max=float(max(nf)),
               G2_mine=dict(ci_lower_above_0=bool(g2), own_gain=own), G3_parts_mine=g3,
               gates_file=gates, swap_pre_vs_base=sw)
    OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
