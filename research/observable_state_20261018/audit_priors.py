"""Check the quoted prior results against repository records and derive the power table.

File summary
- Path: research/observable_state_20261018/audit_priors.py
- Reads only public result files of finished studies (RESULTS.json, HINDSIGHT_CLARIFICATION.json). No outcome tables.
- Writes PRIOR_CHECK.json (each quoted number, its record, match flag) and POWER.json (cluster-level standard errors
  implied by the recorded intervals and the compound counts needed for declared effect sizes).
- Power assumptions are stated in the output: SE scales with 1/sqrt(compounds); one-sided alpha 0.025 (Holm over two
  primaries), power 0.8; the factorial interaction contrast is bounded by 2x the SE of a paired contrast (arms treated as
  independent, conservative).
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist

HERE = Path(__file__).resolve().parent
R = HERE.parent
Z = NormalDist().inv_cdf


def main() -> dict:
    ap = json.loads((R / "acquisition_program_20261018/RESULTS.json").read_text(encoding="utf-8"))
    hs = json.loads((R / "acquisition_program_20261018/HINDSIGHT_CLARIFICATION.json").read_text(encoding="utf-8"))
    rates, con = ap["contrasts"]["rates_per_64_compounds"], ap["contrasts"]
    quoted = [
        ("fixed design events/64", 1.822, rates["fixed"], 1e-3),
        ("handwritten lookahead", 1.717, rates["handwritten_lookahead"], 1e-3),
        ("agent-search incumbent", 1.725, rates["agent_search"], 1e-3),
        ("no-feedback prior", 0.931, rates["prior"], 1e-3),
        ("lookahead - fixed", -0.106, con["lookahead_vs_fixed"]["mean"], 1e-3),
        ("lookahead - fixed CI lo", -0.262, con["lookahead_vs_fixed"]["ci95"][0], 1e-3),
        ("lookahead - fixed CI hi", 0.022, con["lookahead_vs_fixed"]["ci95"][1], 1e-3),
        ("agent - fixed", -0.097, con["agent_vs_fixed"]["mean"], 1e-3),
        ("agent - lookahead", 0.008, con["agent_vs_lookahead"]["mean"], 1e-3),
        ("hindsight second-pool total (held-out)", 704, ap["hindsight_acquisition_choice_total_UNAVAILABLE"], 0),
        ("fixed total (held-out)", 656, ap["totals"]["fixed"]["total"], 0),
        ("campaign best-of hits", 131, hs["hits"]["campaign_best_of"], 0),
        ("R1 hits", 100, hs["hits"]["R1"], 0),
        ("ridge hits", 95, hs["hits"]["ridge"], 0),
    ]
    checks = [{"quantity": q, "quoted": a, "record": b, "match": abs(a - b) <= tol} for q, a, b, tol in quoted]
    hind = ap["hindsight_acquisition_choice_total_UNAVAILABLE"] / ap["totals"]["fixed"]["total"] - 1
    # --- power
    n0, fam0 = con["lookahead_vs_fixed"]["n_compounds"], con["lookahead_vs_fixed"]["n_families"]
    ses = {k: (v["ci95"][1] - v["ci95"][0]) / (2 * 1.96) for k, v in con.items() if isinstance(v, dict) and "ci95" in v and v["ci95"][1] > v["ci95"][0]}
    k_ = Z(1 - 0.025) + Z(0.8)
    floor = 0.1875
    rel15 = 0.15 * rates["fixed"]
    table = {}
    for name in ("lookahead_vs_fixed", "agent_vs_lookahead", "R1_vs_fixed", "agent_vs_R1"):
        se = ses[name]
        row = {"se_at_%d_compounds" % n0: se, "mde_at_%d_compounds" % n0: k_ * se}
        for tag, delta in (("floor_0.1875", floor), ("15pct_of_fixed", rel15)):
            row["compounds_needed_" + tag] = math.ceil(n0 * (k_ * se / delta) ** 2)
            row["campaigns64_needed_" + tag] = math.ceil(row["compounds_needed_" + tag] / 64)
        table[name] = row
    inter_se = 2 * ses["R1_vs_fixed"]
    inter = {"assumed_se_interaction_at_%d_compounds" % n0: inter_se, "assumption": "2 x SE of the highest-variance recorded paired contrast (R1 - fixed); arms treated independent (conservative)"}
    for tag, delta in (("floor_0.1875", floor), ("15pct_of_fixed", rel15)):
        inter["compounds_needed_" + tag] = math.ceil(n0 * (k_ * inter_se / delta) ** 2)
        inter["campaigns64_needed_" + tag] = math.ceil(inter["compounds_needed_" + tag] / 64)
    power = {"basis": f"{n0} compounds / {fam0} MoA-family clusters in acquisition_program_20261018 held-out assessment",
             "alpha_one_sided": 0.025, "power": 0.8, "practical_floor_events_per_64": floor, "15pct_of_fixed_events_per_64": rel15,
             "contrasts": table, "factorial_interaction": inter,
             "reading": "Contrasts between arms with a shared backend and different acquisition (low variance) are resolvable at a few hundred to ~1k compounds; contrasts that change the predictor or labels (R1-type) need thousands. The registered thresholds must come from the arm-specific pilot SE on D_search, not from this table.",
             "headroom_reference": {"second_pool_hindsight_vs_fixed_heldout": hind, "development": 410 / 305 - 1}}
    (HERE / "PRIOR_CHECK.json").write_text(json.dumps({"all_match": all(c["match"] for c in checks), "checks": checks}, indent=1) + "\n", encoding="utf-8")
    (HERE / "POWER.json").write_text(json.dumps(power, indent=1) + "\n", encoding="utf-8")
    return {"checks": checks, "power": power}


if __name__ == "__main__":
    o = main()
    print("all_match", all(c["match"] for c in o["checks"]))
    print(json.dumps(o["power"]["contrasts"], indent=1)[:1500])
    print(o["power"]["factorial_interaction"], o["power"]["headroom_reference"])
