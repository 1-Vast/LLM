"""Independent raw CSV aggregation audit. Does not import or rerun prediction code."""
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "log/20261023/cxcl9_source_feasibility"
OUT = BASE / "constructive"


def quantile(values, probability):
    """Linearly interpolate ordered sample quantiles at (n-1)*p."""
    point = (len(values)-1)*probability
    lower = math.floor(point)
    weight = point-lower
    return values[lower]*(1-weight)+values[math.ceil(point)]*weight


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    saved = json.loads((BASE/"PREDICTIONS.json").read_text(encoding="utf-8"))
    schema = {r["file"]: r for r in json.loads((BASE/"SCHEMA_LITERAL.json").read_text())}
    keys = [tuple(k) for k in saved["keys"]]
    assert len(keys) == 24 and len(set(keys)) == 24
    files = {"E3CA": ("BxPC3", "source"), "E3CB": ("BxPC3", "target"),
             "E3DA": ("AsPC1", "source"), "E3DB": ("AsPC1", "target")}
    expected_fields = ["Cell line", "Sample", "Cytokines", "Cytokine concentration (ng/mL)",
                       "Inhibitors", "Inhibitor concentration (uM)", "Condition",
                       "Fluorescent intensity (PE)"]
    comparisons, count_checks, details, inputs = [], 0, [], []
    for code, (cell, side) in files.items():
        path = BASE/"raw"/("00_Raw_Data_"+code+".csv")
        inputs.append(path)
        groups = defaultdict(list)
        ids = defaultdict(set)
        categories = defaultdict(set)
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            assert reader.fieldnames == expected_fields
            rows = 0
            for row in reader:
                rows += 1
                assert row["Cell line"] == cell
                key = (row["Condition"], row["Cytokines"], row["Inhibitors"])
                value = float(row["Fluorescent intensity (PE)"])
                assert math.isfinite(value)
                groups[key].append(value)
                ids[key].add(row["Sample"])
                for field in ("Cell line", "Condition", "Cytokines", "Inhibitors"):
                    categories[field].add(row[field])
        assert rows == schema[code]["rows"]
        assert len(groups) == 48 == schema[code]["groups"]
        assert all(len(v) == 1 for v in ids.values())
        for name, values in categories.items():
            assert sorted(values) == schema[code]["categories"][name]
        assert min(map(len, groups.values())) == schema[code]["min_beads_per_group"]
        assert max(map(len, groups.values())) == schema[code]["max_beads_per_group"]
        samples = sorted(categories["Condition"])
        assert samples == ["Sample1", "Sample2"]
        for variant in ("within_well_iqr", "untrimmed"):
            record = saved["records"][variant+"/"+cell]
            counts = {(r["sample"], r["cytokine"], r["drug"]): r
                      for r in record[side+"_counts"]}
            assert len(counts) == 48
            transformed = {}
            for group, values in groups.items():
                ordered = sorted(values)
                q1, q3 = quantile(ordered, .25), quantile(ordered, .75)
                low, high = q1-1.5*(q3-q1), q3+1.5*(q3-q1)
                kept = [v for v in values if low <= v <= high] if variant == "within_well_iqr" else values
                mean = math.fsum(kept)/len(kept)
                assert math.isfinite(mean) and mean > 0
                transformed[group] = math.log10(mean)
                expected = counts[group]
                assert expected["file"] == code
                assert expected["raw_beads"] == len(values)
                assert expected["retained_beads"] == len(kept)
                count_checks += 1
                details.append({"file": code, "variant": variant, "group": group,
                                "raw_count": len(values), "kept_count": len(kept),
                                "mean_PE": mean})
            array = record[side+"_samples"]
            assert len(array) == 2 and all(len(a) == 24 for a in array)
            for sample_index, sample in enumerate(samples):
                blank = transformed[(sample, "None", "None")]
                for index, (cytokine, drug) in enumerate(keys):
                    actual = transformed[(sample, cytokine, drug)]-blank
                    expected = array[sample_index][index]
                    difference = abs(actual-expected)
                    assert difference <= 1e-12
                    comparisons.append({"file": code, "variant": variant, "sample": sample,
                                        "cytokine": cytokine, "drug": drug,
                                        "recomputed": actual, "saved": expected, "abs_diff": difference})
    assert len(comparisons) == count_checks == 384
    paths = inputs+[BASE/"PREDICTIONS.json", BASE/"PREDICTION_PROTOCOL.md",
                    BASE/"SCHEMA_LITERAL.json", Path(__file__)]
    result = {"status": "PASS_RAW_AGGREGATION_AUDIT", "scope": "raw means, inclusive local IQR means, blank-centering, schema and counts only; no model/metric audit or rerun",
              "scalar_comparisons": len(comparisons), "group_count_comparisons": count_checks,
              "raw_rows": {k: schema[k]["rows"] for k in files},
              "max_absolute_difference": max(c["abs_diff"] for c in comparisons),
              "quantile": "linear order-statistic interpolation at (n-1)*p; inclusive IQR boundaries",
              "independent_aggregation": "csv.DictReader + sorted quantile + math.fsum/log10; no root import",
              "comparisons": comparisons, "means_and_counts": details,
              "input_sha256": {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}}
    (OUT/"RAW_AUDIT.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("comparisons", "means_and_counts", "input_sha256")}, indent=2))


if __name__ == "__main__":
    main()
