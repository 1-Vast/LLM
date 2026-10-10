"""Fix the line split before any PRISM viability value is parsed (writes SPLIT.json once).

Lines: the 50 Tahoe-100M files. Exclusions follow phenotype_anchor_20261010:
five CONTEXT_UNDERCOUNTED lines are refused; five STATE zero-shot lines are the held-out tier.
PRISM coverage uses only secondary-screen-cell-line-info.csv / primary-screen-cell-line-info.csv.
Reference lines with PRISM are permuted with seed 20261010: the first 15 are development, the
remaining 16 are confirmation (sealed until FREEZE.json exists).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PA = ROOT / "research/astra/phenotype_anchor_20261010"
RAW = ROOT / "data/external/prism_19q4/raw"
SEED = 20261010
HELDOUT = ("c12.h5ad", "c20.h5ad", "c26.h5ad", "c27.h5ad", "c31.h5ad")
UNDERCOUNTED = ("c36.h5ad", "c39.h5ad", "c40.h5ad", "c44.h5ad", "c45.h5ad")


def main() -> dict:
    out_path = HERE / "SPLIT.json"
    if out_path.exists():
        raise SystemExit("SPLIT.json exists; the split is written once")
    cells = pd.read_parquet(ROOT / "data/external/tahoe_phenotype_20261010/metadata/tahoe_cells.parquet")
    dep = cells.drop_duplicates("cell_name").set_index("cell_name")["Cell_ID_DepMap"].to_dict()
    prism = set(pd.read_csv(RAW / "primary-screen-cell-line-info.csv").depmap_id.dropna())
    lines = {}
    for i in range(50):
        f = f"c{i}.h5ad"
        name = json.loads((PA / "obs" / f"{f}.json").read_text(encoding="utf-8"))["cell_name"][0]
        lines[f] = {"name": name, "depmap_id": dep.get(name), "prism_primary": dep.get(name) in prism}
    ref_prism = [f for f in lines if f not in HELDOUT + UNDERCOUNTED and lines[f]["prism_primary"]]
    perm = np.random.default_rng(SEED).permutation(len(ref_prism))
    order = [ref_prism[i] for i in perm]
    split = {
        "seed": SEED,
        "development": sorted(order[:15], key=lambda f: int(f[1:-5])),
        "confirmation": sorted(order[15:], key=lambda f: int(f[1:-5])),
        "heldout_zeroshot": [f for f in HELDOUT if lines[f]["prism_primary"]],
        "heldout_no_late_endpoint": [f for f in HELDOUT if not lines[f]["prism_primary"]],
        "reference_no_late_endpoint": [f for f in lines if f not in HELDOUT + UNDERCOUNTED and not lines[f]["prism_primary"]],
        "undercounted": list(UNDERCOUNTED),
        "lines": lines,
    }
    out_path.write_text(json.dumps(split, indent=1), encoding="utf-8")
    return split


if __name__ == "__main__":
    s = main()
    for k in ("development", "confirmation", "heldout_zeroshot", "heldout_no_late_endpoint", "reference_no_late_endpoint"):
        print(k, len(s[k]), [s["lines"][f]["name"] for f in s[k]])
