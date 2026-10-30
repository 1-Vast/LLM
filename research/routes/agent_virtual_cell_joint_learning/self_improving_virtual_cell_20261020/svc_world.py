"""Retrospective intervention-response environments with a defensible information boundary.

A `World` holds the hidden activity matrix A[pair, cell] and the common information (derived monotherapy
reference, monotherapy activities). Solvers only ever see:

* `History`  - released labels (R = A - A_ref) of explicitly released cells,
* `Campaign` - a new cell: its common information plus a ledgered `query` for full-grid pair measurements.

The query unit is one pair-by-cell dose grid (a logical unit; not wells, cultures or money). Re-reading the
same unit is free and counted once. Unavailable outcomes are never imputed: only recorded cells are queryable.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PRIOR_WORK = ROOT / "tmp" / "functional_rule_revision_20261020"
WORK = ROOT / "tmp" / "self_improving_virtual_cell_20261020"
N_MODULES = 4
SHORTLIST_K = 5


def digest(*arrays, extra: str = "") -> str:
    h = hashlib.sha256(extra.encode())
    for a in arrays:
        a = np.ascontiguousarray(a)
        h.update(str(a.shape).encode())
        h.update(a.tobytes())
    return h.hexdigest()


# --------------------------------------------------------------------------- static pair metadata
@dataclass
class Static:
    """Cell-independent identities: which drugs form each pair, and the functional class of each pair."""
    drugs: tuple
    pair_i: np.ndarray
    pair_j: np.ndarray
    drug_module: np.ndarray
    pair_names: tuple

    @property
    def n(self) -> int:
        return len(self.pair_i)

    @property
    def n_drugs(self) -> int:
        return len(self.drugs)

    @property
    def classes(self) -> list:
        k = int(self.drug_module.max()) + 1
        return [(a, b) for a in range(k) for b in range(a, k)]

    @property
    def pair_class(self) -> np.ndarray:
        classes = {c: k for k, c in enumerate(self.classes)}
        mi, mj = self.drug_module[self.pair_i], self.drug_module[self.pair_j]
        return np.array([classes[(min(a, b), max(a, b))] for a, b in zip(mi, mj)])


@dataclass
class History:
    """Released labels for a set of cells (A - A_ref), plus the common monotherapy features of those cells."""
    cells: tuple
    R: np.ndarray            # [n, h]
    Aref: np.ndarray         # [n, h]
    amin: np.ndarray         # [n, h]
    amax: np.ndarray         # [n, h]

    @property
    def version(self) -> str:
        return digest(self.R, self.Aref, extra="|".join(map(str, self.cells)))[:16]

    def subset(self, keep) -> "History":
        keep = list(keep)
        return History(tuple(self.cells[k] for k in keep), self.R[:, keep], self.Aref[:, keep], self.amin[:, keep], self.amax[:, keep])


@dataclass
class Campaign:
    """A new cell background: common information, a query budget and a ledger."""
    cell: object
    Aref: np.ndarray
    amin: np.ndarray
    amax: np.ndarray
    budget: int
    _read: object = field(repr=False, default=None)
    queried: dict = field(default_factory=dict)       # pair -> recorded activity A
    log: list = field(default_factory=list)
    probe_mask: np.ndarray | None = None              # None: all pairs queryable; else only these (transfer contract)

    def query(self, pairs, stage: str = "") -> dict:
        new = list(dict.fromkeys(int(p) for p in pairs if int(p) not in self.queried))      # repeated reads count once, also within one call
        if len(self.queried) + len(new) > self.budget:
            raise BudgetExceeded(f"{len(self.queried)} + {len(new)} > {self.budget}")
        if self.probe_mask is not None and not all(self.probe_mask[p] for p in new):
            raise IllegalAction("query outside the legal probe set")
        values = self._read(new)
        for p, v in zip(new, values):
            self.queried[p] = float(v)
        self.log.append({"stage": stage, "pairs": new, "re_reads_not_counted": len(list(pairs)) - len(new)})
        return {int(p): self.queried[int(p)] for p in pairs}

    @property
    def spent(self) -> int:
        return len(self.queried)

    @property
    def left(self) -> int:
        return self.budget - self.spent


class BudgetExceeded(RuntimeError):
    pass


class IllegalAction(RuntimeError):
    pass


class World:
    """Holds the hidden truth; hands out History, Campaign and the evaluator's realized utility."""

    def __init__(self, static: Static, cells, Aref, amin, amax, A_truth, label: str = ""):
        self.static, self.cells = static, tuple(cells)
        self._Aref, self._amin, self._amax = Aref, amin, amax
        self.__truth = np.asarray(A_truth, dtype=float)
        self.label = label
        self.meta = {}                                  # evaluator-only generating-process facts (synthetic worlds)
        self._index = {c: k for k, c in enumerate(self.cells)}

    def history(self, cells) -> History:
        ix = [self._index[c] for c in cells]
        return History(tuple(cells), self.__truth[:, ix] - self._Aref[:, ix], self._Aref[:, ix], self._amin[:, ix], self._amax[:, ix])

    def campaign(self, cell, budget: int, probe_mask=None) -> Campaign:
        k = self._index[cell]
        truth = self.__truth

        def read(pairs):
            return truth[list(pairs), k]

        return Campaign(cell, self._Aref[:, k].copy(), self._amin[:, k].copy(), self._amax[:, k].copy(), budget, read, probe_mask=probe_mask)

    def anchor_only(self, seed: int = 0) -> "World":
        """Matched control: keep each cell's shared drug-cell effects (additive drug model of R), break the pair-specific relationship
        by permuting the remaining residual across pairs within each cell. Same Aref, monotherapy information and scale."""
        rng = np.random.default_rng(seed)
        st = self.static
        n, h = self.__truth.shape
        D = np.zeros((n, st.n_drugs + 1))
        D[np.arange(n), st.pair_i] = 1
        D[np.arange(n), st.pair_j] = 1
        D[:, -1] = 1
        R = self.__truth - self._Aref
        coef = np.linalg.solve(D.T @ D + 1.0 * np.eye(D.shape[1]), D.T @ R)
        add = D @ coef
        resid = R - add
        perm = np.stack([rng.permutation(n) for _ in range(h)], 1)
        resid_p = np.take_along_axis(resid, perm, 0)
        w = World(st, self.cells, self._Aref, self._amin, self._amax, self._Aref + add + resid_p, label=self.label + "_anchor_only")
        return w

    # evaluator-only interface (never passed to a solver)
    def truth_column(self, cell) -> np.ndarray:
        return self.__truth[:, self._index[cell]].copy()


