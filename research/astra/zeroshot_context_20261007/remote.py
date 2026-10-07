"""Byte-accounted HTTP range reads of pinned public Tahoe h5ad files.

Only the bytes a stage asks for are fetched. Every request is written to a
JSONL ledger (file, byte span, SHA-256 of the returned bytes, attempts, time),
so an independent verifier can re-fetch any span and compare. Signed CDN URLs
are never written to disk; only the pinned Hugging Face resolve path is.
"""
from __future__ import annotations

import hashlib
import io
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = "arcinstitute/State-Tahoe-Filtered"
REVISION = "fdf87abece385feea6fa5e9944ab46e173b6af50"
ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / "data/external/tahoe_zeroshot_20261007"


def resolve_path(name: str) -> str:
    return f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{name}"


class RangeClient:
    """Thread-safe range fetcher with redirect refresh and a per-process ledger."""

    def __init__(self, ledger: Path, user_agent: str = "MAESTRO-zeroshot-context/1"):
        self.ledger = Path(ledger)
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._local = threading.local()
        self._locations: dict[str, tuple[str, float]] = {}
        self.user_agent = user_agent
        self.bytes = 0
        self.requests = 0

    def _session(self) -> requests.Session:
        if not hasattr(self._local, "session"):
            self._local.session = requests.Session()
            self._local.session.headers["User-Agent"] = self.user_agent
        return self._local.session

    def _location(self, name: str, refresh: bool = False) -> str:
        with self._lock:
            cached = self._locations.get(name)
        if cached and not refresh and time.time() - cached[1] < 1200:
            return cached[0]
        response = self._session().head(resolve_path(name), allow_redirects=False, timeout=60)
        if response.status_code not in (301, 302, 307, 308):
            raise RuntimeError(f"unexpected resolve status {response.status_code} for {name}")
        location = response.headers["location"]
        with self._lock:
            self._locations[name] = (location, time.time())
        return location

    def size(self, name: str) -> int:
        location = self._location(name)
        response = self._session().get(location, headers={"Range": "bytes=0-0"}, timeout=60)
        return int(response.headers["Content-Range"].split("/")[-1])

    def fetch(self, name: str, start: int, end: int, purpose: str) -> bytes:
        """Return bytes [start, end] inclusive; retries, verifies length, records a receipt."""
        if end < start:
            raise ValueError("empty range")
        attempts, started, error = 0, time.perf_counter(), None
        while attempts < 6:
            attempts += 1
            try:
                location = self._location(name, refresh=attempts > 1)
                response = self._session().get(location, headers={"Range": f"bytes={start}-{end}"}, timeout=180)
                if response.status_code != 206:
                    raise RuntimeError(f"status {response.status_code}")
                span = response.headers.get("Content-Range", "").split()[-1].split("/")[0]
                if span != f"{start}-{end}":
                    raise RuntimeError("returned span mismatch")
                data = response.content
                if len(data) != end - start + 1:
                    raise RuntimeError("short read")
                error = None
                break
            except Exception as exc:  # network messages may embed signed URLs; keep the type only
                error = type(exc).__name__ + ":" + str(exc).split("?")[0][:120]
                time.sleep(min(30, 2 ** attempts))
        record = {"file": name, "revision": REVISION, "start": start, "end": end,
                  "bytes": 0 if error else len(data), "attempts": attempts,
                  "seconds": round(time.perf_counter() - started, 4), "purpose": purpose,
                  "utc": datetime.now(timezone.utc).isoformat(), "error": error,
                  "sha256": None if error else hashlib.sha256(data).hexdigest()}
        with self._lock:
            with self.ledger.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
            self.requests += 1
            if not error:
                self.bytes += len(data)
        if error:
            raise RuntimeError(f"range retrieval failed after {attempts} attempts: {error}")
        return data


class BlockFile(io.RawIOBase):
    """Read-only seekable view for h5py metadata access, cached in fixed blocks on disk."""

    def __init__(self, client: RangeClient, name: str, size: int, block: int = 524288, cache_dir: Path | None = None):
        self.client, self.name, self._size, self.block = client, name, size, block
        self.position = 0
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._blocks: dict[int, bytes] = {}

    def _get(self, index: int) -> bytes:
        if index in self._blocks:
            return self._blocks[index]
        path = self.cache_dir / f"{index}.blk" if self.cache_dir else None
        if path is not None and path.exists():
            data = path.read_bytes()
        else:
            start = index * self.block
            end = min(start + self.block, self._size) - 1
            data = self.client.fetch(self.name, start, end, "hdf5_metadata_block")
            if path is not None:
                path.write_bytes(data)
        self._blocks[index] = data
        return data

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self._size + offset
        return self.position

    def readinto(self, buffer):
        want = min(len(buffer), max(0, self._size - self.position))
        view, filled = memoryview(buffer), 0
        while filled < want:
            index, offset = divmod(self.position, self.block)
            data = self._get(index)
            n = min(want - filled, len(data) - offset)
            view[filled:filled + n] = data[offset:offset + n]
            filled += n
            self.position += n
        return filled


def dataset_layout(dataset) -> dict:
    """Contiguous, uncompressed storage is required for exact row-span reads.

    Chunked datasets are described without querying their storage size: that
    query walks the whole chunk index, which for the multi-GB count matrix
    means thousands of remote metadata blocks (the first census attempt did
    exactly this and was stopped).
    """
    layout = {"shape": list(dataset.shape), "dtype": dataset.dtype.str, "chunks": dataset.chunks,
              "compression": dataset.compression, "offset": None, "storage_bytes": None}
    if dataset.chunks is None:
        layout["offset"] = dataset.id.get_offset()
        layout["storage_bytes"] = dataset.id.get_storage_size()
    return layout


def read_contiguous(client: RangeClient, name: str, layout: dict, purpose: str, part: int = 33554432):
    import numpy as np
    if layout["chunks"] is not None or layout["compression"] is not None or layout["offset"] is None:
        raise ValueError("dataset is not contiguous uncompressed storage")
    total = layout["storage_bytes"]
    pieces, start = [], layout["offset"]
    while start < layout["offset"] + total:
        end = min(start + part, layout["offset"] + total) - 1
        pieces.append(client.fetch(name, start, end, purpose))
        start = end + 1
    return np.frombuffer(b"".join(pieces), dtype=np.dtype(layout["dtype"])).reshape(layout["shape"])
