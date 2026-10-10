"""Independent, offline reconstruction of finite paired axis calibration."""
import hashlib
import io
import json
from fractions import Fraction
from pathlib import Path

import h5py
import numpy as np
import pyarrow.parquet as pq


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CALIBRATION = HERE.parent / "calibration"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RetainedFile(io.RawIOBase):
    """Read received immutable spans only, without a producer or network import."""

    def __init__(self, size, spans):
        self.size, self.position = size, 0
        self.spans = sorted(spans, key=lambda span: span[0])

    def at(self, first, last):
        if not 0 <= first <= last <= self.size:
            raise ValueError("out_of_bounds_source_range")
        parts, cursor = [], first
        for start, body in self.spans:
            if start > cursor:
                break
            stop = min(last, start + len(body))
            if stop > cursor:
                parts.append(body[cursor-start:stop-start])
                cursor = stop
            if cursor == last:
                return b"".join(parts)
        if first == last:
            return b""
        raise ValueError("unretained_source_range")

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        return self.position

    def readinto(self, buffer):
        length = min(len(buffer), self.size - self.position)
        buffer[:length] = self.at(self.position, self.position + length)
        self.position += length
        return length


def extract(source, dataset, first, last):
    assert dataset.compression is None and not dataset.shuffle and not dataset.fletcher32
    assert dataset.scaleoffset is None
    assert 0 <= first <= last <= dataset.shape[0]
    width = dataset.dtype.itemsize
    if dataset.chunks is None:
        offset = dataset.id.get_offset()
        return np.frombuffer(source.at(offset+first*width, offset+last*width), dtype=dataset.dtype)
    parts, cursor = [], first
    while cursor < last:
        origin = cursor // dataset.chunks[0] * dataset.chunks[0]
        info = dataset.id.get_chunk_info_by_coord((origin,))
        assert info.filter_mask == 0 and info.byte_offset is not None
        stop = min(last, origin+dataset.chunks[0])
        parts.append(source.at(info.byte_offset+(cursor-origin)*width,
                               info.byte_offset+(stop-origin)*width))
        cursor = stop
    return np.frombuffer(b"".join(parts), dtype=dataset.dtype)


def spans_for(dataset, first, last):
    width = dataset.dtype.itemsize
    if dataset.chunks is None:
        offset = dataset.id.get_offset()
        return [(offset+first*width, offset+last*width-1)]
    spans, cursor = [], first
    while cursor < last:
        origin = cursor // dataset.chunks[0] * dataset.chunks[0]
        info = dataset.id.get_chunk_info_by_coord((origin,))
        assert info.filter_mask == 0 and info.byte_offset is not None
        stop = min(last, origin+dataset.chunks[0])
        spans.append((info.byte_offset+(cursor-origin)*width, info.byte_offset+(stop-origin)*width-1))
        cursor = stop
    return spans


def covered_interval(first, last, intervals):
    cursor = first
    for start, stop in sorted(intervals):
        if start > cursor:
            break
        cursor = max(cursor, stop+1)
        if cursor > last:
            return True
    return False


def certify_coordinate(names, discovery, heldout, trajectory, heldout_trajectory, expected, tolerance):
    """Discovery searches every source gene; heldout must independently be informative."""
    assert discovery.shape[1] == heldout.shape[1] == len(names)
    assert discovery.shape[0] == len(trajectory) and heldout.shape[0] == len(heldout_trajectory)
    assert np.isfinite(discovery).all() and np.isfinite(heldout).all()
    assert np.isfinite(trajectory).all() and np.isfinite(heldout_trajectory).all()
    matches = []
    for first in range(0, len(names), 4096):
        differences = np.max(np.abs(discovery[:, first:first+4096]-trajectory[:, None]), axis=0)
        matches.extend((np.flatnonzero(differences <= tolerance)+first).tolist())
    index = matches[0] if len(matches) == 1 else None
    nonzero = int((np.abs(trajectory) > tolerance).sum())
    duplicates = names.count(expected)
    discovery_pass = (index is not None and names[index] == expected and duplicates == 1 and nonzero >= 2)
    heldout_nonzero = int((np.abs(heldout_trajectory) > tolerance).sum())
    if index is not None:
        heldout_error = float(np.max(np.abs(heldout[:, index]-heldout_trajectory)))
        discovery_error = float(np.max(np.abs(discovery[:, index]-trajectory)))
        heldout_pass = heldout_error <= tolerance and heldout_nonzero >= 1
    else:
        discovery_error, heldout_error, heldout_pass = None, None, False
    return dict(matching_raw_gene_count=len(matches), unique_raw_gene_index=index,
                expected_symbol=expected, raw_source_symbol_duplicate_count=duplicates,
                discovery_nonzero_cells=nonzero, discovery_pass=discovery_pass,
                discovery_maximum_absolute_error=discovery_error,
                heldout_maximum_absolute_error=heldout_error, heldout_nonzero_cells=heldout_nonzero,
                heldout_pass=heldout_pass, passed=bool(discovery_pass and heldout_pass))