def shortlist(score: np.ndarray, pool_mask: np.ndarray, k: int = SHORTLIST_K) -> np.ndarray:
    idx = np.nonzero(pool_mask)[0]
    order = np.lexsort((idx, -score[idx]))
    return idx[order[:k]]


def realized_utility(world: World, campaign: Campaign, nominated, pool_mask=None) -> dict:
    """Realized published-outcome utility: mean recorded activity of the nominated pairs. Queried candidates keep
    their recorded value (direct-measurement replay); the unqueried-only score is a separate endpoint."""
    truth = world.truth_column(campaign.cell)
    pool = np.ones(len(truth), bool) if pool_mask is None else pool_mask
    nominated = [int(p) for p in nominated]
    assert len(set(nominated)) == len(nominated) == SHORTLIST_K and all(pool[p] for p in nominated), "duplicate or out-of-pool nomination"
    oracle = float(np.sort(truth[pool])[::-1][:SHORTLIST_K].mean())
    unq = [p for p in nominated if p not in campaign.queried]
    return {"utility": float(truth[nominated].mean()), "oracle": oracle, "regret": oracle - float(truth[nominated].mean()),
            "n_nominated_queried": SHORTLIST_K - len(unq),
            "unqueried_only_utility": float(truth[unq].mean()) if unq else None}


