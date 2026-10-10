"""Independent offline audit of the single bounded adaptive supplement."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
import pyarrow.parquet as pq

from . import calibration_verify as first


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
STAGE1 = BASE / "calibration"
STAGE2 = BASE / "calibration_v2"
ROOT = HERE.parents[3]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(path):
    recorded = read(path)
    for name, expected in recorded["sha256"].items():
        assert digest(path.parent / name) == expected, name
    return recorded


def retained(protocol, censuses):
    ledger = first.json_lines(STAGE2 / "NETWORK.jsonl")
    cache = first.json_lines(STAGE2 / "CACHE_REUSE.jsonl")
    spans = {file: [] for file in censuses}
    prior_receipts = first.json_lines(STAGE1 / "NETWORK.jsonl") + first.json_lines(STAGE1 / "CACHE_REUSE.jsonl")
    for folder, records in ((STAGE1, prior_receipts), (STAGE2, ledger+cache)):
        for entry in records:
            file = entry["file"]
            assert entry["source_revision"] == protocol["source_revision"]
            assert entry["public_url"] == (f"https://huggingface.co/datasets/{protocol['source_repo']}"
                                           f"/resolve/{protocol['source_revision']}/{file}")
            if entry["status"] == "HEAD":
                assert entry["bytes"] == 0
                continue
            body = (folder / entry["path"]).read_bytes()
            assert len(body) == entry["bytes"] and hashlib.sha256(body).hexdigest() == entry["sha256"]
            if entry["status"] not in ("RETAINED", "REUSED"):
                continue
            assert len(body) == entry["end"]-entry["start"]+1
            assert 0 <= entry["start"] <= entry["end"] < censuses[file]["file_bytes"]
            if entry["status"] == "RETAINED":
                assert entry["http_status"] == 206
                assert entry["content_range"] == f"bytes {entry['start']}-{entry['end']}/{censuses[file]['file_bytes']}"
            elif folder == STAGE2:
                original = entry["original_receipt"]
                assert original["sha256"] == entry["sha256"] and original["bytes"] == len(body)
                assert (ROOT / entry["source_asset"]).read_bytes() == body
                assert entry["newly_received_body_bytes"] == 0 and entry["prior_stage"] == "calibration"
                assert any(item.get("sha256") == original["sha256"] and item.get("start") == original["start"]
                           and item["end"] == original["end"] for item in prior_receipts)
            spans[file].append((entry["start"], body))
    prior_bytes = sum(entry["bytes"] for entry in first.json_lines(STAGE1 / "NETWORK.jsonl"))
    new_bytes = sum(entry["bytes"] for entry in ledger)
    assert prior_bytes == protocol["prior_stage_known_body_bytes"] == 12_397_900
    amendment = read(BASE / "BUDGET_AMENDMENT.json")
    assert amendment["supplementary_indices_read_at_amendment"] is False
    assert amendment["scientific_acceptance_changed"] is False and amendment["unlimited_retries"] is False
    assert amendment["known_stage1_body_bytes"] == prior_bytes
    assert new_bytes <= protocol["total_response_body_cap_bytes"] == amendment["remaining_new_supplement_body_cap"] == 15_602_100
    assert prior_bytes+new_bytes <= protocol["combined_calibration_body_cap_bytes"] == amendment["new_combined_calibration_cap"] == 28_000_000
    prefix = first.json_lines(STAGE2 / "METADATA_NETWORK.jsonl")
    assert ledger[:len(prefix)] == prefix
    assert sum(entry["bytes"] for entry in prefix) == protocol["metadata_preparation_body_bytes"]
    return {file: first.RetainedFile(census["file_bytes"], spans[file]) for file, census in censuses.items()}, ledger, new_bytes


def validate_inputs(protocol, censuses, inputs):
    closure = read(HERE / "CLOSURE_CALIBRATION.json")
    for path, record in closure["files"].items():
        assert (ROOT / path).stat().st_size == record["bytes"] and digest(ROOT / path) == record["sha256"]
    assert inputs["prior_stage_closure_sha256"] == digest(STAGE1 / "CLOSURE.json")
    for entry in inputs["inputs"]:
        path = STAGE2 / entry["path"]
        assert path.stat().st_size == entry["bytes"] and digest(path) == entry["sha256"]
        if entry["original_path"] is not None:
            assert path.read_bytes() == (ROOT / entry["original_path"]).read_bytes()
    freeze(STAGE1 / "INDEX_FREEZE.json")
    supplementary = read(STAGE2 / "inputs/SUPPLEMENTARY_SELECTION.json")
    combined = read(STAGE2 / "inputs/SELECTION.json")
    old = read(STAGE1 / "inputs/SELECTION.json")
    assert combined["selected"] == old["selected"]+supplementary["selected"]
    full_cover_freeze = read(STAGE2 / "inputs/INFORMATIVE_V2_FREEZE.json")
    assert full_cover_freeze["new_indices_read"] is False
    for path, expected in full_cover_freeze["sha256"].items():
        assert digest(BASE / path) == expected, path
    amendment = read(BASE / "BUDGET_AMENDMENT.json")
    assert (STAGE2 / "inputs/BUDGET_AMENDMENT.json").read_bytes() == (BASE / "BUDGET_AMENDMENT.json").read_bytes()
    assert amendment["planning_result_sha256"] == digest(BASE / "informative_v2/cost_review/SELECTION.json")
    assert all(sum(group["file"] == file for group in supplementary["selected"]) <= 8 for file in censuses)
    assert protocol["adaptive_design"] is True and protocol["maximum_supplements"] == 1
    assert protocol["forbid_further_expansion_after_failure"] is True
    assert protocol["endpoint"] == read(STAGE1 / "inputs/ENDPOINT.json")
    assert protocol["absolute_tolerance"] == 1e-5
    assert protocol["transform"] == "log1p(stored normalized X) once; no additional normalization"
    old_censuses = read(STAGE1 / "CENSUSES.json")
    assert censuses == old_censuses
    old_groups = read(STAGE1 / "QC_ROWS.json")["groups"]
    groups = read(STAGE2 / "QC_ROWS.json")["groups"]
    assert groups[:len(old_groups)] == old_groups
    assert len(groups) == protocol["selected_conditions"] == len(combined["selected"])
    exclusions = read(STAGE2 / "inputs/EXCLUSIONS.json")
    controls = read(STAGE2 / "inputs/CONTROL_PLAN.json")
    protected_rows = {(group["file"], row) for group in controls["selected"] for row in group["rows"]}
    sample_records = {row["sample"]: row for row in pq.read_table(STAGE2 / "inputs/SAMPLES.parquet").to_pylist()}
    dictionaries = {}
    for file, census in censuses.items():
        for suffix in ("GENES.json", "CODES.npz", "POINTERS.npy", "CENSUS_SEED.json"):
            assert (STAGE2 / f"inputs/{file}_{suffix}").read_bytes() == (STAGE1 / f"inputs/{file}_{suffix}").read_bytes()
        names = read(STAGE2 / f"inputs/{file}_GENES.json")
        assert len(names) == census["source_gene_count"] and all(names.count(gene) == 1 for gene in protocol["endpoint"]["symbols"])
        dictionaries[file] = names
        codes = np.load(STAGE2 / f"inputs/{file}_CODES.npz", allow_pickle=False)
        categories = census["categories"]
        seen = set()
        for group in (group for group in groups if group["file"] == file):
            candidate = [item for item in combined["selected"] if item["file"] == file and item["label"] == group["label"]]
            assert len(candidate) == 1 and candidate[0]["plate"] == group["plate"]
            assert group["label"] not in exclusions["excluded_exact_sentinel_labels"]
            mask = np.ones(census["n_cells"], dtype=bool)
            for column, target in (("drugname_drugconc", group["label"]), ("plate", group["plate"]),
                                   ("cell_line", group["cell_line_id"]), ("pass_filter", "full")):
                mask &= codes[column] == categories[column].index(target)
            rows = [row for row in np.flatnonzero(mask).tolist() if (file, row) not in protected_rows
                    and categories["sample"][int(codes["sample"][row])] not in exclusions["excluded_pooled_sample_ids"]]
            assert rows == group["eligible_rows"] and len(rows) == group["full_qc_available"] >= 50
            assert not seen & set(rows)
            seen.update(rows)
            samples = sorted({categories["sample"][int(codes["sample"][row])] for row in rows})
            assert samples == group["samples"]
            for sample in samples:
                assert sample_records[sample]["plate"] == group["plate"]
                assert sample_records[sample]["drugname_drugconc"] == group["label"]
    return groups, dictionaries


def compact_allocation(file, groups, jobs, presence, protocol):
    occurrences = presence.sum(0).astype(int)
    if (occurrences < 3).any():
        return None, "BLOCKED/NECESSARY_INDEX_SUPPORT_BELOW_THREE", occurrences
    group_by_id = {group["condition_id"]: group for group in groups}
    free = set(range(len(jobs)))
    chosen = {"holdout": [], "discovery": []}
    counts = {role: np.zeros(presence.shape[1], dtype=int) for role in chosen}
    remaining = occurrences.copy()
    for role, target, cap in (("holdout", 1, protocol["maximum_holdout_cells_per_file"]),
                             ("discovery", 2, protocol["maximum_discovery_cells_per_file"])):
        while (counts[role] < target).any():
            ranked = []
            if len(chosen[role]) < cap:
                for index in free:
                    if role == "holdout" and (remaining-presence[index] < 2).any():
                        continue
                    gene_ids = np.flatnonzero(presence[index] & (counts[role] < target))
                    score = sum((Fraction(1, int(occurrences[gene])) for gene in gene_ids), Fraction(0))
                    group = group_by_id[jobs[index]["condition_id"]]
                    key = "|".join((protocol["hash_seed"], file, role, group["label"], ",".join(group["samples"]), str(jobs[index]["row"])))
                    if score > 0:
                        ranked.append((-score, hashlib.sha256(key.encode()).hexdigest(), index))
            if not ranked:
                return None, "BLOCKED/INDEX_ALLOCATION_HEURISTIC_FAILURE", occurrences
            index = min(ranked)[2]
            free.remove(index)
            chosen[role].append(index)
            counts[role] += presence[index]
            remaining[:] -= presence[index]
    output = []
    for group in groups:
        item = dict(group)
        for role in chosen:
            item[f"{role}_rows"] = sorted(jobs[index]["row"] for index in chosen[role]
                                           if jobs[index]["condition_id"] == group["condition_id"])
        output.append(item)
    return output, "INDEX_ALLOCATION_READY", occurrences


def interval_union(spans):
    merged = []
    for start, stop in sorted(spans):
        if merged and start <= merged[-1][1]+1:
            merged[-1] = (merged[-1][0], max(stop, merged[-1][1]))
        else:
            merged.append((start, stop))
    return merged


def uncovered(spans, cached):
    charge = 0
    for start, stop in interval_union(spans):
        cursor = start
        for left, right in interval_union(cached):
            if right < cursor:
                continue
            if left > stop:
                break
            if left > cursor:
                charge += min(left, stop+1)-cursor
            cursor = max(cursor, right+1)
            if cursor > stop:
                break
        charge += max(0, stop-cursor+1)
    return charge


def verify_cost(protocol, censuses, groups):
    cost = read(STAGE2 / "PAIRED_COST.json")
    prefix = first.json_lines(STAGE2 / "INDEX_NETWORK.jsonl") if (STAGE2 / "INDEX_NETWORK.jsonl").exists() else first.json_lines(STAGE2 / "NETWORK.jsonl")
    cached = first.json_lines(STAGE1 / "NETWORK.jsonl")+first.json_lines(STAGE1 / "CACHE_REUSE.jsonl")+prefix
    layouts = read(STAGE2 / "INDEX_LAYOUTS.json")
    values, hvg = 0, 0
    for file in protocol["source_files"]:
        retained_spans = [(entry["start"], entry["end"]) for entry in cached if entry["file"] == file and entry["status"] in ("RETAINED", "REUSED")]
        rows = {row for group in groups if group["file"] == file for row in group["discovery_rows"]+group["holdout_rows"]}
        values += uncovered([tuple(span) for job in layouts[file] if job["row"] in rows for span in job["values"]], retained_spans)
        offset = censuses[file]["layouts"]["obsm/X_hvg"]["offset"]
        hvg += uncovered([(offset+row*8000, offset+(row+1)*8000-1) for row in rows], retained_spans)
    spent = sum(entry["bytes"] for entry in prefix)
    assert cost["known_fresh_body_bytes"] == spent
    assert cost["prior_stage_body_bytes"] == 12_397_900
    assert cost["exact_fresh_selected_value_bytes"] == values
    assert cost["exact_fresh_selected_HVG_bytes"] == hvg
    assert cost["projected_combined_body_bytes"] == 12_397_900+spent+values+hvg
    assert cost["combined_cap_bytes"] == protocol["combined_calibration_body_cap_bytes"]
    assert cost["fits"] == (spent+values+hvg <= protocol["total_response_body_cap_bytes"])
    return cost


def reconstruct_screen(protocol, censuses, sources, dictionaries, groups, ledger):
    layouts = read(STAGE2 / "INDEX_LAYOUTS.json")
    old_layouts = read(STAGE1 / "INDEX_LAYOUTS.json")
    recorded = read(STAGE2 / "INDEX_RESULTS.json")
    selected, summaries = [], []
    for file in protocol["source_files"]:
        names = dictionaries[file]
        gene_ids = [names.index(gene) for gene in protocol["endpoint"]["symbols"]]
        jobs = layouts[file]
        assert jobs[:len(old_layouts[file])] == old_layouts[file]
        file_groups = [group for group in groups if group["file"] == file]
        assert [(row, group["condition_id"]) for group in file_groups for row in group["eligible_rows"]] == [
            (job["row"], job["condition_id"]) for job in jobs]
        presence, permitted_indices, permitted_values = [], [], []
        with h5py.File(sources[file], "r") as h5:
            for job in jobs:
                start, stop = map(int, first.extract(sources[file], h5["X/indptr"], job["row"], job["row"]+2))
                columns = first.extract(sources[file], h5["X/indices"], start, stop)
                assert len(columns) == job["nnz"] == stop-start == len(np.unique(columns))
                assert ((columns >= 0) & (columns < len(names))).all()
                index_spans = first.spans_for(h5["X/indices"], start, stop)
                value_spans = first.spans_for(h5["X/data"], start, stop)
                assert index_spans == [tuple(span) for span in job["indices"]]
                assert value_spans == [tuple(span) for span in job["values"]]
                permitted_indices.extend(index_spans)
                permitted_values.extend(value_spans)
                presence.append(np.isin(gene_ids, columns))
            hvg = h5["obsm/X_hvg"]
            assert hvg.chunks is None
            offset = hvg.id.get_offset()
            prohibited = permitted_values+[(offset, offset+hvg.size*hvg.dtype.itemsize-1)]
            for entry in ledger:
                if entry["file"] != file or entry["status"] != "RETAINED":
                    continue
                if entry["stage"] == "metadata":
                    assert all(entry["end"] < start or entry["start"] > stop for start, stop in prohibited)
                elif entry["stage"] == "index_screen":
                    assert entry["purpose"] == "index_screen_CSR_indices"
                    assert first.covered_interval(entry["start"], entry["end"], permitted_indices)
        presence = np.asarray(presence)
        cached = np.load(STAGE2 / f"{file}_PRESENCE.npz", allow_pickle=False)
        np.testing.assert_array_equal(cached["rows"], [job["row"] for job in jobs])
        np.testing.assert_array_equal(cached["presence"], presence)
        np.testing.assert_array_equal(cached["source_gene_indices"], gene_ids)
        old_presence = np.load(STAGE1 / f"{file}_PRESENCE.npz", allow_pickle=False)
        np.testing.assert_array_equal(presence[:len(old_layouts[file])], old_presence["presence"])
        chosen, status, occurrences = compact_allocation(file, file_groups, jobs, presence, protocol)
        observed = next(item for item in recorded["files"] if item["file"] == file)
        assert status == observed["status"] and occurrences.tolist() == observed["index_occurrences_per_gene"]
        assert observed["necessary_support_count_below_three"] == np.flatnonzero(occurrences < 3).tolist()
        if chosen is not None:
            for role in ("discovery", "holdout"):
                chosen_rows = {row for group in chosen for row in group[f"{role}_rows"]}
                assert observed[f"{role}_index_coverage"] == presence[[job["row"] in chosen_rows for job in jobs]].sum(0).tolist()
            selected.extend(chosen)
        summaries.append(dict(file=file, screened_cells=len(jobs), status=status, index_occurrences_per_gene=occurrences.tolist()))
    ready = all(summary["status"] == "INDEX_ALLOCATION_READY" for summary in summaries)
    assert recorded["status"] == ("READY_FOR_PAIRED_FREEZE" if ready else "BLOCKED/INDEX_INFORMATION")
    assert recorded["screened_calibration_cells"] == sum(summary["screened_cells"] for summary in summaries)
    assert recorded["raw_values_read"] is False and recorded["X_hvg_read"] is False
    if ready and (STAGE2 / "PAIR_FREEZE.json").exists():
        manifest = read(STAGE2 / "ROW_MANIFEST.json")
        assert manifest["groups"] == selected
        assert manifest["selected_cells"] == sum(len(group["discovery_rows"])+len(group["holdout_rows"]) for group in selected) <= 256
    elif not ready:
        assert not (STAGE2 / "PAIR_FREEZE.json").exists()
    return ready, selected, summaries


def verify():
    frozen = freeze(STAGE2 / "INDEX_FREEZE.json")
    assert frozen["expression_values_and_HVG_read"] is False
    parent_review = read(ROOT / "outputs/decision_value/AXIS_RECOVERY_V2_INDEX_REVIEW.json")
    assert parent_review["status"] == "PASS_PARENT_INDEX_PREFLIGHT"
    assert parent_review["freeze_sha256"] == digest(STAGE2 / "INDEX_FREEZE.json")
    assert parent_review["budget_reconciliation_sha256"] == digest(STAGE2 / "BUDGET_RECONCILIATION.json")
    assert parent_review["new_indices_seen"] is False and parent_review["values_or_HVG_seen"] is False
    assert parent_review["index_execution_authorized"] is True and parent_review["expression_read_authorized"] is False
    protocol, censuses = read(STAGE2 / "PROTOCOL.json"), read(STAGE2 / "CENSUSES.json")
    assert protocol["source_files"] == ["c44.h5ad", "c45.h5ad"]
    groups, names = validate_inputs(protocol, censuses, read(STAGE2 / "SOURCES.json"))
    sources, ledger, new_bytes = retained(protocol, censuses)
    ready, selected, screen = reconstruct_screen(protocol, censuses, sources, names, groups, ledger)
    paired, certified = [], False
    if ready:
        cost = verify_cost(protocol, censuses, selected)
    if (STAGE2 / "PAIR_FREEZE.json").exists():
        assert ready and cost["fits"]
        frozen = freeze(STAGE2 / "PAIR_FREEZE.json")
        assert frozen["raw_values_and_HVG_read"] is False
        assert frozen["index_screen_freeze_sha256"] == digest(STAGE2 / "INDEX_FREEZE.json")
        prefix = first.json_lines(STAGE2 / "INDEX_NETWORK.jsonl")
        assert ledger[:len(prefix)] == prefix
        assert all(entry["stage"] in ("metadata", "index_screen") for entry in prefix)
        paired_review = read(ROOT / "outputs/decision_value/AXIS_RECOVERY_V2_PAIRED_REVIEW.json")
        assert paired_review["status"] == "PASS_PARENT_PAIRED_PREFLIGHT"
        first.CALIBRATION = STAGE2
        paired, certified = first.reconstruct_paired(protocol, censuses, sources, names, selected, ledger)
        result = read(STAGE2 / "RESULTS.json")
        assert result["actual_new_body_bytes"] == new_bytes
        assert result["combined_calibration_body_bytes"] == 12_397_900+new_bytes
    else:
        assert all(entry["stage"] in ("metadata", "index_screen") for entry in ledger)
        if ready:
            assert cost["fits"] is False and read(STAGE2 / "PAIR_BLOCKED.json")["status"] == "BLOCKED/COMPACT_PAIRED_BODY_CAP"
    verdict = dict(schema="independent_single_adaptive_calibration_reconstruction_v1",
        status="PASS_INDEPENDENT_OFFLINE_RECONSTRUCTION", screened=screen, paired=paired,
        file_local_endpoint39_verified=certified, first_stage_known_body_bytes=12_397_900,
        second_stage_new_body_bytes=new_bytes, combined_calibration_body_bytes=12_397_900+new_bytes,
        combined_body_cap_bytes=protocol["combined_calibration_body_cap_bytes"],
        budget_amendment_sha256=digest(BASE / "BUDGET_AMENDMENT.json"),
        parent_index_review_sha256=digest(ROOT / "outputs/decision_value/AXIS_RECOVERY_V2_INDEX_REVIEW.json"),
        selected_paired_cells=sum(len(group["discovery_rows"])+len(group["holdout_rows"]) for group in selected) if paired else 0,
        maximum_supplements=1, new_network_requests=0, producer_imports=False,
        index_presence_selection_recomputed=True, all_source_gene_matching_recomputed=bool(paired),
        old250_noise_study_released=False, full2000_axis_certified=False, STATE_checkpoint_axis_certified=False,
        independent_culture_validation=False, decision_gain=None, verifier_sha256=digest(Path(__file__)),
        independent_helper_sha256=digest(HERE / "calibration_verify.py"))
    if paired:
        verdict["axis_artifact_sha256"] = {name: digest(STAGE2 / name) for name in (
            "PROTOCOL.json", "INDEX_FREEZE.json", "PAIR_FREEZE.json", "ROW_MANIFEST.json", "RESULTS.json", "CERTIFICATE.json")}
    with (HERE / "CALIBRATION_V2_VERIFIED.json").open("x", encoding="utf-8") as stream:
        json.dump(verdict, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(verdict))
    return verdict


if __name__ == "__main__":
    verify()
