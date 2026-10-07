"""Stage 1: metadata-only census of every pinned State-Tahoe-Filtered context.

Reads obs categorical codes and HDF5 storage layouts. No expression matrix value
(X, obsm/X_hvg, obsm/X_state) is read here. The output identifies which file
holds each documented zero-shot test context and how many cells each
drug-dose/plate condition has, so sampling can be planned before any response
is seen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from remote import CACHE, REVISION, BlockFile, RangeClient, dataset_layout, read_contiguous  # noqa: E402

LOCAL = {"c39.h5ad": Path(__file__).resolve().parents[3] / "data/external/arc_state/tahoe_metadata_source/c39.h5ad"}
COLUMNS = ("drugname_drugconc", "plate", "sample", "pass_filter", "cell_name", "cell_line", "drug")


def _categories(group):
    raw = group["categories"][:]
    return [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in raw]


def census_one(name: str) -> dict:
    import h5py
    import numpy as np
    started = time.perf_counter()
    client = RangeClient(HERE / "census" / "ledgers" / f"{name}.jsonl")
    if name in LOCAL:
        handle, size, source = LOCAL[name], LOCAL[name].stat().st_size, "local_pinned_copy"
    else:
        size = client.size(name)
        handle = BlockFile(client, name, size, cache_dir=CACHE / "blocks" / name)
        source = "remote_range"
    out = {"file": name, "revision": REVISION, "source": source, "file_bytes": size}
    with h5py.File(handle, "r") as f:
        obs = f["obs"]
        codes = {}
        for column in COLUMNS:
            if column not in obs:
                continue
            group = obs[column]
            out.setdefault("categories", {})[column] = _categories(group)
            layout = dataset_layout(group["codes"])
            out.setdefault("code_layouts", {})[column] = layout
            if source == "local_pinned_copy":
                codes[column] = group["codes"][:]
            else:
                codes[column] = read_contiguous(client, name, layout, f"obs_codes:{column}")
        out["n_cells"] = int(len(codes["drugname_drugconc"]))
        out["layouts"] = {key: dataset_layout(f[key]) for key in ("obsm/X_hvg", "X/indptr", "X/indices", "X/data") if key in f}
        if "obsm/X_state" in f:
            out["layouts"]["obsm/X_state"] = dataset_layout(f["obsm/X_state"])
        out["obs_columns"] = sorted(obs.keys())
    labels = np.asarray(out["categories"]["drugname_drugconc"])[codes["drugname_drugconc"]]
    plates = np.asarray(out["categories"]["plate"])[codes["plate"]]
    pairs = Counter(zip(labels.tolist(), plates.tolist()))
    out["condition_plate_counts"] = [[label, plate, int(n)] for (label, plate), n in sorted(pairs.items())]
    runs = 1 + int(np.count_nonzero(np.diff(codes["drugname_drugconc"].astype(np.int64))))
    out["label_runs"] = runs
    out["cell_names"] = sorted(set(np.asarray(out["categories"]["cell_name"])[codes["cell_name"]].tolist()))
    if "pass_filter" in codes:
        out["pass_filter_counts"] = {k: int(v) for k, v in Counter(np.asarray(out["categories"]["pass_filter"])[codes["pass_filter"]].tolist()).items()}
    target = CACHE / "census" / f"{name}.npz"
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(target, **{k: v for k, v in codes.items()})
    out["codes_npz"] = str(target.relative_to(CACHE))
    out["codes_sha256"] = {k: hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest() for k, v in codes.items()}
    out["remote_requests"], out["remote_bytes"] = client.requests, client.bytes
    out["seconds"] = round(time.perf_counter() - started, 3)
    (HERE / "census" / f"{name}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return {k: out[k] for k in ("file", "cell_names", "n_cells", "label_runs", "remote_bytes", "seconds")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="*", default=[f"c{i}.h5ad" for i in range(50)])
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    (HERE / "census").mkdir(exist_ok=True)
    todo = [f for f in args.files if not (HERE / "census" / f"{f}.json").exists()]
    with Pool(args.workers) as pool:
        for row in pool.imap_unordered(census_one, todo):
            print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
