"""Build combination-screen libraries with one pre-declared label rule per source.

File summary
- Path: research/certified_discovery/screens.py
- Purpose: turn the O'Neil 2016 (development) and NCI-ALMANAC 2017 (confirmatory) releases into
  one canonical experiment library: unordered drug pair x cell line, a measured synergy label,
  the single-agent context available before any combination is bought, and laboratory cost.
- Core points:
  - Label rule (declared before any label was computed, DESIGN.md section 4): the Bliss excess
    in percentage points averaged over the experiment's combination dose grid; a hit is a label
    above 10 (the SynergyFinder synergy convention). O'Neil: expected = min(rA,1)*min(rB,1) on
    the published X/X0 scale, singles interpolated in log concentration. ALMANAC: NCI's own
    per-well SCORE = ExpectedGrowth - PercentGrowth, averaged over every combination record.
  - Context (features the agent may use before buying a combination) comes from single-agent
    measurements only.
  - ALMANAC outcome columns are read only through `open_vault`, which refuses until a freeze
    record exists and every frozen file still matches its digest (`VAULT_SEALED`,
    `FREEZE_MISMATCH`), and which appends every opening to a log.
- Interfaces: `Library`, `build_oneil`, `oneil_reproducibility`, `almanac_design`, `almanac_names`,
  `build_almanac`, `open_vault`, `load_library`.
- Depends on: numpy, pandas (ALMANAC CSV), `xlsx.iter_rows`.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .xlsx import iter_rows

ROOT = Path(__file__).resolve().parents[2]
ONEIL_DIR = ROOT / "data/raw/oneil2026_qualification"
ONEIL_COMBINATION = ONEIL_DIR / "15357163mct150843-sup-156849_1_supp_1_w2lrww.xls"
ONEIL_SINGLE = ONEIL_DIR / "15357163mct150843-sup-156849_1_supp_0_w2lh45.xlsx"
ALMANAC_DIR = ROOT / "data/external/nci_almanac_2017"
ALMANAC_ZIP = ALMANAC_DIR / "ComboDrugGrowth_Nov2017.zip"
CACHE = ROOT / "data/processed/certified_discovery"

HIT_THRESHOLD = 10.0          # SynergyFinder: score above 10 is synergistic
ONEIL_DAYS_PER_ROUND = 5.0    # 96 h assay plus plating day (O'Neil et al. 2016 methods)
ALMANAC_DAYS_PER_ROUND = 3.0  # 48 h NCI-60 assay plus 24 h pre-incubation (Holbeck et al. 2017)
LIBRARY_BATCHES = ("1", "2")  # primary screen; batch 3 is the published validation repeat


@dataclass
class Library:
    """One screen as candidate experiments plus their hidden measured outcomes."""

    name: str
    drugs: tuple[str, ...]
    lines: tuple[str, ...]
    a: np.ndarray            # drug index, a < b
    b: np.ndarray
    c: np.ndarray            # cell-line index
    y: np.ndarray            # label, percentage points
    cost_points: np.ndarray  # combination dose-point records bought with the experiment
    expected: np.ndarray     # mean Bliss-expected inhibition from singles (context, not outcome)
    mono_mean: np.ndarray    # (drugs, lines) mean single-agent inhibition over combination doses
    mono_top: np.ndarray     # (drugs, lines) single-agent inhibition at the top combination dose
    days_per_round: float
    threshold: float = HIT_THRESHOLD
    provenance: dict = field(default_factory=dict)

    @property
    def hits(self) -> np.ndarray:
        return self.y > self.threshold

    def __len__(self) -> int:
        return int(self.y.size)

    def subset(self, mask: np.ndarray, name: str) -> "Library":
        keep = np.flatnonzero(mask)
        return Library(name, self.drugs, self.lines, self.a[keep], self.b[keep], self.c[keep], self.y[keep],
                       self.cost_points[keep], self.expected[keep], self.mono_mean, self.mono_top,
                       self.days_per_round, self.threshold, dict(self.provenance, parent=self.name))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, a=self.a, b=self.b, c=self.c, y=self.y, cost_points=self.cost_points,
                            expected=self.expected, mono_mean=self.mono_mean, mono_top=self.mono_top)
        meta = {"name": self.name, "drugs": list(self.drugs), "lines": list(self.lines),
                "days_per_round": self.days_per_round, "threshold": self.threshold,
                "provenance": self.provenance}
        path.with_suffix(".json").write_text(json.dumps(meta, indent=1, sort_keys=True), encoding="utf-8")


def load_library(path: Path) -> Library:
    arrays = np.load(path)
    meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    return Library(meta["name"], tuple(meta["drugs"]), tuple(meta["lines"]), arrays["a"], arrays["b"],
                   arrays["c"], arrays["y"], arrays["cost_points"], arrays["expected"], arrays["mono_mean"],
                   arrays["mono_top"], meta["days_per_round"], meta["threshold"], meta["provenance"])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


# --------------------------------------------------------------------------- O'Neil (development)

def _interp_log(conc: np.ndarray, response: np.ndarray, at: float) -> float:
    """Linear interpolation in log10 concentration, held flat beyond the measured range."""
    order = np.argsort(conc)
    x = np.log10(conc[order])
    return float(np.interp(math.log10(at), x, response[order]))


def _read_singles() -> dict[tuple[str, str, str], tuple[np.ndarray, np.ndarray]]:
    grouped: dict[tuple[str, str, str], dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    rows = iter_rows(ONEIL_SINGLE)
    header = next(rows)
    col = {name: header.index(name) for name in ("BatchID", "cell_line", "drug_name", "X/X0")}
    conc_col = next(i for i, name in enumerate(header) if name and name.startswith("Drug_concentration"))
    for row in rows:
        if not row or row[col["X/X0"]] in (None, ""):
            continue
        key = (row[col["BatchID"]], row[col["cell_line"]], row[col["drug_name"]].strip())
        grouped[key][float(row[conc_col])].append(float(row[col["X/X0"]]))
    out = {}
    for key, by_conc in grouped.items():
        conc = np.array(sorted(by_conc))
        out[key] = (conc, np.array([np.mean(by_conc[x]) for x in conc]))
    return out


def _read_combinations() -> dict[tuple[str, str, str, str], list[tuple[float, float, float]]]:
    grouped: dict[tuple[str, str, str, str], list[tuple[float, float, float]]] = defaultdict(list)
    rows = iter_rows(ONEIL_COMBINATION)
    header = next(rows)
    col = {name: header.index(name) for name in ("BatchID", "cell_line", "drugA_name", "drugB_name", "X/X0")}
    conc_a = next(i for i, name in enumerate(header) if name and name.startswith("drugA Conc"))
    conc_b = next(i for i, name in enumerate(header) if name and name.startswith("drugB Conc"))
    for row in rows:
        if not row or row[col["X/X0"]] in (None, ""):
            continue
        key = (row[col["BatchID"]], row[col["cell_line"]], row[col["drugA_name"]].strip(), row[col["drugB_name"]].strip())
        grouped[key].append((float(row[conc_a]), float(row[conc_b]), float(row[col["X/X0"]])))
    return grouped


def _single(singles, batch: str, line: str, drug: str):
    if (batch, line, drug) in singles:
        return singles[(batch, line, drug)], batch
    for other in ("1", "2", "3"):
        if (other, line, drug) in singles:
            return singles[(other, line, drug)], other
    return None, None


def _oneil_experiments():
    singles = _read_singles()
    combos = _read_combinations()
    experiments = []
    for (batch, line, drug_a, drug_b), points in combos.items():
        single_a, batch_a = _single(singles, batch, line, drug_a)
        single_b, batch_b = _single(singles, batch, line, drug_b)
        if single_a is None or single_b is None:
            experiments.append({"batch": batch, "line": line, "a": drug_a, "b": drug_b, "y": None,
                                "reason": "SINGLE_AGENT_MISSING"})
            continue
        excess, expected_inhibition = [], []
        for ca, cb, observed in points:
            ra = min(_interp_log(*single_a, ca), 1.0)
            rb = min(_interp_log(*single_b, cb), 1.0)
            expected = ra * rb
            excess.append(100.0 * (expected - observed))
            expected_inhibition.append(1.0 - expected)
        experiments.append({
            "batch": batch, "line": line, "a": drug_a, "b": drug_b, "y": float(np.mean(excess)),
            "expected": float(np.mean(expected_inhibition)), "points": len(points),
            "doses_a": sorted({p[0] for p in points}), "doses_b": sorted({p[1] for p in points}),
            "single_batch_fallback": batch_a != batch or batch_b != batch,
        })
    return singles, experiments


def build_oneil(cache: Path = CACHE / "oneil_v1.npz", *, force: bool = False) -> Library:
    """Primary-screen library (batches 1 and 2); duplicated pair x line labels are averaged."""
    if cache.exists() and not force:
        return load_library(cache)
    started = time.time()
    singles, experiments = _oneil_experiments()
    usable = [e for e in experiments if e["y"] is not None and e["batch"] in LIBRARY_BATCHES]
    drugs = tuple(sorted({e["a"] for e in usable} | {e["b"] for e in usable}))
    lines = tuple(sorted({e["line"] for e in usable}))
    drug_index = {name: i for i, name in enumerate(drugs)}
    line_index = {name: i for i, name in enumerate(lines)}
    merged: dict[tuple[int, int, int], list[dict]] = defaultdict(list)
    combination_doses: dict[tuple[int, int], set[float]] = defaultdict(set)
    for e in usable:
        i, j = sorted((drug_index[e["a"]], drug_index[e["b"]]))
        merged[(i, j, line_index[e["line"]])].append(e)
        combination_doses[(drug_index[e["a"]], line_index[e["line"]])].update(e["doses_a"])
        combination_doses[(drug_index[e["b"]], line_index[e["line"]])].update(e["doses_b"])
    keys = sorted(merged)
    a = np.array([k[0] for k in keys], dtype=np.int32)
    b = np.array([k[1] for k in keys], dtype=np.int32)
    c = np.array([k[2] for k in keys], dtype=np.int32)
    y = np.array([np.mean([e["y"] for e in merged[k]]) for k in keys])
    expected = np.array([np.mean([e["expected"] for e in merged[k]]) for k in keys])
    cost = np.array([sum(e["points"] for e in merged[k]) for k in keys], dtype=np.int32)
    mono_mean = np.full((len(drugs), len(lines)), np.nan)
    mono_top = np.full((len(drugs), len(lines)), np.nan)
    for (d, l), doses in combination_doses.items():
        curve, _ = _single(singles, "1", lines[l], drugs[d])
        if curve is None:
            continue
        inhibition = [1.0 - min(_interp_log(*curve, dose), 1.0) for dose in sorted(doses)]
        mono_mean[d, l] = float(np.mean(inhibition))
        mono_top[d, l] = inhibition[-1]
    provenance = {
        "source": "O'Neil et al. 2016 Mol Cancer Ther, doi:10.1158/1535-7163.MCT-15-0843 (CC BY 4.0)",
        "combination_sha256": sha256(ONEIL_COMBINATION), "single_sha256": sha256(ONEIL_SINGLE),
        "label": "mean Bliss excess (pp) over the dose grid; expected=min(rA,1)*min(rB,1); X/X0 scale",
        "batches": list(LIBRARY_BATCHES), "duplicates_averaged": int(sum(len(v) > 1 for v in merged.values())),
        "refused_single_agent_missing": int(sum(e["y"] is None for e in experiments)),
        "single_batch_fallbacks": int(sum(e.get("single_batch_fallback", False) for e in usable)),
        "build_seconds": round(time.time() - started, 1),
    }
    library = Library("oneil2016", drugs, lines, a, b, c, y, cost, expected, mono_mean, mono_top,
                      ONEIL_DAYS_PER_ROUND, HIT_THRESHOLD, provenance)
    library.save(cache)
    reproducibility = _reproducibility(experiments, drug_index, line_index)
    (cache.parent / "oneil_v1_reproducibility.json").write_text(json.dumps(reproducibility, indent=1), encoding="utf-8")
    return library


def _reproducibility(experiments, drug_index, line_index) -> dict:
    primary: dict[tuple, list[float]] = defaultdict(list)
    repeat: dict[tuple, list[float]] = defaultdict(list)
    for e in experiments:
        if e["y"] is None or e["a"] not in drug_index or e["b"] not in drug_index or e["line"] not in line_index:
            continue
        key = (*sorted((e["a"], e["b"])), e["line"])
        (primary if e["batch"] in LIBRARY_BATCHES else repeat)[key].append(e["y"])
    shared = sorted(set(primary) & set(repeat))
    if not shared:
        return {"pairs": 0}
    first = np.array([np.mean(primary[k]) for k in shared])
    second = np.array([np.mean(repeat[k]) for k in shared])
    hit_1, hit_2 = first > HIT_THRESHOLD, second > HIT_THRESHOLD
    return {
        "pairs": len(shared), "pearson": float(np.corrcoef(first, second)[0, 1]),
        "label_sd_difference": float(np.std(first - second, ddof=1)),
        "hit_rate_primary": float(hit_1.mean()), "hit_rate_repeat": float(hit_2.mean()),
        "hit_agreement": float((hit_1 == hit_2).mean()),
        "repeat_hit_given_primary_hit": float(hit_2[hit_1].mean()) if hit_1.any() else None,
    }


def oneil_reproducibility(cache: Path = CACHE / "oneil_v1_reproducibility.json") -> dict:
    return json.loads(cache.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- ALMANAC (confirmatory)

DESIGN_COLUMNS = ["NSC1", "NSC2", "CONCINDEX1", "CONCINDEX2", "CELLNAME", "SCREENER", "PLATE"]
OUTCOME_COLUMNS = ["PERCENTGROWTH", "SCORE"]


def _almanac_frame(columns: list[str], source: Path = ALMANAC_ZIP):
    import pandas as pd

    with zipfile.ZipFile(source) as archive:
        with archive.open("ComboDrugGrowth_Nov2017.csv") as handle:
            frame = pd.read_csv(handle, usecols=columns, low_memory=False,
                                dtype={"NSC1": "Int64", "NSC2": "Int64", "CELLNAME": "string"})
    frame["CELLNAME"] = frame["CELLNAME"].str.strip()
    return frame


def almanac_design(source: Path = ALMANAC_ZIP) -> dict:
    """Design-only census: pairs, lines and records per experiment. Reads no outcome column."""
    frame = _almanac_frame(DESIGN_COLUMNS, source)
    combo = frame[(frame["CONCINDEX1"] > 0) & (frame["CONCINDEX2"] > 0) & frame["NSC2"].notna()]
    lo = combo[["NSC1", "NSC2"]].min(axis=1)
    hi = combo[["NSC1", "NSC2"]].max(axis=1)
    keys = combo.assign(lo=lo, hi=hi).groupby(["lo", "hi", "CELLNAME"]).size()
    return {
        "records": int(len(frame)), "combination_records": int(len(combo)),
        "drugs": int(len(set(lo) | set(hi))), "pairs": int(keys.reset_index()[["lo", "hi"]].drop_duplicates().shape[0]),
        "lines": int(combo["CELLNAME"].nunique()), "experiments": int(len(keys)),
        "records_per_experiment_median": float(keys.median()),
        "screeners": sorted(map(str, frame["SCREENER"].dropna().unique())),
    }


class VaultRefusal(RuntimeError):
    """Confirmatory outcomes stay sealed; the code names why."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


