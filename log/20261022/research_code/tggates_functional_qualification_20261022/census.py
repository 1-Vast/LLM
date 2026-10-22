"""Join only whitelisted identities and missingness; never read source responses."""
from collections import Counter, defaultdict
from decimal import Decimal
import json
from pathlib import Path

from worker import FLAGS, IDENTITY, KEY

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/tggates_functional_qualification"
OLD = ROOT / "log/20261022/tggates_source_qualification"


def key(row):
    return tuple(row[c] for c in KEY)


def group(rows):
    result = defaultdict(list)
    for row in rows:
        result[key(row)].append(row)
    return result


def join_flags(cells, attrs, functional):
    """Require key AND all ten identity strings, plus CEL barcode agreement."""
    by_f, by_a = group(functional), group(attrs)
    joined, mismatches = [], []
    for cell in cells:
        f_rows, a_rows = by_f.get(key(cell), []), by_a.get(key(cell), [])
        f_fields = [c for c in IDENTITY if any(r[c] != cell[c] for r in f_rows)]
        a_fields = [c for c in IDENTITY + ["BARCODE"] if any(r[c] != cell[c] for r in a_rows)]
        if f_fields or a_fields:
            mismatches.append({**{c: cell[c] for c in KEY}, "functional_mismatch_fields": f_fields,
                               "cel_mismatch_fields": a_fields})
        f_ok = bool(f_rows) and not f_fields and not any(r["identity_conflict"] for r in f_rows)
        a_ok = len(a_rows) == 1 and not a_fields and bool(cell["BARCODE"].strip())
        record = {**cell, "functional_source_rows": len(f_rows), "functional_identity_match": f_ok,
                  "CEL_identity_and_barcode_match": a_ok,
                  "DNA_nonmissing_unconflicted": f_ok and all(not r["DNA_missing"] and not r["DNA_conflict"] for r in f_rows),
                  "LDH_nonmissing_unconflicted": f_ok and all(not r["LDH_missing"] and not r["LDH_conflict"] for r in f_rows)}
        joined.append(record)
    return joined, mismatches


def temporal_census(joined):
    menus = defaultdict(list)
    for row in joined:
        if row["DOSE_LEVEL"] == "Control":
            continue
        menus[(row["COMPOUND_NAME"], str(Decimal(row["DOSE"]).normalize()), row["DOSE_UNIT"])].append(row)
    full = {"2 hr", "8 hr", "24 hr"}
    definitions = {
        "all_identity_samples": lambda r: True,
        "functional_identity_match": lambda r: r["functional_identity_match"],
        "CEL_identity_and_barcode_match": lambda r: r["CEL_identity_and_barcode_match"],
        "CEL_and_DNA_nonmissing": lambda r: r["CEL_identity_and_barcode_match"] and r["DNA_nonmissing_unconflicted"],
        "CEL_and_LDH_nonmissing": lambda r: r["CEL_identity_and_barcode_match"] and r["LDH_nonmissing_unconflicted"],
        "CEL_and_both_nonmissing": lambda r: r["CEL_identity_and_barcode_match"] and r["DNA_nonmissing_unconflicted"] and r["LDH_nonmissing_unconflicted"],
    }
    result = {}
    for name, permitted in definitions.items():
        selected, all_samples, two_each = [], [], []
        for menu, rows in menus.items():
            qualified = [r for r in rows if permitted(r)]
            counts = Counter(r["SACRIFICE_PERIOD"] for r in qualified)
            if full.issubset(counts):
                selected.append(menu)
                if all(permitted(r) for r in rows):
                    all_samples.append(menu)
                if all(counts[t] >= 2 for t in full):
                    two_each.append(menu)
        result[name] = {"at_least_one_per_time_conditions": len(selected),
                        "at_least_one_per_time_compounds": len({k[0] for k in selected}),
                        "at_least_two_per_time_conditions": len(two_each),
                        "all_original_samples_qualified_conditions": len(all_samples)}
    result["identity_time_set_counts"] = dict(Counter("|".join(sorted({r["SACRIFICE_PERIOD"] for r in rows})) for rows in menus.values()))
    result["compound_dose_unit_conditions"] = len(menus)
    return result


