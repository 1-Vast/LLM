"""Check frozen bytes, export scope and availability arithmetic without raw outcomes."""
import hashlib
import json
from pathlib import Path

import pandas as pd

from worker import FLAGS, IDENTITY

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification"


def main():
    destination = OUT / "VERIFICATION.json"
    if destination.exists():
        raise RuntimeError("Verification exists")
    checks = 0
    def check(condition):
        nonlocal checks
        if not condition:
            raise AssertionError("Availability verification failed")
        checks += 1
    def read(name):
        return json.loads((OUT / name).read_text(encoding="utf-8"))
    for name, expected in read("PRE_OPEN_FREEZE.json")["sha256"].items():
        check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected)
    receipt = read("NETWORK.json")
    archive = OUT / "sealed_source/open_tggates_cell_viability.zip"
    check(archive.stat().st_size == receipt["received_body_bytes"] <= 2_000_000)
    check(hashlib.sha256(archive.read_bytes()).hexdigest() == receipt["sha256"])
    flags = read("HUMAN_FUNCTIONAL_FLAGS.json")
    for row in flags:
        check(set(row) == set(IDENTITY + FLAGS))
        check(all(type(row[column]) is bool for column in FLAGS))
    raw = pd.DataFrame(flags)
    result = read("FUNCTIONAL_CENSUS.json")
    counts = result["counts"]
    check(len(raw) == counts["human_functional_rows"])
    check(raw["DNA_missing"].sum() == counts["DNA_missing_rows"])
    check(raw["LDH_missing"].sum() == counts["LDH_missing_rows"])
    check((~raw["DNA_missing"] & ~raw["LDH_missing"]).sum() == counts["both_nonmissing_rows"])
    check(raw.duplicated(IDENTITY[:3]).sum() == counts["functional_duplicate_excess_rows"])
    for label, values in result["unmatched_keys"].items():
        check(len(values) == counts["absent_key_counts"][label])
    joined = pd.DataFrame(read("JOINED_IDENTITY_FLAGS.json"))
    check(len(joined) == counts["human_cell_rows"])
    for column, total in counts["sample_qualification_counts"].items():
        check(joined[column].sum() == total)
    check(counts["human_functional_rows"] + len(result["unmatched_keys"]["cell_keys_without_functional"]) == counts["human_cell_rows"])
    check(counts["human_cel_attribute_rows"] + len(result["unmatched_keys"]["cell_keys_without_cel_attributes"]) == counts["human_cell_rows"])
    missing_cel = result["five_missing_cel_attributes_identity_explanation"]
    check(len(missing_cel) == 5)
    check(all(r["barcode_link_is_empty"] and not r["barcode_matches_any_human_cel_attribute"] and r["functional_key_present"] for r in missing_cel))
    # Independent dataframe aggregation uses dose strings rather than the census's Decimal/group-loop.
    # In this official archive, exact dose strings preserve every tested level-specific menu.
    treated = joined[joined["DOSE_LEVEL"].ne("Control")].copy()
    keys = ["EXP_ID", "COMPOUND_NAME", "DOSE", "DOSE_UNIT", "DOSE_LEVEL"]
    pairwise = read("EARLY_LATE_MENU_COUNTS.json")
    check(hashlib.sha256((OUT / "JOINED_IDENTITY_FLAGS.json").read_bytes()).hexdigest() == pairwise["source_sha256"])
    for early, late in [("2 hr", "8 hr"), ("2 hr", "24 hr"), ("8 hr", "24 hr")]:
        expected = pairwise["counts"][f"{early}_to_{late}"]
        early_good = treated[treated["SACRIFICE_PERIOD"].eq(early) & treated["CEL_identity_and_barcode_match"]].groupby(keys).size()
        for endpoint in ["DNA", "LDH", "both"]:
            good = treated["DNA_nonmissing_unconflicted"] & treated["LDH_nonmissing_unconflicted"] if endpoint == "both" else treated[f"{endpoint}_nonmissing_unconflicted"]
            late_good = treated[treated["SACRIFICE_PERIOD"].eq(late) & good].groupby(keys).size()
            for threshold, name in [(1, "at_least_one_early_CEL_and_late_functional"), (2, "at_least_two_early_CEL_and_late_functional")]:
                overlap = early_good[early_good >= threshold].index.intersection(late_good[late_good >= threshold].index)
                check(len(overlap) == expected[endpoint][name]["conditions"])
                check(len(set(overlap.get_level_values("COMPOUND_NAME"))) == expected[endpoint][name]["compound_labels"])
    record = {"status": "PASS", "checks": checks,
              "raw_functional_archive_decoded_by_verifier": False,
              "scope": "Frozen bytes, exact export schema/booleans, joins/count arithmetic, independent early/late availability aggregation; no outcome signal validation"}
    destination.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record))


if __name__ == "__main__":
    main()
