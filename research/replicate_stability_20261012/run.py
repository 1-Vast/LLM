"""Frozen, descriptive same-plate PRISM repeat-contrast diagnosis."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RAW = ROOT / "data/external/prism_19q4/raw"
OLD = ROOT / "research/context_probe_20261011"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def finite_or_none(value):
    return float(value) if value is not None and np.isfinite(value) else None


def diagnose_pair(secondary_differences, primary_difference, prior_difference):
    values = np.asarray(secondary_differences, dtype=float)
    if values.ndim != 1 or not np.isfinite(prior_difference) or prior_difference > 0:
        raise ValueError("one-dimensional repeat differences and nonpositive finite prior difference required")
    observed = values[np.isfinite(values)]
    complete = len(values) >= 2 and len(observed) == len(values)
    positive, negative, zero = (int((observed > 0).sum()), int((observed < 0).sum()), int((observed == 0).sum()))
    if not len(values):
        status = "NO_METADATA_PAIR"
    elif not complete:
        status = "INCOMPLETE_REPEAT_OBSERVATIONS"
    elif positive and negative:
        status = "DIRECTION_DISAGREEMENT"
    elif zero == len(values):
        status = "ALL_ZERO_TIES"
    elif zero:
        status = "TIES_WITH_ONE_DIRECTION"
    else:
        status = "STABLE_OPPOSES_PRIOR_ORDER" if positive else "STABLE_SUPPORTS_PRIOR_ORDER"
    pairs = list(combinations(observed.tolist(), 2))
    nonzero = [(a, b) for a, b in pairs if a != 0 and b != 0]
    primary = finite_or_none(primary_difference)
    return {
        "secondary_differences": [finite_or_none(v) for v in values],
        "expected_repeats": len(values), "observed_repeats": len(observed), "complete": complete,
        "positive_repeats": positive, "negative_repeats": negative, "zero_repeats": zero,
        "nonzero_repeat_comparisons": len(nonzero),
        "discordant_repeat_comparisons": sum((a > 0) != (b > 0) for a, b in nonzero),
        "tied_repeat_comparisons": len(pairs) - len(nonzero),
        "missing_repeat_comparisons": len(values) * (len(values) - 1) // 2 - len(pairs),
        "mean_secondary_difference": float(observed.mean()) if len(observed) else None,
        "min_abs_secondary_difference": float(np.abs(observed).min()) if len(observed) else None,
        "primary_difference": primary, "prior_difference": float(prior_difference),
        "prior_prediction_tied": prior_difference == 0,
        "primary_opposes_prior_order": primary > 0 if primary is not None else None,
        "status": status,
    }


def validate_pair_columns(case, metadata):
    """Reject fake cross-plate contrasts without accepting response values."""
    if not case["eligible"]:
        if case["repeat_columns"]:
            raise ValueError("ineligible case must not release a replacement pair")
        return
    blocks = [block for block in case["blocks"] if block["eligible"]]
    if len(blocks) != 1 or case["repeat_columns"] != blocks[0]["repeat_columns"]:
        raise ValueError("one explicit compound-plate block required")
    columns = case["repeat_columns"]
    plates = [r["detection_plate"] for r in columns]
    if len(plates) < 2 or len(set(plates)) != len(plates) or plates != blocks[0]["expected_detection_plates"]:
        raise ValueError("unique expected actual detection plates required")
    complete_plate_sets = []
    for side in ("left", "right"):
        full_group = [record for record in metadata.values()
                      if record["broad_id"] == case[f"{side}_broad_id"]
                      and record["screen_id"] == "HTS002" and float(record["dose"]) == 2.5
                      and record["perturbation_type"] == "experimental_treatment"
                      and record["compound_plate"] == blocks[0]["compound_plate"]]
        actual_plates = [record["detection_plate"] for record in full_group]
        if len(set(actual_plates)) != len(actual_plates) or len({r["well"] for r in full_group}) != 1:
            raise ValueError("ambiguous full treatment group or inconsistent repeated wells")
        complete_plate_sets.append(set(actual_plates))
    if plates != sorted(complete_plate_sets[0].intersection(complete_plate_sets[1])):
        raise ValueError("expected repeats must preserve all common actual metadata plates")
    used = set()
    for repeat in columns:
        for side in ("left", "right"):
            name = repeat[f"{side}_column"]
            record = metadata[name]
            if (name in used or record["broad_id"] != case[f"{side}_broad_id"]
                    or record["screen_id"] != "HTS002" or float(record["dose"]) != 2.5
                    or record["perturbation_type"] != "experimental_treatment"
                    or record["compound_plate"] != blocks[0]["compound_plate"]
                    or record["detection_plate"] != repeat["detection_plate"]
                    or record["well"] != repeat[f"{side}_well"]):
                raise ValueError("drug/condition/actual plate alignment mismatch")
            used.add(name)


def average(values):
    values = [value for value in values if value is not None]
    return float(np.mean(values)) if values else None


def summarize(rows, contexts):
    summaries = []
    for context in contexts:
        rr = [r for r in rows if r["context"] == context["context"]]
        eligible = [r for r in rr if r["eligible"]]
        complete = [r for r in eligible if r["complete"]]
        primary_wrong = [r for r in complete if r["primary_opposes_prior_order"] is True]
        statuses = {name: sum(r["status"] == name for r in complete) for name in (
            "STABLE_OPPOSES_PRIOR_ORDER", "STABLE_SUPPORTS_PRIOR_ORDER", "DIRECTION_DISAGREEMENT",
            "ALL_ZERO_TIES", "TIES_WITH_ONE_DIRECTION")}
        comparisons = sum(r["nonzero_repeat_comparisons"] for r in eligible)
        discordant = sum(r["discordant_repeat_comparisons"] for r in eligible)
        replicated = sum(r["status"] == "STABLE_OPPOSES_PRIOR_ORDER" for r in primary_wrong)
        summaries.append({
            "context": context["context"], "index": context["index"], "intended_pairs": len(rr),
            "metadata_eligible_pairs": len(eligible), "complete_pairs": len(complete),
            "incomplete_eligible_pairs": len(eligible) - len(complete), "statuses": statuses,
            "nonzero_repeat_comparisons": comparisons, "discordant_repeat_comparisons": discordant,
            "tied_repeat_comparisons": sum(r["tied_repeat_comparisons"] for r in eligible),
            "missing_repeat_comparisons": sum(r["missing_repeat_comparisons"] for r in eligible),
            "repeat_discordance_fraction": discordant / comparisons if comparisons else None,
            "stable_opposes_fraction_complete": statuses["STABLE_OPPOSES_PRIOR_ORDER"] / len(complete) if complete else None,
            "primary_wrong_complete_pairs": len(primary_wrong), "replicated_primary_wrong_pairs": replicated,
            "primary_wrong_replication_fraction": replicated / len(primary_wrong) if primary_wrong else None,
        })
    return {"scope": "Released, jointly processed, matched same-plate contrasts only; no inference or full-menu decision benefit",
            "contexts": len(summaries), "intended_pairs": len(rows),
            "metadata_eligible_pairs": sum(r["metadata_eligible_pairs"] for r in summaries),
            "complete_pairs": sum(r["complete_pairs"] for r in summaries),
            "contexts_with_eligible_pairs": sum(r["metadata_eligible_pairs"] > 0 for r in summaries),
            "contexts_with_complete_pairs": sum(r["complete_pairs"] > 0 for r in summaries),
            "repeat_comparison_counts": {name: sum(r[name] for r in summaries) for name in (
                "nonzero_repeat_comparisons", "discordant_repeat_comparisons", "tied_repeat_comparisons", "missing_repeat_comparisons")},
            "status_counts_complete": {name: sum(r["statuses"][name] for r in summaries) for name in summaries[0]["statuses"]},
            "context_macro": {name: {"mean": average(r[name] for r in summaries),
                                     "contributing_contexts": sum(r[name] is not None for r in summaries)} for name in (
                "repeat_discordance_fraction", "stable_opposes_fraction_complete", "primary_wrong_replication_fraction")},
            "primary_wrong_complete_pairs": sum(r["primary_wrong_complete_pairs"] for r in summaries),
            "replicated_primary_wrong_pairs": sum(r["replicated_primary_wrong_pairs"] for r in summaries),
            "context_rows": summaries}


def run(output):
    output = Path(output)
    if output.exists():
        raise ValueError("fresh output path required; preserve prior receipts")
    started = time.perf_counter()
    manifest = read(HERE / "data/MANIFEST.json")
    if sha(HERE / "prepare.py") != manifest["prepare_sha256"]:
        raise ValueError("changed metadata preparation executable")
    for name, digest in manifest["artifact_sha256"].items():
        if sha(HERE / "data" / name) != digest:
            raise ValueError(f"changed frozen metadata artifact: {name}")
    for source in read(HERE / "data/SOURCES.json"):
        if sha(ROOT / source["path"]) != source["sha256"]:
            raise ValueError(f"changed recorded source: {source['path']}")
    cases = read(HERE / "data/PAIR_CASES.json")
    contexts = read(HERE / "data/CONTEXTS.json")
    with np.load(OLD / "data/output.npz", allow_pickle=False) as archive:
        ids, roles, drugs = archive["context_id"], archive["role"], archive["drug_id"]
    with np.load(OLD / "runs/fixed8/predictions.npz", allow_pickle=False) as archive:
        prior = archive["predictions"][:, 0]
    indices = np.flatnonzero(roles == "evaluation")
    probes = read(OLD / "runs/fixed8/FIT_FREEZE.json")["probe_indices"]
    menu = np.setdiff1d(np.arange(len(drugs)), probes)
    orders = {str(ids[index]): menu[np.lexsort((menu, prior[position, menu]))][:20]
              for position, index in enumerate(indices)}
    if len(contexts) != 106 or [r["context"] for r in contexts] != ids[indices].tolist() or len(cases) != 10600:
        raise ValueError("fixed intended population mismatch")
    positions = {str(ids[index]): position for position, index in enumerate(indices)}
    expected_keys = {(str(ids[index]), left, right) for index in indices for left in range(1, 11) for right in range(11, 21)}
    if {(r["context"], r["left_rank"], r["right_rank"]) for r in cases} != expected_keys:
        raise ValueError("all intended fixed prior comparisons required")
    treatments = pd.read_csv(RAW / "secondary-screen-replicate-treatment-info.csv", keep_default_na=False).set_index("column_name").to_dict("index")
    representatives = {group["drug_id"]: group["representative_broad_id"] for group in read(OLD / "data/drug_groups.json")}
    for case in cases:
        order, position = orders[case["context"]], positions[case["context"]]
        left, right = case["left_index"], case["right_index"]
        if (left != int(order[case["left_rank"] - 1]) or right != int(order[case["right_rank"] - 1])
                or case["context"] != str(ids[case["index"]]) or roles[case["index"]] != "evaluation"
                or case["left_drug_id"] != str(drugs[left]) or case["right_drug_id"] != str(drugs[right])
                or case["left_broad_id"] != representatives[str(drugs[left])]
                or case["right_broad_id"] != representatives[str(drugs[right])]
                or case["left_prediction"] != float(prior[position, left])
                or case["right_prediction"] != float(prior[position, right])
                or case["predicted_difference"] != float(prior[position, left] - prior[position, right])):
            raise ValueError("fixed prior identity/order mismatch")
        validate_pair_columns(case, treatments)
    old_manifest = read(OLD / "data/MANIFEST.json")
    old_review = read(OLD / "review/VERIFICATION.json")
    if sha(OLD / "data/output.npz") != old_manifest["output_npz_sha256"]:
        raise ValueError("changed primary archive")
    for name, digest in old_review["files"].items():
        if sha(OLD / "runs/fixed8" / name) != digest:
            raise ValueError(f"changed archived prediction/commit receipt: {name}")
    sources = [HERE / "PROTOCOL.json", Path(__file__), HERE / "prepare.py",
               *sorted((HERE / "data").glob("*.json")), *sorted((HERE / "literature").glob("*.json")),
               HERE / "literature/SCOPE_REVIEW.md", HERE / "review/METADATA_VERIFICATION.json",
               OLD / "data/output.npz", OLD / "data/drug_groups.json", OLD / "data/MANIFEST.json", OLD / "review/VERIFICATION.json",
               *[OLD / "runs/fixed8" / name for name in old_review["files"]],
               *[RAW / name for name in ("secondary-screen-logfold-change.csv", "secondary-screen-replicate-treatment-info.csv",
                                        "secondary-screen-cell-line-info.csv", "secondary-screen-pooling-info.csv", "secondary-screen-readme.txt")]]
    output.mkdir(parents=True)
    dump(output / "FREEZE.json", {"response_access": "Created before loading new secondary response values", "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}})
    # Outcome admission starts only after the protocol, menu and source bytes are frozen.
    response_path = RAW / "secondary-screen-logfold-change.csv"
    header = pd.read_csv(response_path, nrows=0).columns.tolist()
    columns = {repeat[f"{side}_column"] for case in cases if case["eligible"]
               for repeat in case["repeat_columns"] for side in ("left", "right")}
    values = pd.read_csv(response_path, usecols=[header[0]] + sorted(columns.intersection(header)), index_col=0)
    if not values.index.is_unique:
        raise ValueError("ambiguous secondary cell-row identities")
    with np.load(OLD / "data/output.npz", allow_pickle=False) as archive:
        primary = archive["y"]
    rows = []
    for case in cases:
        row_id = case["secondary_row_name"]
        differences = []
        for repeat in case["repeat_columns"]:
            a, b = repeat["left_column"], repeat["right_column"]
            differences.append(float(values.at[row_id, a] - values.at[row_id, b])
                               if row_id in values.index and a in values and b in values else np.nan)
        primary_difference = primary[case["index"], case["left_index"]] - primary[case["index"], case["right_index"]]
        rows.append({"case_id": case["case_id"], "context": case["context"], "index": case["index"],
                     "eligible": case["eligible"], "eligibility_reason": case["reason"],
                     "left_index": case["left_index"], "right_index": case["right_index"],
                     **diagnose_pair(differences, primary_difference, case["predicted_difference"])})
    dump(output / "ROWS.json", rows)
    dump(output / "RESULTS.json", summarize(rows, contexts))
    dump(output / "RECEIPT.json", {"seconds": time.perf_counter() - started, "intended_cases": len(rows),
         "secondary_response_columns_materialized": len(columns.intersection(header)), "secondary_response_rows": len(values),
         "freeze_sha256": sha(output / "FREEZE.json"), "rows_sha256": sha(output / "ROWS.json"),
         "results_sha256": sha(output / "RESULTS.json"), "new_model_fits": 0, "new_llm_calls": 0, "new_wet_measurements": 0})
    print(json.dumps({"output": str(output), "cases": len(rows), "eligible": sum(r["eligible"] for r in rows), "complete": sum(r["complete"] for r in rows)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
