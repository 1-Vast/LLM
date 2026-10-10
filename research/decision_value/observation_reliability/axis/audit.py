"""Frozen, bounded control-only raw-CSR to X_hvg coordinate authentication."""
import hashlib
import io
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import h5py
import numpy as np
import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


class Source(io.RawIOBase):
    """Exact spans: metadata or selected control data; never full CSR chunks."""
    def __init__(self, name, size, protocol, budget):
        self.name, self.size, self.protocol, self.budget = name, size, protocol, budget
        self.position, self.cache = 0, {}
        self.lock, self.local = threading.Lock(), threading.local()
        self.public_url = f"https://huggingface.co/datasets/{protocol['source_repo']}/resolve/{protocol['source_revision']}/{name}"
        response = requests.head(self.public_url, allow_redirects=False, timeout=(15, 30))
        if response.status_code not in (301, 302, 307, 308):
            raise RuntimeError("public_source_redirect_unavailable")
        self.location = response.headers["Location"]

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        return self.position

    def fetch(self, start, end, purpose):
        key = (int(start), int(end))
        with self.lock:
            cached = self.cache.get(key)
            if cached is None:
                for (left, right), payload in self.cache.items():
                    if left <= start and end <= right:
                        cached = payload[start - left:end - left + 1]
                        break
        if cached is not None:
            return cached
        size = end - start + 1
        with self.budget["lock"]:
            if self.budget["reserved"] + size > self.protocol["axis_network_body_cap_bytes"]:
                raise RuntimeError("axis_network_budget_exceeded")
            self.budget["reserved"] += size
        if not hasattr(self.local, "session"):
            self.local.session = requests.Session()
        with self.local.session.get(self.location, headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}, stream=True, timeout=(15, 40)) as response:
            if response.status_code != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{self.size}":
                raise RuntimeError("source_range_mismatch")
            chunks, received = [], 0
            for chunk in response.iter_content(65536):
                received += len(chunk)
                if received > size:
                    raise RuntimeError("source_range_overrun")
                chunks.append(chunk)
        payload = b"".join(chunks)
        if len(payload) != size:
            raise RuntimeError("source_range_truncated")
        path = HERE / "assets" / f"{self.name}_{start}_{end}.bin"
        with self.lock:
            self.cache[key] = payload
            path.write_bytes(payload)
        receipt = dict(file=self.name, source_revision=self.protocol["source_revision"], public_url=self.public_url,
                       start=int(start), end=int(end), bytes=size, sha256=hashlib.sha256(payload).hexdigest(),
                       http_status=206, purpose=purpose, asset=path.relative_to(ROOT).as_posix())
        with self.budget["lock"]:
            self.budget["received"] += size
            self.budget["receipts"].append(receipt)
            with (HERE / "NETWORK.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(receipt) + "\n")
        return payload

    def readinto(self, buffer):
        n = min(len(buffer), self.size - self.position)
        if n <= 0: return 0
        value = self.fetch(self.position, self.position + n - 1, "hdf5_metadata_or_gene_name")
        buffer[:n] = value
        self.position += n
        return n


def physical_spans(dataset, start, end):
    """Map a logical 1D slice to exact bytes, avoiding adjacent treated values."""
    if dataset.compression is not None or dataset.shuffle or dataset.fletcher32 or dataset.scaleoffset is not None:
        raise RuntimeError("filtered_CSR_storage_unsupported")
    stride = dataset.dtype.itemsize
    if dataset.chunks is None:
        offset = dataset.id.get_offset()
        if offset is None: raise RuntimeError("missing_contiguous_dataset_offset")
        return [(offset + start * stride, offset + end * stride - 1)]
    width = dataset.chunks[0]
    spans = []
    cursor = start
    while cursor < end:
        chunk_start = cursor // width * width
        chunk = dataset.id.get_chunk_info_by_coord((chunk_start,))
        if chunk.filter_mask or chunk.byte_offset is None:
            raise RuntimeError("unsupported_CSR_chunk")
        stop = min(end, chunk_start + width)
        spans.append((chunk.byte_offset + (cursor - chunk_start) * stride, chunk.byte_offset + (stop - chunk_start) * stride - 1))
        cursor = stop
    return spans


def raw_values(source, spans, dtype, purpose):
    payload = b"".join(source.fetch(start, end, purpose) for start, end in spans)
    return np.frombuffer(payload, dtype=dtype)


def merge_adjacent(spans):
    """Coalesce touching selected spans without fetching gaps or other rows."""
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def authenticate_file(file, protocol, meta, budget):
    groups = [group for group in protocol["selected"] if group["file"] == file]
    rows = sorted({row for group in groups for row in group["rows"]})
    handle = Source(file, meta["file_bytes"], protocol, budget)
    endpoint = protocol["endpoint"]["original_primary"]["mapped"]
    coordinates = np.array([record["coordinate"] for record in endpoint])
    jobs = []
    with h5py.File(handle, "r") as h5:
        names = [value.decode("utf-8") if isinstance(value, bytes) else str(value) for value in h5["var/gene_name"][:]]
        pointers, indices, data = h5["X/indptr"], h5["X/indices"], h5["X/data"]
        # Whole indptr is row-offset metadata, not RNA; coalescing removes hundreds of tiny requests.
        ptr = raw_values(handle, merge_adjacent(physical_spans(pointers, 0, pointers.shape[0])), pointers.dtype, "CSR_row_offset_metadata")
        for row in rows:
            a, b = int(ptr[row]), int(ptr[row + 1])
            jobs.append(dict(row=row, indices=physical_spans(indices, a, b), data=physical_spans(data, a, b),
                             indices_dtype=indices.dtype.str, data_dtype=data.dtype.str))
    offset = meta["layouts"]["obsm/X_hvg"]["offset"]
    fetches = []
    for key, purpose in (("indices", "selected_control_CSR_indices"), ("data", "selected_control_CSR_values")):
        fetches += [(start, end, purpose) for start, end in merge_adjacent([span for job in jobs for span in job[key]])]
    fetches += [(start, end, "selected_control_X_hvg") for start, end in merge_adjacent([(offset + row * 8000, offset + (row + 1) * 8000 - 1) for row in rows])]
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda job: handle.fetch(*job), fetches))

    def read_row(job):
        row = job["row"]
        idx = raw_values(handle, job["indices"], job["indices_dtype"], "selected_control_CSR_indices")
        val = raw_values(handle, job["data"], job["data_dtype"], "selected_control_CSR_values")
        if len(np.unique(idx)) != len(idx) or len(idx) != len(val):
            raise RuntimeError("duplicate_or_misaligned_CSR_indices")
        dense = np.zeros(len(names), dtype=np.float32)
        dense[idx] = val
        if not np.isfinite(dense).all() or np.min(dense) < 0:
            raise RuntimeError("invalid_source_expression")
        hvg = np.frombuffer(handle.fetch(offset + row * 8000, offset + (row + 1) * 8000 - 1, "selected_control_X_hvg"), dtype="<f4")
        return dense, hvg[coordinates].astype(np.float64)

    with ThreadPoolExecutor(max_workers=8) as pool:
        readings = list(pool.map(read_row, jobs))
    counts = np.array([reading[0] for reading in readings])
    stored = np.array([reading[1] for reading in readings])
    raw = np.log1p(counts.astype(np.float64))
    records = []
    tol = protocol["matching_absolute_tolerance"]
    for j, expected in enumerate(endpoint):
        target = stored[:, j]
        possible = np.arange(len(names))
        for row in np.argsort(-np.abs(target)):
            possible = possible[np.abs(raw[row, possible] - target[row]) <= tol]
            if not len(possible): break
        nonzero = int((np.abs(target) > tol).sum())
        index = int(possible[0]) if len(possible) == 1 else None
        identity_ok = index is not None and names[index] == expected["gene"]
        passed = identity_ok and names.count(expected["gene"]) == 1 and nonzero >= protocol["minimum_nonzero_cells_per_coordinate_per_file"]
        records.append(dict(coordinate=expected["coordinate"], expected_symbol=expected["gene"], matching_raw_gene_count=len(possible),
                            unique_raw_gene_index=index, source_symbol=names[index] if index is not None else None,
                            raw_source_symbol_duplicate_count=names.count(expected["gene"]), nonzero_cells=nonzero, passed=passed,
                            max_abs_mismatch=float(np.max(np.abs(raw[:, index] - target))) if index is not None else None))
    np.savez_compressed(HERE / f"{file}_CONTROL_AUTH.npz", row_ids=np.array(rows), raw_gene_indices=np.array([r["unique_raw_gene_index"] if r["unique_raw_gene_index"] is not None else -1 for r in records]),
                        X_hvg_endpoint=stored, expected_log1p_raw_X=np.column_stack([raw[:, r["unique_raw_gene_index"]] if r["unique_raw_gene_index"] is not None else np.full(len(rows), np.nan) for r in records]))
    return dict(file=file, cells=len(rows), source_gene_count=len(names), passed=all(record["passed"] for record in records),
                endpoint_records=records, row_ids=rows, controls_only=True, identity_scope="39 declared endpointcoordinates, not full native or STATEcheckpoint axes")


