"""Offline recheck from retained HTTP payloads; no producer import or network."""
import hashlib
import io
import json
from pathlib import Path

import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class RetainedSource(io.RawIOBase):
    def __init__(self, name, size, receipts):
        self.name, self.size, self.position = name, size, 0
        self.spans = []
        for entry in receipts:
            if entry["file"] != name: continue
            assert entry["http_status"] == 206 and entry["end"] - entry["start"] + 1 == entry["bytes"]
            assert entry["source_revision"] == "fdf87abece385feea6fa5e9944ab46e173b6af50"
            assert entry["public_url"] == f"https://huggingface.co/datasets/arcinstitute/State-Tahoe-Filtered/resolve/{entry['source_revision']}/{name}"
            path = ROOT / entry["asset"]
            value = path.read_bytes()
            assert len(value) == entry["bytes"] and hashlib.sha256(value).hexdigest() == entry["sha256"]
            self.spans.append((entry["start"], entry["end"], value))

    def bytes_at(self, start, end):
        for left, right, value in self.spans:
            if left <= start and end <= right:
                return value[start - left:end - left + 1]
        raise RuntimeError(f"Unretained exact source span: {self.name}:{start}-{end}")

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        return self.position
    def readinto(self, buffer):
        n = min(len(buffer), self.size - self.position)
        buffer[:n] = self.bytes_at(self.position, self.position + n - 1)
        self.position += n
        return n


def array_slice(source, dataset, start, stop):
    parts = []
    itemsize = dataset.dtype.itemsize
    assert dataset.compression is None and not dataset.shuffle and not dataset.fletcher32
    if dataset.chunks is None:
        offset = dataset.id.get_offset()
        return np.frombuffer(source.bytes_at(offset + start * itemsize, offset + stop * itemsize - 1), dtype=dataset.dtype)
    width = dataset.chunks[0]
    cursor = start
    while cursor < stop:
        origin = (cursor // width) * width
        storage = dataset.id.get_chunk_info_by_coord((origin,))
        end = min(stop, origin + width)
        parts.append(source.bytes_at(storage.byte_offset + (cursor - origin) * itemsize,
                                     storage.byte_offset + (end - origin) * itemsize - 1))
        cursor = end
    return np.frombuffer(b"".join(parts), dtype=dataset.dtype)


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    assert all(sha(ROOT / name) == digest for name, digest in freeze["sha256"].items())
    cert = json.loads((HERE / "CERTIFICATE.json").read_text())
    for name, key in (("MAPPING.json", "mapping_sha256"), ("PROTOCOL.json", "protocol_sha256"),
                      ("FREEZE.json", "freeze_sha256"), ("RESULTS.json", "results_sha256")):
        assert sha(HERE / name) == cert[key]
    assert sha(HERE.parent / "ENDPOINT.json") == cert["endpoint_definition_sha256"]
    protocol = json.loads((HERE / "PROTOCOL.json").read_text())
    result = json.loads((HERE / "RESULTS.json").read_text())
    census = json.loads((HERE / "CENSUSES.json").read_text())
    receipts = [json.loads(line) for line in (HERE / "NETWORK.jsonl").read_text().splitlines()]
    assert [entry["file"] for entry in result["files"]] == protocol["source_files"]
    assert cert["source_files"] == protocol["source_files"]
    noise_plan = json.loads((HERE.parent / "CONTROL_PLAN.json").read_text())
    noise_rows = {(group["file"], int(row)) for group in noise_plan["selected"] for row in group["rows"]}
    summary = []
    for file_result in result["files"]:
        name = file_result["file"]
        source = RetainedSource(name, census[name]["file_bytes"], receipts)
        endpoint = protocol["endpoint"]["original_primary"]["mapped"]
        coordinates = [entry["coordinate"] for entry in endpoint]
        assert [entry["coordinate"] for entry in file_result["endpoint_records"]] == coordinates
        assert [entry["expected_symbol"] for entry in file_result["endpoint_records"]] == [entry["gene"] for entry in endpoint]
        planned = sorted({row for group in protocol["selected"] if group["file"] == name for row in group["rows"]})
        assert file_result["row_ids"] == planned and all((name, row) not in noise_rows for row in planned)
        raw_rows, hvg_rows = [], []
        with h5py.File(source, "r") as h5:
            names = [value.decode("utf-8") if isinstance(value, bytes) else str(value) for value in h5["var/gene_name"][:]]
            for row in file_result["row_ids"]:
                a, b = map(int, array_slice(source, h5["X/indptr"], row, row + 2))
                indices = array_slice(source, h5["X/indices"], a, b)
                data = array_slice(source, h5["X/data"], a, b)
                assert len(indices) == len(data) and len(np.unique(indices)) == len(indices)
                dense = np.zeros(len(names), dtype=np.float64)
                dense[indices] = data
                raw_rows.append(np.log1p(dense))
                offset = census[name]["layouts"]["obsm/X_hvg"]["offset"]
                hvg_rows.append(np.frombuffer(source.bytes_at(offset + row * 8000, offset + (row + 1) * 8000 - 1), dtype="<f4")[coordinates])
        raw, stored = np.array(raw_rows), np.array(hvg_rows)
        checks = []
        for j, entry in enumerate(file_result["endpoint_records"]):
            matched = []
            for start in range(0, len(names), 4096):
                maximum = np.max(np.abs(raw[:, start:start + 4096] - stored[:, j:j+1]), axis=0)
                matched.extend((np.flatnonzero(maximum <= protocol["matching_absolute_tolerance"]) + start).tolist())
            assert len(matched) == entry["matching_raw_gene_count"]
            assert (matched[0] if len(matched) == 1 else None) == entry["unique_raw_gene_index"]
            assert int((np.abs(stored[:, j]) > protocol["matching_absolute_tolerance"]).sum()) == entry["nonzero_cells"]
            if entry["unique_raw_gene_index"] is not None:
                assert names[matched[0]] == entry["source_symbol"]
                assert float(np.max(np.abs(raw[:, matched[0]] - stored[:, j]))) == entry["max_abs_mismatch"]
            duplicate_count = names.count(endpoint[j]["gene"])
            assert duplicate_count == entry["raw_source_symbol_duplicate_count"]
            calculated_pass = (len(matched) == 1 and names[matched[0]] == endpoint[j]["gene"] and duplicate_count == 1
                               and entry["nonzero_cells"] >= protocol["minimum_nonzero_cells_per_coordinate_per_file"])
            assert calculated_pass == entry["passed"]
            checks.append(calculated_pass)
        assert all(checks) == file_result["passed"]
        summary.append(dict(file=name, cells=len(stored), reproduced_coordinates=len(checks), passed_coordinates=sum(checks)))
    verdict = len(summary) == len(protocol["source_files"]) and all(row["passed_coordinates"] == 39 for row in summary)
    assert verdict == cert["endpoint39_verified"]
    bytes_read = protocol["metadata_preparation_bytes"] + sum(entry["bytes"] for entry in receipts)
    assert bytes_read == result["actual_network_body_bytes"] <= protocol["axis_network_body_cap_bytes"]
    verification = dict(schema="offline_axis_verification_v1", passed=True, source_files=summary,
                        certificate_status=cert["status"], verified_payloads=len(receipts), actual_network_body_bytes=bytes_read,
                        new_network_calls=0, producer_imported=False, verifier_sha256=sha(Path(__file__)))
    with (HERE / "VERIFY2.json").open("x", encoding="utf-8") as stream:
        json.dump(verification, stream, indent=2); stream.write("\n")
    print(json.dumps(verification))


if __name__ == "__main__":
    main()
