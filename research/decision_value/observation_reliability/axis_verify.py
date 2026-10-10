"""Supplemental independent axis checks from retained bytes; no network."""
import hashlib
import io
import json
from pathlib import Path

import h5py
import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AXIS = HERE / "axis"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SavedFile(io.RawIOBase):
    def __init__(self, file, size, receipts):
        self.file, self.size, self.position = file, size, 0
        self.spans = [(item["start"], item["end"], (ROOT / item["asset"]).read_bytes())
                      for item in receipts if item["file"] == file]

    def at(self, start, stop):
        for left, right, body in self.spans:
            if left <= start and stop - 1 <= right:
                return body[start-left:stop-left]
        raise ValueError(f"Retained span unavailable: {self.file}:{start}:{stop}")

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        return self.position
    def readinto(self, buffer):
        n = min(len(buffer), self.size - self.position)
        buffer[:n] = self.at(self.position, self.position + n)
        self.position += n
        return n


def slice_array(source, dataset, start, stop):
    assert dataset.compression is None and not dataset.shuffle and not dataset.fletcher32
    assert dataset.scaleoffset is None
    width = dataset.dtype.itemsize
    if dataset.chunks is None:
        origin = dataset.id.get_offset()
        return np.frombuffer(source.at(origin + start*width, origin + stop*width), dtype=dataset.dtype)
    parts, cursor = [], start
    while cursor < stop:
        origin = cursor // dataset.chunks[0] * dataset.chunks[0]
        chunk = dataset.id.get_chunk_info_by_coord((origin,))
        assert chunk.filter_mask == 0 and chunk.byte_offset is not None
        end = min(stop, origin + dataset.chunks[0])
        parts.append(source.at(chunk.byte_offset + (cursor-origin)*width,
                               chunk.byte_offset + (end-origin)*width))
        cursor = end
    return np.frombuffer(b"".join(parts), dtype=dataset.dtype)


