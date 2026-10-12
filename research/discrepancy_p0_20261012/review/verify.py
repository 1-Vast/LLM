"""Independent P0 artifact and arithmetic audit; imports no producer functions."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
import math
from pathlib import Path
import re
from statistics import fmean

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]
OLD = ROOT / "research/context_probe_20261011"
ARCHIVE = OLD / "runs/fixed8"


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
        assert len(actual) == len(expected), (actual, expected)
        for left, right in zip(actual, expected):
            check(left, right)
    elif isinstance(expected, float):
        assert actual is not None and math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-12), (actual, expected)
    else:
        assert actual == expected, (actual, expected)


def average(values):
    measured = [v for v in values if v is not None]
    return fmean(measured) if measured else None


def literature_audit():
    packet = read(STUDY / "literature/SOURCES.json")
    reused = read(STUDY / "literature/SOURCE_READ_RECEIPTS.json")
    retrieved = read(STUDY / "literature/RETRIEVAL_RECEIPTS.json")
    checks = read(STUDY / "literature/CHECKS.json")
    assert checks["overall_passed"] and len(checks["checks"]) == 35 and all(c["passed"] for c in checks["checks"])
    source_paths = {}
    for receipt in reused:
        path = Path(receipt["local_path"])
        assert sha(path) == receipt["sha256"] and path.stat().st_size == receipt["bytes"]
        assert receipt["access_kind"] == "reused_local_source" and receipt["read_at_utc"]
        source_paths[receipt["id"]] = path
    for receipt in retrieved:
        if "saved_response_path" in receipt:
            path = Path(receipt["saved_response_path"])
            assert sha(path) == receipt["saved_sha256"] and path.stat().st_size == receipt["saved_bytes"]
            assert path.stat().st_size <= receipt["maximum_response_bytes"]
            source_paths[receipt["id"]] = path
        else:
            assert receipt["status"] == "transport_failure"
    assert len({r["id"] for r in reused + retrieved}) == len(reused) + len(retrieved)
    for candidate in packet["candidates"]:
        assert set(candidate["reused_source_ids"]) <= {r["id"] for r in reused}
        assert set(candidate["new_retrieval_ids"]) <= {r["id"] for r in retrieved}
        for excerpt in candidate["exact_method_excerpts"]:
            body = source_paths[excerpt["source_receipt_id"]].read_text(encoding="utf-8")
            body = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))
            assert excerpt["quote"] in body, excerpt
    check(packet["access_summary"], {"new_network_attempts": len(retrieved),
        "reused_local_sources": len(reused), "new_outcome_matrices_downloaded": 0,
        "new_outcome_values_read": 0, "llm_api_calls": 0, "usable_source_archives_obtained": 0})
    archives = [r for r in retrieved if r["id"].endswith("_archive")]
    assert len(archives) == packet["access_summary"]["source_archive_attempts"] == 2
    for attempt in archives:
        if "saved_response_path" in attempt:
            with Path(attempt["saved_response_path"]).open("rb") as stream:
                assert stream.read(4) != b"PK\x03\x04"  # Validate only the header of the retained HTML response.
            assert attempt["content_validation"]["status"] == "invalid_expected_archive"
    return {"literature_reused_source_receipts": len(reused),
            "literature_retrieval_receipts": len(retrieved), "original_method_quotes_checked":
            sum(len(c["exact_method_excerpts"]) for c in packet["candidates"])}


def source_audit():
    audit = read(STUDY / "data/SOURCE_AUDIT.json")
    sources = read(STUDY / "data/SOURCES.json")
    checks = read(STUDY / "data/CHECKS.json")
    assert checks["status"] == "PASS" and len(checks["checks"]) == 13 and all(checks["checks"].values())
    assert checks["source_audit_sha256"] == sha(STUDY / "data/SOURCE_AUDIT.json")
    assert checks["script_sha256"] == sha(STUDY / "audit_sources.py")
    paths = {}
    for source in sources:
        path = ROOT / source["path"]
        assert sha(path) == source["sha256"] and path.stat().st_size == source["bytes"], path
        paths[path.name] = path
    assert audit["script_sha256"] == sha(STUDY / "audit_sources.py")
    assert audit["llm_api_calls"] == 0
    network = read(STUDY / "data/NETWORK_SOURCES.json")
    assert {r["name"] for r in network} == {
        "primary-screen-replicate-treatment-info.csv", "primary-screen-pooling-info.csv"
    }
    for row in network:
        path, official = ROOT / row["path"], ROOT / row["official_page_path"]
        assert row["status"] == 200 and row["bytes"] <= row["limit_bytes"]
        assert sha(path) == row["sha256"] and sha(official) == row["official_page_sha256"]
        text = official.read_text(encoding="utf-8")
        assert row["name"] in text and row["requested_url"] in text
    literature = read(STUDY / "literature/RETRIEVAL_RECEIPTS.json")
    for receipt in literature:
        if "saved_response_path" in receipt:
            path = Path(receipt["saved_response_path"])
            assert sha(path) == receipt["saved_sha256"] and path.stat().st_size == receipt["saved_bytes"]
            assert receipt["saved_bytes"] <= receipt["maximum_response_bytes"]
    literature_audit()

    def metadata(name):
        return pd.read_csv(paths[name], keep_default_na=False, low_memory=False)

    def dose_records(name, screen=None):
        records = metadata(name).to_dict("records")
        numeric = []
        for record in records:
            try:
                dose = float(record["dose"])
            except ValueError:
                continue  # Recorded NA for controls is not an experimental dose.
            if dose == 2.5:
                numeric.append(record)
        return [r for r in numeric if (screen is None or r["screen_id"] == screen)
                and r.get("perturbation_type", "experimental_treatment") == "experimental_treatment"]

    for label, name, screen, filename in (
        ("primary_replicates", "primary-screen-replicate-treatment-info.csv", "HTS", "PRIMARY_HTS_REPLICATE_GROUPS.csv"),
        ("secondary_replicates", "secondary-screen-replicate-treatment-info.csv", None, "SECONDARY_REPLICATE_GROUPS.csv"),
    ):
        records = dose_records(name, screen)
        groups = defaultdict(list)
        for row in records:
            groups[(row["broad_id"], float(row["dose"]), row["screen_id"], row["compound_plate"])].append(row)
        expected_groups = {key: (len(rr), len({r["detection_plate"] for r in rr}), len({r["well"] for r in rr})) for key, rr in groups.items()}
        exported = pd.read_csv(STUDY / "data" / filename, keep_default_na=False).to_dict("records")
        actual_groups = {(r["broad_id"], float(r["dose"]), r["screen_id"], r["compound_plate"]):
                         (r["metadata_rows"], r["detection_plates"], r["recorded_well_positions"]) for r in exported}
        assert len(exported) == len(actual_groups) and actual_groups == expected_groups
        time_tokens = Counter((m.group(1) if (m := re.search(r"_(\d+)H_", r["detection_plate"])) else "NOT_ENCODED") for r in records)
        expected = {"exactdose_experimental_rows": len(records), "condition_groups": len(groups),
            "distinct_broad_ids": len({r["broad_id"] for r in records}),
            "condition_group_keys": ["broad_id", "dose", "screen_id", "compound_plate"],
            "groups_with_different_recorded_wells": sum(counts[2] > 1 for counts in expected_groups.values()),
            "detection_plates": len({r["detection_plate"] for r in records}),
            "compound_plates": len({r["compound_plate"] for r in records}),
            "groups_with_multiple_detection_plates": sum(counts[1] > 1 for counts in expected_groups.values()),
            "metadata_rows_per_group": {str(n): count for n, count in Counter(len(rr) for rr in groups.values()).items()},
            "encoded_plate_time_tokens": dict(time_tokens), "independent_culture_ids": False,
            "biological_repeat_count": None}
        if "detection_plate_scan_time" in records[0]:
            expected["detection_scan_time_nonempty"] = sum(r["detection_plate_scan_time"] != "" for r in records)
        check(audit["prism"][label], expected)
    primary = dose_records("primary-screen-replicate-collapsed-treatment-info.csv", "HTS")
    secondary = dose_records("secondary-screen-replicate-collapsed-treatment-info.csv")
    check(audit["prism"]["primary_collapsed"], {
        "metadata_rows": len(metadata("primary-screen-replicate-collapsed-treatment-info.csv")),
        "exactdose_HTS_columns": len(primary), "unique_exactdose_HTS_columns": len({r["column_name"] for r in primary})})
    pids = {r["broad_id"] for r in primary}
    overlap = [r for r in secondary if r["broad_id"] in pids]
    emitted_overlap = pd.read_csv(STUDY / "data/PRISM_PRIMARY_SECONDARY_ID_OVERLAP.csv", keep_default_na=False).to_dict("records")
    check(emitted_overlap, [{name: r[name] for name in ("broad_id", "dose", "screen_id", "column_name", "compound_plate")} for r in overlap])
    screens = defaultdict(set)
    for row in secondary:
        screens[(row["broad_id"], float(row["dose"]))].add(row["screen_id"])
    check(audit["prism"]["cross_screen"], {
        "secondary_exactdose_columns": len(secondary),
        "secondary_exactdose_columns_by_screen": dict(Counter(r["screen_id"] for r in secondary)),
        "exact_full_broad_id_overlap": len(pids & {r["broad_id"] for r in secondary}),
        "same_drug_dose_multiple_secondary_screens": sum(len(ss) > 1 for ss in screens.values()),
        "cell_metadata_row_id_overlap": len(set(metadata("primary-screen-cell-line-info.csv").row_name) & set(metadata("secondary-screen-cell-line-info.csv").row_name)),
        "cell_drug_complete_pairs": None, "matching_time_culture_and_QC_complete_pairs": None})
    for label, name in (("primary_pool", "primary-screen-pooling-info.csv"), ("secondary_pool", "secondary-screen-pooling-info.csv")):
        records, identities = metadata(name).to_dict("records"), defaultdict(set)
        for row in records:
            identities[row["screen_id"]].add(row["row_name"])
        check(audit["prism"][label], {"metadata_rows": len(records),
            "rows_by_screen": dict(Counter(r["screen_id"] for r in records)),
            "distinct_row_ids_by_screen": {screen: len(ids) for screen, ids in identities.items()}})

    for section, key in ((audit["prism"]["published_protocol"], "paper_path"), (audit["cxcl9"], "paper_path")):
        paper = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", (ROOT / section[key]).read_text(encoding="utf-8"))))
        for excerpt in section["paper_excerpts"].values():
            assert excerpt and excerpt in paper
    check(audit["prism"]["published_protocol"], {"nominal_time_hours": 120, "independent_culture_start_ids_verified": False})
    assert "five-day incubation" in audit["prism"]["published_protocol"]["paper_excerpts"]["duration"]
    assert "independently treated plates" in audit["prism"]["published_protocol"]["paper_excerpts"]["assay_repeats"]
    check(audit["prism"]["qualification"], {"repeat_assay_plate_design": "QUALIFIED_BY_PUBLISHED_METHODS",
        "independent_culture_start_hierarchy": "UNRESOLVED", "biological_vs_technical_cause": "NON_IDENTIFIABLE"})

    # Read only the specified treatment/sample fields from cached CXCL9 tables.
    design_columns = ["Cell line", "Sample", "Condition", "Cytokines", "Cytokine concentration (ng/mL)", "Inhibitors", "Inhibitor concentration (uM)"]
    design, all_rows, counts = Counter(), [], {}
    for item in audit["cxcl9"]["raw_files"]:
        name = f"00_Raw_Data_{item['file']}.csv"
        header = pd.read_csv(paths[name], nrows=0).columns.tolist()
        rows = pd.read_csv(paths[name], usecols=design_columns, keep_default_na=False).to_dict("records")
        assert len(rows) == item["rows"] and header == item["columns"]
        assert item["outcome_columns_read"] == [] and item["Cas3_channel"] is False
        record = next(r for r in sources if Path(r["path"]).name == name)
        assert set(record["columns_read"]) == set(design_columns)
        for row in rows:
            key = (item["file"], item["passage"], *(str(row[c]) for c in design_columns))
            design[key] += 1
        counts[item["file"]] = len(rows)
        all_rows += rows
    emitted = pd.read_csv(STUDY / "data/CXCL9_SAMPLE_DESIGN.csv", dtype=str, keep_default_na=False).to_dict("records")
    emitted_design = {(r["source_file"], r["passage"], *(r[c] for c in design_columns)): int(r["bead_event_rows"]) for r in emitted}
    assert len(emitted) == len(emitted_design) and emitted_design == dict(design)
    duplicate_conditions = Counter(f"{key[0]}|{key[4]}" for key in design)
    check(audit["cxcl9"], {"local_raw_contexts": sorted({r["Cell line"] for r in all_rows}),
        "paper_reported_biological_screenings": 2, "screen_file_candidates": 2,
        "sample_condition_records": len(design), "conditions_per_file_duplicate": dict(duplicate_conditions),
        "cytokines": sorted({r["Cytokines"] for r in all_rows}), "inhibitors": sorted({r["Inhibitors"] for r in all_rows}),
        "cytokine_doses_recorded_ng_ml": sorted({str(r["Cytokine concentration (ng/mL)"]) for r in all_rows}),
        "inhibitor_doses_recorded_um": sorted({str(r["Inhibitor concentration (uM)"]) for r in all_rows}),
        "Cas3_condition_pairing": "NOT_EVALUABLE_IN_CACHED_RAW_FILES"})
    assert counts == {"E3CA": 52298, "E3CB": 47230}
    check(audit["cxcl9"]["qualification"], {"general_context_transport": "NOT_ESTABLISHED_BY_SINGLE_RAW_CONTEXT_TWO_SCREENINGS",
        "mechanism_discrimination_cell_loss_vs_signaling": "NOT_EVALUABLE_WITHOUT_PAIRED_Cas3_OR_VIABILITY"})
    return audit, sources, literature


def verify(out):
    out = Path(out).resolve()
    freeze, receipt = read(out / "FREEZE.json"), read(out / "RECEIPT.json")
    prior_review = read(OLD / "review/VERIFICATION.json")
    required = {STUDY / "PROTOCOL.json", STUDY / "diagnose_archive.py", OLD / "data/output.npz",
                OLD / "review/VERIFICATION.json", OLD / "PROTOCOL.json", ARCHIVE / "COMMIT_RECEIPT.json",
                *[ARCHIVE / name for name in prior_review["files"]]}
    pinned = {ROOT / relative for relative in freeze["files"]}
    assert required <= pinned
    for relative, expected in freeze["files"].items():
        assert sha(ROOT / relative) == expected, relative
    assert prior_review["status"] == "PASS_ARITHMETIC_AND_ARTIFACT_AUDIT"
    assert sha(OLD / "review/verify.py") == prior_review["verifier_sha256"]
    for name, expected in prior_review["files"].items():
        assert sha(ARCHIVE / name) == expected, name
    old_freeze, old_receipt = read(ARCHIVE / "FREEZE.json"), read(ARCHIVE / "RECEIPT.json")
    for relative, expected in old_freeze["files"].items():
        assert sha(ROOT / relative) == expected, relative
    manifest = read(OLD / "data/MANIFEST.json")
    assert sha(OLD / "data/output.npz") == old_freeze["input_sha256"] == manifest["output_npz_sha256"]
    for source in manifest["sources"]:
        assert sha(ROOT / source["path"]) == source["sha256"], source["path"]
    for name, expected in manifest["derived_file_sha256"].items():
        assert sha(OLD / "data" / name) == expected, name
    commit_receipt = read(ARCHIVE / "COMMIT_RECEIPT.json")
    for name, key in (("COMMITS.json", "commits_sha256"), ("predictions.npz", "predictions_sha256"), ("FIT_FREEZE.json", "fit_sha256")):
        assert sha(ARCHIVE / name) == commit_receipt[key]
    for name, key in (("ROWS.json", "rows_sha256"), ("RESULTS.json", "results_sha256")):
        assert sha(out / name) == receipt[key] and sha(ARCHIVE / name) == old_receipt[key]
    audit, sources, literature = source_audit()

    # Load identity/prediction axes before materializing outcome values.
    with np.load(OLD / "data/output.npz", allow_pickle=False) as archive:
        contexts, roles, identities = archive["context_id"], archive["role"], archive["identity_key"]
        drugs, lineages = archive["drug_id"], archive["lineage"]
    with np.load(ARCHIVE / "predictions.npz", allow_pickle=False) as archive:
        predictions = archive["predictions"]
    protocol = read(STUDY / "PROTOCOL.json")
    arms = read(OLD / "PROTOCOL.json")["arms"]
    assert arms == ["zero_purchase", "paid_no_update", "offset", "lowrank", "shuffled_lowrank", "conditional"]
    k = protocol["top_k"]
    assert k == 10 and len(contexts) == 561 and len(drugs) == 3621
    assert len(set(contexts)) == len(set(identities)) == len(contexts) and len(set(drugs)) == len(drugs)
    for identity, role in zip(identities, roles):
        unit = int(hashlib.sha256(f"{manifest['context_roles']['salt']}|{identity}".encode()).hexdigest(), 16) / 2**256
        assert role == ("reference" if unit < .6 else "development" if unit < .8 else "evaluation")
    evaluation = [i for i, role in enumerate(roles) if role == "evaluation"]
    assert len(evaluation) == 106 and evaluation[0] == 5 and contexts[5] == "ACH-000013"
    assert predictions.shape == (106, 6, 3621) and np.isfinite(predictions).all()
    fit, probe_freeze = read(ARCHIVE / "FIT_FREEZE.json"), read(ARCHIVE / "PROBE_FREEZE.json")
    probes = fit["probe_indices"]
    assert len(probes) == len(set(probes)) == 8
    assert drugs[probes].tolist() == fit["probe_ids"] == probe_freeze["probe_ids"]
    assert probes == probe_freeze["probe_indices"]
    menu = sorted(set(range(len(drugs))) - set(probes))
    assert len(menu) == 3613 == fit["terminal_count"] == receipt["terminal_menu_count"]
    assert hashlib.sha256(np.asarray(menu, dtype="<i8").tobytes()).hexdigest() == receipt["terminal_menu_sha256"]
    groups = [g for g in read(OLD / "data/drug_groups.json") if g["eligible"]]
    assert [g["drug_id"] for g in groups] == drugs.tolist()
    commits, rows, results = read(ARCHIVE / "COMMITS.json"), read(out / "ROWS.json"), read(out / "RESULTS.json")
    assert len(commits) == len(rows) == 636 == receipt["arm_contexts"]
    for position, index in enumerate(evaluation):
        for arm_position, arm in enumerate(arms):
            record = commits[position * len(arms) + arm_position]
            chosen = sorted(menu, key=lambda d: (float(predictions[position, arm_position, d]), d))[:k]
            check(record, {"index": index, "context": str(contexts[index]), "arm": arm,
                           "selected_indices": chosen, "selected_ids": drugs[chosen].tolist(),
                           "resource": 0 if arm == "zero_purchase" else 10})

    with np.load(OLD / "data/output.npz", allow_pickle=False) as archive:
        truth, availability = archive["y"], archive["available"]
    np.testing.assert_array_equal(availability, np.isfinite(truth))
    source_paths = {s["name"]: ROOT / s["path"] for s in manifest["sources"]}
    original = pd.read_csv(source_paths["responses"], index_col=0)
    context_table = pd.read_csv(OLD / "data/contexts.csv")
    np.testing.assert_array_equal(original.loc[context_table.response_row_id, [g["representative_column"] for g in groups]].to_numpy(), truth)

    rebuilt = []
    for position, index in enumerate(evaluation):
        y, prior = truth[index], predictions[position, 0]
        prior_order = sorted(menu, key=lambda d: (float(prior[d]), d))
        bands = {"all": menu, "selected_prior": prior_order[:k], "boundary": prior_order[k:3*k], "remainder": prior_order[3*k:]}
        base_selected = commits[position * len(arms)]["selected_indices"]
        finite_menu = [d for d in menu if math.isfinite(y[d])]
        hindsight = sorted(finite_menu, key=lambda d: (float(y[d]), d))[:k]
        best_observed = -fmean(y[d] for d in hindsight) if len(hindsight) == k else None
        oracle = best_observed if len(finite_menu) == len(menu) else None
        base_utility = -fmean(y[d] for d in base_selected) if all(math.isfinite(y[d]) for d in base_selected) else None
        for arm_position, arm in enumerate(arms):
            record = commits[position * len(arms) + arm_position]
            selected, pred = record["selected_indices"], predictions[position, arm_position]
            utility = -fmean(y[d] for d in selected) if all(math.isfinite(y[d]) for d in selected) else None
            delta = utility - base_utility if utility is not None and base_utility is not None else None
            added, removed = sorted(set(selected) - set(base_selected)), sorted(set(base_selected) - set(selected))
            measured = {name: [d for d in band if math.isfinite(y[d])] for name, band in bands.items()}
            mse = {name: fmean((float(pred[d])-float(y[d]))**2 for d in dd) if dd else None for name, dd in measured.items()}
            pair_errors = [((float(pred[a])-float(pred[b]))-(float(y[a])-float(y[b])))**2
                           for a in prior_order[:k] for b in prior_order[k:2*k] if math.isfinite(y[a]) and math.isfinite(y[b])]
            expected = {"context": str(contexts[index]), "index": index, "lineage": str(lineages[index]),
                "arm": arm, "resource": record["resource"], "update_status": record["update_status"],
                "selected_indices": selected, "baseline_selected_indices": base_selected,
                "added_indices": added, "removed_indices": removed, "utility": utility,
                "baseline_utility": base_utility, "utility_increment": delta,
                "swap_gain": (math.fsum(y[d] for d in removed)-math.fsum(y[d] for d in added))/k if delta is not None else None,
                "selected_missing": sum(not math.isfinite(y[d]) for d in selected), "mse": mse,
                "measured_per_band": {name: len(dd) for name, dd in measured.items()},
                "pairwise_difference_mse": fmean(pair_errors) if pair_errors else None,
                "pairwise_observed_pairs": len(pair_errors),
                "prior_margin_10_11": float(prior[prior_order[k]]-prior[prior_order[k-1]]),
                "exact_full_menu_oracle_utility": oracle,
                "exact_full_menu_regret": oracle-utility if oracle is not None and utility is not None else None,
                "exact_oracle_status": "COMPLETE_FIXED_MENU" if oracle is not None else "UNKNOWN_MISSING_MENU_OUTCOMES",
                "observed_subset_hindsight_utility": best_observed,
                "full_menu_regret_lower_bound": best_observed-utility if best_observed is not None and utility is not None else None}
            assert set(rows[len(rebuilt)]) == set(expected)
            check(rows[len(rebuilt)], expected)
            check(expected["swap_gain"], delta)
            if expected["full_menu_regret_lower_bound"] is not None:
                assert expected["full_menu_regret_lower_bound"] >= -1e-12
            rebuilt.append(expected)

    baseline_rows = {r["context"]: r for r in rebuilt if r["arm"] == "zero_purchase"}
    for arm in arms:
        rr = [r for r in rebuilt if r["arm"] == arm]
        complete = [r for r in rr if r["utility_increment"] is not None]
        expected = {"contexts": len(rr), "paired_complete_contexts": len(complete),
            "improved": sum(r["utility_increment"] > 1e-12 for r in complete),
            "harmed": sum(r["utility_increment"] < -1e-12 for r in complete),
            "equal": sum(abs(r["utility_increment"]) <= 1e-12 for r in complete),
            "mean_utility_increment": average(r["utility_increment"] for r in complete),
            "mean_positive_contribution": average(max(0., r["utility_increment"]) for r in complete),
            "mean_negative_contribution": average(min(0., r["utility_increment"]) for r in complete),
            "mse_improves_but_utility_harmed": sum(r["mse"]["all"] < baseline_rows[r["context"]]["mse"]["all"] and r["utility_increment"] < -1e-12 for r in complete),
            "mean_mse": {name: average(r["mse"][name] for r in rr) for name in bands},
            "mean_pairwise_difference_mse": average(r["pairwise_difference_mse"] for r in rr),
            "exact_oracle_contexts": sum(r["exact_full_menu_regret"] is not None for r in rr),
            "mean_exact_regret_complete_menu_only": average(r["exact_full_menu_regret"] for r in rr),
            "lower_bound_contexts": sum(r["full_menu_regret_lower_bound"] is not None for r in rr),
            "mean_regret_lower_bound_complete_selection_only": average(r["full_menu_regret_lower_bound"] for r in rr),
            "scenario_net_increment": {str(price): average(r["utility_increment"]-price*r["resource"] for r in complete) for price in protocol["price_grid"]}}
        assert set(results["arms"][arm]) == set(expected)
        check(results["arms"][arm], expected)
    check(receipt, {"contexts": 106, "source_artifact_hashes_matched": len(prior_review["files"]),
                    "new_model_fits": 0, "new_measurements": 0, "llm_calls": 0})
    check(results, {"status": "EXPOSED_ARCHIVE_DIAGNOSIS_COMPLETE_NO_NEW_POLICY", "contexts": 106, "arm_contexts": 636})
    files = [out / name for name in ("FREEZE.json", "ROWS.json", "RESULTS.json", "RECEIPT.json")]
    files += list((STUDY / "data").glob("*.json")) + list((STUDY / "data").glob("*.csv"))
    files += [STUDY / "audit_sources.py", STUDY / "tests/test_safety.py", STUDY / "literature/RETRIEVAL_RECEIPTS.json"]
    files += [STUDY / "literature" / name for name in ("SOURCES.json", "SOURCE_READ_RECEIPTS.json", "DESIGN_NOTES.md", "CHECKS.json")]
    return {"status": "PASS_INDEPENDENT_ARTIFACT_AND_ARITHMETIC_AUDIT", "scope": protocol["scope"],
        "contexts": 106, "arm_contexts": 636, "terminal_menu_count": len(menu),
        "source_records": len(sources), "literature_retrieval_receipts": len(literature),
        "reviewer_imports": "No producer runner, selection, scoring or summary functions imported",
        "verified": ["old and new freeze, commitment and score hash chains", "source receipt hashes and metadata download limits",
            "PRISM dose/screen overlap and assay-repeat metadata groups; source quotes for five-day repeated plate design",
            "CXCL9 single raw context, two screening candidates, technical nesting and secretion endpoint provenance; no PE values materialized or scored",
            "final literature source/read/retrieval chains and original-method quote provenance; failed archive access retained as unresolved",
            "identity roles, prediction axes, probe/alias-group exclusion and original commitments", "original response-matrix alignment including missing outcomes",
            "all 636 utilities, missingness, fixed prediction bands, pairwise errors and swap decompositions",
            "complete-menu exact oracles; incomplete-menu null oracles and observed-subset hindsight lower bounds",
            "all paired descriptive summaries and declared price scenarios"],
        "not_verified": ["independent culture-start hierarchy and sample-specific elapsed exposure linkage", "raw publisher normalization isolation",
            "biological mechanism causes or causal target engagement", "lawful purchasable information value or EVSI",
            "prospective scientific benefit, inferential coverage, actual prices or latency"],
        "scientific_status": "Fixed-eight-probe branch remains stopped; P0 audit supplies no new model or biological confirmation",
        "files": {path.relative_to(ROOT).as_posix(): sha(path) for path in files}, "verifier_sha256": sha(__file__)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    report = verify(parser.parse_args().output)
    (HERE / "VERIFICATION.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "contexts", "arm_contexts", "terminal_menu_count")}))
