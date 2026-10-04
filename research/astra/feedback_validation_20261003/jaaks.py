"""Plate-disjoint orientation-split panels from the Jaaks et al. 2022 anchored combination screen.

File summary
- Path: research/astra/feedback_validation_20261003/jaaks.py
- Purpose: turn the GDSC anchored screen (Jaaks et al. 2022 Nature 603:166, figshare 16843597,
  `original_screen_all_tissues_fitted.csv`) into discovery panels whose purchasable screen
  measurement and hidden validation measurement of every candidate sit on disjoint plates.
- Core points:
  - Plate structure (design columns): every plate holds one cell line, a fixed doublet of library
    (titrated) drugs and all anchors; doublets recur across lines. A frozen seeded split of the
    doublets into S and V per tissue makes the menu S x V pairs. Replicate "SV": screen = S drug
    anchored with the V drug titrated (V-library plates); validation = V drug anchored with the S
    drug titrated (S-library plates). Replicate "VS" swaps the roles on the same menu. Screen and
    validation plates are therefore disjoint by construction, and this is asserted per line.
  - Measurement QC (authors' rule): drop rows with SYNERGY_RMSE > 0.2 or LIBRARY_RMSE > 0.2 or a
    missing Synergy / delta-Emax / observed Emax; counts recorded.
  - Authors' calls: per anchor concentration synergistic if >= half of replicate rows say so
    (strict-majority calls are kept for a sensitivity analysis); an ordered combination in a line
    is synergistic if so at either anchor concentration.
  - Screen label y (learning and ranking) = 100 x max over anchor concentrations of the mean
    SYNERGY_DELTA_EMAX of the screen orientation. Menu = S x V pairs with both orientations present
    after QC. History = other lines of the same tissue, screen orientation of the same replicate.
  - Wells charged per purchase = 14 (7 library doses x 2 anchor concentrations) x screen plates.
  - Outcome columns are read only through `build_panels`, which requires a vault ticket whose
    data digest matches the file.
- Interfaces: `plate_design`, `build_panels`, `rescreen_calls`, `synthetic_release`.
- Depends on: numpy, pandas, research.certified_discovery.screens (frozen; imported), `study.Panel`.
"""
from __future__ import annotations

import gzip
from pathlib import Path

import numpy as np
import pandas as pd

from research.certified_discovery.screens import Library, sha256

from .study import Panel

ROOT = Path(__file__).resolve().parents[3]
RELEASE = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare/original_screen_all_tissues_fitted.csv"
RESCREEN = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare/validation_screen_all_tissues_fitted.csv"
DESIGN_COLUMNS = ["BARCODE", "Tissue", "CELL_LINE_NAME", "SIDM", "ANCHOR_ID", "ANCHOR_NAME", "ANCHOR_CONC",
                  "LIBRARY_ID", "LIBRARY_NAME", "LIBRARY_CONC"]
OUTCOME_COLUMNS = ["SYNERGY_DELTA_EMAX", "SYNERGY_OBS_EMAX", "SYNERGY_RMSE", "LIBRARY_RMSE", "Synergy"]
TISSUE_CODE = {"Breast": 1, "Colon": 2, "Pancreas": 3}
SPLIT_SEED = 20261003
RMSE_MAX = 0.2
WELLS_PER_PLATE = 14               # 7 library doses x 2 anchor concentrations, single replicate
LABEL_THRESHOLD = 20.0             # delta-Emax >= 0.2 (authors' Emax criterion); p_hit use only
EFFICACY_VIABILITY = 0.5           # "meaningful efficacy": combination viability <= 50% at top dose
REPLICATES = ("SV", "VS")


def _read(path: Path, columns: list[str]) -> pd.DataFrame:
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        frame = pd.read_csv(handle, usecols=columns, low_memory=False,
                            dtype={"ANCHOR_ID": str, "LIBRARY_ID": str, "SIDM": str, "BARCODE": str, "Tissue": str,
                                   "CELL_LINE_NAME": str, "ANCHOR_CONC": str})   # composite anchors: "0.5|0.03"
    for column in ("ANCHOR_ID", "LIBRARY_ID", "SIDM", "BARCODE", "Tissue"):
        frame[column] = frame[column].str.strip()
    return frame


