"""Verify the kinobeads substitution package.

Checks the freeze digests (own files, reused action-substitution files, Klaeger data), recomputes every primary point
estimate from kb_units.csv, re-runs the seeded cluster bootstrap to reproduce the intervals exactly, and re-applies the
pre-registered verdict rule. Usage: python verify.py
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AS = ROOT / "research/action_substitution_20261019"
KL = ROOT / "data/external/klaeger2017_chembl"


def digest(p):
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    ok = True

    def check(cond, msg):
        nonlocal ok
        ok &= bool(cond)
        print(f"{'ok ' if cond else 'BAD'} {msg}")

    fr = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for f, h in fr["files"].items():
        check(digest(HERE / f) == h, f"freeze {f}")
    for f, h in fr["reused_from_action_substitution"].items():
        check(digest(AS / f) == h, f"reused {f}")
    for f, h in fr["data"].items():
        check(digest(KL / f) == h, f"data {f}")
    man = json.loads((KL / "MANIFEST.json").read_text(encoding="utf-8"))
    for f, h in man["sha256"].items():
        check(hashlib.sha256((KL / f).read_bytes()).hexdigest() == h, f"manifest {f}")

    sys.path.insert(0, str(HERE))
    sys.argv = sys.argv[:1]
    import kb_run as K  # imports frozen lofo for auroc only; no data read
    r = json.loads((HERE / "KB_RESULT.json").read_text(encoding="utf-8"))
    mp = json.loads((HERE / "MAPPING.json").read_text(encoding="utf-8"))
    check(mp["n_mapped"] >= 15 and mp["coverage_gate"] == "PASS", f"coverage {mp['n_mapped']} mapped >= 15")
    check(r["gate"]["pass"] and r["gate"]["n_new"] == 1950 and r["gate"]["unmatched"] == 0, "reproduction gate recorded PASS")
    u = pd.read_csv(HERE / "kb_units.csv", dtype={"X": str}, float_precision="round_trip")
    check(len(u) == 1950 and u.X.nunique() == 27, f"kb_units: {len(u)} units, {u.X.nunique()} implementations")
    prim_names = set(r["primary_implementations"])
    check(len(prim_names) == 20 and "Dactolisib" not in prim_names
          and prim_names <= set(mp["evaluable_mapped"]), "primary = 20 mapped implementations with a defined profile")
    prim = u[u.name.isin(prim_names)]
    pt = K.stats(prim)
    for k, v in pt.items():
        check(abs(v - r["primary"]["point"][k]) < 1e-12, f"point {k} = {v:.6g}")
    rng = np.random.default_rng(20261019)
    b = K.boot(prim, rng)
    for k, v in b["ci"].items():
        check(np.allclose(v, r["primary"]["ci"][k], rtol=0, atol=1e-12), f"ci {k} [{v[0]:.6g}, {v[1]:.6g}]")
    b2 = K.boot(u, rng)
    check(all(np.allclose(v, r["secondary_all27"]["ci"][k], rtol=0, atol=1e-12) for k, v in b2["ci"].items()), "secondary all-27 intervals")
    ci = b["ci"]
    t1 = ci["B5_minus_K"][0] > 0 and ci["B0_minus_K"][0] > 0
    t2 = ci["auroc_sim_kb"][0] > 0.5
    verdict = "SUPPORTED" if t1 and t2 else "NOT_SUPPORTED"
    check(verdict == r["verdict"] == "NOT_SUPPORTED" and t1 == r["test1_prediction"]["pass_"] and t2 == r["test2_ranking"]["pass_"],
          f"verdict {verdict} (test1 {t1}, test2 {t2})")
    print("VERIFY OK" if ok else "VERIFY FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
