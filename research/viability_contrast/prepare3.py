"""Additive data-pack extension for the v3 dual-core run (SMILES table).

File summary
- Path: research/viability_contrast/prepare3.py
- Purpose: write outputs/viability_contrast_20260928/prepared/smiles.csv mapping every pack
  compound to its first-variant SMILES from the same PRISM source release. This is an
  addition, not a rebuild: the v1/v2 pack files stay byte-identical (freeze.json and
  freeze2.json still verify), and freeze3.json covers this file.
- Depends on: research/viability_contrast/prepare.py
"""
from __future__ import annotations

import pandas as pd

from . import prepare

OUT = prepare.OUT


def build() -> str:
    cols = ["broad_id", "smiles"]
    df = pd.read_csv(prepare.PRISM, usecols=cols, low_memory=False)
    df["compound"] = df["broad_id"].map(prepare.compound_id)
    smi = df.drop_duplicates("compound").set_index("compound")["smiles"]
    pack = prepare.load_pack()
    out = pd.DataFrame({"compound": pack["compounds"],
                        "smiles": [smi.get(c) for c in pack["compounds"]]})
    path = OUT / "smiles.csv"
    out.to_csv(path, index=False)
    missing = int(out["smiles"].isna().sum())
    return f"smiles.csv written for {len(out)} compounds ({missing} missing)"


if __name__ == "__main__":
    print(build())