def main():
    protocol, result, certificate, mapping, census = [read(AXIS / name) for name in
        ("PROTOCOL.json", "RESULTS.json", "CERTIFICATE.json", "MAPPING.json", "CENSUSES.json")]
    frozen = read(AXIS / "FREEZE.json")
    for path, expected in frozen["sha256"].items():
        assert digest(ROOT / path) == expected
    for name, key in (("PROTOCOL.json", "protocol_sha256"), ("RESULTS.json", "results_sha256"),
                      ("FREEZE.json", "freeze_sha256"), ("MAPPING.json", "mapping_sha256")):
        assert digest(AXIS / name) == certificate[key]
    assert digest(HERE / "ENDPOINT.json") == certificate["endpoint_definition_sha256"]
    receipts = [json.loads(line) for line in (AXIS / "NETWORK.jsonl").read_text().splitlines()]
    for item in receipts:
        assert item["http_status"] == 206 and item["source_revision"] == protocol["source_revision"]
        assert item["public_url"] == (f"https://huggingface.co/datasets/{protocol['source_repo']}"
            f"/resolve/{protocol['source_revision']}/{item['file']}")
        assert 0 <= item["start"] <= item["end"] < census[item["file"]]["file_bytes"]
        body = (ROOT / item["asset"]).read_bytes()
        assert len(body) == item["bytes"] == item["end"] - item["start"] + 1
        assert hashlib.sha256(body).hexdigest() == item["sha256"]
    assert [item["file"] for item in result["files"]] == protocol["source_files"]
    endpoint = protocol["endpoint"]["original_primary"]["mapped"]
    coordinates = [item["coordinate"] for item in endpoint]
    assert len(coordinates) == len(set(coordinates)) == 39
    later = read(HERE / "CONTROL_PLAN.json")["selected"]
    summaries = []
    for file_result in result["files"]:
        name = file_result["file"]
        planned = sorted({row for group in protocol["selected"] if group["file"] == name for row in group["rows"]})
        excluded = {row for group in later if group["file"] == name for row in group["rows"]}
        assert file_result["row_ids"] == planned and not set(planned) & excluded
        assert file_result["cells"] == len(planned) == 224
        assert len(file_result["endpoint_records"]) == 39
        source = SavedFile(name, census[name]["file_bytes"], receipts)
        raw, stored = [], []
        with h5py.File(source, "r") as h5:
            symbols = [s.decode() if isinstance(s, bytes) else str(s) for s in h5["var/gene_name"][:]]
            for row in planned:
                start, stop = map(int, slice_array(source, h5["X/indptr"], row, row+2))
                indices = slice_array(source, h5["X/indices"], start, stop)
                counts = slice_array(source, h5["X/data"], start, stop)
                assert len(indices) == len(counts) == len(np.unique(indices))
                assert np.isfinite(counts).all() and (counts >= 0).all()
                dense = np.zeros(len(symbols)); dense[indices] = counts
                raw.append(np.log1p(dense))
                offset = census[name]["layouts"]["obsm/X_hvg"]["offset"]
                stored.append(np.frombuffer(source.at(offset + row*8000, offset + (row+1)*8000), dtype="<f4")[coordinates])
        raw, stored = np.asarray(raw), np.asarray(stored)
        reconstructed = []
        for j, (expected, observed) in enumerate(zip(endpoint, file_result["endpoint_records"])):
            assert expected["coordinate"] == observed["coordinate"] and expected["gene"] == observed["expected_symbol"]
            matches = []
            for start in range(0, raw.shape[1], 4096):
                difference = np.max(np.abs(raw[:, start:start+4096] - stored[:, j, None]), axis=0)
                matches.extend((np.flatnonzero(difference <= protocol["matching_absolute_tolerance"]) + start).tolist())
            nonzero = int((np.abs(stored[:, j]) > protocol["matching_absolute_tolerance"]).sum())
            index = matches[0] if len(matches) == 1 else None
            duplicates = symbols.count(expected["gene"])
            passed = (index is not None and symbols[index] == expected["gene"] and duplicates == 1
                      and nonzero >= protocol["minimum_nonzero_cells_per_coordinate_per_file"])
            assert observed["matching_raw_gene_count"] == len(matches)
            assert observed["unique_raw_gene_index"] == index and observed["nonzero_cells"] == nonzero
            assert observed["raw_source_symbol_duplicate_count"] == duplicates and observed["passed"] == passed
            reconstructed.append(passed)
        cached = np.load(AXIS / f"{name}_CONTROL_AUTH.npz", allow_pickle=False)
        np.testing.assert_array_equal(cached["row_ids"], planned)
        np.testing.assert_array_equal(cached["X_hvg_endpoint"], stored)
        assert file_result["passed"] == all(reconstructed)
        summaries.append(dict(file=name, cells=len(planned), passed_coordinates=sum(reconstructed),
            required_coordinates=39, passed=all(reconstructed)))
    certified = all(item["passed"] for item in summaries)
    assert certificate["endpoint39_verified"] == certified
    assert certificate["status"] == result["status"] == ("PASS" if certified else "BLOCKED/AXIS_AUTHENTICATION")
    assert certificate["full_axis_verified"] is False and certificate["state_checkpoint_axis_verified"] is False
    if not certified:
        assert all(symbol is None for symbol in mapping["names"])
    verdict = dict(status="PASS_INDEPENDENT_SUPPLEMENTAL_RECONSTRUCTION", certificate_status=certificate["status"],
        reconstructed=summaries, retained_payloads=len(receipts), new_network_requests=0,
        producer_imports=False, later250_controls_read=False, verifier_sha256=digest(Path(__file__)),
        interpretation="Correctly blocked endpoint identity; no noise estimate or checkpoint-axis certificate.")
    destination = AXIS / "VERIFY_SUPPLEMENTAL.json"
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(verdict, stream, indent=2); stream.write("\n")
    print(json.dumps(verdict))


if __name__ == "__main__":
    main()
