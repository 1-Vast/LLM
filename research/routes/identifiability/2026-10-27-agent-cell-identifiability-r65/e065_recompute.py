"""E065: recompute the three prose-only register numbers from stored data.

R64 found three numbers that exist only in report prose (C2's validation tau pair and its
layout-clustered CI, C23's between-unit sd). The register forbids rewriting old records, so
this round RECOMPUTES them from stored data and stores the result in a supplementary file.

Pre-registered in PROTOCOL_E063.md.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

R = Path(r"D:\MAESTRO\research")
E = "2026-10-27-agent-cell-identifiability-"
OUT = R / (E + "r65")
OUT.mkdir(parents=True, exist_ok=True)

# ---------------- C2: validation tau pair and layout-clustered CI ----------------
d5 = json.load(open(R / (E + "r5") / "E006_RESULTS.json", encoding="utf-8"))
cc = d5["cellpair_comparisons"]

half = np.array([c["tau_half_mean"] for c in cc], dtype=float)
cross = np.array([c["tau_cross"] for c in cc], dtype=float)
diff = np.array([c["diff"] for c in cc], dtype=float)
layouts = np.array([c["layout"] for c in cc])
uniq = sorted(set(layouts))

med_half = float(np.median(half))
med_cross = float(np.median(cross))
med_diff = float(np.median(diff))

# layout-clustered bootstrap of the MEDIAN difference
rng = np.random.default_rng(20261027)
draws = []
by_layout = {L: diff[layouts == L] for L in uniq}
for _ in range(4000):
    pick = rng.choice(uniq, size=len(uniq), replace=True)
    sample = np.concatenate([by_layout[L] for L in pick])
    draws.append(np.median(sample))
ci_lo, ci_hi = float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))

# ---------------- C23: between-unit sd from stored variance components ----------------
d28 = json.load(open(R / (E + "r28") / "E028_RESULTS.json", encoding="utf-8"))
share = d28["results"]["between_unit_share"]
total_var = d28["audit"]["total_var"]
within_sd = d28["results"]["within_unit_sd_median"]
between_sd = math.sqrt(share * total_var)
ratio = within_sd / between_sd if between_sd else float("nan")

res = {
    "kind": "recomputation_of_prose_only_register_numbers",
    "purpose": "R64 reported three numbers that exist only in report prose; the register forbids rewriting old records, so they are recomputed here from what IS stored",
    "C2_validation": {
        "n_cellpairs": int(len(cc)),
        "n_layouts": len(uniq),
        "recomputed_median_tau_half": med_half,
        "recomputed_median_tau_cross": med_cross,
        "recomputed_median_diff": med_diff,
        "recomputed_layout_clustered_ci95_of_median_diff": [ci_lo, ci_hi],
        "prose_values": {"tau_half": 0.891, "tau_cross": 0.712, "ci": [0.116, 0.291]},
        "match_tau_half": abs(med_half - 0.891) < 0.005,
        "match_tau_cross": abs(med_cross - 0.712) < 0.005,
        "ci_overlaps_prose": not (ci_hi < 0.116 or ci_lo > 0.291),
        "bootstrap_note": "4000 layout-resamplings, seed 20261027; the original seed is unknown, so the CI endpoints are not expected to match to the digit"
    },
    "C23_between_sd": {
        "between_unit_share": share,
        "total_var": total_var,
        "within_unit_sd_median": within_sd,
        "recomputed_between_unit_sd": between_sd,
        "prose_value": 0.032,
        "match": abs(between_sd - 0.032) < 0.002,
        "recomputed_ratio_within_over_between": ratio,
        "prose_ratio": 1.38,
        "ratio_match": abs(ratio - 1.38) < 0.05,
        "formula": "between_sd = sqrt(between_share * total_var), which is the only way the stored fields determine it"
    },
}

ok = (res["C2_validation"]["match_tau_half"] and res["C2_validation"]["match_tau_cross"]
      and res["C2_validation"]["ci_overlaps_prose"]
      and res["C23_between_sd"]["match"] and res["C23_between_sd"]["ratio_match"])
res["decisions"] = {"H164_prose_numbers_reproducible": bool(ok)}
res["limits"] = [
    "recomputation uses the stored per-cell data and the stored variance components; if either was itself computed with an unknown seed, small differences are expected",
    "the bootstrap CI endpoints depend on the seed and are compared by overlap, not equality",
    "read-only with respect to old records: nothing in E006 or E028 was modified",
]
(OUT / "E065_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

print("C2  recomputed tau_half median = %.4f (prose 0.891)" % med_half)
print("C2  recomputed tau_cross median = %.4f (prose 0.712)" % med_cross)
print("C2  recomputed median diff = %.4f" % med_diff)
print("C2  layout-clustered CI = [%.4f, %.4f]  (prose [0.116, 0.291])" % (ci_lo, ci_hi))
print("C23 between-unit sd = %.4f (prose 0.032)  ratio %.3f (prose 1.38)" % (between_sd, ratio))
print("\nH164 prose numbers reproducible:", res["decisions"]["H164_prose_numbers_reproducible"])
