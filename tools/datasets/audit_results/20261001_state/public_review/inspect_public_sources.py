"""Metadata-only qualification; no model calls, fitting, or utility estimates."""
import collections
import datetime
import gzip
import hashlib
import io
import json
import pathlib
import platform
import re
import sys
import xml.etree.ElementTree as ET

import pandas as pd
import scipy.io

BASE = pathlib.Path(__file__).resolve().parent


def write_new(name, value):
    path = BASE / name
    if path.exists():
        raise RuntimeError("Refuse to overwrite " + str(path))
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True), encoding="utf-8")


receipts = []
for name in ("receipts_initial.json", "receipts_extended.json"):
    receipts.extend(json.loads((BASE / name).read_text(encoding="utf-8")))
by_id = {row["id"]: row for row in receipts}
for row in receipts:
    raw = (BASE / (row["id"] + ".raw")).read_bytes()
    if hashlib.sha256(raw).hexdigest() != row["response_sha256"]:
        raise RuntimeError("Original receipt changed: " + row["id"])
    row["content_type"] = next(
        (v for k, v in row["response_headers"].items() if k.lower() == "content-type"), None
    )
    if row["id"].endswith(("soft", "features", "clones", "metadata")) and raw[:2] == b"\x1f\x8b":
        row["expected_format"] = "gzip containing SOFT/TSV/MatrixMarket"
        row["parse_status"] = "gzip_decompression_passed"
        gzip.decompress(raw)
    elif row["id"] in ("schaff_article_xml",):
        row["expected_format"] = "article XML"
        ET.fromstring(raw)
        row["parse_status"] = "xml_parse_passed"
    elif row["id"] in ("larry_readme",):
        row["expected_format"] = "author Markdown"
        row["parse_status"] = "utf8_decode_passed"
        raw.decode("utf-8")
    elif row["id"] in ("thunor_hts001",):
        row["expected_format"] = "comma-delimited CSV"
        row["parse_status"] = "csv_parse_passed"
    elif row["id"] in ("schaff_geo_browser", "schaff_pipeline_landing"):
        row["expected_format"] = "official HTML record"
        row["parse_status"] = "landing_only_not_file_or_timing_verification"
    else:
        row["expected_format"] = "JSON registry metadata"
        json.loads(raw)
        row["parse_status"] = "json_parse_passed"
    row["failure_rule"] = "Non-200 status, transport error, parse failure, or absent expected identity is a source failure; 200 alone is insufficient."


def evidence(source_id, field, status, detail):
    return {
        "source_id": source_id, "source_sha256": by_id[source_id]["response_sha256"],
        "original_field": field, "status": status, "detail": detail,
    }


soft = gzip.decompress((BASE / "schaff_geo_soft.raw").read_bytes()).decode()
samples = []
for block in soft.split("^SAMPLE = ")[1:]:
    lines = block.splitlines()
    samples.append({
        "sample_id": lines[0],
        "title": next(line.split(" = ", 1)[1] for line in lines if line.startswith("!Sample_title = ")),
        "treatment": next(line.split("treatment: ", 1)[1] for line in lines if "!Sample_characteristics_ch1 = treatment: " in line),
        "raw_execution_status": "record_level_only",
        "supplementary_urls": [line.split(" = ", 1)[1].replace("ftp://", "https://", 1) for line in lines if line.startswith("!Sample_supplementary_file_")],
    })
features = {}
for name in ("schaff_naive1_features", "schaff_dabrafenib_features"):
    text = gzip.decompress((BASE / (name + ".raw")).read_bytes()).decode()
    features[name] = {
        "decompressed_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "rows": len(text.splitlines()),
        "feature_types": dict(collections.Counter(line.split("\t")[-1] for line in text.splitlines())),
        "scope": "Shared feature vocabulary; expression counts and cell-to-clone measurements were not downloaded or verified.",
    }

larry = pd.read_csv(io.BytesIO(gzip.decompress((BASE / "larry_cytokine_metadata.raw").read_bytes())), sep="\t")
clones = scipy.io.mmread(io.BytesIO(gzip.decompress((BASE / "larry_cytokine_clones.raw").read_bytes()))).tocsr()
if clones.shape[1] != len(larry):
    raise RuntimeError("Cannot certify clone/cell axis for this exact metadata file")
