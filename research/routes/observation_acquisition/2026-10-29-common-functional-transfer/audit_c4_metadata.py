"""Audit frozen identities/windows without selecting any response field."""
from collections import Counter, defaultdict
from pathlib import Path
import csv
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
freeze = json.loads((HERE / "metadata_freeze.json").read_text(encoding="utf-8"))
OUT = HERE / "metadata_audit.json"
assert not OUT.exists(), "Do not overwrite an audit"
train = {c["id"] for c in freeze["cells"] if c["role"] == "train"}
cell_fields = defaultdict(lambda: defaultdict(set))
reverse = defaultdict(lambda: defaultdict(set))
names, drug_names = defaultdict(set), defaultdict(set)
windows, pairs = defaultdict(lambda: defaultdict(set)), Counter()
bad_ids, bad_windows = [], []
with Path(freeze["source"]).open(encoding="utf-8-sig", newline="") as handle:
    for i, full in enumerate(csv.DictReader(handle)):
        row = {k: full[k] for k in ("DATASET", "SANGER_MODEL_ID", "COSMIC_ID",
               "CELL_LINE_NAME", "TCGA_DESC", "DRUG_ID", "DRUG_NAME", "MIN_CONC",
               "MAX_CONC", "NLME_RESULT_ID")}
        sidm = row["SANGER_MODEL_ID"]
        if row["DATASET"] != "GDSC2" or not re.fullmatch(r"SIDM\d+", sidm):
            continue
        for key in ("COSMIC_ID", "CELL_LINE_NAME", "TCGA_DESC"):
            value = row[key]
            cell_fields[sidm][key].add(value)
            if value and key != "TCGA_DESC":
                reverse[key][value].add(sidm)
        name = re.sub(r"[^a-z0-9]", "", row["DRUG_NAME"].lower())
        names[name].add(row["DRUG_NAME"])
        drug_names[row["DRUG_ID"]].add(name)
        window = (row["DRUG_ID"], row["MIN_CONC"], row["MAX_CONC"])
        if sidm in train:
            windows[name][window].add(sidm)
        pairs[(sidm, name, window, row["NLME_RESULT_ID"])] += 1
        if not re.fullmatch(r"\d+", row["NLME_RESULT_ID"]):
            bad_ids.append(i)
        try:
            low, high = float(row["MIN_CONC"]), float(row["MAX_CONC"])
            assert 0 < low < high < float("inf")
        except (ValueError, AssertionError):
            bad_windows.append(i)

inconsistent = {sidm: {k: sorted(v) for k, v in fields.items() if len(v) != 1}
                for sidm, fields in cell_fields.items() if any(len(v) != 1 for v in fields.values())}
window_changes, unique_counts = [], {}
for condition in freeze["conditions"]:
    name = condition["id"]
    chosen = min(windows[name], key=lambda w: (-len(windows[name][w]), w))
    previous = (condition["drug_id"], condition["min_conc_raw"], condition["max_conc_raw"])
    unique_counts[name] = len(windows[name][chosen])
    if chosen != previous:
        window_changes.append({"id": name, "previous": previous, "unique_cell_mode": chosen})
result = {
    "source_sha256": freeze["source_sha256"],
    "freeze_sha256": hashlib.sha256((HERE / "metadata_freeze.json").read_bytes()).hexdigest(),
    "response_values_consumed": 0,
    "inconsistent_cell_metadata": inconsistent,
    "reverse_identity_collisions": {k: {v: sorted(s) for v, s in values.items() if len(s) > 1}
                                    for k, values in reverse.items()},
    "normalised_name_collisions": {k: sorted(v) for k, v in names.items() if len(v) > 1},
    "drug_ids_with_multiple_names": {k: sorted(v) for k, v in drug_names.items() if len(v) > 1},
    "unparseable_result_ids_source_rows": bad_ids,
    "invalid_concentration_metadata_source_rows": bad_windows,
    "duplicate_same_identity_window_result_id_groups": sum(n > 1 for n in pairs.values()),
    "additional_same_identity_window_result_id_rows": sum(n-1 for n in pairs.values()),
    "unique_cell_mode_changes": window_changes,
    "train_unique_cell_counts_per_frozen_condition": unique_counts,
    "conditions_with_unique_train_coverage_at_least_90pct": sum(n / len(train) >= .9 for n in unique_counts.values()),
    "boundary": "Metadata consistency only. No structure/donor validation, response quality or potency verification."
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "train_unique_cell_counts_per_frozen_condition"}, ensure_ascii=False))