def open_vault(freeze_path: Path, log_path: Path, *, purpose: str, source: Path = ALMANAC_ZIP,
               root: Path = ROOT) -> dict:
    """Allow outcome access only against an intact freeze; append the opening to the vault log."""
    if not freeze_path.is_file():
        raise VaultRefusal("VAULT_SEALED", f"no freeze record at {freeze_path}")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    changed = [name for name, digest in freeze["files"].items() if sha256(root / name) != digest]
    if changed:
        raise VaultRefusal("FREEZE_MISMATCH", "frozen files changed: " + ", ".join(changed))
    entry = {"opened_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "purpose": purpose,
             "freeze_sha256": sha256(freeze_path), "data_sha256": sha256(source)}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    previous = log_path.read_text(encoding="utf-8").splitlines() if log_path.exists() else []
    entry["prior_openings"] = len(previous)
    with open(log_path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def almanac_names(path: Path = ALMANAC_DIR / "ComboCompoundNames_small.txt") -> dict[str, str]:
    """NSC -> first listed name (the file lists synonyms on repeated NSC rows)."""
    names: dict[str, str] = {}
    if path.is_file():
        for row in path.read_text(encoding="utf-8", errors="replace").splitlines():
            nsc, _, name = row.partition("\t")
            if nsc.strip() and name.strip():
                names.setdefault(nsc.strip(), name.strip())
    return names


def build_almanac(ticket: dict, cache: Path = CACHE / "almanac_v1.npz", *, source: Path = ALMANAC_ZIP,
                  names_path: Path = ALMANAC_DIR / "ComboCompoundNames_small.txt") -> Library:
    """Confirmatory library. `ticket` must come from `open_vault`; it is recorded in provenance."""
    if not ticket or "freeze_sha256" not in ticket:
        raise VaultRefusal("VAULT_SEALED", "build_almanac needs an open_vault ticket")
    started = time.time()
    frame = _almanac_frame(DESIGN_COLUMNS + ["CONC1", "CONC2"] + OUTCOME_COLUMNS, source)
    both = (frame["CONCINDEX1"] > 0) & (frame["CONCINDEX2"] > 0) & frame["NSC2"].notna()
    combo = frame[both].copy()
    combo["lo"] = combo[["NSC1", "NSC2"]].min(axis=1)
    combo["hi"] = combo[["NSC1", "NSC2"]].max(axis=1)
    combo = combo[np.isfinite(combo["SCORE"].astype(float))]
    experiments = combo.groupby(["lo", "hi", "CELLNAME"]).agg(y=("SCORE", "mean"), points=("SCORE", "size"))
    experiments = experiments.reset_index()
    # Single-agent records: drug 1 at a grid concentration and no drug 2 (the release's
    # pattern; rows with both indices 0 and no drug 2 are undocumented and excluded, counted).
    alone = (frame["CONCINDEX1"] > 0) & ~(frame["CONCINDEX2"] > 0) & frame["NSC2"].isna()
    excluded_rows = int((~both & ~alone).sum())
    single = frame[alone].copy()
    single["drug"] = single["NSC1"]
    single["conc"] = single["CONC1"]
    single["inhibition"] = (100.0 - np.minimum(single["PERCENTGROWTH"].astype(float), 100.0)) / 100.0
    curve = single.groupby(["drug", "CELLNAME", "conc"])["inhibition"].mean().reset_index()
    nscs = tuple(str(int(x)) for x in sorted(set(experiments["lo"]) | set(experiments["hi"])))
    lines = tuple(sorted(experiments["CELLNAME"].unique()))
    drug_index = {name: i for i, name in enumerate(nscs)}
    names = almanac_names(names_path)
    drugs = tuple(names.get(nsc, f"NSC {nsc}") for nsc in nscs)
    line_index = {name: i for i, name in enumerate(lines)}
    mono_mean = np.full((len(drugs), len(lines)), np.nan)
    mono_top = np.full((len(drugs), len(lines)), np.nan)
    for (drug, line), group in curve.groupby(["drug", "CELLNAME"]):
        if str(int(drug)) not in drug_index or line not in line_index:
            continue
        group = group.sort_values("conc")
        mono_mean[drug_index[str(int(drug))], line_index[line]] = float(group["inhibition"].mean())
        mono_top[drug_index[str(int(drug))], line_index[line]] = float(group["inhibition"].iloc[-1])
    a = np.array([drug_index[str(int(x))] for x in experiments["lo"]], dtype=np.int32)
    b = np.array([drug_index[str(int(x))] for x in experiments["hi"]], dtype=np.int32)
    c = np.array([line_index[x] for x in experiments["CELLNAME"]], dtype=np.int32)
    ma, mb = mono_mean[a, c], mono_mean[b, c]
    expected = 1.0 - (1.0 - np.clip(np.nan_to_num(ma), 0, 1)) * (1.0 - np.clip(np.nan_to_num(mb), 0, 1))
    provenance = {
        "source": "NCI-ALMANAC ComboDrugGrowth_Nov2017 (Holbeck et al. 2017 Cancer Res, doi:10.1158/0008-5472.CAN-17-0489)",
        "data_sha256": sha256(source), "vault_ticket": ticket, "nsc": list(nscs),
        "label": "mean NCI SCORE (ExpectedGrowth - PercentGrowth, pp) over all combination records",
        "excluded_undocumented_rows": excluded_rows, "single_agent_rows": int(alone.sum()),
        "build_seconds": round(time.time() - started, 1),
    }
    library = Library("almanac2017", drugs, lines, a, b, c, experiments["y"].to_numpy(float),
                      experiments["points"].to_numpy(np.int32), expected, mono_mean, mono_top,
                      ALMANAC_DAYS_PER_ROUND, HIT_THRESHOLD, provenance)
    library.save(cache)
    return library