early = set(clones[:, larry["Time point"].to_numpy() == 2].nonzero()[0])
late = set(clones[:, larry["Time point"].to_numpy() > 2].nonzero()[0])
larry_actions = []
for condition in sorted(larry["Cytokine condition"].unique()):
    subset = larry[(larry["Cytokine condition"] == condition) & (larry["Time point"] > 2)]
    larry_actions.append({
        "action": condition, "raw_execution_status": "deposited_cell_rows_only",
        "source_id": "larry_cytokine_metadata", "source_sha256": by_id["larry_cytokine_metadata"]["response_sha256"],
        "original_field": "Cytokine condition", "response_cell_rows": len(subset),
        "rows_by_day": {str(int(day)): int(count) for day, count in subset["Time point"].value_counts().items()},
        "attempted_aliquot_denominator": None, "well_or_batch_execution_id": None,
    })

thunor = pd.read_csv(BASE / "thunor_hts001.raw")
thunor_actions = []
for (drug, concentration), subset in thunor.groupby(["drug1", "drug1.conc"], dropna=False):
    thunor_actions.append({
        "drug": drug, "dose_M": float(concentration),
        "raw_execution_status": "measured_count_rows_after_treatment",
        "source_id": "thunor_hts001", "source_sha256": by_id["thunor_hts001"]["response_sha256"],
        "original_fields": ["drug1", "drug1.conc", "upid", "well", "time", "cell.count"],
        "measurement_rows": len(subset),
        "unique_plate_wells": int(subset[["upid", "well"]].drop_duplicates().shape[0]),
        "first_exposure_time_h": float(subset["time"].min()),
    })