def main():
    target = OUT / "FUNCTIONAL_CENSUS.json"
    if target.exists():
        raise RuntimeError("Census exists; no overwrite")
    cells = json.loads((OLD / "HUMAN_CELL_IDENTITIES.json").read_text(encoding="utf-8"))
    attrs = json.loads((OLD / "HUMAN_CEL_IDENTITIES.json").read_text(encoding="utf-8"))
    functional = json.loads((OUT / "HUMAN_FUNCTIONAL_FLAGS.json").read_text(encoding="utf-8"))
    if any(set(r) != set(IDENTITY + FLAGS) or any(type(r[c]) is not bool for c in FLAGS) for r in functional):
        raise RuntimeError("Restricted functional projection contract failed")
    cg, ag, fg = group(cells), group(attrs), group(functional)
    if any(len(v) != 1 for v in cg.values()):
        raise RuntimeError("Previous cell identity keys are not unique")
    joined, mismatches = join_flags(cells, attrs, functional)
    absent = {
        "cell_keys_without_functional": [{c: r[c] for c in IDENTITY} for r in cells if key(r) not in fg],
        "functional_keys_without_cell": [{c: r[c] for c in IDENTITY} for r in functional if key(r) not in cg],
        "cell_keys_without_cel_attributes": [r for r in cells if key(r) not in ag],
        "cel_attribute_keys_without_cell": [r for r in attrs if key(r) not in cg],
    }
    missing_cel_explanation = [{**r,
        "barcode_link_is_empty": not bool(r["BARCODE"].strip()),
        "barcode_matches_any_human_cel_attribute": any(a["BARCODE"] == r["BARCODE"] for a in attrs),
        "functional_key_present": key(r) in fg} for r in absent["cell_keys_without_cel_attributes"]]
    sample_flags = {name: sum(bool(r[name]) for r in joined) for name in
                    ["functional_identity_match", "CEL_identity_and_barcode_match", "DNA_nonmissing_unconflicted", "LDH_nonmissing_unconflicted"]}
    counts = {"human_cell_rows": len(cells), "human_cel_attribute_rows": len(attrs),
              "human_functional_rows": len(functional), "human_functional_unique_keys": len(fg),
              "functional_duplicate_keys": sum(len(v) > 1 for v in fg.values()),
              "functional_duplicate_excess_rows": sum(len(v) - 1 for v in fg.values()),
              "cel_duplicate_keys": sum(len(v) > 1 for v in ag.values()),
              "DNA_missing_rows": sum(r["DNA_missing"] for r in functional),
              "LDH_missing_rows": sum(r["LDH_missing"] for r in functional),
              "both_nonmissing_rows": sum(not r["DNA_missing"] and not r["LDH_missing"] for r in functional),
              "identity_conflict_keys": sum(any(r["identity_conflict"] for r in v) for v in fg.values()),
              "DNA_conflict_keys": sum(any(r["DNA_conflict"] for r in v) for v in fg.values()),
              "LDH_conflict_keys": sum(any(r["LDH_conflict"] for r in v) for v in fg.values()),
              "identity_mismatch_keys": len(mismatches),
              "absent_key_counts": {k: len(v) for k, v in absent.items()},
              "sample_qualification_counts": sample_flags}
    temporal = temporal_census(joined)
    old_temporal = json.loads((OLD / "TEMPORAL_IDENTITY.json").read_text(encoding="utf-8"))
    if temporal["all_identity_samples"]["at_least_one_per_time_conditions"] != old_temporal["same_compound_dose_unit_all_three_times"]:
        raise RuntimeError("Previous temporal identity census not reproduced")
    result = {"counts": counts, "temporal": temporal,
              "unmatched_keys": absent, "identity_mismatches": mismatches,
              "five_missing_cel_attributes_identity_explanation": missing_cel_explanation,
              "no_numeric_response_values_read_by_census": True,
              "nonmissing_does_not_establish_numerical_validity": True,
              "pairing_scope": "Official same EXP_ID/GROUP_ID/INDIVIDUAL_ID condition linkage; not proof of same physical cell, culture, well, lot or donor"}
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "JOINED_IDENTITY_FLAGS.json").write_text(json.dumps(joined, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"counts": counts, "temporal": temporal}, indent=2))


if __name__ == "__main__":
    main()
