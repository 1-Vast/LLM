"""Regenerate cache/plates.csv (one row per plate: seeding date, cell stock) from the Jaaks raw-data zip; reads no response.

Usage: python plates.py [out.csv]   (default cache/plates.csv; refuses to overwrite)
"""
import sys
import zipfile
from pathlib import Path

import pandas as pd

import cas_data as D

HERE = Path(__file__).resolve().parent
COLS = ["BARCODE", "RESEARCH_PROJECT", "DATE_CREATED", "SCAN_DATE", "CELL_ID", "MASTER_CELL_ID", "CELL_LINE_NAME",
        "DRUGSET_ID", "SEEDING_DENSITY"]

if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "cache/plates.csv"
    if out.exists():
        raise SystemExit(f"{out} exists")
    with zipfile.ZipFile(D.RAW_ZIP) as z:
        name = [n for n in z.namelist() if n.endswith(".csv")][0]
        parts = []
        with z.open(name) as f:
            for chunk in pd.read_csv(f, usecols=COLS, chunksize=2_000_000, low_memory=False):
                parts.append(chunk.drop_duplicates("BARCODE"))
    p = pd.concat(parts).drop_duplicates("BARCODE").sort_values("BARCODE")
    p["CELL_LINE_NAME"] = p.CELL_LINE_NAME.astype(str).str.strip()
    out.parent.mkdir(exist_ok=True)
    p.to_csv(out, index=False, lineterminator="\n")
    print(len(p), "plates ->", out)
