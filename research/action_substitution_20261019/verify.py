"""Verify the action-substitution package: freeze digests, source checksum, and recomputation of reported numbers.

Usage: python verify.py            (fast: digests + recomputation from saved unit tables)
       python verify.py --data     (also checks the source file MD5, about 200 MB read)
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
METHODS = ["B0", "B1", "B1p", "B2", "B3", "B4", "B5", "M", "MnoP"]


def digest(p):
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    ok = True
    for fz in ("FREEZE.json", "FREEZE_P3.json"):
        fr = json.loads((HERE / fz).read_text(encoding="utf-8"))
        for f, h in fr["files"].items():
            same = digest(HERE / f) == h
            ok &= same
            print(f"{'ok ' if same else 'BAD'} {fz} {f}")
    expect = {"SYNERGY_DELTA_AUC": ("PARTNER_SPECIFIC_REFINEMENT", "PARTNER_SPECIFIC_REFINEMENT"),
              "SYNERGY_OBS_AUC": ("GENERIC_REFINEMENT_ONLY", "NO_REFINEMENT_VALUE")}
    for ep, (l0, l2) in expect.items():
        r = json.loads((HERE / f"REFINE_{ep}.json").read_text(encoding="utf-8"))
        same = r["prior_B0"]["label"] == l0 and r["prior_B2"]["label"] == l2
        ok &= same
        m = r["prior_B0"]["mse"]
        print(f"{'ok ' if same else 'BAD'} refine {ep}: B0-prior {r['prior_B0']['label']} (R0 {m['R0']:.6f} R1 {m['R1']:.6f} "
              f"R2 {m['R2']:.6f}), B2-prior {r['prior_B2']['label']}")
    if "--data" in sys.argv:
        import cas_data as D
        same = D.md5(D.ORIGINAL) == D.MD5_ORIGINAL
        ok &= same
        print(f"{'ok ' if same else 'BAD'} source md5")
    rep = json.loads((HERE / "REPRO.json").read_text(encoding="utf-8"))
    print("gate:", rep["decision"]["label"])
    ok &= rep["decision"]["label"] == "CONDITIONALLY_QUALIFIED"
    for ep in ("SYNERGY_DELTA_AUC", "SYNERGY_OBS_AUC"):
        res_p = HERE / f"LOFO_{ep}.json"
        if not res_p.exists():
            print("missing", res_p.name)
            ok = False
            continue
        res = json.loads(res_p.read_text(encoding="utf-8"))
        u = pd.read_csv(HERE / f"lofo_units_{ep}.csv")
        mse = {m: float(np.mean((u["d_" + m] - u.obs) ** 2)) for m in METHODS}
        same = all(abs(mse[m] - res["primary"]["mse"][m]) < 1e-12 for m in METHODS) and len(u) == res["primary"]["n_units"]
        ok &= same
        best = res["primary"]["best_baseline"]
        print(f"{'ok ' if same else 'BAD'} {ep}: n={len(u)} label={res['primary']['label']} best={best} "
              f"MSE best={mse[best]:.6f} M={mse['M']:.6f} rel={(mse[best] - mse['M']) / mse[best]:+.4f}")
    print("ALL OK" if ok else "VERIFICATION FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