def validate_groups(groups, exclusions, protected_rows):
    """Exclusions apply across all cell lines and discovery/holdout source roles."""
    seen = set()
    for group in groups:
        assert group["label"] not in exclusions["excluded_exact_sentinel_labels"]
        assert group["sample"] not in exclusions["excluded_pooled_sample_ids"]
        assert group["role"] in ("discovery", "holdout")
        assert len(group["rows"]) == len(set(group["rows"])) == 16
        for row in group["rows"]:
            unit = (group["file"], row)
            assert unit not in seen and unit not in protected_rows
            seen.add(unit)
    return seen


def json_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def retained_sources(protocol, censuses):
    ledger = json_lines(CALIBRATION / "NETWORK.jsonl")
    reused = json_lines(CALIBRATION / "CACHE_REUSE.jsonl")
    spans = {file: [] for file in censuses}
    for entry in ledger + reused:
        file = entry["file"]
        assert file in censuses and entry["source_revision"] == protocol["source_revision"]
        assert entry["public_url"] == (f"https://huggingface.co/datasets/{protocol['source_repo']}"
            f"/resolve/{protocol['source_revision']}/{file}")
        if entry["status"] == "HEAD":
            assert entry["bytes"] == 0
            continue
        body = (CALIBRATION / entry["path"]).read_bytes()
        assert len(body) == entry["bytes"] and hashlib.sha256(body).hexdigest() == entry["sha256"]
        if entry["status"] not in ("RETAINED", "REUSED"):
            continue
        assert len(body) == entry["end"]-entry["start"]+1
        assert 0 <= entry["start"] <= entry["end"] < censuses[file]["file_bytes"]
        if entry["status"] == "RETAINED":
            assert entry["http_status"] == 206
            assert entry["content_range"] == f"bytes {entry['start']}-{entry['end']}/{censuses[file]['file_bytes']}"
        else:
            original = entry["original_receipt"]
            assert entry["newly_received_body_bytes"] == 0
            assert original["file"] == file and original["sha256"] == entry["sha256"]
            assert original["start"] == entry["start"] and original["end"] == entry["end"]
            assert (ROOT / entry["source_asset"]).read_bytes() == body
            assert entry["start"] <= entry["requested_subspan"][0] <= entry["requested_subspan"][1] <= entry["end"]
        spans[file].append((entry["start"], body))
    received = sum(entry["bytes"] for entry in ledger)
    assert received <= protocol["total_response_body_cap_bytes"] == 25_000_000
    prefix = json_lines(CALIBRATION / "METADATA_NETWORK.jsonl")
    assert ledger[:len(prefix)] == prefix
    assert sum(entry["bytes"] for entry in prefix) == protocol["metadata_preparation_body_bytes"]
    return {file: RetainedFile(census["file_bytes"], spans[file]) for file, census in censuses.items()}, received, ledger