def main():
    if (HERE / "RESULTS.json").exists() or (HERE / "NETWORK.jsonl").exists():
        raise FileExistsError("axis audit refuses overwrite")
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, digest in freeze["sha256"].items():
        if sha(ROOT / name) != digest: raise RuntimeError("frozen_input_hash_mismatch")
    protocol = json.loads((HERE / "PROTOCOL.json").read_text())
    metadata = json.loads((HERE / "CENSUSES.json").read_text())
    (HERE / "assets").mkdir(exist_ok=False)
    budget = dict(reserved=protocol["metadata_preparation_bytes"], received=protocol["metadata_preparation_bytes"], lock=threading.Lock(), receipts=[])
    files, error = [], None
    try:
        for file in protocol["source_files"]:
            print("Authenticating control-only source: " + file, flush=True)
            files.append(authenticate_file(file, protocol, metadata[file], budget))
    except Exception as exc:
        error = dict(error_type=type(exc).__name__, reason=str(exc) if str(exc) in {"axis_network_budget_exceeded", "source_range_mismatch", "source_range_truncated", "duplicate_or_misaligned_CSR_indices", "invalid_source_expression"} else "Source audit failed; see retained receipts.")
    passed = len(files) == len(protocol["source_files"]) and all(file["passed"] for file in files) and error is None
    result = dict(schema="control_only_axis_results_v1", status="PASS" if passed else "BLOCKED/AXIS_AUTHENTICATION", files=files, error=error,
                  actual_network_body_bytes=budget["received"], network_range_calls=len(budget["receipts"]), network_cap_bytes=protocol["axis_network_body_cap_bytes"],
                  treated_cell_expression_requested=False, new_STATE_inference_calls=0, later250_noise_cells_read=False)
    write(HERE / "RESULTS.json", result)
    names = [None] * 2000
    if passed:
        for entry in files[0]["endpoint_records"]: names[entry["coordinate"]] = entry["expected_symbol"]
    write(HERE / "MAPPING.json", dict(schema="partially_authenticated_source_axis_v1", names=names,
                                       source_revision=protocol["source_revision"], records_by_file={file["file"]: file["endpoint_records"] for file in files},
                                       named_coordinates=sum(name is not None for name in names), unresolved_coordinates=sum(name is None for name in names)))
    certificate = dict(schema="endpoint39_axis_certificate_v1", status=result["status"], endpoint39_verified=passed,
                       source_revision=protocol["source_revision"], source_files=protocol["source_files"], expression_transform=protocol["expression_transform"],
                       per_file_endpoint39_verified={file["file"]: file["passed"] for file in files}, full_axis_verified=False, state_checkpoint_axis_verified=False,
                       mapping_file=(HERE / "MAPPING.json").relative_to(ROOT).as_posix(), mapping_sha256=sha(HERE / "MAPPING.json"),
                       protocol_sha256=sha(HERE / "PROTOCOL.json"), freeze_sha256=sha(HERE / "FREEZE.json"), results_sha256=sha(HERE / "RESULTS.json"),
                       endpoint_definition_sha256=sha(HERE.parent / "ENDPOINT.json"))
    write(HERE / "CERTIFICATE.json", certificate)
    print(json.dumps(dict(status=result["status"], bytes=budget["received"], files=len(files), error=error)), flush=True)


if __name__ == "__main__":
    main()
