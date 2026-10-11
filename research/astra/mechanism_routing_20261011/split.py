"""Unit split for block N (metadata only; no PRISM value is read).

Units: drugs with a block M L1000 profile (GSE92742, 9 lines x {6 h, 24 h}, 10 uM) that also appear
by name in the PRISM Repurposing 19Q4 primary screen. Within each Repurposing Hub mechanism class,
drugs are shuffled (seed 20261011) and assigned reference 50%, development 20%, confirmation 30%,
with cumulative rounding so small classes are spread across roles.

Writes SPLIT.json once.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BLOCK_M = ROOT / "research/astra/mechanism_falsification_20261010"
PRISM = ROOT / "data/external/prism_19q4/raw"
SEED = 20261011
SHARES = (("reference", 0.5), ("development", 0.2), ("confirmation", 0.3))


def l1000_drugs() -> tuple[list[str], list[str]]:
    sys.path.insert(0, str(BLOCK_M))
    import study as S  # noqa: E402
    names, moas = [], []
    for tier in ("open", "sealed"):
        t = S.load_tier(tier)
        names += [str(x) for x in t["drug"]]
        moas += [str(x) for x in t["moa"]]
    return names, moas


def main() -> dict:
    out = HERE / "SPLIT.json"
    if out.exists():
        raise SystemExit("SPLIT.json exists; the split is written once")
    names, moas = l1000_drugs()
    info = pd.read_csv(PRISM / "primary-screen-replicate-collapsed-treatment-info.csv")
    prism_cols = {}
    for r in info.itertuples():
        prism_cols.setdefault(str(r.name).lower(), []).append(str(r.column_name))
    units = sorted((n, m) for n, m in zip(names, moas) if n.lower() in prism_cols)
    rng = np.random.default_rng(SEED)
    role = {}
    by_class: dict[str, list[str]] = {}
    for n, m in units:
        by_class.setdefault(m, []).append(n)
    carry = np.zeros(len(SHARES))
    for m in sorted(by_class):
        drugs = sorted(by_class[m])
        rng.shuffle(drugs)
        for d in drugs:
            carry += np.array([s for _, s in SHARES])
            k = int(np.argmax(carry))
            carry[k] -= 1.0
            role[d] = SHARES[k][0]
    rec = {"seed": SEED, "source": "block M L1000 drugs x PRISM primary names; metadata only",
           "counts": {r: sum(v == r for v in role.values()) for r, _ in SHARES},
           "units": {n: {"moa": m, "role": role[n], "prism_columns": prism_cols[n.lower()]} for n, m in units}}
    out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


if __name__ == "__main__":
    r = main()
    print(r["counts"], len(r["units"]))