def reconstruct_metadata(protocol, censuses, sources, inputs, groups, ledger):
    """Rejoin actual source codes and source-sample identities, independently."""
    for entry in inputs["inputs"]:
        path = CALIBRATION / entry["path"]
        assert path.stat().st_size == entry["bytes"] and digest(path) == entry["sha256"]
        assert (ROOT / entry["original_path"]).read_bytes() == path.read_bytes()
    exclusions = read(CALIBRATION / "inputs/EXCLUSIONS.json")
    protected = read(CALIBRATION / "inputs/CONTROL_PLAN.json")
    protected_rows = {(group["file"], row) for group in protected["selected"] for row in group["rows"]}
    selection = read(CALIBRATION / "inputs/SELECTION.json")
    sample_records = {entry["sample"]: entry for entry in pq.read_table(CALIBRATION / "inputs/SAMPLES.parquet").to_pylist()}
    endpoint = read(CALIBRATION / "inputs/ENDPOINT.json")
    assert protocol["endpoint"] == endpoint
    assert protocol["absolute_tolerance"] == 1e-5
    assert protocol["discovery_min_nonzero"] == 2 and protocol["holdout_min_nonzero"] == 1
    assert protocol["transform"] == "log1p(stored normalized X) once; no additional normalization"
    dictionaries, row_metadata = {}, {}
    for file, census in censuses.items():
        source = sources[file]
        seed_entry = inputs["census_seeds"][file]
        assert digest(CALIBRATION / seed_entry["path"]) == seed_entry["sha256"]
        seed = read(CALIBRATION / seed_entry["path"])
        assert seed["revision"] == census["source_revision"] == protocol["source_revision"]
        assert seed["file_bytes"] == census["file_bytes"] and seed["n_cells"] == census["n_cells"]
        with h5py.File(source, "r") as h5:
            known_expression = []
            dataset = h5["obsm/X_hvg"]
            assert dataset.chunks is None
            offset = dataset.id.get_offset()
            known_expression.append((offset, offset+dataset.size*dataset.dtype.itemsize-1))
            state_layout = seed.get("layouts", {}).get("obsm/X_state")
            if state_layout and state_layout.get("offset") is not None:
                known_expression.append((state_layout["offset"], state_layout["offset"]+state_layout["storage_bytes"]-1))
            names = [name.decode() if isinstance(name, bytes) else str(name) for name in h5["var/gene_name"][:]]
            gene_entry = inputs["gene_dictionaries"][file]
            assert digest(CALIBRATION / gene_entry["path"]) == gene_entry["sha256"]
            assert names == read(CALIBRATION / gene_entry["path"])
            assert len(names) == gene_entry["count"] == census["source_gene_count"]
            assert all(names.count(symbol) == 1 for symbol in endpoint["symbols"])
            assert h5["X"].attrs["shape"].tolist() == [census["n_cells"], len(names)]
            dictionaries[file] = names
            code_entry = inputs["code_arrays"][file]
            assert digest(CALIBRATION / code_entry["path"]) == code_entry["sha256"]
            saved_codes = np.load(CALIBRATION / code_entry["path"], allow_pickle=False)
            categories, codes = {}, {}
            for column in ("drugname_drugconc", "plate", "sample", "pass_filter", "cell_name", "cell_line"):
                categories[column] = [name.decode() if isinstance(name, bytes) else str(name)
                                      for name in h5[f"obs/{column}/categories"][:]]
                assert categories[column] == census["categories"][column] == seed["categories"][column]
                dataset = h5[f"obs/{column}/codes"]
                values = extract(source, dataset, 0, census["n_cells"])
                assert hashlib.sha256(values.tobytes()).hexdigest() == seed["codes_sha256"][column]
                np.testing.assert_array_equal(values, saved_codes[column])
                codes[column] = values
            pointer = extract(source, h5["X/indptr"], 0, census["n_cells"]+1)
            assert np.all(np.diff(pointer) >= 0) and pointer[0] == 0
            assert pointer[-1] == h5["X/indices"].shape[0] == h5["X/data"].shape[0]
            assert digest(CALIBRATION / census["pointer_path"]) == census["pointer_sha256"]
            np.testing.assert_array_equal(pointer, np.load(CALIBRATION / census["pointer_path"], allow_pickle=False))
            for group in (group for group in groups if group["file"] == file):
                planned = [candidate for candidate in selection["selected"]
                           if candidate["file"] == file and candidate["label"] == group["label"]]
                assert len(planned) == 1 and planned[0]["plate"] == group["plate"]
                assert planned[0]["cell_line_id"] == group["cell_line_id"]
                assert group["label"] not in exclusions["excluded_exact_sentinel_labels"]
                mask = np.ones(census["n_cells"], dtype=bool)
                for column, target in (("drugname_drugconc", group["label"]), ("plate", group["plate"]),
                                       ("cell_line", group["cell_line_id"]), ("pass_filter", "full")):
                    mask &= codes[column] == categories[column].index(target)
                eligible = []
                for row in np.flatnonzero(mask).tolist():
                    assert codes["sample"][row] >= 0 and codes["cell_name"][row] >= 0
                    sample = categories["sample"][int(codes["sample"][row])]
                    if sample in exclusions["excluded_pooled_sample_ids"] or (file, row) in protected_rows:
                        continue
                    eligible.append(row)
                    row_metadata[(file, row)] = dict(sample=sample, label=group["label"], condition_id=group["condition_id"],
                        cell_name=categories["cell_name"][int(codes["cell_name"][row])])
                assert eligible == group["eligible_rows"] and len(eligible) == group["full_qc_available"] >= 50
                layout_jobs = read(CALIBRATION / "INDEX_LAYOUTS.json")[file]
                known_expression.extend(tuple(span) for job in layout_jobs for span in job["values"])
                samples = sorted({row_metadata[(file, row)]["sample"] for row in eligible})
                assert samples == group["samples"] == sorted(planned[0]["official_pooled_sample_ids"])
                for sample in samples:
                    assert sample_records[sample]["plate"] == group["plate"]
                    assert sample_records[sample]["drugname_drugconc"] == group["label"]
            for entry in ledger:
                if entry["file"] == file and entry["stage"] == "metadata" and entry["status"] == "RETAINED":
                    assert all(entry["end"] < start or entry["start"] > stop for start, stop in known_expression)
    return dictionaries, row_metadata, protected_rows, exclusions