def _doublets(design: pd.DataFrame) -> list[tuple[str, ...]]:
    """Connected components of library drugs that share plates."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for libs in design.groupby("BARCODE")["LIBRARY_ID"].agg(lambda s: sorted(set(s))):
        for x in libs:
            find(x)
        for x in libs[1:]:
            parent[find(x)] = find(libs[0])
    groups: dict[str, list[str]] = {}
    for x in list(parent):
        groups.setdefault(find(x), []).append(x)
    return sorted(tuple(sorted(g)) for g in groups.values())


def split_drugs(tissue: str, design: pd.DataFrame) -> dict[str, str]:
    """Frozen seeded split of library doublets into S and V (drug -> 'S' | 'V')."""
    components = _doublets(design)
    order = np.random.default_rng([SPLIT_SEED, TISSUE_CODE[tissue]]).permutation(len(components))
    side = {}
    for rank, index in enumerate(order):
        for drug in components[index]:
            side[drug] = "S" if rank < len(components) // 2 else "V"
    return side


def plate_design(path: Path = RELEASE) -> dict:
    """Design-only: doublets, split, plate disjointness and menu sizes per tissue (no outcomes)."""
    design = _read(path, DESIGN_COLUMNS)
    out = {}
    for tissue, d in design.groupby("Tissue"):
        side = split_drugs(tissue, d)
        anchor_side = d["ANCHOR_ID"].map(side)
        library_side = d["LIBRARY_ID"].map(side)
        mixed = d.assign(ls=library_side).groupby("BARCODE")["ls"].nunique()
        cross = d[(anchor_side.notna()) & (library_side.notna()) & (anchor_side != library_side)]
        lo = np.where(cross["ANCHOR_ID"].map(side) == "S", cross["ANCHOR_ID"], cross["LIBRARY_ID"])
        hi = np.where(cross["ANCHOR_ID"].map(side) == "S", cross["LIBRARY_ID"], cross["ANCHOR_ID"])
        orient = cross.assign(s=lo, v=hi, s_anchored=cross["ANCHOR_ID"].map(side) == "S")
        both = orient.groupby(["s", "v", "SIDM"])["s_anchored"].nunique()
        menu = both[both == 2]
        out[tissue] = {"doublets": len(_doublets(d)), "S": sorted(k for k, v in side.items() if v == "S"),
                       "V": sorted(k for k, v in side.items() if v == "V"),
                       "plates": int(d["BARCODE"].nunique()), "mixed_plates": int((mixed > 1).sum()),
                       "lines": int(d["SIDM"].nunique()), "menu_pair_x_line": int(menu.size),
                       "menu_per_line_median": float(menu.groupby(level="SIDM").size().median()) if menu.size else 0.0}
    return out


def _calls(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["syn"] = frame["Synergy"].astype(str).str.strip().str.upper().map(
        {"TRUE": 1.0, "FALSE": 0.0, "1": 1.0, "0": 0.0, "1.0": 1.0, "0.0": 0.0})
    if frame["syn"].isna().any():
        bad = sorted(frame.loc[frame["syn"].isna(), "Synergy"].astype(str).unique())[:5]
        raise ValueError(f"UNPARSEABLE_SYNERGY: {bad}")
    keys = ["Tissue", "SIDM", "ANCHOR_ID", "LIBRARY_ID"]
    per_conc = frame.groupby(keys + ["ANCHOR_CONC"]).agg(
        syn=("syn", "mean"), demax=("SYNERGY_DELTA_EMAX", "mean"), obs=("SYNERGY_OBS_EMAX", "mean"),
        plates=("BARCODE", "nunique")).reset_index()
    per_conc["call"] = per_conc["syn"] >= 0.5
    per_conc["strict"] = per_conc["syn"] > 0.5
    per = per_conc.groupby(keys).agg(hit=("call", "any"), strict=("strict", "any"), y=("demax", "max"),
                                     obs_min=("obs", "min"), plates=("plates", "max")).reset_index()
    per["y"] = 100.0 * per["y"]
    return per


def build_panels(ticket: dict, path: Path = RELEASE) -> tuple[dict[str, Panel], dict, dict]:
    """Outcome access; `ticket` must come from open_vault for this exact file."""
    digest = sha256(path)
    if not ticket or "freeze_sha256" not in ticket or ticket.get("data_sha256") != digest:
        raise PermissionError("VAULT_SEALED: build_panels needs an open_vault ticket for this file")
    raw = _read(path, DESIGN_COLUMNS + OUTCOME_COLUMNS)
    qc_fail = (raw["SYNERGY_RMSE"] > RMSE_MAX) | (raw["LIBRARY_RMSE"] > RMSE_MAX)
    missing = raw["Synergy"].isna() | raw["SYNERGY_DELTA_EMAX"].isna() | raw["SYNERGY_OBS_EMAX"].isna()
    report = {"rows": int(len(raw)), "qc_rmse_excluded": int(qc_fail.sum()),
              "missing_excluded": int((missing & ~qc_fail).sum()), "nan_rmse_rows": int(
                  (raw["SYNERGY_RMSE"].isna() | raw["LIBRARY_RMSE"].isna()).sum()),
              "release_sha256": digest, "panels": {}}
    calls = _calls(raw[~qc_fail & ~missing])
    panels: dict[str, Panel] = {}
    candidates: dict[str, dict] = {}
    for tissue, design in raw.groupby("Tissue"):
        side = split_drugs(tissue, design)            # split from design rows before any QC
        g = calls[calls["Tissue"] == tissue]
        g = g[g["ANCHOR_ID"].map(side).notna() & g["LIBRARY_ID"].map(side).notna()
              & (g["ANCHOR_ID"].map(side) != g["LIBRARY_ID"].map(side))].copy()
        s_anchored = g["ANCHOR_ID"].map(side) == "S"
        g["s"] = np.where(s_anchored, g["ANCHOR_ID"], g["LIBRARY_ID"])
        g["v"] = np.where(s_anchored, g["LIBRARY_ID"], g["ANCHOR_ID"])
        g["s_anchored"] = s_anchored
        sa = g[g["s_anchored"]].set_index(["s", "v", "SIDM"])
        va = g[~g["s_anchored"]].set_index(["s", "v", "SIDM"])
        menu = sa.index.intersection(va.index).sort_values()
        sa, va = sa.loc[menu], va.loc[menu]
        plates = _plate_sets(design, side)
        overlap = sum(len(plates[(sidm, "V")] & plates[(sidm, "S")]) for sidm in set(menu.get_level_values(2)))
        if overlap:
            raise ValueError(f"PLATE_OVERLAP: {tissue} has {overlap} plates holding both screen and validation rows")
        drugs = tuple(sorted(set(menu.get_level_values(0)) | set(menu.get_level_values(1))))
        lines = tuple(sorted(set(menu.get_level_values(2))))
        di = {d: i for i, d in enumerate(drugs)}
        li = {x: i for i, x in enumerate(lines)}
        first = [di[x] for x in menu.get_level_values(0)]
        second = [di[x] for x in menu.get_level_values(1)]
        a = np.minimum(first, second).astype(np.int32)
        b = np.maximum(first, second).astype(np.int32)
        c = np.array([li[x] for x in menu.get_level_values(2)], np.int32)
        zeros = np.zeros((len(drugs), len(lines)))
        for rep in REPLICATES:
            screen, valid = (sa, va) if rep == "SV" else (va, sa)
            provenance = {"source": "Jaaks et al. 2022 Nature 603:166, figshare 16843597 (GDSC anchored screen)",
                          "release_sha256": digest, "tissue": tissue, "replicate": rep, "vault_ticket": ticket,
                          "split_seed": [SPLIT_SEED, TISSUE_CODE[tissue]],
                          "label": "100 x max over anchor concentrations of mean SYNERGY_DELTA_EMAX (screen orientation)",
                          "context": "none (mono/expected arrays are zeros and unused: WorldConfig(context=False))"}
            lib = Library(f"jaaks2022_{tissue.lower()}_{rep}", drugs, lines, a, b, c, screen["y"].to_numpy(float),
                          (WELLS_PER_PLATE * screen["plates"].to_numpy()).astype(np.int32), np.zeros(len(menu)),
                          zeros, zeros.copy(), float("nan"), LABEL_THRESHOLD, provenance)
            panels[f"{tissue}_{rep}"] = Panel(
                lib.name, tissue, lib, screen["hit"].to_numpy(bool), valid["hit"].to_numpy(bool),
                valid["y"].to_numpy(float), (valid["obs_min"] <= EFFICACY_VIABILITY).to_numpy(bool),
                np.zeros(len(menu), bool), screen["strict"].to_numpy(bool), valid["strict"].to_numpy(bool), rep)
        candidates[tissue] = {"pairs_s_v": [[s, v] for s, v, _ in menu], "line_sidm": list(lines),
                              "S": sorted(k for k, x in side.items() if x == "S"),
                              "V": sorted(k for k, x in side.items() if x == "V")}
        report["panels"][tissue] = {"lines": len(lines), "drugs": len(drugs), "menu": int(len(menu)),
                                    "plate_overlap": overlap, "screen_hits_SV": int(sa["hit"].sum()),
                                    "screen_hits_VS": int(va["hit"].sum())}
    return panels, report, candidates


def _plate_sets(design: pd.DataFrame, side: dict[str, str]) -> dict[tuple[str, str], set]:
    """(line, library side) -> plate barcodes; S-anchored rows sit on V-library plates."""
    sets: dict[tuple[str, str], set] = {}
    d = design[design["LIBRARY_ID"].map(side).notna()]
    for (sidm, lib_side), plates in d.groupby(["SIDM", d["LIBRARY_ID"].map(side)])["BARCODE"]:
        sets[(sidm, lib_side)] = set(plates)
    for sidm in d["SIDM"].unique():
        sets.setdefault((sidm, "S"), set())
        sets.setdefault((sidm, "V"), set())
    return sets


def rescreen_calls(ticket: dict, path: Path = RESCREEN) -> pd.DataFrame:
    """Authors' validation rescreen (selective menu): per (tissue, unordered pair, line) any-orientation call."""
    if not ticket or ticket.get("data_sha256") != sha256(path):
        raise PermissionError("VAULT_SEALED: rescreen_calls needs an open_vault ticket for this file")
    raw = _read(path, DESIGN_COLUMNS + OUTCOME_COLUMNS)
    keep = ~((raw["SYNERGY_RMSE"] > RMSE_MAX) | (raw["LIBRARY_RMSE"] > RMSE_MAX)) & raw["Synergy"].notna()
    per = _calls(raw[keep])
    per["lo"] = per[["ANCHOR_ID", "LIBRARY_ID"]].min(axis=1)
    per["hi"] = per[["ANCHOR_ID", "LIBRARY_ID"]].max(axis=1)
    return per.groupby(["Tissue", "lo", "hi", "SIDM"])["hit"].any().reset_index()


