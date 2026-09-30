"""Verify whether the served STATE prediction output differs at the embedding level, not the file level.

File summary
- Path: research/identifiability_audit/verify_state_outputs.py
- Purpose: the prediction files of two arms can differ byte-wise simply because the output carries a
  copy of the query's `obs`. This hashes the predicted embedding itself, so "the served shift is
  unchanged" is a statement about numbers rather than about file bytes.
- Run: <state python> -m research.identifiability_audit.verify_state_outputs
- Interfaces: `main`
- Depends on: anndata, numpy, hashlib
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "identifiability_audit_20260930" / "state_sensitivity"
EMBED_KEY = "X_hvg"


def main() -> None:
    import anndata as ad

    predictions = sorted((OUT / "predictions").glob("*.h5ad"))
    rows = []
    for path in predictions:
        if path.name.endswith(".subset.h5ad"):
            continue
        data = ad.read_h5ad(path)
        matrix = np.asarray(data.obsm[EMBED_KEY], dtype=np.float32)
        rows.append({"arm": path.stem, "output_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "embedding_sha256": hashlib.sha256(np.ascontiguousarray(matrix).tobytes()).hexdigest(),
                     "rows": int(matrix.shape[0]), "features": int(matrix.shape[1])})
    report = {"embed_key": EMBED_KEY, "arms": rows}
    (OUT / "output_embedding_identity.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    for row in rows:
        print(row["arm"], row["embedding_sha256"][:16], "file", row["output_file_sha256"][:12], row["rows"])


if __name__ == "__main__":
    main()
