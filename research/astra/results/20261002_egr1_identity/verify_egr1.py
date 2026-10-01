"""Read-only, chunked EGR1 identity check; does not import or execute STATE."""
from pathlib import Path
import hashlib
import json

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent / "receipt.json"
FILES = {
    "dataset": ROOT / "data/external/arc_state/tahoe_metadata_source/c39.h5ad",
    "axis": ROOT / "data/virtual_cell/tahoe_c39_x_hvg_feature_names.json",
    "identity": ROOT / "data/external/arc_state/hvg_identity.json",
    "installed_forward": ROOT / "data/external/arc_state/source/src/state/tx/models/state_transition.py",
    "installed_infer": ROOT / "data/external/arc_state/source/src/state/_cli/_tx/_infer.py",
    "source": Path(__file__).resolve(),
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    if OUT.exists():
        raise FileExistsError("Keep the existing evidence receipt frozen.")
    before = {key: digest(path) for key, path in FILES.items()}
    axis = json.loads(FILES["axis"].read_text(encoding="utf-8"))
    identity = json.loads(FILES["identity"].read_text(encoding="utf-8"))
    hvg_column = axis["names"].index("EGR1")
    maximum_difference = 0.0
    above_tolerance = nonzero = 0
    raw_min = hvg_min = float("inf")
    raw_max = hvg_max = float("-inf")
    hvg_sum = 0.0
    with h5py.File(FILES["dataset"], "r") as f:
        x = f["X"]
        encoding = x.attrs["encoding-type"]
        assert encoding == "csr_matrix"
        shape = tuple(int(value) for value in x.attrs["shape"])
        columns = np.flatnonzero(f["var/gene_name"].asstr()[:] == "EGR1")
        assert len(columns) == 1
        x_column = int(columns[0])
        assert identity["gene_names"][hvg_column] == "EGR1"
        assert identity["gene_indices"][hvg_column] == x_column
        assert f["obsm/X_hvg"].shape == (shape[0], axis["feature_count"])
        # Row pointers are small; expression data and indices stay chunked.
        pointers = x["indptr"][:]
        for start in range(0, shape[0], 1024):
            stop = min(start + 1024, shape[0])
            lo, hi = int(pointers[start]), int(pointers[stop])
            indices = x["indices"][lo:hi]
            positions = np.flatnonzero(indices == x_column)
            raw = np.zeros(stop - start, dtype=x["data"].dtype)
            if len(positions):
                values = x["data"][lo:hi]
                rows = np.searchsorted(pointers[start:stop + 1] - lo, positions, side="right") - 1
                np.add.at(raw, rows, values[positions])
            hvg = f["obsm/X_hvg"][start:stop, hvg_column]
            difference = np.abs(np.log1p(raw) - hvg)
            assert np.isfinite(raw).all() and np.isfinite(hvg).all()
            maximum_difference = max(maximum_difference, float(difference.max()))
            above_tolerance += int(np.count_nonzero(difference > 1e-5))
            nonzero += int(np.count_nonzero(raw))
            raw_min, raw_max = min(raw_min, float(raw.min())), max(raw_max, float(raw.max()))
            hvg_min, hvg_max = min(hvg_min, float(hvg.min())), max(hvg_max, float(hvg.max()))
            hvg_sum += float(hvg.astype(np.float64).sum())
    after = {key: digest(path) for key, path in FILES.items()}
    assert before == after, "Source changed during the check."
    receipt = {
        "purpose": "local EGR1 coordinate identity; no STATE forwards or biological evaluation",
        "files": {key: {"path": str(path), "sha256_before": before[key], "sha256_after": after[key]}
                  for key, path in FILES.items()},
        "encoding": encoding, "shape": shape, "row_chunk": 1024,
        "x_column": x_column, "x_hvg_column": hvg_column,
        "raw_nonzero": nonzero, "raw_range": [raw_min, raw_max],
        "hvg_range": [hvg_min, hvg_max], "hvg_mean_float64": hvg_sum / shape[0],
        "max_abs_log1p_difference": maximum_difference,
        "tolerance": 1e-5, "rows_above_tolerance": above_tolerance,
        "passed": above_tolerance == 0 and nonzero > 0,
        "bounds": "X is normalized expression, not raw UMI. Only this gene and fixed c39 file are checked; other unresolved genes, new RNA, training exposure, and biological utility remain uncertified.",
    }
    OUT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
