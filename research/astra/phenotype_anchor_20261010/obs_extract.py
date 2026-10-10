"""Stage 1: obs-only extraction of same-well phenotype inputs from pinned State-Tahoe-Filtered.

Reads per-cell categorical codes (condition, plate, well, QC flag, cell-cycle phase) and the
continuous S/G2M scores. No expression value (X, obsm/X_hvg, obsm/X_state) is read. Held-out
contexts are refused unless ``--allow-heldout`` is passed, which the protocol permits only after
the freeze in ``FREEZE.json`` exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research/astra/zeroshot_context_20261007"))
from remote import REVISION, BlockFile, RangeClient, dataset_layout, read_contiguous  # noqa: E402

CACHE = ROOT / "data/external/tahoe_phenotype_20261010"
HELDOUT = ("c12.h5ad", "c20.h5ad", "c26.h5ad", "c27.h5ad", "c31.h5ad")
CATEGORICAL = ("drugname_drugconc", "plate", "sample", "pass_filter", "phase")
NUMERIC = ("S_score", "G2M_score")


def _categories(group):
    return [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in group["categories"][:]]


def extract_one(name: str) -> dict:
    import h5py
    import numpy as np
    target = CACHE / "obs" / f"{name}.npz"
    receipt_path = HERE / "obs" / f"{name}.json"
    if target.exists() and receipt_path.exists():
        return json.loads(receipt_path.read_text(encoding="utf-8"))
    started = time.perf_counter()
    client = RangeClient(HERE / "obs" / "ledgers" / f"{name}.jsonl", user_agent="MAESTRO-phenotype-anchor/1")
    size = client.size(name)
    handle = BlockFile(client, name, size, cache_dir=CACHE / "blocks" / name)
    out = {"file": name, "revision": REVISION, "file_bytes": size, "categories": {}, "layouts": {}}
    arrays = {}
    with h5py.File(handle, "r") as f:
        obs = f["obs"]
        out["cell_name"] = _categories(obs["cell_name"])
        for column in CATEGORICAL:
            group = obs[column]
            out["categories"][column] = _categories(group)
            layout = dataset_layout(group["codes"])
            out["layouts"][column] = layout
            arrays[column] = read_contiguous(client, name, layout, f"obs_codes:{column}")
        for column in NUMERIC:
            layout = dataset_layout(obs[column])
            out["layouts"][column] = layout
            arrays[column] = read_contiguous(client, name, layout, f"obs_numeric:{column}")
    n = {len(v) for v in arrays.values()}
    if len(n) != 1:
        raise ValueError(f"{name}: obs column lengths differ {n}")
    out["n_cells"] = n.pop()
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(target, **arrays)
    out["sha256"] = {k: hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest() for k, v in arrays.items()}
    out["remote_requests"], out["remote_bytes"] = client.requests, client.bytes
    out["seconds"] = round(time.perf_counter() - started, 3)
    out["expression_read"] = False
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="*", default=[f"c{i}.h5ad" for i in range(50)])
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--allow-heldout", action="store_true")
    args = parser.parse_args()
    files = list(args.files)
    if not args.allow_heldout:
        files = [f for f in files if f not in HELDOUT]
    elif not (HERE / "FREEZE.json").exists():
        raise SystemExit("held-out obs may be read only after FREEZE.json exists")
    with Pool(args.workers) as pool:
        for row in pool.imap_unordered(extract_one, files):
            print(json.dumps({k: row[k] for k in ("file", "cell_name", "n_cells", "remote_bytes", "seconds")}), flush=True)


if __name__ == "__main__":
    main()
