"""Raw O'Neil 2016 adapter for the functional-rule-revision pilot.

Responsibilities: parse the authenticated original workbooks, keep original row locators, build
canonical unordered drug-pair x cell groups on the primary batches (1, 2), compute the derived
same-batch monotherapy reference, and expose outcomes only through role-restricted views.

The endpoint is A = 1 - mean(X/X0) over the 16 published grid points (equal weight, no clipping).
The reference residual is R = A - A_ref, where A_ref = 1 - mean(X_a(c_a) * X_b(c_b)) uses
same-batch log-concentration interpolation of the single-agent X/X0 curves (never extrapolated,
never borrowed from another batch). Interpolated values are derived references, not observations.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from tools.datasets.combination_screens import (  # noqa: E402  (reuse the maintained streaming reader)
    ONEIL_COMBINATION, ONEIL_DIR, ONEIL_SINGLE, iter_xlsx_rows)

PRIMARY_BATCHES = ("1", "2")
GRID_POINTS = 16
REL_TOL, ABS_TOL = 1e-7, 1e-12


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(path: Path) -> str:
    """Line-ending-normalised digest (Windows CRLF must not change a frozen hash)."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _num(text) -> float:
    if text is None or str(text).strip() == "":
        return float("nan")
    try:
        return float(text)
    except ValueError:
        return float("nan")


# --------------------------------------------------------------------------- raw readers
def read_single_agent(path: Path | None = None) -> dict:
    path = path or ONEIL_DIR / ONEIL_SINGLE
    rows = iter_xlsx_rows(path)
    header = next(rows)
    col = {name: i for i, name in enumerate(header) if name}
    conc_col = next(i for name, i in col.items() if name.startswith("Drug_concentration"))
    out = defaultdict(list)
    for number, row in enumerate(rows, start=2):  # worksheet row number (header is row 1)
        row = row + [None] * (len(header) - len(row))
        out["row"].append(number)
        out["batch"].append(str(row[col["BatchID"]]).strip())
        out["cell"].append(str(row[col["cell_line"]]).strip())
        out["drug"].append(str(row[col["drug_name"]]).strip())
        out["conc"].append(_num(row[conc_col]))
        out["x"].append(_num(row[col["X/X0"]]))
        out["mu"].append(_num(row[col["mu/muMax"]]))
        out["viability"].append([_num(row[col[f"viability{k}"]]) for k in range(1, 7)])
    return _arrays(out)


def read_combination(path: Path | None = None) -> dict:
    path = path or ONEIL_DIR / ONEIL_COMBINATION
    rows = iter_xlsx_rows(path)
    header = next(rows)
    col = {name: i for i, name in enumerate(header) if name}
    a_conc = next(i for name, i in col.items() if name.startswith("drugA Conc"))
    b_conc = next(i for name, i in col.items() if name.startswith("drugB Conc"))
    out = defaultdict(list)
    for number, row in enumerate(rows, start=2):
        row = row + [None] * (len(header) - len(row))
        out["row"].append(number)
        out["batch"].append(str(row[col["BatchID"]]).strip())
        out["cell"].append(str(row[col["cell_line"]]).strip())
        out["drug_a"].append(str(row[col["drugA_name"]]).strip())
        out["drug_b"].append(str(row[col["drugB_name"]]).strip())
        out["conc_a"].append(_num(row[a_conc]))
        out["conc_b"].append(_num(row[b_conc]))
        out["x"].append(_num(row[col["X/X0"]]))
        out["mu"].append(_num(row[col["mu/muMax"]]))
        out["viability"].append([_num(row[col[f"viability{k}"]]) for k in range(1, 5)])
    return _arrays(out)


def _arrays(columns: dict) -> dict:
    result = {}
    for key, values in columns.items():
        if key in ("batch", "cell", "drug", "drug_a", "drug_b"):
            result[key] = np.array(values, dtype=object)
        elif key == "row":
            result[key] = np.array(values, dtype=np.int64)
        else:
            result[key] = np.array(values, dtype=float)
    return result


