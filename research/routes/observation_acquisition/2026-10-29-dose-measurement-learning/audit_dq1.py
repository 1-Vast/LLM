"""Frozen DQ1 exported-response consistency audit; no fitted labels or model training."""
from pathlib import Path
from decimal import Decimal, InvalidOperation
import hashlib
import json
import time
import zipfile
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE.parent.parent / "tmp/extq1/gsdc_well_stats.zip"
MEMBER = "combo_well_stats_GDSC_007_05May22.csv"
COLS = ["PROJECT_ID", "BARCODE", "MASTER_CELL_ID", "CELL_ID", "POSITION", "cmatrix",
        "lib1_drug_id", "lib1_drug", "lib1_conc", "lib1_y",
        "lib2_drug_id", "lib2_drug", "lib2_conc", "lib2_y"]
started = time.monotonic()
sha = hashlib.sha256()
with RAW.open("rb") as stream:
    for block in iter(lambda: stream.read(1 << 20), b""):
        sha.update(block)
assert sha.hexdigest() == "e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259"
with zipfile.ZipFile(RAW) as archive:
    with archive.open(MEMBER) as stream:
        frame = pd.read_csv(stream, usecols=COLS, nrows=20_000, dtype=str, keep_default_na=False)


def number(value):
    try:
        result = Decimal(value)
        return result if result.is_finite() else None
    except InvalidOperation:
        return None


groups, identity, bad_dose, bad_y, outside, zero = {}, {}, 0, 0, 0, 0
for row in frame.to_dict(orient="records"):
    for side in (1, 2):
        conc, y = number(row[f"lib{side}_conc"]), number(row[f"lib{side}_y"])
        if conc is None or conc < 0:
            bad_dose += 1
            continue
        zero += int(conc == 0)
        bad_y += int(y is None)
        outside += int(y is not None and (y < 0 or y > 1))
        key = (row["PROJECT_ID"], row["MASTER_CELL_ID"], row[f"lib{side}_drug"], conc)
        item = groups.setdefault(key, {"appearances": 0, "texts": set(), "values": set(), "invalid_y": 0})
        item["appearances"] += 1
        item["texts"].add(row[f"lib{side}_y"])
        if y is None:
            item["invalid_y"] += 1
        else:
            item["values"].add(y)
        identity.setdefault(key[:3], set()).add((row["BARCODE"], row["MASTER_CELL_ID"], row[f"lib{side}_drug_id"]))

conflicts = [key for key in sorted(groups) if len(groups[key]["values"]) > 1]
mapping_conflicts = sum(len(values) > 1 for values in identity.values())
packet = []
for key in sorted(groups)[:16]:
    item = groups[key]
    packet.append({"id": f"K{len(packet)+1:02d}", "key": [str(v) for v in key],
                   "appearance_count": item["appearances"], "distinct_raw_y_strings": sorted(item["texts"]),
                   "invalid_y_count": item["invalid_y"]})
qualified = bad_dose == bad_y == mapping_conflicts == len(conflicts) == 0
out = {
    "protocol_sha256": hashlib.sha256((HERE / "DQ1_protocol.md").read_bytes()).hexdigest(),
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "raw_sha256": sha.hexdigest(), "member": MEMBER, "fixed_prefix_rows": len(frame), "columns": COLS,
    "response_fields_examined": 2 * len(frame), "first_response_exposure": "This fixed prefix is now development-exposed; old exposure elsewhere is not erased",
    "csv_row_bytes_include_fitted_fields": True, "fitted_fields_retained_or_numerically_parsed": [],
    "invalid_nonfinite_or_negative_dose_appearances": bad_dose, "zero_dose_appearances": zero,
    "invalid_or_nonfinite_y_appearances": bad_y, "y_appearances_outside_zero_one": outside,
    "unique_exported_keys": len(groups), "repeated_exported_keys": sum(x["appearances"] > 1 for x in groups.values()),
    "keys_with_multiple_raw_y_strings": sum(len(x["texts"]) > 1 for x in groups.values()),
    "keys_with_multiple_finite_numeric_y": len(conflicts), "reference_identity_mapping_conflicts": mapping_conflicts,
    "first_conflict_keys_lexicographic": [[str(v) for v in k] for k in conflicts[:8]],
    "numeric_consistency_tolerance": "exact Decimal equality; zero tolerance; no rounding/averaging/clipping",
    "exported_key_usable_for_retrospective_development": qualified,
    "qualification_scope": "Fixed-prefix same-screen deterministic exported-reference prediction only; not original well identity, culture independence, noise mean, cross-screen generalization or scientific benefit",
    "seconds": round(time.monotonic() - started, 3)
}
assert out["seconds"] < 120
(HERE / "dq1_result.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(HERE / "dq1_arithmetic_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
