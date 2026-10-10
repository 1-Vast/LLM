"""A separate gene-named control diagnostic from already retained source bytes.

This channel does not authenticate X_hvg or release the old 250-cell study.
All source cells were previously exposed in the failed coordinate audit.
"""
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np

from research.decision_value.observation_reliability.axis_verify import SavedFile, slice_array
from research.decision_value.observation_reliability.noise import audit_groups


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = HERE.parent / "observation_reliability"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    destination = HERE / "named_channel"
    if (destination / "RESULTS.json").exists():
        raise FileExistsError("Named-channel diagnostic refuses overwrite")
    protocol = json.loads((destination / "PROTOCOL.json").read_text())
    freeze = json.loads((destination / "FREEZE.json").read_text())
    for name, expected in freeze["sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("frozen_input_hash_mismatch")
    receipts = [json.loads(line) for line in (OLD / "axis/NETWORK.jsonl").read_text().splitlines()]
    for item in receipts:
        if item["file"] == protocol["source_file"]:
            body = (ROOT / item["asset"]).read_bytes()
            if len(body) != item["bytes"] or hashlib.sha256(body).hexdigest() != item["sha256"]:
                raise ValueError("retained_source_payload_hash_mismatch")
    census = json.loads((OLD / "axis/CENSUSES.json").read_text())[protocol["source_file"]]
    source = SavedFile(protocol["source_file"], census["file_bytes"], receipts)
    groups, metadata, all_rows, matrices = [], [], [], []
    with h5py.File(source, "r") as handle:
        names = [v.decode() if isinstance(v, bytes) else str(v) for v in handle["var/gene_name"][:]]
        if any(names.count(symbol) != 1 for symbol in protocol["symbols"]):
            raise ValueError("exact_singleton_source_gene_required")
        gene_indices = [names.index(symbol) for symbol in protocol["symbols"]]
        for group in protocol["selected"]:
            vectors = []
            for row in group["rows"]:
                start, stop = map(int, slice_array(source, handle["X/indptr"], row, row + 2))
                indices = slice_array(source, handle["X/indices"], start, stop)
                values = slice_array(source, handle["X/data"], start, stop)
                if len(indices) != len(values) or len(set(indices)) != len(indices):
                    raise ValueError("invalid_sparse_gene_values")
                if not np.isfinite(values).all() or (values < 0).any():
                    raise ValueError("invalid_source_expression")
                sparse = dict(zip(indices.tolist(), values.tolist()))
                vectors.append(np.log1p([sparse.get(index, 0.0) for index in gene_indices]))
            matrix = np.asarray(vectors, dtype=float)
            groups.append(matrix)
            metadata.append({key: group[key] for key in ("file", "cell", "plate", "sample", "rows")})
            all_rows.extend(group["rows"])
            matrices.append(matrix)
    result = audit_groups(groups, protocol["weights"], metadata,
                          protocol["bootstrap_draws"], protocol["seed"])
    result.update(schema="direct_gene_named_control_diagnostic_v1", status="PASS_DIAGNOSTIC_ONLY",
                  source_revision=protocol["source_revision"], source_file=protocol["source_file"],
                  channel="log1p(normalized_stored_X)[exact_gene_names]",
                  source_gene_indices=gene_indices, source_symbols=protocol["symbols"],
                  cells=len(all_rows), pooled_sample_ids=len({g["sample"] for g in metadata}),
                  new_network_calls=0, old_HVG_axis_authenticated=False,
                  old250_noise_study_released=False, decision_gain=None)
    ratios = [g["full_to_diagonal_ratio"] for g in result["groups"] if g["full_to_diagonal_ratio"] is not None]
    result["descriptive_summary"] = {
        "groups": len(groups), "cells_per_group": [len(g) for g in groups],
        "full_to_diagonal_ratio_min_median_max": np.quantile(ratios, [0, .5, 1]).tolist(),
        "nonzero_cells_by_named_gene": (np.concatenate(matrices) > 0).sum(0).tolist(),
        "independent_culture_count": None,
        "interpretation": "Conditional n=8 cell sampling diagnostic in previously exposed controls; no equivalence to hidden HVG coordinates or new biological confirmation.",
    }
    np.savez_compressed(destination / "VECTORS.npz", rows=np.asarray(all_rows),
                        expression=np.concatenate(matrices), symbols=np.asarray(protocol["symbols"]))
    write(destination / "RESULTS.json", result)
    print(json.dumps(result["descriptive_summary"]))


if __name__ == "__main__":
    main()
