"""Feature-axis compatibility: X_hvg columns of each held-out file equal log1p(X[:, gene]) for the
1,969 coordinates identified on c39 (and c0-c2) by the 2026-09 identity receipt.

For sampled DMSO cells already extracted, the sparse normalised-count row is read by HTTP range
through h5py and compared with the stored X_hvg row. Unresolved coordinates are reported, not named.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from remote import CACHE, BlockFile, RangeClient  # noqa: E402

IDENTITY = json.loads((ROOT / "data/external/arc_state/hvg_identity.json").read_text(encoding="utf-8"))
C39_VAR = None


def check(file: str, cells: int = 16) -> dict:
    import h5py
    plan = json.loads((CACHE / "extract" / "plans" / f"{file}.plan.json").read_text(encoding="utf-8"))
    rows = np.load(CACHE / "extract" / file / "rows.npy", mmap_mode="r")
    slots = np.load(CACHE / "extract" / file / "slots.npz")
    start = dict(zip(slots["group"].tolist(), slots["start"].tolist()))
    control = next(g for g in plan["groups"] if g["control"])
    picks = list(range(0, len(control["rows"]), max(1, len(control["rows"]) // cells)))[:cells]
    client = RangeClient(HERE / "axis_check" / "ledgers" / f"{file}.jsonl")
    size = client.size(file)
    handle = BlockFile(client, file, size, cache_dir=CACHE / "blocks" / file)
    gene_index = np.array([-1 if i is None else i for i in IDENTITY["gene_indices"]])
    named = gene_index >= 0
    worst, nonzero_checked, all_zero_unresolved = 0.0, 0, []
    with h5py.File(handle, "r") as f:
        names = f["var"]["gene_name"]
        n_var = names.shape[0]
        sample_names = [names[int(i)] for i in gene_index[named][:: max(1, named.sum() // 40)]]
        indptr = f["X"]["indptr"]
        for p in picks:
            r = int(control["rows"][p])
            a, b = int(indptr[r]), int(indptr[r + 1])
            idx = f["X"]["indices"][a:b]
            val = f["X"]["data"][a:b]
            dense = np.zeros(n_var, dtype=np.float64)
            dense[idx] = val
            stored = np.asarray(rows[start[control["group"]] + p], dtype=np.float64)
            expected = np.log1p(dense[gene_index[named]])
            worst = max(worst, float(np.max(np.abs(expected - stored[named]))))
            nonzero_checked += int((expected > 0).sum())
            library = float(dense.sum())
    sample_names = [x.decode() if isinstance(x, bytes) else str(x) for x in sample_names]
    expected_names = [IDENTITY["gene_names"][j] for j in np.flatnonzero(named)[:: max(1, named.sum() // 40)]]
    result = {"file": file, "cells_checked": len(picks), "named_coordinates": int(named.sum()),
              "max_abs_log1p_mismatch": worst, "nonzero_values_checked": nonzero_checked,
              "last_cell_library_size": library, "var_length": int(n_var),
              "sampled_gene_names_match_identity_receipt": sample_names == expected_names,
              "unresolved_coordinates": int((~named).sum()), "passed": worst < 1e-5 and sample_names == expected_names,
              "remote_requests": client.requests, "remote_bytes": client.bytes}
    (HERE / "axis_check").mkdir(exist_ok=True)
    (HERE / "axis_check" / f"{file}.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(json.dumps(check(f)), flush=True)
