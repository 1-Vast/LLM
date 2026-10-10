"""Offline source-QC, adaptive selection and byte-projection verification."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CALIBRATION = BASE / "calibration"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    frozen = load(HERE / "FREEZE.json")
    for path, digest in frozen["sha256"].items():
        assert hashlib.sha256((BASE / path).read_bytes()).hexdigest() == digest
    selected = load(HERE / "SELECTION.json")
    pool = load(HERE / "CANDIDATE_POOL.json")
    sources = load(CALIBRATION / "CENSUSES.json")
    old = load(CALIBRATION / "QC_ROWS.json")
    endpoint = load(CALIBRATION / "inputs/ENDPOINT.json")
    sample = pd.read_parquet(CALIBRATION / "inputs/SAMPLES.parquet").set_index("sample", verify_integrity=True)
    counts = load(CALIBRATION / "INDEX_RESULTS.json")
    remaining = {entry["file"]: {g: max(3-int(n), 0) for g, n in zip(
        endpoint["symbols"], entry["index_occurrences_per_gene"])} for entry in counts["files"]}
    assert remaining == selected["initial_index_deficits_to_three"]
    arrays = {file: np.load(CALIBRATION / "inputs" / f"{file}_CODES.npz", allow_pickle=False) for file in sources}
    pointers = {file: np.load(CALIBRATION / meta["pointer_path"], allow_pickle=False) for file, meta in sources.items()}
    for candidate in pool:
        file = candidate["file"]
        codes, ptr, cats = arrays[file], pointers[file], sources[file]["categories"]
        assert candidate["label"] not in {g["label"] for g in old["groups"] if g["file"] == file}
        assert candidate["label"] not in old["exclusions"]["excluded_exact_sentinel_labels"]
        mask = ((codes["drugname_drugconc"] == cats["drugname_drugconc"].index(candidate["label"]))
            & (codes["plate"] == cats["plate"].index("plate1"))
            & (codes["pass_filter"] == cats["pass_filter"].index("full"))
            & (codes["cell_line"] == cats["cell_line"].index(candidate["cell_line_id"])))
        rows = [int(i) for i in np.flatnonzero(mask)
                if cats["sample"][int(codes["sample"][i])] not in old["exclusions"]["excluded_pooled_sample_ids"]]
        assert rows == candidate["eligible_rows"] and len(rows) == candidate["full_qc_available"] >= 50
        samples = {cats["sample"][int(codes["sample"][i])] for i in rows}
        assert samples == set(candidate["samples"])
        assert all(sample.loc[sid, "plate"] == "plate1" and
                   sample.loc[sid, "drugname_drugconc"] == candidate["label"] for sid in samples)
        nnz = [int(ptr[i+1])-int(ptr[i]) for i in rows]
        assert candidate["index_screen_bytes"] == 4*sum(nnz)
        assert candidate["largest_32_raw_value_bytes"] == 4*sum(sorted(nnz, reverse=True)[:32])
    reconstructed, spent = [], 0
    available = list(pool)
    while available:
        rankings = []
        for c in available:
            if sum(r["file"] == c["file"] for r in reconstructed) >= 8 or spent+c["index_screen_bytes"] > 8_500_000:
                continue
            hints = [g for g, d in remaining[c["file"]].items() if d > 0 and c["all39_named_deltas"][g] > 0]
            value = sum(remaining[c["file"]][g] for g in hints)
            if value:
                magnitude = sum(Fraction.from_float(c["normalized_positive_hint"][g]) for g in hints)
                rankings.append((-value, -magnitude, c["label"], c["file"], c, hints))
        if not rankings:
            break
        _, _, _, file, winner, hints = min(rankings, key=lambda x: x[:4])
        recorded = selected["selected"][len(reconstructed)]
        assert winner["file"] == recorded["file"] and winner["label"] == recorded["label"]
        assert hints == recorded["newly_counted_positive_hint_genes"]
        assert {g: d for g, d in remaining[file].items() if d > 0} == recorded["remaining_hint_deficits_before"]
        reconstructed.append(winner)
        spent += winner["index_screen_bytes"]
        for g in hints:
            remaining[file][g] -= 1
        available = [c for c in available if not (c["file"] == file and c["label"] == winner["label"])]
    assert len(reconstructed) == len(selected["selected"])
    assert spent == selected["exact_new_index_payload_bytes"] == 8_141_672
    assert remaining == selected["remaining_hint_deficits"]
    assert selected["prior_calibration_body_bytes"] == counts["cumulative_new_body_bytes"] == 12_397_900
    projected = 12_397_900 + spent + 4_000_000 + selected["new_metadata_and_error_body_cap"]
    assert projected == selected["projected_total_with_raw_and_error_reserves"] == 24_641_672 <= 25_000_000
    assert selected["new_metadata_and_error_body_cap"] == 102_100
    assert selected["new_network_calls"] == 0 and frozen["new_indices_read"] is False
    verdict = {"schema": "offline_supplementary_panel_verification_v1", "status": "PASS",
        "source_QC_candidates_rebuilt": len(pool), "selected_new_conditions": len(reconstructed),
        "eligible_full_QC_rows": sum(len(c["eligible_rows"]) for c in reconstructed),
        "projected_new_index_bytes": spent, "total_with_reserves": projected,
        "new_network_calls": 0, "new_expression_reads": False,
        "all_hint_deficits_covered": False,
        "boundary": "Frozen adaptive proposal; no proof actualindices or values satisfyauthentication; greedybudgetlimit isnotglobalinfeasibility."}
    (HERE / "VERIFIED.json").write_text(json.dumps(verdict, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(verdict))


if __name__ == "__main__":
    main()
