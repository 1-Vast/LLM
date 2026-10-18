"""Derive the practical-effect threshold and the attainable precision from the development data alone.

File summary
- Path: research/feedback_propagation_20261018/thresholds.py
- Purpose: fix, before the comparison on the estimation folds, (1) the smallest gain that is worth acting on and
  (2) what the estimation folds can resolve. Reads DEVELOPMENT.json (folds 0 and 1) and the family labels of those
  two folds; no estimation-fold outcome and no 24Q2 value is read. Write-once.
- Derivation of delta* (hits per 64 compounds on the unmeasured-pair nomination utility, the quantity PROTOCOL.md
  names primary):
  1. Cost equivalence. The ridge-plus-feedback arm on a common target set (pairs outside the first four pools, so
     every budget is graded on the same pairs) is run at 1..4 pools per compound. delta_cost = its average gain per
     additional pool over 1..3 pools, in hits per 64 compounds. A repair is worth acting on only if it buys at least
     what one more pool read per compound (+33% of the 3-pool cost) buys the baseline.
  2. Relative floor. delta_rel = 10% of the ridge-plus-feedback utility at the primary budget.
  3. delta* = max(delta_cost, delta_rel).
- Attainable precision. Family-cluster bootstrap and campaign-level SD of the paired contrasts on the development
  folds, scaled to the estimation folds' size (36 complete campaigns versus 32). The minimum detectable gain is
  (z_{0.95} + z_{0.80}) * SE with SE = half-width / 1.96; it is reported next to delta*. If MDE > delta* the
  comparison can still reject the null, but a gain of delta* would not be resolved and the decision rule says so.
- Usage: ``python -B thresholds.py``.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import bench
import metrics as M
from bench import tc

HERE = Path(__file__).resolve().parent
OUT = HERE / "THRESHOLDS.json"
EST_COMPLETE_CAMPAIGNS = 36   # folds 2, 3, 4: 733 // 64 + 814 // 64 + 851 // 64 (compound counts are in AUDIT.json)
CONTRASTS = (("R1_vs_ridge", "anchored_K10_lam1.0", "ridge"), ("R1_vs_Cstar", "anchored_K10_lam1.0", "knn10"),
             ("R1_vs_mixture_mean", "anchored_K10_lam1.0", "mixture_mean"), ("gated_vs_R1", "repair_K10_lam1.0_kill", "anchored_K10_lam1.0"),
             ("gated_vs_ridge", "repair_K10_lam1.0_kill", "ridge"), ("Cstar_vs_ridge", "knn10", "ridge"))


def per_compound(dev: dict, name: str, ev: str) -> np.ndarray:
    return np.asarray(dev["grid"][name][ev]["unmeasured"]["hits_c"], dtype=float)


def main() -> None:
    if OUT.exists():
        raise SystemExit("THRESHOLDS.json exists; write-once")
    dev = json.loads((HERE / "DEVELOPMENT.json").read_text(encoding="utf-8"))
    T = bench.load_tables()
    sel = dev["selection"]
    assert sel["R1"] == "anchored_K10_lam1.0" and sel["C_star"] == "knn10" and sel["gated"] == "repair_K10_lam1.0_kill", sel
    # per-compound arrays and the complete-campaign mask of each development fold
    fam, keep, camp_index = {}, {}, {}
    for ev in ("0", "1"):
        test = np.where(T["fold"] == int(ev))[0]
        cores = T["cores"][test]
        camps = tc.campaigns(cores)
        sizes = [len(ix) for ix in camps]
        fam[ev] = T["family"][test]
        keep[ev] = M.complete_mask(sizes, camps)
        camp_index[ev] = camps
    out = {"reads": "DEVELOPMENT.json (folds 0 and 1); family labels of folds 0 and 1", "primary_budget_pools": sel["B"]}

    # 1. cost equivalence on the common target set (hits per 64 compounds, complete campaigns)
    curve = dev["budget_curve_common_target"]
    n_comp = sum(int(keep[ev].sum()) for ev in ("0", "1"))
    rate = {}
    for b, r in curve.items():
        rate[b] = {k: sum(sum(h for h, s in zip(v["unmeasured"]["campaign_hits"], v["unmeasured"]["campaign_compounds"]) if s == M.CAMPAIGN)
                          for v in r[k].values()) / (n_comp / M.CAMPAIGN) for k in r}
    ridge = [rate[str(b)]["ridge"] for b in (1, 2, 3, 4)]
    steps = np.diff(ridge[:3])
    delta_cost = float(np.mean(steps))
    out["cost_equivalence"] = {"complete_campaign_compounds": n_comp, "hits_per_64_compounds": rate,
                               "ridge_gain_per_extra_pool_1_to_3": [float(s) for s in steps], "delta_cost": delta_cost,
                               "reading": "ridge-plus-feedback does not gain systematically from more pools on a fixed target set (flat/non-monotone); "
                                          "a repair that buys more than one pool is therefore a change of the propagation bias, not of the budget"}

    # 2. relative floor
    ridge_primary = sum(sum(h for h, s in zip(v["unmeasured"]["campaign_hits"], v["unmeasured"]["campaign_compounds"]) if s == M.CAMPAIGN)
                        for v in (dev["grid"]["ridge"][ev] for ev in ("0", "1"))) / (n_comp / M.CAMPAIGN)
    delta_rel = 0.10 * ridge_primary
    out["relative_floor"] = {"ridge_hits_per_64_compounds_at_primary_budget": ridge_primary, "delta_rel": delta_rel}
    delta_star = max(delta_cost, delta_rel)
    out["delta_star_hits_per_64_compounds"] = delta_star

    # 3. development contrasts and attainable precision
    contrasts = {}
    for label, a, b in CONTRASTS:
        d = np.concatenate([per_compound(dev, a, ev) - per_compound(dev, b, ev) for ev in ("0", "1")])
        fa = np.concatenate([fam["0"], fam["1"]])
        kp = np.concatenate([keep["0"], keep["1"]])
        pf = M.paired_family(d, fa, kp)
        camp_diffs = []
        for ev in ("0", "1"):
            dd = per_compound(dev, a, ev) - per_compound(dev, b, ev)
            camp_diffs += [float(dd[ix].sum()) for ix in camp_index[ev] if len(ix) == M.CAMPAIGN]
        sd_camp = float(np.std(camp_diffs, ddof=1))
        scale = np.sqrt(len(camp_diffs) / EST_COMPLETE_CAMPAIGNS)
        hw_family = (pf["ci95"][1] - pf["ci95"][0]) / 2 * scale
        hw_camp = 1.96 * sd_camp / np.sqrt(EST_COMPLETE_CAMPAIGNS)
        se = max(hw_family, hw_camp) / 1.96
        contrasts[label] = {"dev_mean_per_64": pf["mean"], "dev_ci95_family_bootstrap": pf["ci95"], "dev_p_one_sided": pf["p_one_sided"],
                            "dev_campaigns": len(camp_diffs), "sd_campaign_difference": sd_camp,
                            "expected_halfwidth_family": float(hw_family), "expected_halfwidth_campaign": float(hw_camp),
                            "expected_se_est": float(se), "mde_one_sided_alpha05_power80": float((1.645 + 0.8416) * se)}
    out["contrasts_dev"] = contrasts
    out["mde_primary_R1_vs_ridge"] = contrasts["R1_vs_ridge"]["mde_one_sided_alpha05_power80"]
    out["resolves_delta_star"] = bool(out["mde_primary_R1_vs_ridge"] <= delta_star)
    out["reading"] = ("delta* is derived from costs and the baseline, not from the size of the repair's own development gain. "
                      "The development gain of the repair is an optimistic (selected) estimate; the estimation folds decide.")
    tc.write_json(OUT, out)
    print(json.dumps({k: out[k] for k in ("delta_star_hits_per_64_compounds", "mde_primary_R1_vs_ridge", "resolves_delta_star")}, indent=1))
    print(json.dumps({k: (round(v["dev_mean_per_64"], 3), [round(x, 3) for x in v["dev_ci95_family_bootstrap"]], round(v["expected_se_est"], 3),
                          round(v["mde_one_sided_alpha05_power80"], 3)) for k, v in contrasts.items()}, indent=1))
    print("cost eq", json.dumps(out["cost_equivalence"]["hits_per_64_compounds"]), "delta_cost", delta_cost, "rel", delta_rel)


if __name__ == "__main__":
    main()
