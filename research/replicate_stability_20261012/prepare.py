"""Freeze exact PRISM repeat mappings without reading response values.

Only the secondary response header (nrows=0) and its byte hash are accessed.
The archived NPZ is projected onto identity metadata, never y/available/basal.
All evaluation contexts and prior top10 x next10 cases are retained.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
ARCHIVE = ROOT / "research/context_probe_20261011"
RUN = ARCHIVE / "runs/fixed8"
RAW = ROOT / "data/external/prism_19q4/raw"
SOURCES: list[dict] = []


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source(path: Path, usage: str) -> dict:
    record = {"path": path.relative_to(ROOT).as_posix(),
              "bytes": path.stat().st_size, "sha256": sha256(path), "usage": usage}
    SOURCES.append(record)
    return record


def read_json(path: Path, usage: str):
    source(path, usage)
    return json.loads(path.read_text(encoding="utf-8"))


def metadata(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)
    source(path, "metadata only")["columns_read"] = list(frame.columns)
    return frame


def write_json(name: str, value) -> None:
    (DATA / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n",
                             encoding="utf-8")


def exact_dose(frame: pd.DataFrame, screen: str) -> pd.DataFrame:
    selected = pd.to_numeric(frame.dose, errors="coerce").eq(2.5) & frame.screen_id.eq(screen)
    if "perturbation_type" in frame:
        selected &= frame.perturbation_type.eq("experimental_treatment")
    return frame.loc[selected].copy()


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name: str, condition: bool) -> None:
        if not condition:
            raise ValueError(name)
        checks.append({"name": name, "status": "PASS"})

    protocol = read_json(ARCHIVE / "PROTOCOL.json", "archived arm order and fixed terminal-menu rule")
    receipt = read_json(RUN / "COMMIT_RECEIPT.json", "archived pre-terminal-scoring commitment receipt")
    commits = read_json(RUN / "COMMITS.json", "zero_purchase identities/order only; no probe values used")
    commits = [row for row in commits if row["arm"] == "zero_purchase"]
    check("archived commits match original receipt", sha256(RUN / "COMMITS.json") == receipt["commits_sha256"])
    prediction_source = source(RUN / "predictions.npz", "saved prior predictions only; no model fitting")
    check("archived predictions match original receipt", prediction_source["sha256"] == receipt["predictions_sha256"])
    fit_source = source(RUN / "FIT_FREEZE.json", "byte hash only; archived prior fit was not rerun")
    check("archived fit matches original receipt", fit_source["sha256"] == receipt["fit_sha256"])
    probe_freeze = read_json(RUN / "PROBE_FREEZE.json", "fixed eight probe exclusions only")
    old_manifest = read_json(ARCHIVE / "data/MANIFEST.json", "archived metadata/output integrity hashes only; missingness statistics unused")
    groups = read_json(ARCHIVE / "data/drug_groups.json", "exact representative identities and chemical ambiguity flags")
    archived_contexts = metadata(ARCHIVE / "data/contexts.csv")
    archive_source = source(ARCHIVE / "data/output.npz", "identity metadata arrays only; y/available/basal never materialized")
    check("archived identity NPZ matches original manifest", archive_source["sha256"] == old_manifest["output_npz_sha256"])
    for name in ("contexts.csv", "drug_groups.json"):
        check(f"archived {name} matches original manifest",
              sha256(ARCHIVE / "data" / name) == old_manifest["derived_file_sha256"][name])
    with np.load(ARCHIVE / "data/output.npz", allow_pickle=False) as archive:
        drug_ids = archive["drug_id"].astype(str)
        context_ids = archive["context_id"].astype(str)
        roles = archive["role"].astype(str)
        identity_keys = archive["identity_key"].astype(str)
    with np.load(RUN / "predictions.npz", allow_pickle=False) as archive:
        predictions = archive["predictions"]
    check("all106 evaluation contexts retained", len(commits) == 106 and int((roles == "evaluation").sum()) == 106)
    check("prior prediction axes match archived menu", predictions.shape == (106, len(protocol["arms"]), len(drug_ids)))
    check("all3621 original eligible drug groups retained", len(drug_ids) == 3621 and len(set(drug_ids)) == 3621)
    group_map = {row["drug_id"]: row for row in groups}
    check("drug groups preserve archive ordering", [row["drug_id"] for row in groups if row["eligible"]] == drug_ids.tolist())
    probes = np.array(probe_freeze["probe_indices"], dtype=int)
    check("eight frozen probes preserve exact identities", len(probes) == 8 and drug_ids[probes].tolist() == probe_freeze["probe_ids"])
    terminal = np.setdiff1d(np.arange(len(drug_ids)), probes)
    check("terminal menu preserves3613 unpurchased drugs", len(terminal) == 3613)

    primary = metadata(RAW / "primary-screen-replicate-collapsed-treatment-info.csv")
    primary_cell = metadata(RAW / "primary-screen-cell-line-info.csv")
    secondary = metadata(RAW / "secondary-screen-replicate-treatment-info.csv")
    secondary_cell = metadata(RAW / "secondary-screen-cell-line-info.csv")
    pools = metadata(RAW / "secondary-screen-pooling-info.csv")
    source(RAW / "primary-screen-readme.txt", "publisher preprocessing and endpoint provenance")
    source(RAW / "secondary-screen-readme.txt", "publisher QC/ComBat and MTS010 redo provenance")
    source(ROOT / "research/discrepancy_p0_20261012/literature/raw/prism_paper_methods.body",
           "original publication supporting five-day incubation and independently treated assay plates")
    source(ROOT / "research/discrepancy_p0_20261012/data/SOURCE_AUDIT.json",
           "previous metadata-only audit; no historical response results used")
    outcome_path = RAW / "secondary-screen-logfold-change.csv"
    header = list(pd.read_csv(outcome_path, nrows=0).columns)
    header_set = set(header[1:])
    outcome_source = source(outcome_path, "nrows=0 header read and full-byte hash only; no response values parsed")
    outcome_source["response_rows_parsed"] = 0
    main_rows = exact_dose(secondary, "HTS002")
    redos = exact_dose(secondary, "MTS010")
    check("HTS002 main treatment columns are unique", not main_rows.column_name.duplicated().any())
    check("HTS002 detection plate maps to one compound plate",
          main_rows.groupby("detection_plate").compound_plate.nunique().le(1).all())
    full_main = {key: frame.to_dict("records") for key, frame in main_rows.groupby("broad_id", sort=False)}
    primary_by_column = {key: frame.to_dict("records") for key, frame in primary.groupby("column_name", sort=False)}
    ctx_map = {row["context_id"]: row for row in archived_contexts.to_dict("records")}
    ranks_by_context = []
    intended_indices = set()
    prior_arm = protocol["arms"].index("zero_purchase")
    for evaluation_index, commit in enumerate(commits):
        index = commit["index"]
        check(f"archive evaluation identity {evaluation_index}",
              context_ids[index] == commit["context"] and roles[index] == "evaluation")
        prior = predictions[evaluation_index, prior_arm]
        check(f"finite archived prior {evaluation_index}", bool(np.isfinite(prior).all()))
        top20 = terminal[np.argsort(prior[terminal], kind="stable")[:20]].tolist()
        check(f"original top10 reproduced {evaluation_index}",
              top20[:10] == commit["selected_indices"] and drug_ids[top20[:10]].tolist() == commit["selected_ids"])
        intended_indices.update(top20)
        ranks_by_context.append((commit, top20, prior))

    treatments = []
    treatment_map = {}
    for index in sorted(intended_indices):
        drug_id = drug_ids[index]
        group = group_map[drug_id]
        broad_id = group["representative_broad_id"]
        primary_candidates = primary_by_column.get(group["representative_column"], [])
        matching_primary = [row for row in primary_candidates if row["broad_id"] == broad_id
                            and row["screen_id"] == "HTS" and float(row["dose"]) == 2.5]
        reasons = []
        if len(primary_candidates) != 1 or len(matching_primary) != 1:
            reasons.append("exact_primary_representative_mapping_not_unique")
        rows = full_main.get(broad_id, [])
        if not rows:
            reasons.append("exact_representative_full_broad_id_absent_from_HTS002_2.5")
        treatment = {"index": index, "drug_id": drug_id, "drug_name": group["drug_name"],
                     "representative_broad_id": broad_id,
                     "representative_column": group["representative_column"],
                     "primary_metadata_candidates": primary_candidates,
                     "exact_primary_mapping": matching_primary[0] if len(matching_primary) == 1 else None,
                     "eligible": not reasons, "reason": reasons[0] if reasons else None, "reasons": reasons,
                     "archive_alias_group": {key: group[key] for key in (
                         "names", "broad_prefixes", "source_columns", "n_columns",
                         "multiple_broad_prefixes", "n_distinct_metadata_smiles",
                         "multiple_metadata_structures", "structure_verification", "metadata_smiles")},
                     "chemical_ambiguity_flag": bool(group["multiple_metadata_structures"] or group["multiple_broad_prefixes"]),
                     "main_metadata_rows": [dict(row, column_in_response_header=row["column_name"] in header_set) for row in rows]}
        treatments.append(treatment)
        treatment_map[index] = treatment

    contexts = []
    pair_cases = []
    for evaluation_index, (commit, top20, prior) in enumerate(ranks_by_context):
        context_id = commit["context"]
        archived = ctx_map[context_id]
        row_name = archived["response_row_id"]
        check(f"archive context metadata {evaluation_index}",
              row_name == context_id and archived["role"] == "evaluation"
              and archived["identity_key"] == identity_keys[commit["index"]])
        cell_candidates = secondary_cell[(secondary_cell.row_name == row_name)
                                         | (secondary_cell.depmap_id == context_id)].to_dict("records")
        exact_cells = [row for row in cell_candidates if row["row_name"] == row_name and row["depmap_id"] == context_id]
        primary_candidates = primary_cell[(primary_cell.row_name == row_name)
                                          & (primary_cell.depmap_id == context_id)].to_dict("records")
        pool_candidates = pools[(pools.row_name == row_name) | (pools.depmap_id == context_id)].to_dict("records")
        exact_pools = [row for row in pool_candidates if row["row_name"] == row_name
                       and row["depmap_id"] == context_id and row["screen_id"] == "HTS002"]
        reasons = []
        if len(primary_candidates) != 1 or primary_candidates[0]["passed_str_profiling"] != "TRUE":
            reasons.append("primary_exact_identity_STR_mapping_not_unique_and_passing")
        if len(exact_cells) != 1:
            reasons.append("secondary_exact_row_name_depmap_id_mapping_not_unique")
        elif exact_cells[0]["passed_str_profiling"] != "TRUE":
            reasons.append("secondary_cell_failed_STR")
        if not exact_pools:
            reasons.append("no_exact_HTS002_pool_mapping")
        elif len(exact_pools) != 1:
            reasons.append("ambiguous_exact_HTS002_pool_mapping")
        elif exact_pools[0]["passed_str_profiling"] != "TRUE":
            reasons.append("HTS002_pool_failed_STR")
        context = {"context": context_id, "index": commit["index"], "evaluation_index": evaluation_index,
                   "secondary_row_name": row_name, "lineage": archived["lineage"],
                   "identity_key": archived["identity_key"], "archive_context": archived,
                   "primary_cell_metadata": primary_candidates,
                   "secondary_cell_candidates": cell_candidates,
                   "secondary_cell_metadata": exact_cells[0] if len(exact_cells) == 1 else None,
                   "all_screen_pool_candidates": pool_candidates,
                   "HTS002_pool_metadata": exact_pools[0] if len(exact_pools) == 1 else None,
                   "eligible": not reasons, "reason": reasons[0] if reasons else None, "reasons": reasons,
                   "response_row_presence": None, "finite_outcome_availability": None,
                   "prior_top10_indices": top20[:10], "prior_next10_indices": top20[10:],
                   "prior_top10_ids": drug_ids[top20[:10]].tolist(),
                   "prior_next10_ids": drug_ids[top20[10:]].tolist(),
                   "ranked_drugs": [{"rank": rank, "index": index, "drug_id": drug_ids[index],
                                     "representative_broad_id": treatment_map[index]["representative_broad_id"],
                                     "representative_column": treatment_map[index]["representative_column"],
                                     "prediction": float(prior[index]),
                                     "exact_treatment_metadata_eligible": treatment_map[index]["eligible"],
                                     "chemical_ambiguity_flag": treatment_map[index]["chemical_ambiguity_flag"]}
                                    for rank, index in enumerate(top20, start=1)]}
        contexts.append(context)
        for left_rank, left_index in enumerate(top20[:10], start=1):
            for right_rank, right_index in enumerate(top20[10:], start=11):
                left, right = treatment_map[left_index], treatment_map[right_index]
                pair_reasons = list(reasons)
                pair_reasons.extend(f"left:{reason}" for reason in left["reasons"])
                pair_reasons.extend(f"right:{reason}" for reason in right["reasons"])
                left_rows, right_rows = left["main_metadata_rows"], right["main_metadata_rows"]
                common_plates = sorted({row["compound_plate"] for row in left_rows}
                                       & {row["compound_plate"] for row in right_rows})
                if not common_plates:
                    pair_reasons.append("no_shared_compound_plate_for_exact_representatives")
                blocks = []
                for compound_plate in common_plates:
                    aa = [row for row in left_rows if row["compound_plate"] == compound_plate]
                    bb = [row for row in right_rows if row["compound_plate"] == compound_plate]
                    left_plates = sorted({row["detection_plate"] for row in aa})
                    right_plates = sorted({row["detection_plate"] for row in bb})
                    expected = sorted(set(left_plates) & set(right_plates))
                    block_reasons = []
                    if len(expected) < 2:
                        block_reasons.append("fewer_than_two_common_actual_detection_plates")
                    if len({row["well"] for row in aa}) != 1 or len({row["well"] for row in bb}) != 1:
                        block_reasons.append("drug_well_not_consistent_across_HTS002_repeats")
                    repeats = []
                    for detection_plate in expected:
                        ar = [row for row in aa if row["detection_plate"] == detection_plate]
                        br = [row for row in bb if row["detection_plate"] == detection_plate]
                        if len(ar) != 1 or len(br) != 1:
                            block_reasons.append("ambiguous_drug_detection_plate_mapping")
                        a, b = ar[0] if len(ar) == 1 else None, br[0] if len(br) == 1 else None
                        repeats.append({"detection_plate": detection_plate,
                                        "left_column": a["column_name"] if a else None,
                                        "right_column": b["column_name"] if b else None,
                                        "left_well": a["well"] if a else None,
                                        "right_well": b["well"] if b else None,
                                        "left_column_in_response_header": a["column_in_response_header"] if a else False,
                                        "right_column_in_response_header": b["column_in_response_header"] if b else False})
                    accessible = sum(row["left_column_in_response_header"] and row["right_column_in_response_header"] for row in repeats)
                    if accessible < 2:
                        block_reasons.append("fewer_than_two_header_accessible_common_repeats")
                    block_reasons = list(dict.fromkeys(block_reasons))
                    blocks.append({"compound_plate": compound_plate, "expected_detection_plates": expected,
                                   "left_detection_plates": left_plates, "right_detection_plates": right_plates,
                                   "header_accessible_common_repeats": accessible,
                                   "metadata_eligible": not block_reasons,
                                   "eligible": not block_reasons and not pair_reasons,
                                   "reason": (pair_reasons + block_reasons)[0] if pair_reasons + block_reasons else None,
                                   "reasons": pair_reasons + block_reasons, "repeat_columns": repeats})
                if blocks and not any(block["metadata_eligible"] for block in blocks):
                    pair_reasons.append("no_qualified_shared_repeat_block")
                if sum(block["metadata_eligible"] for block in blocks) > 1:
                    pair_reasons.append("multiple_qualified_compound_plate_blocks")
                eligible = not pair_reasons and len(blocks) == 1 and blocks[0]["metadata_eligible"]
                pair_cases.append({"case_id": f"{context_id}|{left_rank:02d}|{right_rank:02d}",
                                   "context": context_id, "index": commit["index"], "evaluation_index": evaluation_index,
                                   "secondary_row_name": row_name, "left_index": left_index, "right_index": right_index,
                                   "left_rank": left_rank, "right_rank": right_rank,
                                   "left_drug_id": left["drug_id"], "right_drug_id": right["drug_id"],
                                   "left_broad_id": left["representative_broad_id"], "right_broad_id": right["representative_broad_id"],
                                   "left_prediction": float(prior[left_index]), "right_prediction": float(prior[right_index]),
                                   "predicted_difference": float(prior[left_index] - prior[right_index]),
                                   "eligible": bool(eligible), "reason": pair_reasons[0] if pair_reasons else None,
                                   "reasons": pair_reasons, "blocks": blocks,
                                   "compound_plate": blocks[0]["compound_plate"] if len(blocks) == 1 else None,
                                   "expected_detection_plates": blocks[0]["expected_detection_plates"] if len(blocks) == 1 else [],
                                   "repeat_columns": blocks[0]["repeat_columns"] if eligible else [],
                                   "finite_outcome_availability": None})

    check("all10600 intended cases retained in fixed order", len(pair_cases) == 10600 and len({row["case_id"] for row in pair_cases}) == 10600)
    check("every context preserves100 unreplaced cases", set(Counter(row["context"] for row in pair_cases).values()) == {100})
    check("no frozen probes enter either rank band", all(not (set(row["prior_top10_indices"] + row["prior_next10_indices"]) & set(probes.tolist())) for row in contexts))
    absent_columns = main_rows.loc[~main_rows.column_name.isin(header_set)].to_dict("records")
    intended_broads = {row["representative_broad_id"] for row in treatments}
    redo_rows = redos.to_dict("records")
    write_json("CONTEXTS.json", contexts)
    write_json("PAIR_CASES.json", pair_cases)
    write_json("TREATMENTS.json", treatments)
    write_json("EXCLUDED_REDOS.json", {"screen_id": "MTS010", "dose_um": 2.5,
               "reason": "Technical redos excluded from the HTS002-only main study; no substitution permitted",
               "metadata_rows": redo_rows,
               "intended_full_broad_metadata_rows": [row for row in redo_rows if row["broad_id"] in intended_broads]})
    write_json("SOURCES.json", SOURCES)
    write_json("CHECKS.json", checks)
    all_blocks = [block for case in pair_cases for block in case["blocks"]]
    manifest = {
        "schema": "maestro.replicate_stability.metadata.v1",
        "phase": "METADATA_ONLY_CANDIDATE_FREEZE; response values not admitted by this script",
        "scope": "Retrospective exposed published ComBat-corrected assay-repeat ranking stability; no model fit, Agent comparison or mechanism attribution",
        "endpoint": {"screen_id": "HTS002", "dose_um": 2.5,
                     "dose_filter": "Strict numeric equality, no tolerance",
                     "perturbation_type": "experimental_treatment",
                     "response": "Published replicate-level log2-fold-change relative to DMSO; lower is preferred",
                     "nominal_published_time_hours": 120,
                     "per_treatment_time_verified": False},
        "selection": {"archive": ARCHIVE.relative_to(ROOT).as_posix(), "arm": "zero_purchase",
                      "all_archived_evaluation_contexts_retained": True,
                      "rank_bands": {"left": [1, 10], "right": [11, 20]},
                      "order": "Archive evaluation commit order, then left rank, then right rank; stable ascending prior prediction within frozen terminal menu",
                      "next10_status": "Derived now from the archived pre-terminal-scoring full prediction array; ranks11-20 were not historically registered top20 commitments",
                      "probe_exclusions": {"indices": probes.tolist(), "ids": probe_freeze["probe_ids"]},
                      "alias_rule": "Retain original conservative metadata alias groups and exact representative column/full Broad drug-batch ID; no new equivalence, name, prefix, salt or fuzzy substitution",
                      "context_filter": "Exact archived row_name=depmap_id=context, passing primary/secondary STR and unique exact HTS002 pool mapping; excluded contexts retained",
                      "drug_or_context_replacement": False},
        "pairing": {"hierarchy": ["context", "compound_plate", "drug_pair", "actual_shared_detection_plate"],
                    "expected_repeats": "All identical actual detection-plate IDs shared by both exact drugs on the same compound plate in FULL treatment metadata; lexically ordered for storage only",
                    "eligibility": "Unique condition/plate mappings, each drug's well consistent across repeats, at least2 common recorded and header-accessible repeats; eligible is metadata-only",
                    "header_absence": "Retain expected detection plate and exact column; runner must assign absent-header outcome NA without replacing it",
                    "excluded_case_access": "Ineligible cases expose no top-level repeat_columns; full candidate mappings and exclusions remain in blocks without admitting their outcomes",
                    "finite_complete_rule": "Requires finite contrasts for ALL expected metadata repeats; partial finite coverage must be reported separately",
                    "independence": "Pairs reuse drugs/plates; contexts share pools; all corrected repeats share condition-wise ComBat. Counts are descriptive units, not independent biological n"},
        "outcome_access": {"response_values_read_by_preparation": False,
                           "secondary_response_rows_parsed": 0,
                           "archive_npz_arrays_materialized": ["drug_id", "context_id", "role", "identity_key"],
                           "archive_outcome_arrays_materialized": [],
                           "response_row_presence": None, "finite_outcome_availability": None,
                           "per_repeat_publisher_QC_status": None,
                           "availability_warning": "Metadata/header presence is not finite outcome availability or a raw-QC certificate"},
        "publisher_assumptions": {"assay_repeats": "Original methods support up to3 independently treated plates,1-3 after QC",
                                 "separate_culture_start_ids_verified": False,
                                 "processed_QC": "Published outlier-pool and control-separation filtering; not independently reconstructed",
                                 "ComBat": "Joint condition-specific correction across cell-line pool/replicate batches; released repeats do not provide an independent raw-preprocessing holdout",
                                 "MTS010": "Technical redos logged separately and excluded, despite publisher downstream-use recommendation"},
        "response_header": {"index_column": header[0], "columns_including_index": len(header),
                            "response_columns": len(header_set),
                            "ordered_names_sha256": hashlib.sha256(json.dumps(header, separators=(",", ":")).encode()).hexdigest(),
                            "main_metadata_columns_absent_from_header": absent_columns},
        "counts": {"archived_contexts": len(contexts), "context_metadata_qualified": sum(row["eligible"] for row in contexts),
                   "intended_top10_entries": len(contexts) * 10, "intended_top20_entries": len(contexts) * 20,
                   "intended_unique_drug_groups": len(treatments),
                   "exact_representative_treatment_mappings": sum(treatment_map[index]["eligible"] for row in contexts for index in row["prior_top10_indices"] + row["prior_next10_indices"]),
                   "intended_chemical_ambiguity_entries": sum(treatment_map[index]["chemical_ambiguity_flag"] for row in contexts for index in row["prior_top10_indices"] + row["prior_next10_indices"]),
                   "intended_cases": len(pair_cases), "main_exactdose_metadata_rows": len(main_rows),
                   "main_exact_full_broad_ids": int(main_rows.broad_id.nunique()),
                   "main_compound_plates": int(main_rows.compound_plate.nunique()),
                   "main_detection_plates": int(main_rows.detection_plate.nunique()),
                   "main_metadata_columns_in_response_header": len(main_rows) - len(absent_columns),
                   "main_metadata_columns_absent_from_response_header": len(absent_columns),
                   "pair_plate_blocks_before_context_qualification": sum(block["metadata_eligible"] for block in all_blocks),
                   "metadata_eligible_cases": sum(row["eligible"] for row in pair_cases),
                   "contexts_with_metadata_eligible_case": len({row["context"] for row in pair_cases if row["eligible"]}),
                   "distinct_metadata_eligible_drug_pairs": len({(row["left_index"], row["right_index"]) for row in pair_cases if row["eligible"]}),
                   "metadata_eligible_compound_plates": len({row["compound_plate"] for row in pair_cases if row["eligible"]}),
                   "metadata_eligible_detection_plates": len({repeat["detection_plate"] for row in pair_cases if row["eligible"] for repeat in row["repeat_columns"]}),
                   "pair_plate_blocks_after_context_qualification": sum(block["eligible"] for block in all_blocks),
                   "expected_repeat_count_distribution": dict(sorted(Counter(str(len(block["expected_detection_plates"])) for block in all_blocks).items())),
                   "excluded_exactdose_MTS010_metadata_rows": len(redos),
                   "excluded_intended_full_broad_MTS010_metadata_rows": int(redos.broad_id.isin(intended_broads).sum()),
                   "context_exclusion_reasons": dict(Counter(reason for row in contexts for reason in row["reasons"])),
                   "case_exclusion_reasons": dict(Counter(reason for row in pair_cases for reason in row["reasons"]))},
        "prepare_sha256": sha256(Path(__file__)),
        "artifact_sha256": {name: sha256(DATA / name) for name in (
            "CONTEXTS.json", "PAIR_CASES.json", "TREATMENTS.json", "EXCLUDED_REDOS.json", "SOURCES.json", "CHECKS.json")},
        "source_manifest": "SOURCES.json",
        "response_source_sha256": outcome_source["sha256"],
    }
    write_json("MANIFEST.json", manifest)
    print(json.dumps({"manifest_sha256": sha256(DATA / "MANIFEST.json"), "counts": manifest["counts"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