def allocate_rows(file, groups, jobs, presence, protocol):
    """Independently reconstruct frozen rare-cover allocation using exact scores."""
    occurrences = presence.sum(0).astype(int)
    if (occurrences < 3).any():
        return None, "BLOCKED/NECESSARY_INDEX_SUPPORT_BELOW_THREE", occurrences
    group_by_id = {group["condition_id"]: group for group in groups}
    free = set(range(len(jobs)))
    selected = {"discovery": [], "holdout": []}
    coverage = {role: np.zeros(presence.shape[1], dtype=int) for role in selected}
    used = {(role, group["condition_id"]): 0 for role in selected for group in groups}
    remaining = occurrences.copy()

    def ordering(index, role):
        job = jobs[index]
        group = group_by_id[job["condition_id"]]
        key = "|".join((protocol["hash_seed"], file, role, group["label"], ",".join(group["samples"]), str(job["row"])))
        return hashlib.sha256(key.encode()).hexdigest()

    def reserve(index, role):
        free.remove(index)
        selected[role].append(index)
        coverage[role] += presence[index]
        remaining[:] -= presence[index]
        used[(role, jobs[index]["condition_id"])] += 1

    for role, target in (("holdout", 1), ("discovery", 2)):
        while (coverage[role] < target).any():
            choices = []
            for index in free:
                if used[(role, jobs[index]["condition_id"])] == 16:
                    continue
                if role == "holdout" and (remaining-presence[index] < 2).any():
                    continue
                required = np.flatnonzero(presence[index] & (coverage[role] < target))
                score = sum((Fraction(1, int(occurrences[gene])) for gene in required), Fraction(0))
                if score > 0:
                    choices.append((-score, ordering(index, role), index))
            if not choices:
                return None, "BLOCKED/INDEX_ALLOCATION_HEURISTIC_FAILURE", occurrences
            reserve(min(choices)[2], role)
    for role in ("discovery", "holdout"):
        for group in groups:
            choices = sorted((index for index in free if jobs[index]["condition_id"] == group["condition_id"]),
                             key=lambda index: ordering(index, role))
            required = 16-used[(role, group["condition_id"])]
            assert len(choices) >= required
            for index in choices[:required]:
                reserve(index, role)
    output = []
    for group in groups:
        item = dict(group)
        for role in selected:
            item[f"{role}_rows"] = sorted(jobs[index]["row"] for index in selected[role]
                                           if jobs[index]["condition_id"] == group["condition_id"])
        output.append(item)
    return output, "INDEX_ALLOCATION_READY", occurrences


