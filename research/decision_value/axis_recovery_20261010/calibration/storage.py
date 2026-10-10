"""Bounded exact HDF5 ranges with retained bodies and offline replay."""
from datetime import datetime, timezone
import hashlib
import io
import json
import threading
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPO = "arcinstitute/State-Tahoe-Filtered"
REVISION = "fdf87abece385feea6fa5e9944ab46e173b6af50"
CAP = 25_000_000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def write(path, obj):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, indent=2, allow_nan=False)
        stream.write("\n")


def append(path, obj):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(obj) + "\n")


class Source(io.RawIOBase):
    def __init__(self, file, size, *, network=False, stage="metadata", old_cache=True):
        self.file, self.size, self.position = file, size, 0
        self.network, self.stage = network, stage
        self.lock = threading.RLock()
        self.session = requests.Session()
        self.spans = []
        self.public_url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{file}"
        self.location = None
        for row in read_rows(HERE / "NETWORK.jsonl") + read_rows(HERE / "CACHE_REUSE.jsonl"):
            if row.get("file") == file and row.get("status") in ("RETAINED", "REUSED"):
                path = HERE / row["path"]
                if path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
                    raise RuntimeError("retained_range_hash_mismatch")
                self.spans.append((row["start"], row["end"], path, None))
        if old_cache and network and file == "c44.h5ad":
            old = ROOT / "research/decision_value/observation_reliability/axis"
            entries = read_rows(old / "NETWORK.jsonl")
            if (old / "metadata_probe/RESULTS.json").exists():
                entries += json.loads((old / "metadata_probe/RESULTS.json").read_text())["receipts"]
            for row in entries:
                if row.get("file") == file:
                    self.spans.append((row["start"], row["end"], ROOT / row["asset"], row))

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        return self.position

    def cached(self, start, end):
        for left, right, path, original in self.spans:
            if left <= start and end <= right:
                body = path.read_bytes()
                if original is not None:
                    if len(body) != original["bytes"] or hashlib.sha256(body).hexdigest() != original["sha256"]:
                        raise RuntimeError("old_range_hash_mismatch")
                    target = HERE / "assets" / (original["sha256"] + ".bin")
                    target.parent.mkdir(exist_ok=True)
                    if not target.exists(): target.write_bytes(body)
                    record = dict(file=self.file, start=left, end=right, bytes=len(body),
                                  sha256=original["sha256"], path=target.relative_to(HERE).as_posix(),
                                  source_revision=REVISION, public_url=self.public_url, status="REUSED",
                                  requested_subspan=[start, end], newly_received_body_bytes=0,
                                  original_receipt=original, source_asset=path.relative_to(ROOT).as_posix(),
                                  stage=self.stage, exposed_scope="Original retained span; no newly downloaded bytes")
                    append(HERE / "CACHE_REUSE.jsonl", record)
                    self.spans.append((left, right, target, None))
                    self.spans.remove((left, right, path, original))
                return body[start-left:end-left+1]
        return None

    def fetch(self, start, end, purpose):
        start, end = int(start), int(end)
        if not 0 <= start <= end < self.size:
            raise RuntimeError("invalid_physical_range")
        if purpose.startswith("expression_") and self.stage != "expression":
            raise RuntimeError("paired_expression_before_execution_stage")
        if purpose.startswith("index_screen_") and self.stage != "index_screen":
            raise RuntimeError("index_screen_before_frozen_execution_stage")
        with self.lock:
            body = self.cached(start, end)
            if body is not None: return body
            if not self.network: raise RuntimeError(f"Unretained range: {self.file}:{start}-{end}")
            if self.location is None:
                response = self.session.head(self.public_url, allow_redirects=False, timeout=(15, 30))
                append(HERE / "NETWORK.jsonl", dict(file=self.file, public_url=self.public_url,
                       source_revision=REVISION, stage=self.stage, purpose="source_redirect_HEAD",
                       http_status=response.status_code, bytes=0, status="HEAD", utc=datetime.now(timezone.utc).isoformat()))
                if response.status_code not in (301, 302, 307, 308):
                    raise RuntimeError("source_redirect_missing")
                self.location = response.headers["Location"]
            size = end-start+1
            received = sum(row.get("bytes", 0) for row in read_rows(HERE / "NETWORK.jsonl"))
            if received+size > CAP: raise RuntimeError("calibration_total_response_cap")
            record = dict(file=self.file, public_url=self.public_url, source_revision=REVISION,
                          start=start, end=end, stage=self.stage, purpose=purpose,
                          utc=datetime.now(timezone.utc).isoformat(), bytes=0)
            body = bytearray()
            try:
                with self.session.get(self.location, headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"},
                                  allow_redirects=False, stream=True, timeout=(15, 40)) as response:
                    record.update(http_status=response.status_code,
                                  content_range=response.headers.get("Content-Range"),
                                  content_length=response.headers.get("Content-Length"))
                    valid = response.status_code == 206 and response.headers.get("Content-Range") == f"bytes {start}-{end}/{self.size}"
                    # Refuse oversized/incorrect source responses before consuming their bodies.
                    limit = size if valid else min(8192, CAP-received)
                    declared = response.headers.get("Content-Length")
                    if declared and int(declared) > limit:
                        record["status"] = "REFUSED_OVERSIZE"
                    else:
                        while len(body) < limit:
                            block = response.raw.read(min(65536, limit-len(body)))
                            if not block: break
                            body.extend(block)
                        record["status"] = "RETAINED" if valid and len(body) == size else "FAILED_RANGE"
            except Exception as exc:
                record.update(status="NETWORK_ERROR", error_type=type(exc).__name__,
                              undelivered_transport_bytes="unmeasured")
            path = HERE / "assets" / f"{self.file}_{start}_{end}_{len(read_rows(HERE / 'NETWORK.jsonl'))}.bin"
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(body)
            record.update(bytes=len(body), path=path.relative_to(HERE).as_posix(), sha256=sha(path))
            append(HERE / "NETWORK.jsonl", record)
            if record["status"] != "RETAINED": raise RuntimeError("exact_source_range_unavailable")
            self.spans.append((start, end, path, None))
            return bytes(body)

    def readinto(self, buffer):
        count = min(len(buffer), self.size-self.position)
        if count <= 0: return 0
        buffer[:count] = self.fetch(self.position, self.position+count-1, "HDF5_structure_or_gene_name_metadata")
        self.position += count
        return count


# The two pure span helpers below are retained from the old frozen axis/audit.py.
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


def merge_adjacent(spans):
    """Coalesce touching selected spans without fetching gaps or other rows."""
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