# --------------------------------------------------------------------------- monotherapy curves
@dataclass
class Curve:
    conc: np.ndarray        # ascending distinct concentrations (uM)
    x: np.ndarray           # mean X/X0 at each distinct concentration
    n_rows: np.ndarray      # source rows contributing at each concentration
    rows: tuple             # source worksheet row numbers


def build_curves(single: dict) -> dict:
    """(batch, cell, drug) -> Curve. Non-finite X/X0 rows are excluded and counted by the caller."""
    grouped = defaultdict(lambda: defaultdict(list))
    row_ids = defaultdict(list)
    for i in range(len(single["row"])):
        if not (math.isfinite(single["x"][i]) and math.isfinite(single["conc"][i]) and single["conc"][i] > 0):
            continue
        key = (single["batch"][i], single["cell"][i], single["drug"][i])
        grouped[key][single["conc"][i]].append(single["x"][i])
        row_ids[key].append(int(single["row"][i]))
    curves = {}
    for key, by_conc in grouped.items():
        concs = np.array(sorted(by_conc))
        curves[key] = Curve(concs, np.array([np.mean(by_conc[c]) for c in concs]),
                            np.array([len(by_conc[c]) for c in concs]), tuple(row_ids[key]))
    return curves


def interpolate(curve: Curve, dose: float) -> float | None:
    """Log-concentration interpolation strictly inside the measured range; otherwise None (no extrapolation)."""
    lo, hi = curve.conc[0], curve.conc[-1]
    tol = REL_TOL * dose + ABS_TOL
    if dose < lo - tol or dose > hi + tol or len(curve.conc) < 2:
        return None
    return float(np.interp(math.log10(dose), np.log10(curve.conc), curve.x))


# --------------------------------------------------------------------------- group table
@dataclass
class GroupTable:
    """One row per (canonical unordered drug pair, cell) primary group."""
    drugs: tuple
    cells: tuple
    pairs: tuple                       # canonical (drug_i, drug_j) names, sorted alphabetically within the pair
    g_pair: np.ndarray                 # pair index
    g_cell: np.ndarray                 # cell index
    g_batch: np.ndarray                # object array of batch ids
    g_i: np.ndarray                    # drug index (first, alphabetical)
    g_j: np.ndarray                    # drug index (second)
    a_ref: np.ndarray                  # derived reference activity 1 - mean(Xa*Xb)
    a_mono_i: np.ndarray               # mono activity of drug i at its grid doses (derived, interpolated)
    a_mono_j: np.ndarray
    eligible: np.ndarray               # structurally and numerically valid group
    reason: np.ndarray                 # exclusion reason ("" when eligible)
    first_row: np.ndarray              # smallest combination worksheet row (locator)
    n_rows: np.ndarray
    n_dose_matched: np.ndarray         # grid points whose BOTH doses match a measured single-agent dose
    mono_rows_i: list = field(default_factory=list)
    mono_rows_j: list = field(default_factory=list)
    comb_rows: list = field(default_factory=list)   # worksheet rows of the 16 points
    # outcomes are NOT stored here; see build_outcomes
    meta: dict = field(default_factory=dict)


def canonical(a: str, b: str):
    return (a, b) if a <= b else (b, a)