def reconstruct_index_screen(protocol, censuses, sources, dictionaries, groups, ledger):
    layouts = read(CALIBRATION / "INDEX_LAYOUTS.json")
    recorded = read(CALIBRATION / "INDEX_RESULTS.json")
    selected, summaries = [], []
    for file in protocol["source_files"]:
        names = dictionaries[file]
        gene_indices = [names.index(symbol) for symbol in protocol["endpoint"]["symbols"]]
        file_groups = [group for group in groups if group["file"] == file]
        expected_jobs = [(row, group["condition_id"]) for group in file_groups for row in group["eligible_rows"]]
        jobs = layouts[file]
        assert expected_jobs == [(job["row"], job["condition_id"]) for job in jobs]
        presence = []
        with h5py.File(sources[file], "r") as h5:
            permitted = []
            for job in jobs:
                first, last = map(int, extract(sources[file], h5["X/indptr"], job["row"], job["row"]+2))
                intervals = spans_for(h5["X/indices"], first, last)
                assert intervals == [tuple(span) for span in job["indices"]]
                assert spans_for(h5["X/data"], first, last) == [tuple(span) for span in job["values"]]
                permitted.extend(intervals)
                columns = extract(sources[file], h5["X/indices"], first, last)
                assert len(columns) == last-first == job["nnz"] == len(np.unique(columns))
                assert ((columns >= 0) & (columns < len(names))).all()
                presence.append(np.isin(gene_indices, columns))
            for entry in ledger:
                if entry["file"] == file and entry["stage"] == "index_screen" and entry["status"] == "RETAINED":
                    assert entry["purpose"] == "index_screen_CSR_indices"
                    assert covered_interval(entry["start"], entry["end"], permitted)
        presence = np.asarray(presence, dtype=bool)
        saved = np.load(CALIBRATION / f"{file}_PRESENCE.npz", allow_pickle=False)
        assert set(saved.files) == {"rows", "presence", "source_gene_indices"}
        np.testing.assert_array_equal(saved["rows"], [job["row"] for job in jobs])
        np.testing.assert_array_equal(saved["presence"], presence)
        np.testing.assert_array_equal(saved["source_gene_indices"], gene_indices)
        chosen, status, counts = allocate_rows(file, file_groups, jobs, presence, protocol)
        observed = next(item for item in recorded["files"] if item["file"] == file)
        assert observed["status"] == status and observed["index_occurrences_per_gene"] == counts.tolist()
        assert observed["necessary_support_count_below_three"] == np.flatnonzero(counts < 3).tolist()
        if chosen is not None:
            for role in ("discovery", "holdout"):
                rows = {row for group in chosen for row in group[f"{role}_rows"]}
                mask = [job["row"] in rows for job in jobs]
                assert observed[f"{role}_index_coverage"] == presence[mask].sum(0).tolist()
            selected.extend(chosen)
        summaries.append(dict(file=file, status=status, screened_cells=len(jobs), index_occurrences_per_gene=counts.tolist()))
    ready = all(summary["status"] == "INDEX_ALLOCATION_READY" for summary in summaries)
    assert recorded["status"] == ("READY_FOR_PAIRED_FREEZE" if ready else "BLOCKED/INDEX_INFORMATION")
    assert recorded["screened_calibration_cells"] == sum(summary["screened_cells"] for summary in summaries)
    assert recorded["raw_values_read"] is False and recorded["X_hvg_read"] is False
    if ready:
        manifest = read(CALIBRATION / "ROW_MANIFEST.json")
        assert manifest["groups"] == selected
        assert manifest["selected_cells"] == 32*len(selected) <= protocol["max_paired_cells"] == 256
    else:
        assert not (CALIBRATION / "PAIR_FREEZE.json").exists()
    return ready, selected, summaries


