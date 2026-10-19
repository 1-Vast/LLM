"""Verify the P0 gate package: freeze digests (own and imported), and recomputation of headline numbers from saved tables."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent


def digest(p):
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    ok = True
    fr = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for f, h in {**fr["files"], **fr["imported"]}.items():
        same = digest(HERE / f) == h
        ok &= same
        print(f"{'ok ' if same else 'BAD'} freeze {f}")
    rp = HERE / "P0_RESULT.json"
    if not rp.exists():
        print("P0_RESULT.json missing")
        sys.exit(1)
    r = json.loads(rp.read_text(encoding="utf-8"))
    u = pd.read_csv(HERE / "p0_units_S.csv", dtype={"X": str})
    for a in ("F", "T", "FT", "B0", "B1"):
        m = float(np.mean((u["d_" + a] - u.obs) ** 2))
        same = abs(m - r["P0A_S"]["arms"][a]["mse"]) < 1e-12
        ok &= same
        print(f"{'ok ' if same else 'BAD'} P0-A S MSE {a} = {m:.6f}")
    s = pd.read_csv(HERE / "p0c_sets.csv")
    for a in ("F", "T", "FT", "B1"):
        g = float((s[a] - s.random).mean())
        same = abs(g - r["P0C"]["gain_over_random"][a]) < 1e-12
        ok &= same
        print(f"{'ok ' if same else 'BAD'} P0-C gain {a} = {g:+.5f}")
    print("decision:", r["decision"])
    print("ALL OK" if ok else "VERIFICATION FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
