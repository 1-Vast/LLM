"""Authenticate the seven original PTV files and their regenerable arrays."""
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/external/ptv1_proteintalks_20261021"
LOG = ROOT / "log/20261021/rsi_next_qualification"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def main():
    start = time.perf_counter()
    manifest_path = ROOT / "research/dual_core_innovation_validation_20261021/SOURCE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    files = []
    for name, record in manifest["data_host"]["files"].items():
        p = SOURCE / "drive" / name
        actual = sha(p)
        assert actual == record["sha256"] and p.stat().st_size == record["bytes"], name
        files.append({"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": actual})
    caches = []
    for key in ("expr", "pert"):
        p = SOURCE / "cache" / (key + ".npy")
        cached = np.load(p, mmap_mode="r")
        source_path = SOURCE / "drive" / f"allcelltype_drugpair_crossdrug_{key}.csv"
        offset = 0
        for chunk in pd.read_csv(source_path, header=None, chunksize=128, dtype=np.float64):
            values = chunk.to_numpy().astype(cached.dtype)
            assert values.shape[1] == cached.shape[1]
            assert np.array_equal(values, cached[offset:offset + len(values)], equal_nan=True), (key, offset)
            offset += len(values)
        assert offset == len(cached)
        caches.append({"path": str(p.relative_to(ROOT)), "sha256": sha(p), "shape": list(cached.shape),
                       "dtype": str(cached.dtype), "matches_source_elementwise_at_cache_dtype": True})
    result = {"status": "PASS", "exposure": "already_exposed_source_only", "files": files, "caches": caches,
              "source_manifest_sha256": sha(manifest_path), "wall_seconds": time.perf_counter() - start,
              "argv": sys.argv, "new_downloads": 0}
    (LOG / "SOURCE_AUDIT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "raw_files": len(files), "caches": len(caches), "seconds": result["wall_seconds"]}))


if __name__ == "__main__":
    main()