def reconstruct_paired(protocol, censuses, sources, dictionaries, groups, ledger):
    result = read(CALIBRATION / "RESULTS.json")
    certificate = read(CALIBRATION / "CERTIFICATE.json")
    assert result["error"] is None
    assert [item["file"] for item in result["files"]] == protocol["source_files"]
    summaries = []
    for file in protocol["source_files"]:
        names = dictionaries[file]
        discovery_rows = sorted(row for group in groups if group["file"] == file for row in group["discovery_rows"])
        heldout_rows = sorted(row for group in groups if group["file"] == file for row in group["holdout_rows"])
        assert not set(discovery_rows) & set(heldout_rows)
        rows = sorted(discovery_rows+heldout_rows)
        assert len(rows) == len(set(rows))
        observed = next(item for item in result["files"] if item["file"] == file)
        assert observed["discovery_rows"] == discovery_rows and observed["holdout_rows"] == heldout_rows
        assert observed["discovery_cells"] == len(discovery_rows) and observed["holdout_cells"] == len(heldout_rows)
        assert observed["source_gene_count"] == len(names)
        vectors, stored = [], []
        with h5py.File(sources[file], "r") as h5:
            dataset = h5["obsm/X_hvg"]
            assert dataset.chunks is None and dataset.compression is None
            assert dataset.shape == (censuses[file]["n_cells"], 2000) and dataset.dtype.str == "<f4"
            offset = dataset.id.get_offset()
            assert offset == censuses[file]["layouts"]["obsm/X_hvg"]["offset"]
            permitted_values = []
            for row in rows:
                first, last = map(int, extract(sources[file], h5["X/indptr"], row, row+2))
                columns = extract(sources[file], h5["X/indices"], first, last)
                values = extract(sources[file], h5["X/data"], first, last)
                permitted_values.extend(spans_for(h5["X/data"], first, last))
                assert len(columns) == len(values) == len(np.unique(columns))
                assert ((columns >= 0) & (columns < len(names))).all()
                assert np.isfinite(values).all() and (values >= 0).all()
                dense = np.zeros(len(names))
                dense[columns] = values
                vectors.append(np.log1p(dense))
                vector = np.frombuffer(sources[file].at(offset+row*8000, offset+(row+1)*8000), dtype="<f4")
                assert len(vector) == 2000 and np.isfinite(vector).all() and (vector >= 0).all()
                stored.append(vector)
            permitted_hvg = [(offset+row*8000, offset+(row+1)*8000-1) for row in rows]
            for entry in ledger:
                if entry["file"] == file and entry["stage"] == "expression" and entry["status"] == "RETAINED":
                    assert entry["purpose"] in ("expression_selected_CSR_values", "expression_selected_complete_X_hvg")
                    permitted = permitted_values if entry["purpose"] == "expression_selected_CSR_values" else permitted_hvg
                    assert covered_interval(entry["start"], entry["end"], permitted)
        vectors, stored = np.asarray(vectors), np.asarray(stored)
        d = [rows.index(row) for row in discovery_rows]
        h = [rows.index(row) for row in heldout_rows]
        records = []
        assert len(observed["endpoint_records"]) == 39
        for coordinate, symbol, original in zip(protocol["endpoint"]["coordinates"], protocol["endpoint"]["symbols"], observed["endpoint_records"]):
            reconstructed = certify_coordinate(names, vectors[d], vectors[h], stored[d, coordinate],
                                               stored[h, coordinate], symbol, protocol["absolute_tolerance"])
            assert original["coordinate"] == coordinate and original["expected_symbol"] == symbol
            comparisons = {
                "discovery_matching_source_gene_count": "matching_raw_gene_count",
                "discovery_unique_source_gene_index": "unique_raw_gene_index",
                "source_symbol_duplicate_count": "raw_source_symbol_duplicate_count",
                "discovery_nonzero_cells": "discovery_nonzero_cells",
                "holdout_nonzero_cells": "heldout_nonzero_cells",
                "discovery_max_abs_mismatch": "discovery_maximum_absolute_error",
                "holdout_max_abs_mismatch": "heldout_maximum_absolute_error",
                "discovery_passed": "discovery_pass", "holdout_passed": "heldout_pass", "passed": "passed",
            }
            for producer_key, independent_key in comparisons.items():
                value = reconstructed[independent_key]
                if value is None:
                    assert original[producer_key] is None
                elif isinstance(value, float):
                    np.testing.assert_allclose(original[producer_key], value, rtol=1e-12, atol=1e-14)
                else:
                    assert original[producer_key] == value
            index = reconstructed["unique_raw_gene_index"]
            assert original["discovery_source_symbol"] == (names[index] if index is not None else None)
            records.append(dict(coordinate=coordinate, **reconstructed))
        passed = all(record["passed"] for record in records)
        assert observed["passed"] == passed
        summaries.append(dict(file=file, discovery_cells=len(d), holdout_cells=len(h), source_genes=len(names),
                              passed_coordinates=sum(record["passed"] for record in records), passed=passed,
                              failed_symbols=[record["expected_symbol"] for record in records if not record["passed"]]))
    certified = all(summary["passed"] for summary in summaries)
    status = "PASS/FILE_LOCAL_ENDPOINT39" if certified else "BLOCKED/INSUFFICIENT_COORDINATE_INFORMATION"
    assert result["status"] == certificate["status"] == status
    assert certificate["endpoint39_verified"] == certified
    assert certificate["per_file_endpoint39_verified"] == {summary["file"]: summary["passed"] for summary in summaries}
    assert certificate["source_revision"] == protocol["source_revision"] and certificate["source_files"] == protocol["source_files"]
    for field, filename in (("index_freeze_sha256", "INDEX_FREEZE.json"), ("paired_freeze_sha256", "PAIR_FREEZE.json"),
                            ("results_sha256", "RESULTS.json"), ("endpoint_sha256", "inputs/ENDPOINT.json")):
        assert certificate[field] == digest(CALIBRATION / filename)
    assert result["full2000_axis_certified"] is False and result["STATE_checkpoint_axis_certified"] is False
    assert result["decision_effectiveness_test"] is False and result["old250_noise_rows_read"] is False
    assert result["P06_sentinel_RNA_read"] is False and certificate["STATE_checkpoint_axis_certified"] is False
    return summaries, certified