def build_groups(comb: dict, single: dict):
    """Return (GroupTable, outcomes) where outcomes carries A_obs and the point-level data.

    Outcomes are returned separately so a caller can seal them by role before any use.
    """
    curves = build_curves(single)
    sel = np.isin(comb["batch"], PRIMARY_BATCHES)
    idx = np.nonzero(sel)[0]
    grouped = defaultdict(list)
    for i in idx:
        da, db = comb["drug_a"][i], comb["drug_b"][i]
        pair = canonical(da, db)
        if da <= db:
            ca, cb = comb["conc_a"][i], comb["conc_b"][i]
        else:
            ca, cb = comb["conc_b"][i], comb["conc_a"][i]
        grouped[(pair, comb["cell"][i])].append((int(i), comb["batch"][i], ca, cb))
    drugs = tuple(sorted({d for (pair, _), _ in grouped.items() for d in pair}))
    cells = tuple(sorted({c for (_, c) in grouped}))
    pairs = tuple(sorted({pair for (pair, _) in grouped}))
    di = {d: k for k, d in enumerate(drugs)}
    ci = {c: k for k, c in enumerate(cells)}
    pi = {p: k for k, p in enumerate(pairs)}
    keys = sorted(grouped, key=lambda k: (pi[k[0]], ci[k[1]]))

    # drug-cell dose grids come from the design (union of concentrations used in combinations)
    grid = defaultdict(set)
    for (pair, cell), pts in grouped.items():
        for _, batch, ca, cb in pts:
            grid[(batch, cell, pair[0])].add(ca)
            grid[(batch, cell, pair[1])].add(cb)

    n = len(keys)
    arr = lambda dt: np.zeros(n, dtype=dt)  # noqa: E731
    g_pair, g_cell, g_i, g_j = arr(np.int32), arr(np.int32), arr(np.int32), arr(np.int32)
    g_batch = np.empty(n, dtype=object)
    a_ref, a_mi, a_mj = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    eligible, reason = np.zeros(n, bool), np.empty(n, dtype=object)
    first_row, n_rows, n_match = arr(np.int64), arr(np.int32), arr(np.int32)
    mono_i, mono_j, comb_rows = [], [], []
    a_obs, x_points = np.full(n, np.nan), []
    for g, (pair, cell) in enumerate(keys):
        pts = grouped[(pair, cell)]
        g_pair[g], g_cell[g] = pi[pair], ci[cell]
        g_i[g], g_j[g] = di[pair[0]], di[pair[1]]
        batches = {p[1] for p in pts}
        g_batch[g] = sorted(batches)[0]
        first_row[g] = comb["row"][min(p[0] for p in pts)]
        n_rows[g] = len(pts)
        comb_rows.append(tuple(int(comb["row"][p[0]]) for p in pts))
        why = ""
        doses = {(round(p[2], 12), round(p[3], 12)) for p in pts}
        if len(batches) != 1:
            why = "mixed_batch"
        elif len(pts) != GRID_POINTS or len(doses) != GRID_POINTS:
            why = "incomplete_or_duplicated_grid"
        xs = np.array([comb["x"][p[0]] for p in pts])
        if not why and not np.all(np.isfinite(xs)):
            why = "missing_combination_response"
        curve_a = curves.get((g_batch[g], cell, pair[0]))
        curve_b = curves.get((g_batch[g], cell, pair[1]))
        mono_i.append(curve_a.rows if curve_a else ())
        mono_j.append(curve_b.rows if curve_b else ())
        if not why and (curve_a is None or curve_b is None):
            why = "missing_same_batch_monotherapy"
        if not why:
            expected, ok = [], True
            matched = 0
            for _, _, ca, cb in pts:
                xa, xb = interpolate(curve_a, ca), interpolate(curve_b, cb)
                if xa is None or xb is None:
                    ok = False
                    break
                expected.append(xa * xb)
                matched += int(_matches(curve_a, ca) and _matches(curve_b, cb))
            if not ok:
                why = "dose_outside_monotherapy_range"
            else:
                a_ref[g] = 1.0 - float(np.mean(expected))
                n_match[g] = matched
                a_obs[g] = 1.0 - float(np.mean(xs))
                for slot, curve, drug in ((a_mi, curve_a, pair[0]), (a_mj, curve_b, pair[1])):
                    levels = sorted(grid[(g_batch[g], cell, drug)])
                    vals = [interpolate(curve, d) for d in levels]
                    if all(v is not None for v in vals):
                        slot[g] = 1.0 - float(np.mean(vals))
                if not (math.isfinite(a_mi[g]) and math.isfinite(a_mj[g])):
                    why = "monotherapy_grid_outside_range"
        x_points.append(xs)
        eligible[g], reason[g] = (why == ""), why
    table = GroupTable(drugs, cells, pairs, g_pair, g_cell, g_batch, g_i, g_j, a_ref, a_mi, a_mj,
                       eligible, reason, first_row, n_rows, n_match, mono_i, mono_j, comb_rows)
    return table, {"a_obs": a_obs, "x_points": x_points}


