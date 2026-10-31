"""Inspect the layout of the frozen inputs and saved predictions (verifier's own script)."""
import sys
import numpy as np

PROC = "D:/MAESTRO/data/processed/generic_axis_transfer_20261031/"
RUN = "D:/MAESTRO/research/routes/functional_prediction/2026-10-31-generic-axis-transfer/RUN/"

files = [PROC + f for f in ["nci60.npz", "prism24q2.npz", "dev_pool.npz", "l1000_nci.npz", "l1000_24q2.npz"]] + \
        [RUN + "predictions_nci60.npz", RUN + "predictions_prism24q2.npz"]
for f in files:
    print("=" * 100)
    print(f)
    z = np.load(f, allow_pickle=("l1000" in f))
    for k in z.files:
        a = z[k]
        info = f"  {k:20s} shape={a.shape} dtype={a.dtype}"
        if a.dtype.kind in "fc":
            fin = np.isfinite(a)
            info += f" finite={fin.sum()}/{a.size}"
            if fin.any():
                info += f" min={np.nanmin(a):.4g} max={np.nanmax(a):.4g}"
        elif a.dtype.kind in "biu":
            info += f" min={a.min() if a.size else None} max={a.max() if a.size else None} sum={a.sum() if a.size else None}"
        print(info)
        if a.dtype.kind in "USO" and a.size:
            pass
        if a.dtype.kind in "USO" and a.size:
            print("     first:", a.ravel()[:5].tolist())
        if a.ndim == 0:
            print("     value:", a.item())