def verify():
    protocol = read(CALIBRATION / "PROTOCOL.json")
    censuses = read(CALIBRATION / "CENSUSES.json")
    inputs = read(CALIBRATION / "SOURCES.json")
    frozen = read(CALIBRATION / "INDEX_FREEZE.json")
    assert frozen["expression_values_and_HVG_read"] is False
    for path, expected in frozen["sha256"].items():
        assert digest(CALIBRATION / path) == expected, path
    assert protocol["source_files"] == ["c44.h5ad", "c45.h5ad"]
    sources, received, ledger = retained_sources(protocol, censuses)
    groups = read(CALIBRATION / "QC_ROWS.json")["groups"]
    assert len(groups) == protocol["selected_conditions"] <= 8
    assert all(sum(group["file"] == file for group in groups) <= 4 for file in protocol["source_files"])
    dictionaries, _, _, _ = reconstruct_metadata(protocol, censuses, sources, inputs, groups, ledger)
    ready, selected, screen = reconstruct_index_screen(protocol, censuses, sources, dictionaries, groups, ledger)
    paired, certified = [], False
    if ready:
        paired_freeze = read(CALIBRATION / "PAIR_FREEZE.json")
        assert paired_freeze["raw_values_and_HVG_read"] is False
        assert paired_freeze["index_screen_freeze_sha256"] == digest(CALIBRATION / "INDEX_FREEZE.json")
        for path, expected in paired_freeze["sha256"].items():
            assert digest(CALIBRATION / path) == expected, path
        prefix = json_lines(CALIBRATION / "INDEX_NETWORK.jsonl")
        assert ledger[:len(prefix)] == prefix
        assert all(entry["stage"] in ("metadata", "index_screen") for entry in prefix)
        paired, certified = reconstruct_paired(protocol, censuses, sources, dictionaries, selected, ledger)
        assert read(CALIBRATION / "RESULTS.json")["actual_new_body_bytes"] == received
    else:
        assert all(entry["stage"] in ("metadata", "index_screen") for entry in ledger)
    verdict = dict(schema="independent_finite_axis_calibration_reconstruction_v1",
        status="PASS_INDEPENDENT_OFFLINE_RECONSTRUCTION", source_revision=protocol["source_revision"],
        screened=screen, paired=paired, file_local_endpoint39_verified=certified,
        actual_new_body_bytes=received, body_cap_bytes=protocol["total_response_body_cap_bytes"],
        new_network_requests=0, producer_imports=False, selected_paired_cells=32*len(selected) if ready else 0,
        index_presence_selection_recomputed=True, all_source_gene_matching_recomputed=ready,
        old250_noise_study_released=False, full2000_axis_certified=False, STATE_checkpoint_axis_certified=False,
        independent_culture_validation=False, decision_gain=None, verifier_sha256=digest(Path(__file__)))
    with (HERE / "CALIBRATION_VERIFIED.json").open("x", encoding="utf-8") as stream:
        json.dump(verdict, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(verdict))
    return verdict


if __name__ == "__main__":
    verify()
