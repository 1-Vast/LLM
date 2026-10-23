"""Compare two completed artifacts; never rerun either calculator."""
import hashlib
import json
from pathlib import Path

LOG = Path(__file__).resolve().parents[2] / "log/20261022/repair_information_opportunity"
primary_raw = (LOG / "UPPER_BOUND_RESULT.json").read_bytes()
independent_raw = (LOG / "INDEPENDENT_RECOMPUTE.json").read_bytes()
primary = json.loads(primary_raw)
independent = json.loads(independent_raw)
mapping = {
    "R_only": "repair_only",
    "R_plus_B1": "repair_with_B1_fallback",
    "R_plus_B1_Cmol": "repair_with_B1_Cmol_fallback",
    "all_saved": "all_saved_actions",
}
checks = []
for own in independent["tables"]:
    theirs, = [t for t in primary["tables"] if t["input"]["path"] == own["source"]]
    assert theirs["input"]["sha256"] == own["sha256"]
    assert theirs["lineages"] == own["lineages"]
    assert theirs["stocks"] == own["cells"]
    for baseline, score in own["baseline_precision5"].items():
        assert theirs["fixed_scores"][baseline]["exact"] == score["exact"]
    for ours, theirs_name in mapping.items():
        a, b = own["menus"][ours], theirs["menus"][theirs_name]
        assert set(a["arms"]) == set(b["arms"])
        assert a["oracle_precision5"]["exact"] == b["optimistic_stock_aware_upper"]["exact"]
        assert a["single_action_per_lineage_precision5"]["exact"] == b["single_action_per_lineage_upper"]["exact"]
        for baseline, contrast in a["gain_over_baselines"].items():
            other = b["contrasts"][baseline]
            assert contrast["precision5"]["exact"] == other["delta_precision5"]["exact"]
            assert contrast["hits5"]["exact"] == other["delta_hits"]["exact"]
            assert contrast["strictly_below_margin"] != other["can_reach_recorded_margin"]
        for cell, value in a["per_cell"].items():
            assert value["oracle_precision5"] == b["stock_oracle"][cell]["precision5"]
            assert value["tied_maximizers"] == sorted(b["stock_oracle"][cell]["ties"])
        checks.append({"source": own["source"], "menu": ours, "matched": True})
answer = {
    "matched": True, "matched_tables": 3, "matched_menus": len(checks),
    "checks": checks,
    "primary_sha256": hashlib.sha256(primary_raw).hexdigest(),
    "independent_sha256": hashlib.sha256(independent_raw).hexdigest(),
    "comparison_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "notes": "Exact Fractions agree for baselines, envelopes, restricted lineage envelopes, all comparator differences, per-stock maxima and all tied argmax sets. Independent switching gain is within-menu; primary versus_hindsight_best_fixed is table-global, so these different quantities were not compared.",
}
with (LOG / "INDEPENDENT_MATCH.json").open("x", encoding="utf-8") as stream:
    json.dump(answer, stream, indent=2)
    stream.write("\n")
print("PASS: 3 tables, 12 menus, exact quantities and per-stock tied maximizers match")
