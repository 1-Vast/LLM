"""Outcome-blind early-CEL/late-functional availability, preserving dose-level identity."""
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification"


def main():
    target = OUT / "EARLY_LATE_MENU_COUNTS.json"
    if target.exists():
        raise RuntimeError("Pairwise census exists")
    source = OUT / "JOINED_IDENTITY_FLAGS.json"
    rows = json.loads(source.read_text(encoding="utf-8"))
    menus, controls = defaultdict(list), defaultdict(list)
    for row in rows:
        if row["DOSE_LEVEL"] == "Control":
            controls[(row["EXP_ID"], row["SACRIFICE_PERIOD"])].append(row)
        else:
            menu = (row["EXP_ID"], row["COMPOUND_NAME"], str(Decimal(row["DOSE"]).normalize()),
                    row["DOSE_UNIT"], row["DOSE_LEVEL"])
            menus[menu].append(row)
    result = {}
    for early, late in [("2 hr", "8 hr"), ("2 hr", "24 hr"), ("8 hr", "24 hr")]:
        entry = {}
        for endpoint in ["DNA", "LDH", "both"]:
            def functional(r):
                return all(r[f"{e}_nonmissing_unconflicted"] for e in (["DNA", "LDH"] if endpoint == "both" else [endpoint]))
            counters = defaultdict(list)
            for menu, members in menus.items():
                early_rows = [r for r in members if r["SACRIFICE_PERIOD"] == early]
                late_rows = [r for r in members if r["SACRIFICE_PERIOD"] == late]
                if not early_rows or not late_rows:
                    continue
                counters["identity_time_overlap"].append(menu)
                early_ok = [r for r in early_rows if r["CEL_identity_and_barcode_match"]]
                late_ok = [r for r in late_rows if functional(r)]
                if len(early_ok) >= 1 and len(late_ok) >= 1:
                    counters["at_least_one_early_CEL_and_late_functional"].append(menu)
                if len(early_ok) < 2 or len(late_ok) < 2:
                    continue
                counters["at_least_two_early_CEL_and_late_functional"].append(menu)
                if not (all(r["CEL_identity_and_barcode_match"] for r in early_rows) and all(functional(r) for r in late_rows)):
                    continue
                counters["all_original_early_CEL_and_late_functional"].append(menu)
                early_controls = controls.get((menu[0], early), [])
                late_controls = controls.get((menu[0], late), [])
                if sum(r["CEL_identity_and_barcode_match"] for r in early_controls) >= 2 and sum(functional(r) for r in late_controls) >= 2:
                    counters["plus_two_matched_early_CEL_and_late_functional_controls"].append(menu)
                if all(r["CEL_identity_and_barcode_match"] for r in late_rows):
                    counters["also_all_original_late_CEL"].append(menu)
            entry[endpoint] = {name: {"conditions": len(values), "compound_labels": len({m[1] for m in values})}
                               for name, values in counters.items()}
        result[f"{early}_to_{late}"] = entry
    record = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "condition_key": ["EXP_ID", "COMPOUND_NAME", "decimal_canonical_DOSE", "DOSE_UNIT", "DOSE_LEVEL"],
              "basis": "Whitelisted identities/null/conflict flags only; no response values",
              "control_scope": "Same EXP_ID and time; not authenticated same physical culture, lot, well or donor",
              "counts": result}
    target.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
