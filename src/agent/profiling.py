"""Certified profiling campaign: complete a compound x line response map within a well budget.

File summary
- Path: src/agent/profiling.py
- Purpose: run one budgeted profiling campaign over a library of unprofiled compounds. The agent
  profiles cells, and the virtual cell fills the rest with certified transfer.
- Core points:
  - The agent never reads a response it did not profile. `measure(cells)` is the only route to an
    outcome, whether a laboratory or a replay of a measured screen.
  - State: the profiled cells and their responses, written into the agent's own copy of the atlas
    rows of the library. Reference quantities (maps, generic directions, gamma) never change.
  - Two planners:
    - ``"sparse_transfer"`` (default) spends the whole budget in one turnaround with
      `maestro.transfer_value.sparse_transfer_design`.
    - ``"value_of_information"`` spends it over ``rounds`` turnarounds. Each round:
      1. certify every open cell, with the compound's profiled lines visible;
      2. plan the batch with `maestro.transfer_value.plan_batch`;
      3. profile it;
      4. replan.
  - Block Q (2026-10-12) chose the default:
    - at one well per compound, the sparse design beat the value-of-information planner in 11 of
      11 sealed campaigns;
    - with at least two wells per compound, the planner won in 10 of 11 (secondary).
  - The report gives:
    - the profiled cells;
    - the certified fill of every other cell, refusal codes included;
    - the laboratory cost in wells and plate turnarounds.
- Interfaces: `PLANNERS`, `ProfilingSpec`, `ProfilingReport`, `run_profiling`.
- Depends on: numpy, `maestro.transfer_value`, `virtual_cell.knowledge_transfer`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from maestro.transfer_value import plan_batch, sparse_transfer_design
from virtual_cell import knowledge_transfer as kt

PLANNERS = ("sparse_transfer", "value_of_information")


@dataclass(frozen=True)
class ProfilingSpec:
    budget_wells: int
    planner: str = "sparse_transfer"
    rounds: int = 4                 # used by the value-of-information planner only

    def __post_init__(self) -> None:
        if type(self.budget_wells) is not int or type(self.rounds) is not int:
            raise ValueError("budget_wells and rounds must be integers")
        if self.budget_wells < 0 or self.rounds < 1:
            raise ValueError("need a non-negative budget and at least one round")
        if self.planner not in PLANNERS:
            raise ValueError(f"UNKNOWN_PLANNER: {self.planner!r}; expected one of {PLANNERS}")


@dataclass
class ProfilingReport:
    profiled: np.ndarray            # library x lines boolean
    fills: np.ndarray               # library x lines x genes unit centred fills (0 where profiled)
    p_active: np.ndarray            # library x lines, certified P(active) of unprofiled cells
    expected_cosine: np.ndarray     # library x lines
    refusal: np.ndarray             # library x lines refusal code ("" if none)
    batches: list = field(default_factory=list)

    @property
    def wells(self) -> int:
        return int(self.profiled.sum())

    @property
    def turnarounds(self) -> int:
        return len(self.batches)


def _certify(atlas: kt.TransferAtlas, certifier: kt.Certifier, library: np.ndarray, grid: np.ndarray,
             profiled: np.ndarray, static: dict) -> dict:
    n, L = grid.shape
    out = {"dir": np.zeros((n, L, atlas.Yc.shape[2])), "p": np.zeros((n, L)), "ecos": np.zeros((n, L)),
           "rho": np.zeros((n, L)), "refusal": np.full((n, L), "", dtype="<U40")}
    for T in range(L):
        rows = np.flatnonzero(grid[:, T] & ~profiled[:, T])
        if not len(rows):
            continue
        if T not in static:
            static[T] = {k: kt.route_static(atlas, library, T, k) for k in ("chem", "know")}
        sliced = {k: kt.Route(r.pred[rows], r.available[rows], r.support[rows]) for k, r in static[T].items()}
        pred = kt.predict(atlas, certifier, library[rows], T, profiled[rows], static=sliced)
        c = pred.certificate
        out["dir"][rows, T] = pred.direction
        out["p"][rows, T], out["ecos"][rows, T], out["rho"][rows, T], out["refusal"][rows, T] = (
            c.p_active, c.expected_cosine, c.rho, c.refusal)
    return out


def run_profiling(atlas: kt.TransferAtlas, certifier: kt.Certifier, library: np.ndarray, grid: np.ndarray,
                  measure: Callable[[np.ndarray], np.ndarray], spec: ProfilingSpec, *, kappa: np.ndarray | None = None,
                  seed: int = 0) -> ProfilingReport:
    """Run one campaign over ``library``, the atlas rows of unprofiled compounds.

    ``grid`` marks the cells of the library that can be profiled.

    ``measure(cells)`` takes an array of (library index, line) pairs and returns their raw responses
    (cells x genes). The library rows of the atlas are overwritten with what is measured, so the
    caller passes an atlas whose library rows hold no response (NaN).
    """
    library = np.asarray(library)
    grid = np.asarray(grid, bool)
    if grid.shape != (len(library), atlas.Yc.shape[1]):
        raise ValueError("AXIS_MISMATCH: grid must be library x lines")
    if atlas.ref[library].any():
        raise ValueError("LIBRARY_CONTAINS_REFERENCES")
    if np.isfinite(atlas.Yc[library, :, 0]).any():
        raise ValueError("LIBRARY_RESPONSES_VISIBLE: library rows must hold no response before profiling")
    kappa = kt.transfer_table(atlas) if kappa is None else np.asarray(kappa, dtype=float)
    profiled = np.zeros_like(grid)
    batches: list = []
    static: dict = {}

    def profile(chosen: np.ndarray) -> None:
        cells = np.argwhere(chosen)
        if not len(cells):
            return
        values = np.asarray(measure(cells), dtype=float)
        if values.shape != (len(cells), atlas.Yc.shape[2]) or not np.isfinite(values).all():
            raise ValueError("measure() must return one finite response per profiled cell")
        atlas.Yc[library[cells[:, 0]], cells[:, 1]] = values - atlas.mu[cells[:, 1]]
        profiled[:] |= chosen
        batches.append([tuple(map(int, c)) for c in cells])

    if spec.planner == "sparse_transfer":
        profile(sparse_transfer_design(grid, kappa, spec.budget_wells, seed=seed))
    else:
        batch = int(math.ceil(spec.budget_wells / spec.rounds)) if spec.budget_wells else 0
        for r in range(spec.rounds):
            k = min(batch, spec.budget_wells - int(profiled.sum()), int((grid & ~profiled).sum()))
            if k <= 0:
                break
            st = _certify(atlas, certifier, library, grid, profiled, static)
            profile(plan_batch(st["p"], st["ecos"], st["rho"], grid & ~profiled, kappa, atlas.gamma, k,
                               seed=seed + r))
    st = _certify(atlas, certifier, library, grid, profiled, static)
    return ProfilingReport(profiled, st["dir"], st["p"], st["ecos"], st["refusal"], batches)
