"""Build drug-combination screen libraries for certified discovery (O'Neil 2016, NCI-ALMANAC 2017).

File summary
- Path: tools/datasets/combination_screens.py
- Purpose: turn public full-factorial combination screens into `virtual_cell.combination_world`
  screens with one declared label rule per source, laboratory cost, and provenance; keep a
  confirmatory screen's outcomes sealed behind a freeze-checked vault.
- Core points:
  - Label: Bliss excess in percentage points averaged over the experiment's combination dose
    grid; hit = label > 10 (SynergyFinder convention). O'Neil: expected = min(rA,1)*min(rB,1) on
    the published X/X0 scale with singles interpolated in log concentration from the same
    batch, primary-screen batches 1-2 only. ALMANAC: NCI's own per-well SCORE averaged over all
    combination records of a pair x line.
  - Context (usable before buying a combination): single-agent inhibition per drug x line,
    mean over combination doses and at the top dose.
  - O'Neil workbooks are read with a streaming stdlib .xlsx reader (no spreadsheet dependency).
  - `open_vault` refuses until a freeze exists and every frozen file still matches
    (VAULT_SEALED, FREEZE_MISMATCH) and appends every opening to a log.
  - Promoted from research/certified_discovery/screens.py and xlsx.py (frozen there).
- Interfaces: `ScreenLibrary`, `iter_xlsx_rows`, `build_oneil`, `almanac_design`, `open_vault`,
  `build_almanac`, `save_library`, `load_library`, `VaultRefusal`; CLI `python -m
  tools.datasets.combination_screens {oneil,almanac-design}`.
- Depends on: numpy; pandas for the ALMANAC CSV; `virtual_cell.combination_world`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import numpy as np

from virtual_cell.combination_world import CombinationScreen

ROOT = Path(__file__).resolve().parents[2]
ONEIL_DIR = ROOT / "data/raw/oneil2026_qualification"
ONEIL_COMBINATION = "15357163mct150843-sup-156849_1_supp_1_w2lrww.xls"
ONEIL_SINGLE = "15357163mct150843-sup-156849_1_supp_0_w2lh45.xlsx"
ALMANAC_DIR = ROOT / "data/external/nci_almanac_2017"
ALMANAC_ZIP = ALMANAC_DIR / "ComboDrugGrowth_Nov2017.zip"
ALMANAC_NAMES = ALMANAC_DIR / "ComboCompoundNames_small.txt"
CACHE = ROOT / "data/processed/certified_discovery"
HIT_THRESHOLD = 10.0
ONEIL_DAYS_PER_ROUND = 5.0     # 96 h assay plus plating
ALMANAC_DAYS_PER_ROUND = 3.0   # 48 h assay plus 24 h pre-incubation
ONEIL_REPLICATE_WELLS = 4      # combination plates carried up to 4 replicates
_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


@dataclass
class ScreenLibrary:
    name: str
    screen: CombinationScreen
    cost_points: np.ndarray
    days_per_round: float
    wells_per_point: int = 1
    provenance: dict = field(default_factory=dict)

    @property
    def hits(self) -> np.ndarray:
        return self.screen.y > self.screen.threshold


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def save_library(library: ScreenLibrary, path: Path) -> None:
    s = library.screen
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, a=s.a, b=s.b, c=s.c, y=s.y, cost_points=library.cost_points, expected=s.expected,
                        mono_mean=s.mono_mean, mono_top=s.mono_top)
    meta = {"name": library.name, "drugs": list(s.drugs), "lines": list(s.lines), "threshold": s.threshold,
            "days_per_round": library.days_per_round, "wells_per_point": library.wells_per_point,
            "provenance": library.provenance}
    path.with_suffix(".json").write_text(json.dumps(meta, indent=1, sort_keys=True), encoding="utf-8")


def load_library(path: Path) -> ScreenLibrary:
    arrays = np.load(path)
    meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    screen = CombinationScreen(tuple(meta["drugs"]), tuple(meta["lines"]), arrays["a"], arrays["b"], arrays["c"],
                               arrays["y"], arrays["expected"], arrays["mono_mean"], arrays["mono_top"],
                               float(meta["threshold"]))
    return ScreenLibrary(meta["name"], screen, arrays["cost_points"], float(meta["days_per_round"]),
                         int(meta.get("wells_per_point", 1)), meta["provenance"])


# --------------------------------------------------------------------------- xlsx reader
def iter_xlsx_rows(path: Path, sheet: int = 1) -> Iterator[list[str | None]]:
    """Stream worksheet rows as lists indexed by column (blank cells stay in place)."""
    with zipfile.ZipFile(path) as archive:
        try:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(t.text or "" for t in si.iter(_NS + "t")) for si in root.iter(_NS + "si")]
        except KeyError:
            strings = []
        with archive.open(f"xl/worksheets/sheet{sheet}.xml") as handle:
            for _, element in ET.iterparse(handle, events=("end",)):
                if element.tag != _NS + "row":
                    continue
                cells: dict[int, str | None] = {}
                for cell in element.iter(_NS + "c"):
                    letters = re.match(r"[A-Z]+", cell.get("r")).group(0)
                    column = 0
                    for letter in letters:
                        column = column * 26 + ord(letter) - 64
                    value = cell.find(_NS + "v")
                    if value is None:
                        inline = cell.find(_NS + "is")
                        text = None if inline is None else "".join(t.text or "" for t in inline.iter(_NS + "t"))
                    else:
                        text = strings[int(value.text)] if cell.get("t") == "s" else value.text
                    cells[column - 1] = text
                yield [cells.get(i) for i in range(max(cells) + 1 if cells else 0)]
                element.clear()


# --------------------------------------------------------------------------- O'Neil 2016
def _interp_log(conc: np.ndarray, response: np.ndarray, at: float) -> float:
    order = np.argsort(conc)
    return float(np.interp(math.log10(at), np.log10(conc[order]), response[order]))


def _grouped(path: Path, keys: tuple[str, ...], conc_prefixes: tuple[str, ...]):
    rows = iter_xlsx_rows(path)
    header = next(rows)
    key_cols = [header.index(name) for name in keys]
    conc_cols = [next(i for i, name in enumerate(header) if name and name.startswith(p)) for p in conc_prefixes]
    response = header.index("X/X0")
    for row in rows:
        if row and len(row) > response and row[response] not in (None, ""):
            yield (tuple(row[i].strip() if i >= 2 else row[i] for i in key_cols),
                   tuple(float(row[i]) for i in conc_cols), float(row[response]))


def build_oneil(raw_dir: Path = ONEIL_DIR) -> ScreenLibrary:
    """Primary-screen library: batches 1 and 2, pair x line labels averaged across batches."""
    singles_raw: dict[tuple, dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    for key, (conc,), value in _grouped(raw_dir / ONEIL_SINGLE, ("BatchID", "cell_line", "drug_name"),
                                        ("Drug_concentration",)):
        singles_raw[key][conc].append(value)
    singles = {key: (np.array(sorted(v)), np.array([np.mean(v[c]) for c in sorted(v)])) for key, v in singles_raw.items()}

    def single(batch, line, drug):
        for candidate in (batch, "1", "2", "3"):
            if (candidate, line, drug) in singles:
                return singles[(candidate, line, drug)]
        return None

    combos: dict[tuple, list] = defaultdict(list)
    for key, concs, value in _grouped(raw_dir / ONEIL_COMBINATION, ("BatchID", "cell_line", "drugA_name", "drugB_name"),
                                      ("drugA Conc", "drugB Conc")):
        combos[key].append((*concs, value))
    merged: dict[tuple, list] = defaultdict(list)
    doses: dict[tuple, set] = defaultdict(set)
    refused = 0
    for (batch, line, drug_a, drug_b), points in combos.items():
        if batch not in ("1", "2"):
            continue
        curve_a, curve_b = single(batch, line, drug_a), single(batch, line, drug_b)
        if curve_a is None or curve_b is None:
            refused += 1
            continue
        excess, inhibition = [], []
        for ca, cb, observed in points:
            expected = min(_interp_log(*curve_a, ca), 1.0) * min(_interp_log(*curve_b, cb), 1.0)
            excess.append(100.0 * (expected - observed))
            inhibition.append(1.0 - expected)
        merged[(drug_a, drug_b, line)].append((float(np.mean(excess)), float(np.mean(inhibition)), len(points)))
        doses[(drug_a, line)].update(p[0] for p in points)
        doses[(drug_b, line)].update(p[1] for p in points)
    drugs = tuple(sorted({k[0] for k in merged} | {k[1] for k in merged}))
    lines = tuple(sorted({k[2] for k in merged}))
    di, li = {d: i for i, d in enumerate(drugs)}, {l: i for i, l in enumerate(lines)}
    keyed: dict[tuple, list] = defaultdict(list)
    for (drug_a, drug_b, line), entries in merged.items():
        i, j = sorted((di[drug_a], di[drug_b]))
        keyed[(i, j, li[line])].extend(entries)
    keys = sorted(keyed)
    mono_mean = np.full((len(drugs), len(lines)), np.nan)
    mono_top = np.full((len(drugs), len(lines)), np.nan)
    for (drug, line), used in doses.items():
        curve = single("1", line, drug)
        if curve is not None:
            values = [1.0 - min(_interp_log(*curve, dose), 1.0) for dose in sorted(used)]
            mono_mean[di[drug], li[line]], mono_top[di[drug], li[line]] = float(np.mean(values)), values[-1]
    screen = CombinationScreen(
        drugs, lines, np.array([k[0] for k in keys], np.int32), np.array([k[1] for k in keys], np.int32),
        np.array([k[2] for k in keys], np.int32), np.array([np.mean([e[0] for e in keyed[k]]) for k in keys]),
        np.array([np.mean([e[1] for e in keyed[k]]) for k in keys]), mono_mean, mono_top, HIT_THRESHOLD)
    provenance = {"source": "O'Neil et al. 2016 Mol Cancer Ther, doi:10.1158/1535-7163.MCT-15-0843 (CC BY 4.0)",
                  "combination_sha256": sha256(raw_dir / ONEIL_COMBINATION), "single_sha256": sha256(raw_dir / ONEIL_SINGLE),
                  "refused_single_agent_missing": refused}
    cost = np.array([sum(e[2] for e in keyed[k]) for k in keys], np.int32)
    return ScreenLibrary("oneil2016", screen, cost, ONEIL_DAYS_PER_ROUND, ONEIL_REPLICATE_WELLS, provenance)


# --------------------------------------------------------------------------- NCI-ALMANAC 2017
DESIGN_COLUMNS = ["NSC1", "NSC2", "CONCINDEX1", "CONCINDEX2", "CELLNAME", "SCREENER", "PLATE"]


class VaultRefusal(RuntimeError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


def _almanac_frame(columns: list[str], source: Path):
    import pandas as pd

    with zipfile.ZipFile(source) as archive, archive.open("ComboDrugGrowth_Nov2017.csv") as handle:
        frame = pd.read_csv(handle, usecols=columns, low_memory=False,
                            dtype={"NSC1": "Int64", "NSC2": "Int64", "CELLNAME": "string"})
    frame["CELLNAME"] = frame["CELLNAME"].str.strip()
    return frame


def almanac_design(source: Path = ALMANAC_ZIP) -> dict:
    """Design-only census; reads no outcome column."""
    frame = _almanac_frame(DESIGN_COLUMNS, source)
    combo = frame[(frame["CONCINDEX1"] > 0) & (frame["CONCINDEX2"] > 0) & frame["NSC2"].notna()]
    keys = combo.assign(lo=combo[["NSC1", "NSC2"]].min(axis=1), hi=combo[["NSC1", "NSC2"]].max(axis=1)).groupby(
        ["lo", "hi", "CELLNAME"]).size()
    flat = keys.reset_index()
    return {"records": int(len(frame)), "combination_records": int(len(combo)),
            "drugs": int(len(set(flat["lo"]) | set(flat["hi"]))), "pairs": int(len(flat[["lo", "hi"]].drop_duplicates())),
            "lines": int(flat["CELLNAME"].nunique()), "experiments": int(len(keys)),
            "records_per_experiment_median": float(keys.median())}


def open_vault(freeze_path: Path, log_path: Path, *, purpose: str, source: Path = ALMANAC_ZIP, root: Path = ROOT) -> dict:
    """Outcome access only against an intact freeze; every opening is appended to the log."""
    if not freeze_path.is_file():
        raise VaultRefusal("VAULT_SEALED", f"no freeze record at {freeze_path}")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    changed = [name for name, digest in freeze["files"].items() if sha256(root / name) != digest]
    if changed:
        raise VaultRefusal("FREEZE_MISMATCH", "frozen files changed: " + ", ".join(changed))
    previous = log_path.read_text(encoding="utf-8").splitlines() if log_path.exists() else []
    entry = {"opened_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "purpose": purpose, "freeze_sha256": sha256(freeze_path),
             "data_sha256": sha256(source), "prior_openings": len(previous)}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def _names(path: Path) -> dict[str, str]:
    names: dict[str, str] = {}
    if path.is_file():
        for row in path.read_text(encoding="utf-8", errors="replace").splitlines():
            nsc, _, name = row.partition("\t")
            if nsc.strip() and name.strip():
                names.setdefault(nsc.strip(), name.strip())
    return names


def build_almanac(ticket: dict, *, source: Path = ALMANAC_ZIP, names_path: Path = ALMANAC_NAMES) -> ScreenLibrary:
    """Confirmatory-grade library; `ticket` must come from `open_vault`."""
    if not ticket or "freeze_sha256" not in ticket:
        raise VaultRefusal("VAULT_SEALED", "build_almanac needs an open_vault ticket")
    frame = _almanac_frame(DESIGN_COLUMNS + ["CONC1", "CONC2", "PERCENTGROWTH", "SCORE"], source)
    both = (frame["CONCINDEX1"] > 0) & (frame["CONCINDEX2"] > 0) & frame["NSC2"].notna()
    alone = (frame["CONCINDEX1"] > 0) & ~(frame["CONCINDEX2"] > 0) & frame["NSC2"].isna()
    combo = frame[both].copy()
    combo = combo[np.isfinite(combo["SCORE"].astype(float))]
    combo["lo"], combo["hi"] = combo[["NSC1", "NSC2"]].min(axis=1), combo[["NSC1", "NSC2"]].max(axis=1)
    experiments = combo.groupby(["lo", "hi", "CELLNAME"]).agg(y=("SCORE", "mean"), points=("SCORE", "size")).reset_index()
    single = frame[alone].copy()
    single["inhibition"] = (100.0 - np.minimum(single["PERCENTGROWTH"].astype(float), 100.0)) / 100.0
    curve = single.groupby(["NSC1", "CELLNAME", "CONC1"])["inhibition"].mean().reset_index()
    nscs = tuple(str(int(x)) for x in sorted(set(experiments["lo"]) | set(experiments["hi"])))
    lines = tuple(sorted(experiments["CELLNAME"].unique()))
    di, li = {n: i for i, n in enumerate(nscs)}, {l: i for i, l in enumerate(lines)}
    mono_mean = np.full((len(nscs), len(lines)), np.nan)
    mono_top = np.full((len(nscs), len(lines)), np.nan)
    for (drug, line), group in curve.groupby(["NSC1", "CELLNAME"]):
        if str(int(drug)) in di and line in li:
            group = group.sort_values("CONC1")
            mono_mean[di[str(int(drug))], li[line]] = float(group["inhibition"].mean())
            mono_top[di[str(int(drug))], li[line]] = float(group["inhibition"].iloc[-1])
    a = np.array([di[str(int(x))] for x in experiments["lo"]], np.int32)
    b = np.array([di[str(int(x))] for x in experiments["hi"]], np.int32)
    c = np.array([li[x] for x in experiments["CELLNAME"]], np.int32)
    expected = 1.0 - (1.0 - np.clip(np.nan_to_num(mono_mean[a, c]), 0, 1)) * (1.0 - np.clip(np.nan_to_num(mono_mean[b, c]), 0, 1))
    names = _names(names_path)
    screen = CombinationScreen(tuple(names.get(n, f"NSC {n}") for n in nscs), lines, a, b, c,
                               experiments["y"].to_numpy(float), expected, mono_mean, mono_top, HIT_THRESHOLD)
    provenance = {"source": "NCI-ALMANAC ComboDrugGrowth_Nov2017 (Holbeck et al. 2017, doi:10.1158/0008-5472.CAN-17-0489)",
                  "data_sha256": sha256(source), "vault_ticket": ticket, "nsc": list(nscs),
                  "single_agent_rows": int(alone.sum()), "excluded_undocumented_rows": int((~both & ~alone).sum())}
    return ScreenLibrary("almanac2017", screen, experiments["points"].to_numpy(np.int32), ALMANAC_DAYS_PER_ROUND, 1, provenance)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build combination-screen libraries for certified discovery.")
    sub = parser.add_subparsers(dest="command", required=True)
    oneil = sub.add_parser("oneil", help="build the O'Neil 2016 development library")
    oneil.add_argument("--raw", default=str(ONEIL_DIR))
    oneil.add_argument("--out", default=str(CACHE / "oneil_tools_v1.npz"))
    design = sub.add_parser("almanac-design", help="design-only ALMANAC census (no outcome column read)")
    design.add_argument("--source", default=str(ALMANAC_ZIP))
    args = parser.parse_args(argv)
    if args.command == "oneil":
        library = build_oneil(Path(args.raw))
        save_library(library, Path(args.out))
        print(json.dumps({"experiments": int(library.screen.y.size), "hits": int(library.hits.sum())}))
    else:
        print(json.dumps(almanac_design(Path(args.source)), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