# --------------------------------------------------------------------------- real-data export (allowlisted)
def modules_from_monotherapy(mono: np.ndarray, k: int = N_MODULES) -> np.ndarray:
    from scipy.cluster.hierarchy import fcluster, linkage
    filled = np.where(np.isfinite(mono), mono, np.nanmean(mono, axis=1, keepdims=True))
    raw = fcluster(linkage(filled, method="ward"), t=k, criterion="maxclust") - 1
    order = np.argsort([-filled[raw == c].mean() for c in range(raw.max() + 1)])
    rank = {old: new for new, old in enumerate(order)}
    return np.array([rank[c] for c in raw])


def export_oneil(out: Path | None = None) -> dict:
    """Allowlisted export: all old-S outcomes and ONLY the acquired old-C panel pairs (memory-mapped slices).
    Old G/F outcome files and unpurchased C values are never opened. No raw workbook is parsed."""
    out = Path(out or WORK / "env_export.npz")
    out.parent.mkdir(parents=True, exist_ok=True)
    study = ROOT / "research" / "functional_rule_revision_20261020"
    freeze = json.loads((study / "FREEZE.json").read_text(encoding="utf-8"))
    trace = json.loads((study / "CHALLENGE_TRACE.json").read_text(encoding="utf-8"))
    panel = sorted(int(p) for p in freeze["panel"]["pair_ids"])
    disclosed = next(e["pairs"] for e in trace["vault_ledger"] if e["op"] == "disclose_C")
    assert panel == sorted(disclosed), "panel in FREEZE.json differs from the ledger of the disclosed challenge batch"
    part = json.loads((study / "PARTITION.json").read_text(encoding="utf-8"))
    g = np.load(PRIOR_WORK / "groups.npz", allow_pickle=False)
    pairs = list(zip(g["pair_a"].tolist(), g["pair_b"].tolist()))
    role = np.array([part["roles"]["|".join(p)] for p in pairs])
    s_pairs = [p for p, r in enumerate(role) if r == "S"]
    assert all(role[p] == "C" for p in panel)
    allowed = sorted(set(s_pairs) | set(panel))
    pos = {p: k for k, p in enumerate(allowed)}
    n_cells, drugs = len(g["cells"]), g["drugs"].tolist()
    g_pair, g_cell = g["g_pair"], g["g_cell"]
    A = np.full((len(allowed), n_cells), np.nan)
    aref = np.full_like(A, np.nan)
    amin, amax = np.full_like(A, np.nan), np.full_like(A, np.nan)
    mono = np.full((len(drugs), n_cells), np.nan)
    rows_s = np.nonzero(np.isin(g_pair, s_pairs))[0]
    values_s = np.load(PRIOR_WORK / "sealed" / "outcomes_S.npy")
    rows_c = np.nonzero(np.isin(g_pair, panel))[0]
    values_c = np.load(PRIOR_WORK / "sealed" / "outcomes_C.npy", mmap_mode="r")
    for rows, getter in ((rows_s, lambda r: values_s[r]), (rows_c, lambda r: np.asarray(values_c[r]))):
        vals = getter(rows)
        for r, v in zip(rows, vals):
            A[pos[int(g_pair[r])], g_cell[r]] = v
    for r in np.concatenate([rows_s, rows_c]):
        p, c = pos[int(g_pair[r])], g_cell[r]
        aref[p, c] = g["a_ref"][r]
        ai, aj = g["a_mono_i"][r], g["a_mono_j"][r]
        amin[p, c], amax[p, c] = min(ai, aj), max(ai, aj)
    for r in range(len(g_pair)):                      # monotherapy panel: common information for every pair role
        mono[g["g_i"][r], g_cell[r]] = g["a_mono_i"][r]
        mono[g["g_j"][r], g_cell[r]] = g["a_mono_j"][r]
    assert np.isfinite(A).all() and np.isfinite(aref).all()
    pi = np.array([drugs.index(pairs[p][0]) for p in allowed])
    pj = np.array([drugs.index(pairs[p][1]) for p in allowed])
    module = modules_from_monotherapy(mono)
    np.savez_compressed(out, A=A, Aref=aref, amin=amin, amax=amax, pair_i=pi, pair_j=pj, drug_module=module,
                        drugs=np.array(drugs), cells=g["cells"], pair_ids=np.array(allowed), pair_role=role[allowed],
                        mono=mono)
    return {"path": str(out), "n_pairs": len(allowed), "n_S_pairs": len(s_pairs), "n_C_panel_pairs": len(panel),
            "n_cells": n_cells, "C_panel_pair_ids": panel,
            "c_pairs_not_acquired_excluded": int((role == "C").sum() - len(panel)),
            "g_f_files_opened": False, "raw_workbook_parsed": False}