def synthetic_release(path: Path, *, seed: int = 0, lines: int = 8, drugs: int = 8) -> Path:
    """A small release with the real columns and plate layout (one line x library doublet per plate)."""
    rng = np.random.default_rng(seed)
    rows = []
    for tissue in ("Colon", "Pancreas"):
        ids = [str(1000 + 10 * TISSUE_CODE[tissue] + i) for i in range(drugs)]
        effect = rng.normal(0, 0.08, (drugs, lines))
        for line in range(lines):
            sidm = f"SIDM{TISSUE_CODE[tissue]}{line:03d}"
            for doublet in range(drugs // 2):
                barcode = f"{tissue[0]}{line:03d}{doublet:02d}"
                for j in (2 * doublet, 2 * doublet + 1):
                    for i in range(drugs):
                        if i == j:
                            continue
                        for conc in (0.1, 1.0):
                            demax = 0.05 + effect[i, line] + effect[j, line] + rng.normal(0, 0.08)
                            rows.append({"BARCODE": barcode, "Tissue": tissue, "CELL_LINE_NAME": f"L{line}",
                                         "SIDM": sidm, "ANCHOR_ID": ids[i], "ANCHOR_NAME": f"D{i}", "ANCHOR_CONC": conc,
                                         "LIBRARY_ID": ids[j], "LIBRARY_NAME": f"D{j}", "LIBRARY_CONC": 4.0,
                                         "SYNERGY_DELTA_EMAX": demax,
                                         "SYNERGY_OBS_EMAX": float(np.clip(0.6 - demax, 0, 1)),
                                         "SYNERGY_RMSE": abs(rng.normal(0.05, 0.03)), "LIBRARY_RMSE": 0.05,
                                         "Synergy": bool(demax >= 0.2)})
    frame = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path
