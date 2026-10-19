"""Data access for the conditional action-substitution study (Jaaks et al. 2022 GDSC anchored combination screen).

Design columns (identities, targets, concentrations, plates) and outcome columns are read by separate functions so that
the eligibility census can run without reading any response value. All Jaaks records were already opened by MAESTRO in
October 2026 (research/astra feedback-validation studies); everything here is development evidence.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare"
ORIGINAL = SRC / "Original screen_All tissues_fitted data.csv"
VALIDATION = SRC / "Validation screen_All tissues_fitted data.csv"
RAW_ZIP = SRC / "Original_screen_All_tissues_raw_data.csv.zip"
MD5_ORIGINAL = "786589e5eb556670cc7d24356487f8fd"

DESIGN = ["BARCODE", "COMBI_ID", "Tissue", "CELL_LINE_NAME", "SIDM", "ANCHOR_ID", "ANCHOR_NAME", "ANCHOR_TARGET",
          "ANCHOR_PATHWAY", "ANCHOR_DRUG_TYPE", "ANCHOR_CONC", "LIBRARY_ID", "LIBRARY_NAME", "LIBRARY_TARGET",
          "LIBRARY_PATHWAY", "LIBRARY_DRUG_TYPE", "LIBRARY_CONC"]
OUTCOME = ["ANCHOR_VIABILITY", "LIBRARY_EMAX", "LIBRARY_XMID", "LIBRARY_AUC", "LIBRARY_RMSE", "SYNERGY_RMSE",
           "SYNERGY_EXP_EMAX", "SYNERGY_OBS_EMAX", "SYNERGY_DELTA_EMAX", "SYNERGY_XMID", "SYNERGY_DELTA_XMID",
           "SYNERGY_EXP_AUC", "SYNERGY_OBS_AUC", "SYNERGY_DELTA_AUC", "Synergy", "DAY1_NORM_MEAN", "GROWTH_RATE"]


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def target_set(s) -> frozenset:
    """Normalised annotated target set ('CHEK1, CHEK2' -> {'CHEK1','CHEK2'})."""
    if not isinstance(s, str):
        return frozenset()
    parts = re.split(r"[,;/]", s)
    return frozenset(p.strip().upper() for p in parts if p.strip())


def _read(path: Path, cols: list[str]) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=cols, low_memory=False,
                     dtype={"ANCHOR_ID": str, "LIBRARY_ID": str, "ANCHOR_CONC": str, "COMBI_ID": str})
    for c in ("ANCHOR_NAME", "LIBRARY_NAME", "CELL_LINE_NAME"):
        if c in df:
            df[c] = df[c].astype(str).str.strip()
    return df


def design(screen: str = "original") -> pd.DataFrame:
    """Design-only frame: no response column is read."""
    return _read(ORIGINAL if screen == "original" else VALIDATION, DESIGN)


def full(screen: str = "original") -> pd.DataFrame:
    """Design plus outcome columns (exposed development data)."""
    return _read(ORIGINAL if screen == "original" else VALIDATION, DESIGN + OUTCOME)
