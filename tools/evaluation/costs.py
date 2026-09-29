"""Evaluation costs: consolidated module responsibilities."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


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


# Verified on 2026-09-12 against the provider's published pricing and recorded in the campaign
# ledger of that day; US dollars per million tokens.
RATES: Mapping[str, object] = {
    "model": "deepseek-flash",
    "input_cache_miss": 0.3,
    "input_cache_hit": 0.006,
    "output": 1.2,
    "verified_on": "2026-09-12",
    "source": "https://api-docs.deepseek.com/quick_start/pricing",
}


def price_usage(usage: Mapping[str, object]) -> float:
    """Price one call from the provider's own usage fields, in US dollars."""

    def value(name: str, fallback: int = 0) -> int:
        raw = usage.get(name, fallback)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)) or raw < 0:
            return fallback
        return int(raw)

    miss = value("prompt_cache_miss_tokens", value("prompt_tokens"))
    hit = value("prompt_cache_hit_tokens")
    output = value("completion_tokens")
    return (
        miss * float(RATES["input_cache_miss"])
        + hit * float(RATES["input_cache_hit"])
        + output * float(RATES["output"])
    ) / 1_000_000


@dataclass(frozen=True)
class SpendEntry:
    """One provider call: what it was for, what it cost, and whether it returned."""

    at: str
    label: str
    status: str
    reserved_usd: float
    charged_usd: float
    usage: Mapping[str, object]
    note: str = ""

    def payload(self) -> Mapping[str, object]:
        return {
            "at": self.at,
            "label": self.label,
            "status": self.status,
            "reserved_usd": round(self.reserved_usd, 8),
            "charged_usd": round(self.charged_usd, 8),
            "usage": dict(self.usage),
            "note": self.note,
        }


@dataclass
class SpendLedger:
    """An append-only priced ledger for one run, with a declared prior total and a ceiling."""

    path: Path
    ceiling_usd: float = 5.0
    prior_total_usd: float = 0.0
    prior_note: str = ""
    entries: list[SpendEntry] = field(default_factory=list)

    @property
    def session_total_usd(self) -> float:
        return sum(entry.charged_usd for entry in self.entries)

    @property
    def total_usd(self) -> float:
        return self.prior_total_usd + self.session_total_usd

    @property
    def remaining_usd(self) -> float:
        return self.ceiling_usd - self.total_usd

    def reserve(self, label: str, estimate_usd: float) -> None:
        """Refuse by name before a call that would exceed the declared ceiling."""

        if self.total_usd + estimate_usd > self.ceiling_usd:
            raise ValueError(
                "provider_ceiling_exceeded:"
                f"{label}:total={self.total_usd:.6f}+estimate={estimate_usd:.6f}>ceiling={self.ceiling_usd:.2f}"
            )

    def charge(
        self,
        label: str,
        usage: Mapping[str, object] | None,
        *,
        status: str = "ok",
        reserved_usd: float = 0.0,
        note: str = "",
    ) -> SpendEntry:
        """Record one call. A failure after token processing is charged at its reservation."""

        charged = price_usage(usage) if usage else (reserved_usd if status != "refused" else 0.0)
        entry = SpendEntry(
            at=datetime.now(timezone.utc).isoformat(),
            label=label,
            status=status,
            reserved_usd=reserved_usd,
            charged_usd=charged,
            usage=dict(usage or {}),
            note=note,
        )
        self.entries.append(entry)
        return entry

    def payload(self) -> Mapping[str, object]:
        return {
            "rates": dict(RATES),
            "ceiling_usd": self.ceiling_usd,
            "prior_total_usd": round(self.prior_total_usd, 8),
            "prior_note": self.prior_note,
            "session_total_usd": round(self.session_total_usd, 8),
            "total_usd": round(self.total_usd, 8),
            "remaining_usd": round(self.remaining_usd, 8),
            "calls": len(self.entries),
            "entries": [entry.payload() for entry in self.entries],
        }

    def write(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return self.path

    @classmethod
    def load(cls, path: Path, *, ceiling_usd: float = 5.0, prior_total_usd: float = 0.0, prior_note: str = "") -> "SpendLedger":
        """Continue an existing ledger, or start one with a declared prior total."""

        if Path(path).is_file():
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            ledger = cls(
                path=Path(path),
                ceiling_usd=float(payload.get("ceiling_usd", ceiling_usd)),
                prior_total_usd=float(payload.get("prior_total_usd", prior_total_usd)),
                prior_note=str(payload.get("prior_note", prior_note)),
            )
            for entry in payload.get("entries", ()):
                ledger.entries.append(
                    SpendEntry(
                        at=str(entry.get("at", "")),
                        label=str(entry.get("label", "")),
                        status=str(entry.get("status", "ok")),
                        reserved_usd=float(entry.get("reserved_usd", 0.0)),
                        charged_usd=float(entry.get("charged_usd", 0.0)),
                        usage=dict(entry.get("usage", {})),
                        note=str(entry.get("note", "")),
                    )
                )
            return ledger
        return cls(path=Path(path), ceiling_usd=ceiling_usd, prior_total_usd=prior_total_usd, prior_note=prior_note)


def summarise(ledgers: Sequence[SpendLedger]) -> Mapping[str, object]:
    """Totals across several ledgers, for a record that reports one campaign figure."""

    return {
        "ledgers": len(ledgers),
        "calls": sum(len(ledger.entries) for ledger in ledgers),
        "session_total_usd": round(sum(ledger.session_total_usd for ledger in ledgers), 8),
        "total_usd": round(max((ledger.total_usd for ledger in ledgers), default=0.0), 8),
    }


@dataclass
class TrackingCompleter:
    """Record model and usage metadata without retaining prompts, outputs, or credentials."""

    client: Any
    calls: list[dict[str, Any]] = field(default_factory=list)

    def complete_json(self, messages, **kwargs):
        data, response = self.client.complete_json(messages, **kwargs)
        self.calls.append({
            "model": response.model,
            "finish_reason": response.finish_reason,
            "usage": dict(response.usage),
        })
        return data, response
