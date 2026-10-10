"""Offline, adaptive supplementary condition selection before new CSR indices."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CALIBRATION = BASE / "calibration"
sys.path.insert(0, str(BASE / "informative"))
from project import read_plate1


INDEX_CAP = 8_500_000
RAW_RESERVE = 4_000_000
TOTAL_CAP = 25_000_000
MAX_NEW_CONDITIONS_PER_FILE = 8


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidates():
    endpoint = read(CALIBRATION / "inputs/ENDPOINT.json")
    counts = read(CALIBRATION / "INDEX_RESULTS.json")
    source = read(CALIBRATION / "CENSUSES.json")
    old = read(CALIBRATION / "QC_ROWS.json")
    protected = old["exclusions"]
    samples = pd.read_parquet(CALIBRATION / "inputs/SAMPLES.parquet").set_index("sample", verify_integrity=True)
    assert sha(CALIBRATION / "inputs/SAMPLES.parquet") == "33167f0ce28cff8357c503cda67d1c7fea200bff6918ee1de3c4f3549175b9d3"
    named, _, _ = read_plate1(["cell_line", "treatment"] + endpoint["symbols"])
    named = named.to_pandas()
    deficits = {entry["file"]: {gene: max(3-int(n), 0) for gene, n in
                zip(endpoint["symbols"], entry["index_occurrences_per_gene"])} for entry in counts["files"]}
    pool, source_inputs = [], {}
    for file, meta in source.items():
        assert meta["source_revision"] == "fdf87abece385feea6fa5e9944ab46e173b6af50"
        codes_path = CALIBRATION / "inputs" / f"{file}_CODES.npz"
        pointer_path = CALIBRATION / meta["pointer_path"]
        codes = np.load(codes_path, allow_pickle=False)
        ptr = np.load(pointer_path, allow_pickle=False)
        assert sha(pointer_path) == meta["pointer_sha256"]
        assert all(hashlib.sha256(codes[key].tobytes()).hexdigest() == meta["codes_sha256"][key] for key in codes.files)
        assert meta["layouts"]["X/indices"]["dtype"] == "<i4"
        cats = meta["categories"]
        sid = "CVCL_1715" if file == "c44.h5ad" else "CVCL_1716"
        old_labels = {group["label"] for group in old["groups"] if group["file"] == file}
        old_rows = {row for group in old["groups"] if group["file"] == file for row in group["eligible_rows"]}
        filtered = named.loc[named.cell_line.eq(sid)]
        full_plate_line = ((codes["plate"] == cats["plate"].index("plate1"))
            & (codes["pass_filter"] == cats["pass_filter"].index("full"))
            & (codes["cell_line"] == cats["cell_line"].index(sid)))
        gene_max = {g: float(filtered[g].max()) for g in endpoint["symbols"]}
        for _, row in filtered.iterrows():
            label = row["treatment"]
            if label in old_labels or label in protected["excluded_exact_sentinel_labels"] or label not in cats["drugname_drugconc"]:
                continue
            eligible = np.flatnonzero(full_plate_line & (codes["drugname_drugconc"] == cats["drugname_drugconc"].index(label)))
            rows = [int(i) for i in eligible if cats["sample"][int(codes["sample"][i])] not in protected["excluded_pooled_sample_ids"]]
            if len(rows) < 50:
                continue
            ids = sorted({cats["sample"][int(codes["sample"][i])] for i in rows})
            if any(samples.loc[sample, "plate"] != "plate1" or samples.loc[sample, "drugname_drugconc"] != label for sample in ids):
                raise RuntimeError("official_sample_join_failed")
            assert not set(rows) & old_rows
            nnz = [int(ptr[i+1])-int(ptr[i]) for i in rows]
            assert min(nnz) >= 0
            pool.append({"file": file, "cell_line_id": sid, "label": label, "plate": "plate1",
                "samples": ids, "official_sample_join_verified": True, "full_qc_available": len(rows),
                "eligible_rows": rows, "index_screen_bytes": 4*sum(nnz),
                "largest_32_raw_value_bytes": 4*sum(sorted(nnz, reverse=True)[:32]),
                "all39_named_deltas": {g: float(row[g]) for g in endpoint["symbols"]},
                "normalized_positive_hint": {g: float(row[g])/gene_max[g] if row[g] > 0 and gene_max[g] > 0 else 0.0 for g in endpoint["symbols"]}})
        source_inputs[file] = {"codes_path": codes_path.relative_to(BASE).as_posix(), "codes_sha256": sha(codes_path),
            "pointer_path": pointer_path.relative_to(BASE).as_posix(), "pointer_sha256": sha(pointer_path),
            "source_gene_count": meta["source_gene_count"], "old_index_cells": len(old_rows)}
    return endpoint, counts, source_inputs, pool, deficits


def choose(pool, initial_deficits):
    remaining = {file: dict(values) for file, values in initial_deficits.items()}
    used_bytes, chosen = 0, []
    available = list(pool)
    while available:
        ranked = []
        for candidate in available:
            file = candidate["file"]
            if sum(c["file"] == file for c in chosen) >= MAX_NEW_CONDITIONS_PER_FILE:
                continue
            if used_bytes + candidate["index_screen_bytes"] > INDEX_CAP:
                continue
            covered = [gene for gene, deficit in remaining[file].items()
                       if deficit > 0 and candidate["all39_named_deltas"][gene] > 0]
            score = sum(remaining[file][g] for g in covered)
            magnitude = sum(Fraction.from_float(candidate["normalized_positive_hint"][g]) for g in covered)
            if score:
                ranked.append((-score, -magnitude, candidate["label"], file, candidate, covered))
        if not ranked:
            break
        _, _, _, file, winner, covered = min(ranked, key=lambda x: x[:4])
        winner = dict(winner)
        winner["rank"] = len(chosen)+1
        winner["deficit_weighted_hint_score"] = sum(remaining[file][g] for g in covered)
        winner["newly_counted_positive_hint_genes"] = covered
        winner["remaining_hint_deficits_before"] = {g: n for g, n in remaining[file].items() if n > 0}
        chosen.append(winner)
        used_bytes += winner["index_screen_bytes"]
        for gene in covered:
            remaining[file][gene] -= 1
        available = [c for c in available if not (c["file"] == winner["file"] and c["label"] == winner["label"])]
    return chosen, remaining, used_bytes


def main():
    if (HERE / "FREEZE.json").exists():
        raise FileExistsError("Supplementary selection already frozen")
    HERE.mkdir(exist_ok=True)
    endpoint, prior, inputs, pool, deficits = candidates()
    selected, remaining, index_bytes = choose(pool, deficits)
    prior_bytes = prior["cumulative_new_body_bytes"]
    assert prior_bytes == 12_397_900
    metadata_cap = TOTAL_CAP - prior_bytes - INDEX_CAP - RAW_RESERVE
    assert metadata_cap >= 0
    output = {"schema": "adaptive_named_hint_supplementary_selection_v1",
        "status": "READY_FOR_PARENT_REVIEW_BEFORE_NEW_INDEX_READS",
        "source_repo": "arcinstitute/State-Tahoe-Filtered", "source_revision": "fdf87abece385feea6fa5e9944ab46e173b6af50",
        "summary_revision": "c7963cf334bec0683225d41c9586d900ca6303a2",
        "adaptive_trigger": "Stage1 all1042 eligible indexscreen failednecessary>=3 support; oldcounts retainedunchanged",
        "source_inputs": inputs, "initial_index_deficits_to_three": deficits,
        "selection_rule": "Acrossbothfiles greedilymaximizesumremainingdeficits forstrictpositive namedhints; tiepositive delta/geneplate1maximum (exactfractionofretainedfloat); thenexactlabel,thenfile. Eachnewcondition countsonehinttowardeachcovereddeficit. Excludeoldselectedconditions, protectedlabels/samples, fullQC<50; skipconditions exceedingremaining8.5MBindexbudget; atmost8new/file. No guarantee actualindexsupport.",
        "selection_uses_no_new_raw_or_index_reads": True, "candidate_pool_size": len(pool),
        "selected": selected, "remaining_hint_deficits": remaining,
        "all_hint_deficits_covered": all(n == 0 for values in remaining.values() for n in values.values()),
        "new_conditions_per_file": {file: sum(c["file"] == file for c in selected) for file in deficits},
        "new_full_qc_index_cells": sum(c["full_qc_available"] for c in selected),
        "exact_new_index_payload_bytes": index_bytes, "new_index_payload_cap": INDEX_CAP,
        "new_metadata_and_error_body_cap": metadata_cap, "prior_calibration_body_bytes": prior_bytes,
        "reserved_raw_values_and_HVG_bytes": RAW_RESERVE, "projected_total_with_raw_and_error_reserves": prior_bytes+index_bytes+RAW_RESERVE+metadata_cap,
        "calibration_total_body_cap": TOTAL_CAP, "new_network_calls": 0,
        "paired_read_reselection": "Stillrequiresseparatecombinedindexsupport/rowallocationfreeze; maxpairedcells256retained. Indexsupportnecessitydoesnotcertifyactualnonzerooruniqueness.",
        "exposure": "Alreadyconsultedplate1namedstatistics; newlyscreenedCSRindices furtherexpressionpresenceexposure. All96pooledsamples alreadyexcludedacrosslines; noindependentdecisionvalidation.",
        "source_summary_transform_lineage": "UNKNOWN; positivehintonly. Finalpairingmustverifyexactlog1p(storedX) againsthiddenHVGcolumnwithinfile.",
        "old_axis_gates_unchanged": True, "STATE_checkpoint_axis_certified": False,
        "independent_decision_gain_claimed": False}
    for name, value in (("SELECTION.json", output), ("CANDIDATE_POOL.json", pool)):
        (HERE / name).write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")
    dep_paths = [CALIBRATION / "INDEX_RESULTS.json", CALIBRATION / "QC_ROWS.json", CALIBRATION / "CENSUSES.json",
                 CALIBRATION / "inputs/ENDPOINT.json", CALIBRATION / "inputs/SAMPLES.parquet"]
    dep_paths += [CALIBRATION / "inputs" / f"{file}_{suffix}" for file in deficits for suffix in ("CODES.npz", "POINTERS.npy")]
    dep_paths += [BASE / "informative/NETWORK.jsonl", BASE / "informative/SELECTION.json", BASE / "informative/EXPOSURES.json"]
    frozen = {"schema": "adaptive_supplementary_selection_offline_freeze_v1", "new_indices_read": False,
        "parent_review_required_before_new_index_read": True,
        "sha256": {path.relative_to(BASE).as_posix(): sha(path) for path in dep_paths+[HERE / "choose_conditions.py", HERE / "SELECTION.json", HERE / "CANDIDATE_POOL.json"]}}
    (HERE / "FREEZE.json").write_text(json.dumps(frozen, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("status", "new_conditions_per_file", "new_full_qc_index_cells", "exact_new_index_payload_bytes", "all_hint_deficits_covered", "remaining_hint_deficits", "projected_total_with_raw_and_error_reserves")}))


if __name__ == "__main__":
    main()
