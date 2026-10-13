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

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from agent.case_store import CaseStore, MeasurementResult
from maestro.models import EvidenceAction, EvidenceActionKind, EvidenceKind
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


@dataclass(frozen=True)
class ProfilingPersistence:
    """Opt-in CaseStore binding for a named campaign and ordered axes.

    ``model_version`` must be an immutable identity for the certifier assets; those
    estimator internals are not introspected here. Array callbacks persist only as
    retrieved-source evidence, since shape and finiteness do not attest assay QC.
    """

    store: CaseStore
    case_id: str
    campaign_id: str
    model_version: str
    source_id: str
    reference_id: str
    assay: str
    dose: str
    time: str
    endpoint: str
    compound_ids: tuple[str, ...]
    line_ids: tuple[str, ...]
    gene_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("case_id", "campaign_id", "model_version", "source_id", "reference_id",
                     "assay", "dose", "time", "endpoint"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"profiling_{name}_must_be_canonical_nonempty_text")
        for name in ("compound_ids", "line_ids", "gene_ids"):
            values = tuple(getattr(self, name))
            if not values or any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"profiling_{name}_required")
            if len(set(values)) != len(values):
                raise ValueError(f"profiling_{name}_must_be_unique")
            object.__setattr__(self, name, values)


def _model_planning_digest(atlas: kt.TransferAtlas, library: np.ndarray, kappa: np.ndarray) -> str:
    digest = hashlib.sha256()
    arrays = [atlas.ref, atlas.Yc[atlas.ref], atlas.mu, atlas.fps[atlas.ref], atlas.know[atlas.ref], atlas.thr,
              atlas.fps[library], atlas.know[library], atlas.G, np.asarray([atlas.gamma]), kappa]
    for key in sorted(atlas.maps):
        model = atlas.maps[key]
        arrays.extend((np.asarray(key), model.B, np.asarray([model.lam, model.loo_cosine, model.n])))
    for values in arrays:
        array = np.ascontiguousarray(values)
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.dtype.str.encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()


