"""Independently audit projected metadata only; never open the source ZIP."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / "log/20261022/intervention_program_renewal"
OUT = PHASE / "data_auditor"
SOURCE = PHASE / "az_design"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads((SOURCE / "CENSUS.json").read_text(encoding="utf-8"))
    keys = set()
    backgrounds = set()
    stocks = set()
    drug_ids = set()
    pair_cells = defaultdict(set)
    rows = 0
    shapes = Counter()
    dimensions = Counter()
    member_shapes = defaultdict(Counter)
    member_rows = Counter()
    member_keys = Counter()
    member_pairs = defaultdict(set)
    member_cells = defaultdict(set)
    treatment = Counter()
    short_axes = Counter()
    short_tags = Counter()
    conflicts = duplicates_position = duplicates_dose = non_rectangular = 0
    model_metadata = defaultdict(lambda: defaultdict(set))
    h = hashlib.sha256()
    record_fields = {"member", "PROJECT_ID", "BARCODE", "cmatrix", "rows", "metadata", "dose_pairs", "positions"}
    meta_fields = set(report["allowed_fields"]) - {"PROJECT_ID", "BARCODE", "cmatrix", "POSITION", "lib1_dose", "lib1_conc", "lib2_dose", "lib2_conc"}
    with (SOURCE / "DESIGN_MATRICES.jsonl").open("rb") as stream:
        for line in stream:
            h.update(line)
            r = json.loads(line)
            assert set(r) == record_fields
            key = (r["member"], r["PROJECT_ID"], r["BARCODE"], r["cmatrix"])
            assert key not in keys
            keys.add(key)
            rows += r["rows"]
            member_rows[r["member"]] += r["rows"]
            member_keys[r["member"]] += 1
            conflicts += len(r["metadata"]) != 1
            duplicates_position += sum(count - 1 for count in r["positions"].values())
            duplicates_dose += sum(d["count"] - 1 for d in r["dose_pairs"])
            assert sum(r["positions"].values()) == r["rows"]
            assert sum(d["count"] for d in r["dose_pairs"]) == r["rows"]
            axes = [set(), set()]
            axis_tags = [set(), set()]
            coords = set()
            for d in r["dose_pairs"]:
                assert set(d) == {"lib1_dose", "lib1_conc", "lib2_dose", "lib2_conc", "count"}
                one = (d["lib1_dose"], d["lib1_conc"])
                two = (d["lib2_dose"], d["lib2_conc"])
                axes[0].add(one)
                axes[1].add(two)
                axis_tags[0].add(one[0])
                axis_tags[1].add(two[0])
                coords.add((one, two))
            shape = len(coords)
            shapes[shape] += 1
            dim = (len(axes[0]), len(axes[1]))
            dimensions[dim] += 1
            member_shapes[r["member"]][f"{dim[0]}x{dim[1]}"] += 1
            non_rectangular += shape != dim[0] * dim[1]
            for m in r["metadata"]:
                assert set(m) == meta_fields
                cell = m["MASTER_CELL_ID"]
                pair = tuple(sorted((m["lib1_drug_id"], m["lib2_drug_id"])))
                pair_cells[pair].add(cell)
                backgrounds.add(cell)
                stocks.add((cell, m["CELL_ID"]))
                drug_ids.update(pair)
                member_pairs[r["member"]].add((cell, pair))
                member_cells[r["member"]].add(cell)
                treatment[m["treatment"]] += 1
                for field in ("CELL_LINE_NAME", "COSMIC_ID", "TISSUE", "CANCER_TYPE"):
                    model_metadata[cell][field].add(m[field])
                if shape != 49:
                    for axis in range(2):
                        if len(axes[axis]) != 7:
                            short_axes[(r["member"], m[f"lib{axis + 1}_drug_id"], len(axes[axis]))] += 1
                            short_tags[(len(axes[axis]), tuple(sorted(axis_tags[axis])))] += 1
    top64 = sorted(pair_cells, key=lambda p: (-len(pair_cells[p]), p))[:64]
    common = set.intersection(*(pair_cells[p] for p in top64))
    actual = {"released_rows": rows, "matrix_keys": len(keys), "source_cell_models": len(backgrounds),
              "source_drug_ids": len(drug_ids), "source_unordered_pairs": len(pair_cells),
              "pair_cell_model_units": sum(len(c) for c in pair_cells.values()),
              "cell_model_stock_units": len(stocks), "dose_surface_size_counts": {str(k): v for k, v in sorted(shapes.items())},
              "duplicate_positions_within_matrix": duplicates_position,
              "duplicate_dose_pairs_within_matrix": duplicates_dose}
    assert all(actual[k] == report["overall"][k] for k in actual)
    assert h.hexdigest() == report["design_projection_sha256"]
    assert [list(p) for p in top64] == report["overall"]["descriptive_top64_pairs"]
    assert sorted(common) == report["overall"]["descriptive_top64_common_cell_models"]
    assert conflicts == len(report["overall"]["matrix_identity_conflicts"])
    binding = {"code": digest(ROOT / "research/intervention_program_renewal_20261022/az_design_census.py") == report["code_sha256"],
               "protocol": digest(PHASE / "AZ_METADATA_PROJECTION.md") == report["protocol_sha256"]}
    assert all(binding.values())
    per_member = {m: {"rows": member_rows[m], "matrices": member_keys[m],
                      "cell_models": len(member_cells[m]), "pair_cell_units": len(member_pairs[m]),
                      "dimensions": dict(member_shapes[m])} for m in sorted(member_rows)}
    for member, values in per_member.items():
        expected = report["by_member"][member]
        assert values["rows"] == expected["released_rows"]
        assert values["matrices"] == expected["matrix_keys"]
        assert values["pair_cell_units"] == expected["pair_cell_model_units"]
    result = {"utc": datetime.now(timezone.utc).isoformat(), "actual": actual,
              "census_binding_unchanged": binding, "projection_sha256": h.hexdigest(),
              "matrix_identity_conflicts": conflicts, "non_rectangular_surfaces": non_rectangular,
              "dimension_counts": {f"{a}x{b}": n for (a, b), n in sorted(dimensions.items())},
              "top64_common_cell_models": len(common), "per_member": per_member,
              "source_model_metadata_conflicts": [
                  {"cell": cell, "field": field, "values": sorted(values)}
                  for cell, fields in model_metadata.items() for field, values in fields.items() if len(values) > 1],
              "short_axis_by_member_drug_id": [{"member": m, "drug_id": d, "axis_size": a, "matrices": n}
                                                for (m, d, a), n in sorted(short_axes.items())],
              "short_axis_tag_patterns": [{"axis_size": a, "tags": list(tags), "axes": n}
                                           for (a, tags), n in sorted(short_tags.items())],
              "source_zip_opened_by_auditor": False, "target_values_read": False, "fits": 0,
              "scope": "Independent recount of projected metadata only; no graph scan"}
    (OUT / "CENSUS_REVIEW.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
