"""Check that the promoted module reproduces the confirmed arms on confirmation 1 (NCI-60) and confirmation 2.

Usage: python promotion_check.py SRC_DIR DATA_DIR RUN_DIR OUT_JSON
Uses only the public functions of virtual_cell.transcriptional_transfer found under SRC_DIR.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


def main(src: Path, data: Path, run: Path, out: Path) -> None:
    sys.path.insert(0, str(src))
    from virtual_cell.transcriptional_transfer import (GENERIC_AXES_SCOPE, VALIDATED_SCOPE, fit_generic_axes,
                                                       transfer_profile)
    result = {"module": str(src / "virtual_cell/transcriptional_transfer.py")}
    d = np.load(data / "nci60.npz", allow_pickle=True)
    p = np.load(run / "predictions_nci60.npz", allow_pickle=True)
    X, Y, fold = d["signature"], d["profile"], d["fold"]
    b0, c1 = np.full(Y.shape, np.nan), np.full(Y.shape, np.nan)
    scopes = set()
    for f in range(10):
        q, r = np.where(fold == f)[0], fold != f
        axes = fit_generic_axes(X[r], n_axes=5)
        for i in q:
            o0 = transfer_profile(X[i], X[r], Y[r], k=5)
            o1 = transfer_profile(X[i], X[r], Y[r], k=20, generic_axes=axes)
            b0[i], c1[i] = o0.values, o1.values
            scopes |= {o0.scope, o1.scope}
    result["nci60"] = {"max_abs_diff_B0": float(np.nanmax(np.abs(b0 - p["pred_B0"]))),
                       "max_abs_diff_C1": float(np.nanmax(np.abs(c1 - p["pred_C1"]))),
                       "nan_pattern_equal": bool((np.isnan(b0) == np.isnan(p["pred_B0"])).all()
                                                 and (np.isnan(c1) == np.isnan(p["pred_C1"])).all())}
    pool = np.load(data / "dev_pool.npz", allow_pickle=True)
    q24 = np.load(data / "prism24q2.npz", allow_pickle=True)
    p = np.load(run / "predictions_prism24q2.npz", allow_pickle=True)
    col = {ln: i for i, ln in enumerate(pool["line"])}
    Yr = pool["profile"][:, [col[ln] for ln in q24["line"]]]
    axes = fit_generic_axes(pool["signature"], n_axes=5)
    b0 = np.stack([transfer_profile(x, pool["signature"], Yr, k=5).values for x in q24["signature"]])
    c1 = np.stack([transfer_profile(x, pool["signature"], Yr, k=20, generic_axes=axes).values for x in q24["signature"]])
    result["prism24q2"] = {"max_abs_diff_B0": float(np.nanmax(np.abs(b0 - p["pred_B0"]))),
                           "max_abs_diff_C1": float(np.nanmax(np.abs(c1 - p["pred_C1"])))}
    result["scopes_seen"] = sorted(scopes)
    result["pass"] = bool(max(result["nci60"]["max_abs_diff_B0"], result["nci60"]["max_abs_diff_C1"],
                              result["prism24q2"]["max_abs_diff_B0"], result["prism24q2"]["max_abs_diff_C1"]) < 1e-6
                          and result["nci60"]["nan_pattern_equal"]
                          and set(result["scopes_seen"]) == {VALIDATED_SCOPE, GENERIC_AXES_SCOPE})
    out.write_bytes((json.dumps(result, indent=1) + "\n").encode("utf-8"))
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main(*(Path(a) for a in sys.argv[1:5]))
