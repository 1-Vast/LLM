"""Independent metadata and arithmetic review; no producer helper imports."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import fmean

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]
OLD = ROOT / "research/context_probe_20261011"
RAW = ROOT / "data/external/prism_19q4/raw"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def check(actual, expected):
    if isinstance(expected, dict):
        for key, value in expected.items():
            check(actual[key], value)
    elif isinstance(expected, list):
        assert len(actual) == len(expected), (len(actual), len(expected))
        for left, right in zip(actual, expected):
            check(left, right)
    elif isinstance(expected, float):
        assert actual is not None and math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-12), (actual, expected)
    else:
        assert actual == expected, (actual, expected)


def verify_metadata():
    manifest = read(STUDY / "data/MANIFEST.json")
    for filename, expected in manifest["artifact_sha256"].items():
        assert sha(STUDY / "data" / filename) == expected, filename
    assert sha(STUDY / "prepare.py") == manifest["prepare_sha256"]
    sources = read(STUDY / "data/SOURCES.json")
    for source in sources:
        path = ROOT / source["path"]
        assert sha(path) == source["sha256"] and path.stat().st_size == source["bytes"], path
    assert sha(RAW / "secondary-screen-logfold-change.csv") == manifest["response_source_sha256"]
    checks = read(STUDY / "data/CHECKS.json")
    assert all(item["status"] == "PASS" for item in checks)
    literature = read(STUDY / "literature/SOURCE_READ_RECEIPTS.json")
    for source in literature["reused_sources"]:
        path = Path(source["path"])
        assert sha(path) == source["sha256"] and path.stat().st_size == source["bytes"]
    assert literature["new_network_requests"] == literature["response_values_read"] == 0
    assert literature["attachment_comparison"]["byte_identical"]

    def metadata(name):
        return pd.read_csv(RAW / name, dtype=str, keep_default_na=False).to_dict("records")

    primary_cells = metadata("primary-screen-cell-line-info.csv")
    secondary_cells = metadata("secondary-screen-cell-line-info.csv")
    pools = metadata("secondary-screen-pooling-info.csv")
    primary_treatments = metadata("primary-screen-replicate-collapsed-treatment-info.csv")
    secondary_treatments = metadata("secondary-screen-replicate-treatment-info.csv")
    main = [r for r in secondary_treatments if r["dose"] == "2.5" and r["screen_id"] == "HTS002" and r["perturbation_type"] == "experimental_treatment"]
    # Only this header is read before the frozen runner admits response values.
    with (RAW / "secondary-screen-logfold-change.csv").open(newline="", encoding="utf-8") as stream:
        header = next(csv.reader(stream))
    header[0] = header[0] or "Unnamed: 0"
    assert len(header) == len(set(header)) == 39926
    header_set = set(header[1:])
    check(manifest["response_header"], {"index_column": header[0], "columns_including_index": len(header),
        "response_columns": len(header_set), "ordered_names_sha256": hashlib.sha256(json.dumps(header, separators=(",", ":")).encode()).hexdigest(),
        "main_metadata_columns_absent_from_header": [r for r in main if r["column_name"] not in header_set]})
    assert len(main) == 3840 and len({r["column_name"] for r in main}) == 3840
    compound = defaultdict(lambda: defaultdict(list))
    for row in main:
        compound[row["broad_id"]][row["compound_plate"]].append(row)
    groups = read(OLD / "data/drug_groups.json")
    group_map = {g["drug_id"]: g for g in groups if g["eligible"]}
    with np.load(OLD / "data/output.npz", allow_pickle=False) as archive:
        ids, roles, drugs, identities = archive["context_id"], archive["role"], archive["drug_id"], archive["identity_key"]
    with np.load(OLD / "runs/fixed8/predictions.npz", allow_pickle=False) as archive:
        predictions = archive["predictions"]
    evaluation = [i for i, role in enumerate(roles) if role == "evaluation"]
    probes = read(OLD / "runs/fixed8/PROBE_FREEZE.json")["probe_indices"]
    menu = sorted(set(range(len(drugs))) - set(probes))
    assert len(evaluation) == 106 and len(menu) == 3613 and predictions.shape == (106, 6, 3621)
    old_commits = [c for c in read(OLD / "runs/fixed8/COMMITS.json") if c["arm"] == "zero_purchase"]
    contexts = read(STUDY / "data/CONTEXTS.json")
    cases = read(STUDY / "data/PAIR_CASES.json")
    treatments = read(STUDY / "data/TREATMENTS.json")
    assert len(contexts) == 106 and len(cases) == len({c["case_id"] for c in cases}) == 10600
    treatment_map = {t["index"]: t for t in treatments}
    assert len(treatments) == len(treatment_map)
    orders, qualified, context_reasons = {}, {}, {}
    for position, index in enumerate(evaluation):
        context = str(ids[index])
        order = sorted(menu, key=lambda d: (float(predictions[position, 0, d]), d))[:20]
        orders[context] = order
        check(old_commits[position], {"context": context, "index": index, "selected_indices": order[:10]})
        ledger = contexts[position]
        pcell = [r for r in primary_cells if r["row_name"] == context and r["depmap_id"] == context]
        scell = [r for r in secondary_cells if r["row_name"] == context and r["depmap_id"] == context]
        pool = [r for r in pools if r["row_name"] == context and r["depmap_id"] == context and r["screen_id"] == "HTS002"]
        reasons = []
        if len(pcell) != 1 or pcell[0]["passed_str_profiling"] != "TRUE":
            reasons.append("primary_exact_identity_STR_mapping_not_unique_and_passing")
        if len(scell) != 1:
            reasons.append("secondary_exact_row_name_depmap_id_mapping_not_unique")
        elif scell[0]["passed_str_profiling"] != "TRUE":
            reasons.append("secondary_cell_failed_STR")
        if not pool:
            reasons.append("no_exact_HTS002_pool_mapping")
        elif len(pool) != 1:
            reasons.append("ambiguous_exact_HTS002_pool_mapping")
        elif pool[0]["passed_str_profiling"] != "TRUE":
            reasons.append("HTS002_pool_failed_STR")
        qualified[context], context_reasons[context] = not reasons, reasons
        check(ledger, {"context": context, "index": index, "evaluation_index": position,
            "secondary_row_name": context, "identity_key": str(identities[index]),
            "primary_cell_metadata": pcell, "secondary_cell_metadata": scell[0] if len(scell) == 1 else None,
            "HTS002_pool_metadata": pool[0] if len(pool) == 1 else None, "eligible": not reasons,
            "reason": reasons[0] if reasons else None, "reasons": reasons,
            "response_row_presence": None, "finite_outcome_availability": None,
            "prior_top10_indices": order[:10], "prior_next10_indices": order[10:],
            "prior_top10_ids": drugs[order[:10]].tolist(), "prior_next10_ids": drugs[order[10:]].tolist()})
        for rank, drug in enumerate(order, 1):
            group, treatment = group_map[str(drugs[drug])], treatment_map[drug]
            pmeta = [r for r in primary_treatments if r["column_name"] == group["representative_column"]]
            assert len(pmeta) == 1 and pmeta[0]["broad_id"] == group["representative_broad_id"]
            assert pmeta[0]["dose"] == "2.5" and pmeta[0]["screen_id"] == "HTS"
            main_rows = [r for r in main if r["broad_id"] == group["representative_broad_id"]]
            check(treatment, {"index": drug, "drug_id": str(drugs[drug]),
                "representative_broad_id": group["representative_broad_id"], "representative_column": group["representative_column"],
                "exact_primary_mapping": pmeta[0], "eligible": bool(main_rows),
                "main_metadata_rows": [dict(r, column_in_response_header=r["column_name"] in header_set) for r in main_rows]})
            check(ledger["ranked_drugs"][rank-1], {"rank": rank, "index": drug, "drug_id": str(drugs[drug]),
                "representative_broad_id": group["representative_broad_id"], "prediction": float(predictions[position, 0, drug])})
    assert set(treatment_map) == set(d for order in orders.values() for d in order)

    position = 0
    block_eligible_count = Counter()
    case_reasons = Counter()
    expected_counts = Counter()
    eligible_count = 0
    for evaluation_position, index in enumerate(evaluation):
        context, order = str(ids[index]), orders[str(ids[index])]
        for left_rank in range(1, 11):
            for right_rank in range(11, 21):
                left, right = order[left_rank-1], order[right_rank-1]
                lgroup, rgroup = group_map[str(drugs[left])], group_map[str(drugs[right])]
                lb, rb = lgroup["representative_broad_id"], rgroup["representative_broad_id"]
                case = cases[position]
                check(case, {"case_id": f"{context}|{left_rank:02d}|{right_rank:02d}", "context": context,
                    "index": index, "evaluation_index": evaluation_position, "secondary_row_name": context,
                    "left_rank": left_rank, "right_rank": right_rank, "left_index": left, "right_index": right,
                    "left_drug_id": str(drugs[left]), "right_drug_id": str(drugs[right]),
                    "left_broad_id": lb, "right_broad_id": rb, "left_prediction": float(predictions[evaluation_position, 0, left]),
                    "right_prediction": float(predictions[evaluation_position, 0, right]),
                    "predicted_difference": float(predictions[evaluation_position, 0, left]-predictions[evaluation_position, 0, right]),
                    "finite_outcome_availability": None})
                common = sorted(set(compound[lb]) & set(compound[rb]))
                assert [b["compound_plate"] for b in case["blocks"]] == common
                valid_blocks = []
                for number, plate in enumerate(common):
                    aa, bb = compound[lb][plate], compound[rb][plate]
                    ap, bp = defaultdict(list), defaultdict(list)
                    for record in aa:
                        ap[record["detection_plate"]].append(record)
                    for record in bb:
                        bp[record["detection_plate"]].append(record)
                    expected = sorted(set(ap) & set(bp))
                    repeats = []
                    for repeat in expected:
                        assert len(ap[repeat]) == len(bp[repeat]) == 1
                        a, b = ap[repeat][0], bp[repeat][0]
                        repeats.append({"detection_plate": repeat, "left_column": a["column_name"], "right_column": b["column_name"],
                            "left_well": a["well"], "right_well": b["well"], "left_column_in_response_header": a["column_name"] in header_set,
                            "right_column_in_response_header": b["column_name"] in header_set})
                    accessible = sum(r["left_column_in_response_header"] and r["right_column_in_response_header"] for r in repeats)
                    good = len(expected) >= 2 and accessible >= 2 and len({r["well"] for r in aa}) == len({r["well"] for r in bb}) == 1
                    valid_blocks.append(good)
                    block = case["blocks"][number]
                    check(block, {"expected_detection_plates": expected, "left_detection_plates": sorted(ap), "right_detection_plates": sorted(bp),
                        "header_accessible_common_repeats": accessible, "metadata_eligible": good, "eligible": good and qualified[context],
                        "repeat_columns": repeats})
                    expected_counts[str(len(expected))] += 1
                    block_eligible_count["before"] += good
                    block_eligible_count["after"] += good and qualified[context]
                eligible = qualified[context] and len(common) == 1 and all(valid_blocks)
                assert case["eligible"] == eligible
                assert case["repeat_columns"] == (case["blocks"][0]["repeat_columns"] if eligible else [])
                eligible_count += eligible
                reasons = list(context_reasons[context])
                if not common:
                    reasons.append("no_shared_compound_plate_for_exact_representatives")
                # These exact source conditions all have unique complete mappings.
                assert all(valid_blocks)
                check(case, {"reasons": reasons, "reason": reasons[0] if reasons else None})
                case_reasons.update(reasons)
                position += 1
    check(manifest["counts"], {"archived_contexts": 106, "context_metadata_qualified": sum(qualified.values()),
        "intended_top10_entries": 1060, "intended_top20_entries": 2120, "intended_unique_drug_groups": len(treatments),
        "intended_cases": 10600, "main_exactdose_metadata_rows": len(main),
        "main_metadata_columns_in_response_header": sum(r["column_name"] in header_set for r in main),
        "main_metadata_columns_absent_from_response_header": sum(r["column_name"] not in header_set for r in main),
        "pair_plate_blocks_before_context_qualification": block_eligible_count["before"],
        "pair_plate_blocks_after_context_qualification": block_eligible_count["after"], "metadata_eligible_cases": eligible_count,
        "expected_repeat_count_distribution": dict(expected_counts),
        "context_exclusion_reasons": dict(Counter(r for rr in context_reasons.values() for r in rr)),
        "case_exclusion_reasons": dict(case_reasons)})
    check(manifest["outcome_access"], {"response_values_read_by_preparation": False, "secondary_response_rows_parsed": 0,
        "archive_outcome_arrays_materialized": [], "response_row_presence": None, "finite_outcome_availability": None})
    report = {"status": "PASS_INDEPENDENT_METADATA_AUDIT", "contexts": 106, "intended_pairs": 10600,
        "metadata_qualified_contexts": sum(qualified.values()), "metadata_eligible_pairs": eligible_count,
        "secondary_response_values_read": 0, "reviewer_imports": "No prepare/run/selection/reduction helper imports",
        "verified": ["source and derived-manifest hash chains", "all original contexts and fixed prior top10-versus-next10 choices",
            "exact representative full Broad drug-batch IDs; metadata-only STR and HTS002 pool qualification",
            "all full-metadata common actual detection plates, wells, original column identities and absent-header flags",
            "all ineligible comparisons retained without replacements; no response-row or finite-outcome recruitment"],
        "scientific_scope": "Frozen local ComBat-corrected same-plate assay-repeat reliability; no raw-isolation, biological independence or framework efficacy claim",
        "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in [STUDY / "PROTOCOL.json", STUDY / "prepare.py", STUDY / "run.py",
            *[STUDY / "data" / name for name in ("MANIFEST.json", "PAIR_CASES.json", "CONTEXTS.json", "TREATMENTS.json", "SOURCES.json")],
            *[STUDY / "literature" / name for name in ("SCOPE_REVIEW.md", "SOURCE_READ_RECEIPTS.json", "CHECKS.json", "PAIRING_COORDINATION.json")],
            STUDY / "tests/test_safety.py"]}, "verifier_sha256": sha(__file__)}
    return report, {"cases": cases, "contexts": contexts, "header": header}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    report, _ = verify_metadata()
    (HERE / "METADATA_VERIFICATION.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "contexts", "intended_pairs", "metadata_eligible_pairs")}))
