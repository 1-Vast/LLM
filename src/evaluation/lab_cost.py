"""Laboratory-unit cost: assay wells and turnaround days, with shared controls charged once.

File summary
- Path: src/evaluation/lab_cost.py
- Purpose: make the report's cost rule executable (sections 26, 36 and 55, condition 3).
  An action is priced in wells and turnaround days, so a comparison priced in abstract
  units or in tool calls is visibly not a laboratory-cost comparison.
- Core points:
  - Two bases, declared rather than inferred: a new measurement consumes wells and days;
    a retrieval of an already released record consumes neither, and says so.
  - A shared control is charged once per executed sequence, however many assays use it.
  - An executed action with no declaration makes the whole sequence undeclared. It is
    refused by name (`lab_cost_undeclared`) and never priced at zero.
  - Model calls, API spend and compute are not laboratory cost and never enter these
    totals; the evaluation report keeps them separately.
- Interfaces: `CostBasis`, `LabCost`, `SharedControl`, `CostingProfile`, `SequenceLabCost`,
  `TURNAROUND_CONVENTION`, `sequence_lab_cost`, `lab_cost_from_payload`,
  `shared_control_from_payload`, `load_costing_profile`
- Depends on: (standard library only)
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

COSTING_SCHEMA = "maestro.costing.v1"

# Replay reveals one result per step, so elapsed time is the sum of the executed actions'
# turnaround. A shared control runs beside the first assay that needs it, so its wells are
# charged and its time is not added a second time.
TURNAROUND_CONVENTION = "sequential_sum_of_action_turnaround"


class CostBasis(str, Enum):
    """What executing an action consumes in the laboratory."""

    NEW_MEASUREMENT = "new_measurement"
    RECORD_RETRIEVAL = "record_retrieval"


@dataclass(frozen=True)
class LabCost:
    """The laboratory price of one registered action.

    ``shared_control`` names a control group whose wells are charged once per executed
    sequence. ``source`` says who declared the price and from what: a declared price is a
    modelling input, not a measurement of any laboratory's costs.
    """

    basis: CostBasis
    wells: int
    turnaround_days: float
    shared_control: str | None = None
    reagent_burden: str | None = None
    source: str = ""

    def __post_init__(self) -> None:
        if self.wells < 0 or self.turnaround_days < 0:
            raise ValueError("lab_cost_negative: wells and turnaround days cannot be negative.")
        if self.basis is CostBasis.RECORD_RETRIEVAL and (
            self.wells or self.turnaround_days or self.shared_control
        ):
            raise ValueError(
                "lab_cost_retrieval_consumes_resources: a released-record retrieval uses no wells, "
                "no turnaround and no control; declare it as a new measurement if it does."
            )
        if self.basis is CostBasis.NEW_MEASUREMENT and self.wells <= 0:
            raise ValueError(
                "lab_cost_measurement_without_wells: a new measurement must consume at least one well."
            )

    def price_key(self) -> tuple[str, int, float, str | None]:
        """The fields that make two declarations the same price, ignoring provenance text."""

        return (self.basis.value, self.wells, float(self.turnaround_days), self.shared_control)

    def to_payload(self) -> Mapping[str, object]:
        return {
            "basis": self.basis.value,
            "wells": self.wells,
            "turnaround_days": self.turnaround_days,
            "shared_control": self.shared_control,
            "reagent_burden": self.reagent_burden,
        }


@dataclass(frozen=True)
class SharedControl:
    """A control group several assays may share, charged once when any of them runs."""

    identifier: str
    wells: int
    turnaround_days: float = 0.0
    source: str = ""

    def __post_init__(self) -> None:
        if self.wells <= 0 or self.turnaround_days < 0:
            raise ValueError(
                f"shared_control_invalid:{self.identifier}: a control uses at least one well and "
                "cannot take negative time."
            )


@dataclass(frozen=True)
class CostingProfile:
    """Declared laboratory prices for a case package, kept apart from the frozen case files."""

    identifier: str
    source: str
    actions: Mapping[str, LabCost] = field(default_factory=dict)
    shared_controls: Mapping[str, SharedControl] = field(default_factory=dict)
    sha256: str | None = None

    def __post_init__(self) -> None:
        for name, price in self.actions.items():
            if price.shared_control is not None and price.shared_control not in self.shared_controls:
                raise ValueError(f"costing_shared_control_undeclared:{name}:{price.shared_control}")


@dataclass(frozen=True)
class SequenceLabCost:
    """What one executed sequence consumed in laboratory units, or why that is unknown."""

    declared: bool
    wells: int | None
    turnaround_days: float | None
    assay_wells: int
    control_wells: int
    shared_controls_charged: tuple[str, ...]
    new_measurements: int
    record_retrievals: int
    undeclared_actions: tuple[str, ...] = ()
    refusal: str | None = None
    turnaround_convention: str = TURNAROUND_CONVENTION


def sequence_lab_cost(
    prices: Mapping[str, LabCost | None],
    shared_controls: Mapping[str, SharedControl],
    sequence: Iterable[str],
) -> SequenceLabCost:
    """Price an executed sequence, refusing by name when any executed action is unpriced.

    An empty sequence is a true zero: nothing ran. An unpriced action is not a zero, so the
    partial totals are kept for diagnosis while ``wells`` and ``turnaround_days`` stay None.
    """

    executed = tuple(dict.fromkeys(sequence))
    priced = [(name, prices.get(name)) for name in executed]
    undeclared = tuple(name for name, price in priced if price is None)
    known = [price for _, price in priced if price is not None]
    groups = tuple(sorted({price.shared_control for price in known if price.shared_control}))
    missing_groups = tuple(name for name in groups if name not in shared_controls)
    if missing_groups:
        raise ValueError("costing_shared_control_undeclared:" + ",".join(missing_groups))
    assay_wells = sum(price.wells for price in known)
    control_wells = sum(shared_controls[name].wells for name in groups)
    days = float(sum(price.turnaround_days for price in known))
    new = sum(1 for price in known if price.basis is CostBasis.NEW_MEASUREMENT)
    retrieved = sum(1 for price in known if price.basis is CostBasis.RECORD_RETRIEVAL)
    if undeclared:
        return SequenceLabCost(
            declared=False,
            wells=None,
            turnaround_days=None,
            assay_wells=assay_wells,
            control_wells=control_wells,
            shared_controls_charged=groups,
            new_measurements=new,
            record_retrievals=retrieved,
            undeclared_actions=undeclared,
            refusal="lab_cost_undeclared:" + ",".join(undeclared),
        )
    return SequenceLabCost(
        declared=True,
        wells=assay_wells + control_wells,
        turnaround_days=days,
        assay_wells=assay_wells,
        control_wells=control_wells,
        shared_controls_charged=groups,
        new_measurements=new,
        record_retrievals=retrieved,
    )


def lab_cost_from_payload(data: Any, *, where: str) -> LabCost:
    """Read one declared price; a malformed declaration is refused, never defaulted."""

    if not isinstance(data, dict):
        raise ValueError(f"lab_cost_malformed:{where}: a price must be an object.")
    try:
        basis = CostBasis(data["basis"])
    except (KeyError, ValueError) as error:
        raise ValueError(f"lab_cost_malformed:{where}: 'basis' must be one of {[b.value for b in CostBasis]}.") from error
    wells = data.get("wells")
    days = data.get("turnaround_days")
    if isinstance(wells, bool) or not isinstance(wells, int):
        raise ValueError(f"lab_cost_malformed:{where}: 'wells' must be an integer.")
    if isinstance(days, bool) or not isinstance(days, (int, float)):
        raise ValueError(f"lab_cost_malformed:{where}: 'turnaround_days' must be a number.")
    control = data.get("shared_control")
    burden = data.get("reagent_burden")
    return LabCost(
        basis=basis,
        wells=wells,
        turnaround_days=float(days),
        shared_control=str(control) if isinstance(control, str) and control.strip() else None,
        reagent_burden=str(burden) if isinstance(burden, str) and burden.strip() else None,
        source=str(data.get("source", "")),
    )


def shared_control_from_payload(identifier: str, data: Any, *, where: str) -> SharedControl:
    if not isinstance(data, dict):
        raise ValueError(f"shared_control_malformed:{where}: a shared control must be an object.")
    wells = data.get("wells")
    days = data.get("turnaround_days", 0.0)
    if isinstance(wells, bool) or not isinstance(wells, int):
        raise ValueError(f"shared_control_malformed:{where}: 'wells' must be an integer.")
    if isinstance(days, bool) or not isinstance(days, (int, float)):
        raise ValueError(f"shared_control_malformed:{where}: 'turnaround_days' must be a number.")
    return SharedControl(identifier=identifier, wells=wells, turnaround_days=float(days), source=str(data.get("source", "")))


def load_costing_profile(path: Path | str) -> CostingProfile:
    """Load a costing overlay and record its digest, so a run names the prices it used."""

    raw = Path(path).read_bytes()
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict) or data.get("schema") != COSTING_SCHEMA:
        raise ValueError(f"costing_schema_unsupported: expected schema '{COSTING_SCHEMA}'.")
    identifier = data.get("identifier")
    source = data.get("source")
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("costing_malformed: 'identifier' must be nonempty text.")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("costing_malformed: 'source' must say where the prices come from.")
    actions = data.get("actions", {})
    controls = data.get("shared_controls", {})
    if not isinstance(actions, dict) or not isinstance(controls, dict):
        raise ValueError("costing_malformed: 'actions' and 'shared_controls' must be objects.")
    return CostingProfile(
        identifier=identifier.strip(),
        source=source.strip(),
        actions={str(name): lab_cost_from_payload(value, where=str(name)) for name, value in actions.items()},
        shared_controls={
            str(name): shared_control_from_payload(str(name), value, where=str(name))
            for name, value in controls.items()
        },
        sha256=hashlib.sha256(raw).hexdigest(),
    )
