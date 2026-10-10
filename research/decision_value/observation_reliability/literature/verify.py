"""Verify retained literature, official sample joins and design-only accounting."""
import ast
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq


HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify():
    receipts = [item for name in ("FETCH_RECEIPTS.json", "ADDITIONAL_RECEIPTS.json", "TIME_SEARCH_RECEIPTS.json")
                for item in read(HERE / name)["sources"]]
    for item in receipts:
        if item["status"] != "RECEIVED":
            continue
        body = (HERE / item["path"]).read_bytes()
        assert len(body) == item["bytes"] and hashlib.sha256(body).hexdigest() == item["sha256"]
    qualification = read(HERE / "SOURCE_QUALIFICATION.json")
    sample_path = HERE / qualification["sample_metadata_file"]
    assert hashlib.sha256(sample_path.read_bytes()).hexdigest() == qualification["sample_metadata_sha256"]
    assert qualification["official_lfs_hash_matches"] is True
    samples = pq.read_table(sample_path)
    assert samples.column_names == qualification["sample_metadata_columns"]
    assert samples.num_rows == qualification["sample_metadata_rows"]
    index = {row["sample"]: row for row in samples.to_pylist()}
    assert len(index) == samples.num_rows
    for row in qualification["join_rows"]:
        assert index[row["sample"]] == row["source_record"]
        assert index[row["sample"]]["plate"] == row["filtered_plate"]
        assert row["sample_found"] and row["plate_matches"] and row["recorded_condition_matches"]
    text = (HERE / "sources/tahoe_biorxiv_text_alt.txt").read_text(encoding="utf-8")
    for quote in qualification["paper"]["primary_quotes"]:
        assert quote["quote"] in text
    assert "Cells were exposed to drug media for 24 hours at 37C and 5% CO2" in text
    assert "Plate 14 as a biological replicate of Plate 6" in text
    assert "three cell lines (NCI-H661, NCI-H596, NCI-H2122)" in text
    revised = read(HERE / "UPDATED_SENTINELS.json")
    assert revised["status"].startswith("DESIGN_ONLY")
    assert revised["actual_treated_expression_bytes"] == 0
    selected = revised["selected"]
    for row in selected:
        assert row["file"] in ("c44.h5ad", "c45.h5ad") and row["full_qc_cells"] >= 50
        for sample in row["sample_counts"]:
            official = index[sample]
            assert official["plate"] == row["plate"]
            assert ast.literal_eval(official["drugname_drugconc"]) == ast.literal_eval(row["label"])
    assert len(selected) == revised["proposed_treated_strata"] == 24
    assert len({(row["plate"], sample) for row in selected for sample in row["sample_counts"]}) == 12
    assert sum(row["proposed_cells"] for row in selected) == revised["proposed_treated_cells"] == 768
    assert sum(row["proposed_hvg_bytes"] for row in selected) == revised["proposed_treated_hvg_bytes"] == 6_144_000
    verdict = dict(status="PASS_RETAINED_SOURCE_AND_SAMPLE_JOIN_AUDIT", source_requests=len(receipts),
        successful_responses=sum(row["status"] == "RECEIVED" for row in receipts),
        known_successful_body_bytes=sum(row.get("bytes", 0) for row in receipts),
        original_join_strata=len(qualification["join_rows"]), updated_treated_join_strata=len(selected),
        actual_treated_expression_bytes=0, new_network_calls=0,
        scope="Global published-source protocol and metadata joins; design-only sentinels, not outcome verification.")
    print(json.dumps(verdict))
    return verdict


if __name__ == "__main__":
    verify()
