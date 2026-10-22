"""Data access for the PTV-1 / ProteinTalks release with stage-gated outcome access.

Everything that is an *outcome* of a treated experiment (functional label, treated proteome rows) of a final-evaluation
background is refused unless the write-once stage ledger has a 'final' entry created after FREEZE.json exists.
Baseline and vehicle-control rows of every background are inputs, not outcomes, and are always readable.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:/MAESTRO/data/external/ptv1_proteintalks_20261021")
DRIVE = ROOT / "drive"
CACHE = ROOT / "cache"
STUDY = Path(__file__).parent
LEDGER = STUDY / "STAGE_LEDGER.json"
PREFIX = "allcelltype_drugpair_crossdrug_"
SALT = "dual_core_20261021"
TIMES = (6, 24, 48)


def lineage_of(cell: str) -> str:
    return cell.replace("(ATCC)", "").strip()


def code_hash() -> str:
    h = hashlib.sha256()
    for p in sorted(STUDY.glob("*.py")):
        h.update(p.name.encode()); h.update(p.read_bytes())
    return h.hexdigest()


def partition() -> dict[str, str]:
    """Deterministic lineage -> {dev, sel, final}; fixed by hash before any labelled analysis."""
    lins = sorted({lineage_of(c) for c in ["BT20", "BT549", "DU4475", "HCC1143", "HCC1187", "HCC1395", "HCC1806", "HCC1937",
                                           "HCC38", "HCC70", "HS578T", "MCF7", "MDA-MB-231", "MDA-MB-436", "MDA-MB-453",
                                           "MDA-MB-468", "T47D"]})
    order = sorted(lins, key=lambda s: hashlib.sha256(f"{s}|{SALT}".encode()).hexdigest())
    out = {}
    for i, s in enumerate(order):
        out[s] = "dev" if i < 5 else ("sel" if i < 10 else "final")
    return out


def _fingerprint(s: str) -> np.ndarray:
    return np.asarray(ast.literal_eval(s.replace("nan", "None")), dtype=float)


class Release:
    def __init__(self):
        lab = pd.read_csv(DRIVE / (PREFIX + "loo_label.csv"), header=None, names=["exp", "t"])
        lab["y"] = pd.read_csv(DRIVE / (PREFIX + "pheno.csv"), header=None)[0]
        lab["cell"] = lab.exp.str.split("_").str[0]
        lab["lineage"] = lab.cell.map(lineage_of)
        lab["perts"] = lab.exp.str.split("_", n=1).str[1].str.strip().str.replace(r"\s+", " ", regex=True)
        lab["is_drug"] = lab.perts.str.contains("#")
        lab["ndrug"] = np.where(lab.is_drug, lab.perts.str.split().str.len(), 0)
        lab["part"] = lab.lineage.map(partition())
        self.rows = lab
        self._E = np.load(CACHE / "expr.npy")           # raw abundance, zero = not quantified (access via methods)
        self.P = np.load(CACHE / "pert.npy")            # 0 / 0.5 target-node encoding (a per-perturbation constant)
        self.nodes = pd.read_csv(DRIVE / (PREFIX + "node_Index.csv"), header=None)[0].tolist()
        self.rows["zero_frac"] = (self._E == 0).mean(1)
        self.rows["y_present"] = self.rows.y.notna()              # label presence only (not its value) stays readable
        if not stage_open("final"):
            self.rows.loc[self.rows.part == "final", "y"] = np.nan   # sealed outcome
        self._fp = None

    # ---- drug features -------------------------------------------------
    def fingerprints(self) -> dict[str, np.ndarray]:
        if self._fp is None:
            A = pd.read_csv(DRIVE / (PREFIX + "drug_fp_phychem_A.csv"), header=None)[0]
            B = pd.read_csv(DRIVE / (PREFIX + "drug_fp_phychem_B.csv"), header=None)[0]
            fp: dict[str, np.ndarray] = {}
            for i, r in self.rows[self.rows.is_drug].iterrows():
                ids = r.perts.split()
                if ids[0] not in fp:
                    fp[ids[0]] = _fingerprint(A[i])
                if len(ids) == 2 and ids[1] not in fp:
                    fp[ids[1]] = _fingerprint(B[i])
            self._fp = fp
        return self._fp

    def target_vector(self, drug_id: str) -> np.ndarray:
        r = self.rows[(self.rows.perts == drug_id) & (self.rows.t == 24)].index[0]
        return (self.P[r] != 0).astype(float)

    # ---- inputs (always readable) --------------------------------------
    def baseline(self, cell: str, min_obs: float = 0.5) -> np.ndarray:
        """Per-stock baseline: median of log1p(abundance) over the stock's usable 0 h rows (zero fraction <= 0.5)."""
        r = self.rows[(self.rows.cell == cell) & (self.rows.t == 0) & (self.rows.zero_frac <= min_obs)]
        if r.empty:
            r = self.rows[(self.rows.cell == cell) & (self.rows.t == 0)]
        return np.median(np.log1p(self._E[r.index]), axis=0)

    def control(self, cell: str, t: int, max_zero: float = 0.5) -> np.ndarray | None:
        r = self.rows[(self.rows.cell == cell) & (self.rows.t == t) & (~self.rows.is_drug) & (self.rows.zero_frac <= max_zero)]
        return None if r.empty else np.median(np.log1p(self._E[r.index]), axis=0)

    # ---- experiments (outcomes: stage-gated) ----------------------------
    def experiments(self, ndrug: int | None = None) -> pd.DataFrame:
        d = self.rows[self.rows.is_drug]
        g = d.groupby(["cell", "perts"], sort=True)
        out = g.agg(lineage=("lineage", "first"), part=("part", "first"), ndrug=("ndrug", "first"),
                    n_records=("exp", "nunique"), y_min=("y", "min"), y_max=("y", "max")).reset_index()
        out["y"] = g.y.mean().values
        if not stage_open("final"):
            sealed = out.part == "final"
            out.loc[sealed, ["y", "y_min", "y_max"]] = np.nan
        out["y_conflict"] = (out.y_min != out.y_max) & out.y_min.notna() & out.y_max.notna()
        if ndrug is not None:
            out = out[out.ndrug == ndrug]
        return out.reset_index(drop=True)

    def treated(self, cell: str, perts: str, t: int) -> np.ndarray | None:
        r = self.rows[(self.rows.cell == cell) & (self.rows.perts == perts) & (self.rows.t == t)]
        if r.empty:
            return None
        require_stage(self.rows.loc[r.index[0], "part"])
        return np.median(np.log1p(self._E[r.index]), axis=0)