def _matches(curve: Curve, dose: float) -> bool:
    return bool(np.any(np.abs(curve.conc - dose) <= REL_TOL * np.abs(dose) + ABS_TOL))


# --------------------------------------------------------------------------- role-restricted outcomes
class AccessViolation(RuntimeError):
    """Raised when code asks for outcomes its stage is not allowed to read."""


ROLES = ("S", "C", "G", "F")


def write_sealed(directory: Path, a_obs: np.ndarray, role_of_group: np.ndarray) -> dict:
    """Write one outcome file per role (NaN outside the role); return the sealed-file receipts."""
    directory.mkdir(parents=True, exist_ok=True)
    receipts = {}
    for role in ROLES:
        values = np.where(role_of_group == role, a_obs, np.nan)
        path = directory / f"outcomes_{role}.npy"
        np.save(path, values)
        receipts[role] = {"file": path.name, "sha256": sha256_file(path), "n_groups": int((role_of_group == role).sum())}
    return receipts


class OutcomeVault:
    """Releases activity outcomes only through named, logged operations that read one role file each.

    S is readable from the start. C is readable only for the acquired panel after one disclosure.
    G is readable by one retention query per arm, after the challenge disclosure. F is readable by
    the final evaluator once, after every retention decision. The ledger of reads is part of the
    audit record. Files of a closed role are not opened (poison fixtures verify this in tests).
    """

    def __init__(self, directory: Path, g_pair: np.ndarray, role_of_pair: dict, state_path: Path | None = None):
        self._dir = Path(directory)
        self._pair = np.asarray(g_pair)
        self._role = role_of_pair
        self.ledger: list[dict] = []
        self._panel: tuple | None = None
        self._g_used: set = set()
        self._f_used = False
        self._state = Path(state_path) if state_path else None
        if self._state is not None and self._state.exists():
            saved = json.loads(self._state.read_text(encoding="utf-8"))
            self.ledger = saved["ledger"]
            self._panel = tuple(saved["panel"]) if saved["panel"] is not None else None
            self._g_used = set(saved["g_used"])
            self._f_used = bool(saved["f_used"])

    def _save(self):
        if self._state is not None:
            self._state.write_text(json.dumps({"ledger": self.ledger, "panel": list(self._panel) if self._panel is not None else None,
                                               "g_used": sorted(self._g_used), "f_used": self._f_used}, indent=1) + "\n",
                                   encoding="utf-8", newline="\n")

    def _load(self, role: str) -> np.ndarray:
        return np.load(self._dir / f"outcomes_{role}.npy")

    def _log(self, **event):
        self.ledger.append(event)
        self._save()

    def source(self) -> np.ndarray:
        values = self._load("S")
        self._log(op="read_S", n=int(np.isfinite(values).sum()))
        return values

    def disclose_challenge(self, panel_pairs) -> np.ndarray:
        if self._panel is not None:
            raise AccessViolation("challenge batch already disclosed")
        panel = tuple(sorted(int(p) for p in panel_pairs))
        if any(self._role[p] != "C" for p in panel):
            raise AccessViolation("challenge panel must lie in role C")
        mask = np.isin(self._pair, panel)
        self._panel = panel
        values = np.where(mask, self._load("C"), np.nan)
        self._log(op="disclose_C", pairs=list(panel), n=int(np.isfinite(values).sum()))
        return values

    def retention_query(self, arm: str, evaluator):
        if self._panel is None:
            raise AccessViolation("G is closed until the challenge batch has been disclosed")
        if arm in self._g_used:
            raise AccessViolation(f"arm {arm!r} has already used its single G query")
        self._g_used.add(arm)
        values = self._load("G")
        self._log(op="G_query", arm=arm, n=int(np.isfinite(values).sum()))
        return evaluator(values)

    def final_evaluation(self, evaluator):
        if self._f_used:
            raise AccessViolation("F has already been opened")
        if not self._g_used:
            raise AccessViolation("F is closed until retention decisions are recorded")
        self._f_used = True
        values = self._load("F")
        self._log(op="F_final", n=int(np.isfinite(values).sum()))
        return evaluator(values)