questions = [
    {
        "id": "schaff_gse279162", "experimental_question": "Can pre-treatment sister-clone transcriptomes support choosing among six resistance treatments for the same founder pool?",
        "classification": "replay_only", "state_gain_gate_passed": False,
        "primary_urls": ["https://pmc.ncbi.nlm.nih.gov/articles/PMC13261651/", "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE279162"],
        "versions": {"GEO": "GSE279162; public and last updated 2024-10-14", "code": "Zenodo 13935305 first_release", "gDNA": "Figshare 25024463 version 1", "pipeline": "ScienceDB 10.57760/sciencedb.14653 V1"},
        "licenses": {"article": "CC BY 4.0", "GEO_data": "unverified blanket data license", "gDNA_processed_data": "CC BY 4.0", "pipeline_output_data": "CC BY 4.0", "archived_code": "CC BY 4.0"},
        "field_audit": [
            evidence("schaff_geo_soft", "!Series_overall_design", "collection_order_documented_available_at_missing", "Untreated.naive collection precedes splitting; no timestamp proves processed transcriptome available before treatment decision."),
            evidence("schaff_article_xml", "STAR Methods: scRNA-seq experiment", "sister_clone_relationship_documented", "One founder pool, untreated scRNA aliquot and six later treatments; destroyed sequenced cells are not the same cells receiving drug."),
            evidence("schaff_geo_soft", "!Sample_title; !Sample_characteristics_ch1", "record_level_only", "3 untreated sequencing samples and 6 treated samples; no raw action ledger, nonexecution reason, donor/plate/batch identifiers or aliquot denominators."),
            evidence("schaff_naive1_features", "feature type Custom", "vocabulary_only", "Clone feature vocabulary present; requires expression-count matrices and validated cell-to-clone assignments, not feature-name join alone."),
            evidence("schaff_article_xml", "Methods and Figure 2 versus Figure 3", "independent_physical_batches_not_established", "Two treatment replicates in separate gDNA experiment cannot be transplanted as replicate count for the scRNA experiment; initial scRNA lanes share a founder pool."),
            evidence("schaff_geo_soft", "!Sample_data_processing", "filtered_deposit_only", "Filtered feature-barcode matrices omit the attempted-experiment denominator; QC and nondetection cannot be treated as failure or clone extinction."),
            evidence("schaff_article_xml", "Methods treatment schedules; GEO overall_design", "schedule_discrepancy", "GEO describes doxorubicin 2 weeks plus 2-week holiday; article Methods gives 2.5 weeks plus 1.5-week holiday. Resolve source version before building endpoints."),
        ],
        "actions": [sample for sample in samples if sample["treatment"] != "Untreated"], "samples": samples, "feature_metadata": features,
        "exposure_status": "Unknown for active STATE/checkpoint training; source was public in October 2024, so 2026 publication date does not establish nonexposure. No backend run.",
        "state_blind_control": "Conceptually mask pre-state values on the same matched clone/action records, only after linkage and availability gates pass.",
        "acquisition_plan": ["Use saved GEO SOFT to acquire exact feature/barcode/count files into a new versioned directory with byte budget and SHA256.", "Verify cell-to-clone mapping using Custom counts or ScienceDB pipeline output, QC thresholds, barcode error-merging and collision rates.", "Acquire culture-aliquot/plate/run manifest, all attempts including failures, exact drug schedules and state processing available_at before scoring.", "Independent founder-pool repeats plus predecision assay turnaround are required for an implementable policy claim."],
    },
    {
        "id": "larry_cytokine_2020", "experimental_question": "Can day-2 sister-clone RNA states choose a subsequent cytokine condition and change a preregistered day-4/day-6 differentiation endpoint?",
        "classification": "replay_only", "state_gain_gate_passed": False,
        "primary_urls": ["https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE140802", "https://github.com/AllonKleinLab/paper-data/blob/b8658b78c1c288019dfa60b6f50aace270528a29/Lineage_tracing_on_transcriptional_landscapes_links_state_to_fate_during_differentiation/README.md"],
        "versions": {"GEO": "GSE140802", "author_repository_commit": "b8658b78c1c288019dfa60b6f50aace270528a29"},
        "licenses": {"article": "not reverified in this review", "author_repository": "GitHub license field null", "author_data_files": "unverified explicit data license", "GEO": "public deposit; blanket data license unverified"},
        "field_audit": [
            evidence("larry_readme", "Experiment 3 description", "collection_order_documented_available_at_missing", "Day2 profiling before replating; no transcriptome processing/return timestamp before cytokine assignment."),
            evidence("larry_cytokine_metadata", "Library; Cell barcode; Time point; Cytokine condition", "actual_deposited_cells", "65075 rows. Library is a sequencing label; donor/culture-plate/attempt/batch relationships are absent."),
            evidence("larry_cytokine_clones", "MatrixMarket dimensions", "axis_discrepancy_resolved_for_this_snapshot", "Actual clone matrix is clones x cells (5257 x 65075), whereas README says rows are cells. Match axis to exact 65075 metadata rows, do not assume README orientation."),
            evidence("larry_cytokine_metadata", "Time point x Cytokine condition", "missing_endpoint_action", "SCF has day4 rows but no day6 rows. Absence of deposited cells does not prove that a day6 culture failed or was not attempted."),
            evidence("larry_geo_soft", "!Sample_treatment_protocol_ch1", "record_level_protocol_only", "96-well culture documented, but no donor-specific well map, plate ID or independent experimental pool map in retrieved files."),
            evidence("larry_cytokine_metadata", "Cell type annotation", "derived_endpoint_only", "Author cell-type annotation can be a registered proxy after raw-count validation, not biological correctness ground truth."),
        ],
        "actions": larry_actions,
        "linkage_counts": {"early_clones": len(early), "late_clones": len(late), "shared_early_late_clones": len(early & late), "sparse_memberships": int(clones.nnz), "scope": "Metadata/clone membership counts, not fully observed counterfactual outcomes or independent replicates."},
        "exposure_status": "No checkpoint-specific training manifest audited for this source. Mouse cytokine context is outside the currently registered human compound tasks; no backend support or invocation assumed.",
        "state_blind_control": "Mask matched day2 RNA values while preserving clone/action/menu IDs after availability and raw-expression verification.",
        "acquisition_plan": ["Resolve explicit data license with source record or authors; no third-party license automatically propagates to raw author files.", "Acquire gene names and raw/normalized counts while validating cell axis against exact metadata/clone file hashes.", "Request donor/founder-pool, culture-aliquot and physical plate maps plus day6 SCF nonexecution/missingness explanation.", "Use completed predecision assays and independently repeated pools; reserve physical batches for testing before outcome examination."],
    },
    {
        "id": "thunor_hts001_2026_deposit", "experimental_question": "Can genuine pre-dose cell state improve choosing a drug/dose for the later count endpoint in a matched well?",
        "classification": "replay_only", "state_gain_gate_passed": False,
        "primary_urls": ["https://zenodo.org/records/18292967", "https://docs.thunor.net/create-a-dataset"],
        "versions": {"deposit": "Zenodo 18292967 version 0.1, 2026-01-18", "reviewed_file": "HTS001.csv"},
        "licenses": {"data": "CC BY 4.0", "software": "not used or audited in this review"},
        "field_audit": [
            evidence("thunor_hts001", "time", "no_pretreatment_observation", "48664 rows; all time values >0. Global minimum 0.5 h; first readings per well 0.5 to 6.1 h after exposure. Zero pre-dose/time-zero rows."),
            evidence("thunor_hts001", "upid; well; drug1; drug1.conc; drug1.units; cell.line", "physical_well_mapping_observed", "7 plate IDs, 7 cell lines, 15 drug-name tokens including control; one deposited plate per cell-line label, not independent same-context batches."),
            evidence("thunor_hts001", "header", "missing_declared_experiment_field", "Actual 8-column CSV does not contain expt.id, despite the record's generic schema description; no dosing event or available_at timestamps."),
            evidence("thunor_hts001", "drug1=control", "control_well_rows_observed", "Controls can be grouped by exact plate/well, but temporal availability and shared-control design require protocol validation."),
            evidence("thunor_hts001", "cell.count; time", "counts_only", "Fluorescent nuclei-count proxy after treatment; no baseline expression/morphology or STATE-compatible state supplied."),
            evidence("thunor_zenodo", "files HTS003.csv and HTS031.csv", "declared_duplicate_bytes_unverified", "Both file records have identical declared size and MD5 despite different stated cell-line experiments; do not assume HTS031 identity without downloading and reconciling."),
        ],
        "actions": thunor_actions,
        "observed_counts": {"rows": len(thunor), "plates": int(thunor["upid"].nunique()), "cell_lines": int(thunor["cell.line"].nunique()), "drug_name_tokens_including_control": int(thunor["drug1"].nunique()), "time_zero_rows": int((thunor["time"] == 0).sum()), "global_min_exposure_h": float(thunor["time"].min()), "first_well_min_h": float(thunor.groupby(["upid", "well"])["time"].min().min()), "first_well_max_h": float(thunor.groupby(["upid", "well"])["time"].min().max()), "matched_declared_md5": hashlib.md5((BASE / "thunor_hts001.raw").read_bytes()).hexdigest() == "a5959a38166685707e840369ce34d74d"},
        "exposure_status": "Original underlying studies predate 2026 deposit; a new upload date does not establish untouched checkpoint evaluation. No backend run.",
        "state_blind_control": "Unavailable for genuine pre-dose state because the file contains none; the first exposed count cannot be relabeled as baseline.",
        "acquisition_plan": ["Retrieve original pre-dose image/count files and dose-event logs with plate/well/time map; retain raw acquisition and processing available_at.", "Resolve HTS003/HTS031 duplicate deposited-file metadata before using those releases.", "Collect additional independent same-context physical batches with shared controls, complete failure denominator and measured costs."],
    },
]
for question in questions:
    question["required_field_gaps"] = {
        "state_available_at": "No raw timestamp establishes state processing completed before action assignment.",
        "decision_time": "No actual planner/experiment-assignment event timestamp in retrieved raw records.",
        "attempts_and_unexecuted_reasons": "Deposited samples/cells/readings are not a complete attempted-experiment ledger.",
        "culture_aliquot_and_batch": "Independent founder/culture-batch IDs and shared-sample relationships need a manifest; sequencing Library/plate labels alone are insufficient.",
        "QC_and_failures": "No joined all-attempt QC and assay-failure table was retrieved.",
        "actual_cost_and_turnaround": "No measured money/time/processing-cost ledger tied to action instances.",
        "checkpoint_exposure": "No checkpoint-specific training/calibration/test condition manifest established for this candidate.",
        "state_blind_comparator": "Only a prospective masking plan is available; no gated state-gain experiment was executed.",
    }