def load_export(path: Path | None = None) -> World:
    z = np.load(Path(path or WORK / "env_export.npz"), allow_pickle=False)
    drugs = tuple(z["drugs"].tolist())
    ids = z["pair_ids"]
    names = tuple(f"{drugs[i]}+{drugs[j]}" for i, j in zip(z["pair_i"], z["pair_j"]))
    static = Static(drugs, z["pair_i"], z["pair_j"], z["drug_module"], names)
    return World(static, tuple(z["cells"].tolist()), z["Aref"], z["amin"], z["amax"], z["A"], label="oneil_export")


# --------------------------------------------------------------------------- synthetic worlds (software/method controls)
def make_synthetic(kind: str, seed: int, n_drugs: int = 24, n_cells: int = 24) -> World:
    """Fixed-instance synthetic worlds. kind in {null_anchor, low_rank, compositional}. Not biological evidence."""
    rng = np.random.default_rng(1000 * seed + {"null_anchor": 1, "low_rank": 2, "compositional": 3}[kind])
    drugs = tuple(f"d{k:02d}" for k in range(n_drugs))
    ii, jj = np.triu_indices(n_drugs, 1)
    n = len(ii)
    module = rng.integers(0, N_MODULES, n_drugs)
    names = tuple(f"{drugs[i]}+{drugs[j]}" for i, j in zip(ii, jj))
    static = Static(drugs, ii, jj, module, names)
    cells = tuple(f"c{k:02d}" for k in range(n_cells))
    level = rng.uniform(0.30, 0.50, n_drugs)
    mono = np.clip(level[:, None] + 0.05 * rng.standard_normal((n_drugs, n_cells)), 0.02, 0.95)
    ai, aj = mono[ii], mono[jj]                                   # [n, cells]
    Aref = 1 - (1 - ai) * (1 - aj)
    mu = 0.03 * rng.standard_normal(n)
    noise = 0.015 * rng.standard_normal((n, n_cells))
    delta = 0.02 * rng.standard_normal((n_drugs, n_cells))        # shared-anchor drug-cell effect (not combination specific)
    R = mu[:, None] + noise + delta[ii] + delta[jj]
    cls = static.pair_class
    n_cls = len(static.classes)
    if kind == "low_rank":
        L = rng.standard_normal((n, 2)) * 0.03
        S = rng.standard_normal((n_cells, 2))
        R = R + L @ S.T
    elif kind == "compositional":
        gate = (rng.random((n_cells, 3)) < 0.45).astype(float)    # hidden binary cell attributes
        target = rng.choice(n_cls, 3, replace=False)
        beta = np.array([0.10, -0.08, 0.09])
        for g_ in range(3):
            R = R + beta[g_] * gate[:, g_][None, :] * (cls == target[g_])[:, None]
        conj = gate[:, 0] * gate[:, 1]                             # conjunction effect on a fourth class
        other = rng.choice([c for c in range(n_cls) if c not in target])
        R = R + 0.12 * conj[None, :] * (cls == other)[:, None]
        R = R + 0.02 * rng.standard_normal((1, n_cells)) * rng.standard_normal((n, 1))   # nuisance variation
    world = World(static, cells, Aref, np.minimum(ai, aj), np.maximum(ai, aj), Aref + R, label=f"synthetic_{kind}_{seed}")
    if kind == "compositional":
        world.meta = {"target_classes": [int(t) for t in target], "conjunction_class": int(other)}
    return world