def _campaign_scope(atlas: kt.TransferAtlas, library: np.ndarray, grid: np.ndarray, spec: ProfilingSpec,
                    seed: int, kappa: np.ndarray, persistence: ProfilingPersistence) -> str:
    if (len(persistence.compound_ids) != len(library)
            or len(persistence.line_ids) != atlas.Yc.shape[1]
            or len(persistence.gene_ids) != atlas.Yc.shape[2]):
        raise ValueError("PERSISTENT_CAMPAIGN_AXIS_MISMATCH")
    payload = {
        "campaign_id": persistence.campaign_id,
        "case_id": persistence.case_id,
        "model_version": persistence.model_version,
        "source_id": persistence.source_id,
        "reference_id": persistence.reference_id,
        "assay": persistence.assay,
        "dose": persistence.dose,
        "time": persistence.time,
        "model_planning_sha256": _model_planning_digest(atlas, library, kappa),
        "endpoint": persistence.endpoint,
        "compound_ids": persistence.compound_ids,
        "line_ids": persistence.line_ids,
        "gene_ids": persistence.gene_ids,
        "library_rows": [int(row) for row in library],
        "grid_sha256": hashlib.sha256(np.ascontiguousarray(grid, dtype=np.uint8).tobytes()).hexdigest(),
        "seed": seed,
        "spec": {"budget_wells": spec.budget_wells, "planner": spec.planner, "rounds": spec.rounds},
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _cell_action(scope: str, row: int, line: int, persistence: ProfilingPersistence) -> EvidenceAction:
    conditions = {
        "campaign_scope": scope,
        "campaign_id": persistence.campaign_id,
        "model_version": persistence.model_version,
        "source_id": persistence.source_id,
        "reference_id": persistence.reference_id,
        "assay": persistence.assay,
        "dose": persistence.dose,
        "time": persistence.time,
        "endpoint": persistence.endpoint,
        "compound_id": persistence.compound_ids[row],
        "line_id": persistence.line_ids[line],
        "gene_axis_sha256": hashlib.sha256("\n".join(persistence.gene_ids).encode("utf-8")).hexdigest(),
    }
    return EvidenceAction(
        identifier=f"profile:{scope}:{row}:{line}", description=f"Profile {persistence.compound_ids[row]} in {persistence.line_ids[line]}",
        cost=1.0, distinguishes=(), kind=EvidenceActionKind.EVIDENCE_REVIEW,
        readout=persistence.endpoint, expected_conditions=conditions,
        execution_context=persistence.line_ids[line],
    )


def _restore_persisted(atlas: kt.TransferAtlas, library: np.ndarray, grid: np.ndarray,
                       spec: ProfilingSpec, persistence: ProfilingPersistence,
                       scope: str) -> tuple[np.ndarray, list]:
    store = persistence.store
    store.open_case(persistence.case_id, budget=float(spec.budget_wells))
    actions = {(row, line): _cell_action(scope, row, line, persistence)
               for row, line in map(tuple, np.argwhere(grid))}
    by_identifier = {action.identifier: (cell, action) for cell, action in actions.items()}
    restored: dict[tuple[int, int], np.ndarray] = {}
    batches_by_version: dict[int, list[tuple[int, int]]] = {}
    identities = store.result_identities(persistence.case_id)
    for identity in identities:
        action_id = identity["action_identifier"]
        found = by_identifier.get(action_id)
        if found is None:
            raise ValueError("PERSISTENT_CAMPAIGN_IDENTITY_MISMATCH")
        (row, line), action = found
        result = store.measurement(persistence.case_id, identity["result_id"])
        if (not result.quality_passed or result.source_id != persistence.source_id
                or result.context_identifier != persistence.line_ids[line]
                or result.evidence_kind is not EvidenceKind.RETRIEVED_SOURCE
                or dict(result.conditions) != dict(action.expected_conditions)):
            raise ValueError("PERSISTENT_CAMPAIGN_INVALID_RESULT_RECEIPT")
        try:
            vector = np.asarray(json.loads(result.metrics["response_vector"]), dtype=float)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("PERSISTENT_CAMPAIGN_INVALID_RESULT_RECEIPT") from error
        if vector.shape != (atlas.Yc.shape[2],) or not np.isfinite(vector).all() or (row, line) in restored:
            raise ValueError("PERSISTENT_CAMPAIGN_INVALID_RESULT_RECEIPT")
        restored[(row, line)] = vector
        batches_by_version.setdefault(identity["plan_version"], []).append((row, line))

    pending = store.pending_actions(persistence.case_id)
    if pending:
        if any(not item["action_identifier"].startswith(f"profile:{scope}:") for item in pending):
            raise ValueError("PERSISTENT_CAMPAIGN_IDENTITY_MISMATCH")
        raise ValueError("PERSISTENT_CAMPAIGN_PENDING_RECEIPT_RECOVERY_REQUIRED")

    profiled = np.zeros_like(grid)
    for (row, line), vector in restored.items():
        atlas.Yc[library[row], line] = vector - atlas.mu[line]
        profiled[row, line] = True
    batches = [batches_by_version[version] for version in sorted(batches_by_version)]
    return profiled, batches


def _profile_persisted(atlas: kt.TransferAtlas, library: np.ndarray, chosen: np.ndarray,
                       measure: Callable[[np.ndarray], np.ndarray], persistence: ProfilingPersistence,
                       scope: str, profiled: np.ndarray) -> list[tuple[int, int]]:
    cells = [tuple(map(int, cell)) for cell in np.argwhere(chosen)]
    if not cells:
        return []
    actions = tuple(_cell_action(scope, row, line, persistence) for row, line in cells)
    snapshot = persistence.store.record_plan(persistence.case_id, actions, ready_to_measure=True,
                                             context_identifier=None)
    if snapshot.state.value != "awaiting_result":
        raise ValueError("PERSISTENT_CAMPAIGN_BUDGET_REFUSED")
    for action in actions:
        persistence.store.start_action(persistence.case_id, snapshot.plan_version, action.identifier,
                                       attempt_id=f"attempt:{action.identifier}", source=persistence.source_id)
    values = np.asarray(measure(np.asarray(cells, dtype=int)), dtype=float)
    if values.shape != (len(cells), atlas.Yc.shape[2]) or not np.isfinite(values).all():
        raise ValueError("measure() must return one finite response per profiled cell")
    for (row, line), action, vector in zip(cells, actions, values):
        result = MeasurementResult(
            action_identifier=action.identifier,
            statement="Finite response vector received; external assay QC is not attested by this adapter.",
            source_id=persistence.source_id,
            context_identifier=persistence.line_ids[line],
            time_hours=None,
            independent_units=None,
            quality_passed=True,
            conditions=dict(action.expected_conditions),
            metrics={"response_vector": json.dumps(vector.tolist(), allow_nan=False, separators=(",", ":"))},
            limitations=("Adapter checked response shape and finiteness only; external assay QC is not attested.",),
            evidence_kind=EvidenceKind.RETRIEVED_SOURCE,
        )
        persistence.store.import_measurement(persistence.case_id, result)
    for (row, line), vector in zip(cells, values):
        atlas.Yc[library[row], line] = vector - atlas.mu[line]
        profiled[row, line] = True
    return cells


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
                  seed: int = 0, persistence: ProfilingPersistence | None = None) -> ProfilingReport:
    """Run one campaign over ``library``, the atlas rows of unprofiled compounds.

    ``grid`` marks the cells of the library that can be profiled.

    ``measure(cells)`` takes an array of (library index, line) pairs and returns their raw responses
    (cells x genes). The library rows of the atlas are overwritten with what is measured, so the
    caller passes an atlas whose library rows hold no response (NaN).

    ``persistence`` is opt-in. It stores callback vectors as retrieved-source records, binds them
    to the campaign scope, and restores only exact accepted receipts. An unfinished action raises
    ``PERSISTENT_CAMPAIGN_PENDING_RECEIPT_RECOVERY_REQUIRED``; import its external receipt through
    CaseStore before resuming. The adapter does not attest assay QC or independent biological units.
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
    scope = _campaign_scope(atlas, library, grid, spec, seed, kappa, persistence) if persistence is not None else None
    if persistence is not None:
        profiled, batches = _restore_persisted(atlas, library, grid, spec, persistence, scope)

    def profile(chosen: np.ndarray) -> None:
        cells = np.argwhere(chosen)
        if not len(cells):
            return
        if persistence is not None:
            batch = _profile_persisted(atlas, library, chosen, measure, persistence, scope, profiled)
            if batch:
                batches.append(batch)
            return
        values = np.asarray(measure(cells), dtype=float)
        if values.shape != (len(cells), atlas.Yc.shape[2]) or not np.isfinite(values).all():
            raise ValueError("measure() must return one finite response per profiled cell")
        atlas.Yc[library[cells[:, 0]], cells[:, 1]] = values - atlas.mu[cells[:, 1]]
        profiled[:] |= chosen
        batches.append([tuple(map(int, c)) for c in cells])

    if spec.planner == "sparse_transfer":
        if persistence is None:
            profile(sparse_transfer_design(grid, kappa, spec.budget_wells, seed=seed))
        elif not batches:
            remaining = persistence.store.budget_status(persistence.case_id)["uncommitted"]
            profile(sparse_transfer_design(grid & ~profiled, kappa, int(remaining), seed=seed))
    else:
        batch = int(math.ceil(spec.budget_wells / spec.rounds)) if spec.budget_wells else 0
        completed_rounds = len(batches) if persistence is not None else 0
        for r in range(completed_rounds, spec.rounds):
            remaining = (int(persistence.store.budget_status(persistence.case_id)["uncommitted"])
                         if persistence is not None
                         else spec.budget_wells - int(profiled.sum()))
            k = min(batch, remaining, int((grid & ~profiled).sum()))
            if k <= 0:
                break
            st = _certify(atlas, certifier, library, grid, profiled, static)
            profile(plan_batch(st["p"], st["ecos"], st["rho"], grid & ~profiled, kappa, atlas.gamma, k,
                               seed=seed + r))
    st = _certify(atlas, certifier, library, grid, profiled, static)
    return ProfilingReport(profiled, st["dir"], st["p"], st["ecos"], st["refusal"], batches)