write_new("source_qualification.json", receipts)
write_new("candidate_questions.json", {
    "schema_version": "state-identifiability-public-review-1", "retrieval_date": "2026-10-01",
    "review_completed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "qualified_state_gain_tasks": 0, "questions": questions,
    "experiments_run": [], "models_trained": 0,
    "not_run": ["STATE", "WorldV2", "ReferenceWorld", "state_gain", "policy_comparison", "terminal_utility", "API_calls"],
    "review_scope": "Raw metadata, clone membership, and one small longitudinal count file; no expression-count matrices downloaded.",
})
write_new("review_environment.json", {
    "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
    "pandas": pd.__version__, "scipy": __import__("scipy").__version__,
    "inspection_code_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    "replay_code_sha256": hashlib.sha256((BASE / "replay_sources.py").read_bytes()).hexdigest(),
    "inspection_command": "D:\\anaconda\\envs\\maestro\\python.exe outputs/state_identifiability_20261001/public_review/inspect_public_sources.py",
    "replay_command": "D:\\anaconda\\envs\\maestro\\python.exe outputs/state_identifiability_20261001/public_review/replay_sources.py NEW_EMPTY_OUTPUT_DIRECTORY",
    "command_snapshot_timing": "Replay helper saved after discovery acquisitions. Inspection code saved before execution. Original response bytes and receipt times/hashes are preserved.",
    "working_directory": "D:\\MAESTRO",
})
print(json.dumps({"questions": len(questions), "qualified_state_gain_tasks": 0, "http_receipts_verified": len(receipts), "larry_shared_early_late_clones": len(early & late), "thunor_pretreatment_rows": 0}))
