"""Protocol library: what each candidate action would cost, need and stop on.

File summary
- Path: research/scientific_case_memory/protocol_library.py
- Purpose: turn a study's condition keys into costed, controlled, prerequisite-aware action
  specifications, in laboratory units: assay wells and turnaround days, shared controls counted
  once. API calls and model spend are never part of an action's cost.
- Core points:
  - A condition key is (cell line, time in hours, dose in nM). Its cost is `days_of(key)` and two
    wells; the first use of a (cell line, time) group adds four vehicle wells, so a second dose of
    the same group is cheaper than a new group. `plan_cost` reproduces the runner's own `wells` sum.
  - Detection power is the fraction of training references detected at the condition, estimated
    from training data only and reported as `None` when fewer than `MIN_REFERENCES` were measured,
    so a thin estimate is never presented as a power.
  - Ordering is explicit: the runner never offers a time earlier than one already executed, so the
    library states no prerequisite measurement for these actions. An action whose planned conditions the design never ran is `available=False`
    rather than absent, so a report can say why it was not offered.
  - Every template names its control (matched vehicle wells for the same cell line and time), its
    replicate design, a stopping condition and the readouts that would change the plan.
- Interfaces: `MIN_REFERENCES`, `ProtocolTemplate`, `build_protocol_library`, `plan_cost`
- Depends on: case_schema.py
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from . import case_schema as S

MIN_REFERENCES = 8
"""Fewest training references at a condition before a detection rate may be called a power."""


def action_id(key: Sequence) -> str:
    """The repository's condition identifier (`dynamic_world_model.common.action_id`), e.g. A549|024h|10000nM."""
    line, t, dose = key
    return f"{line}|{int(t):03d}h|{int(dose):05d}nM"


@dataclass(frozen=True)
class ProtocolTemplate:
    action_id: str
    key: tuple
    assay: str
    readout: str
    cost_wells: float
    duration_days: float
    controls: tuple[str, ...]
    replicate_design: str
    detection_power: float | None
    references_measured: int
    prerequisites: tuple[str, ...]
    stopping_condition: str
    available: bool = True

    def to_action_spec(self) -> S.ActionSpec:
        line, t, dose = self.key
        return S.ActionSpec(self.action_id, f"{self.assay}, {line}, {dose:g} nM, {t:g} h", self.assay, self.cost_wells,
                            self.duration_days, self.readout, line, float(t), float(dose), self.prerequisites,
                            self.controls, self.detection_power, self.available)


def plan_cost(keys: Sequence[Sequence], days_of: Callable[[Sequence], float]) -> tuple[float, int]:
    """(assay days, wells) of executing `keys`: two wells each, four vehicle wells per new (line, time)."""
    seen, wells = set(), 0
    for k in keys:
        wells += 2
        if (k[0], k[1]) not in seen:
            seen.add((k[0], k[1]))
            wells += 4
    return float(sum(days_of(k) for k in keys)), wells


def build_protocol_library(keys: Sequence[Sequence], days_of: Callable[[Sequence], float], *, assay: str,
                           readout: str = "transcriptome_shift",
                           detected_at: Mapping[tuple, tuple[int, int]] | None = None,
                           planned: Sequence[Sequence] | None = None) -> tuple[ProtocolTemplate, ...]:
    """One template per key. `detected_at[key]` is (references detected, references measured), training only."""
    out: list[ProtocolTemplate] = []
    planned_set = {tuple(k) for k in planned} if planned is not None else {tuple(k) for k in keys}
    for key in keys:
        key = tuple(key)
        detected, measured = (detected_at or {}).get(key, (0, 0))
        power = detected / measured if measured >= MIN_REFERENCES else None
        out.append(ProtocolTemplate(
            action_id=action_id(key), key=key, assay=assay, readout=readout, cost_wells=2.0,
            duration_days=float(days_of(key)),
            controls=(f"vehicle wells matched to {key[0]} at {key[1]:g} h (four wells, shared by every dose of the group)",),
            replicate_design="two replicate groups; a group under the minimum cell or well count fails QC",
            detection_power=power, references_measured=int(measured),
            prerequisites=(), stopping_condition=("stop at the first qualified elimination; a QC failure or an "
                                                  "undetected or ambiguous reading continues if budget remains"),
            available=key in planned_set))
    return tuple(out)