def _ledger() -> list[dict]:
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else []


def open_stage(name: str) -> None:
    """Write-once stage claim; 'final' requires FREEZE.json with this exact code hash for every frozen file."""
    led = _ledger()
    if any(e["stage"] == name for e in led):
        raise RuntimeError(f"stage {name!r} already claimed")
    freeze_sha = None
    if name == "final":
        fz = STUDY / "FREEZE.json"
        if not fz.exists():
            raise RuntimeError("final stage requires FREEZE.json")
        frozen = json.loads(fz.read_text())["frozen_files"]
        bad = [n for n, h in frozen.items() if not (STUDY / n).exists() or hashlib.sha256((STUDY / n).read_bytes()).hexdigest() != h]
        if bad:
            raise RuntimeError(f"frozen files changed after the freeze: {bad[:5]}")
        freeze_sha = hashlib.sha256(fz.read_bytes()).hexdigest()
    led.append({"stage": name, "code_sha256": code_hash(), "freeze_sha256": freeze_sha})
    LEDGER.write_text(json.dumps(led, indent=1))


def stage_open(name: str) -> bool:
    return any(e["stage"] == name for e in _ledger())


def require_stage(part: str) -> None:
    if part == "final" and not stage_open("final"):
        raise PermissionError("final-evaluation outcomes are sealed until the final stage is claimed")
