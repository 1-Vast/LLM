"""Selective hit-triage contracts: compound identity, assay-context binding, QC admission, budgets and the outcome seal.

File summary
- Path: src/maestro/hit_triage.py
- Purpose: the engineering contracts a phenotypic hit-triage campaign needs before any scoring rule
  is trusted. These contracts are not a scoring rule. The rules themselves stay in
  `research/selective_hit_triage_20261013` until independent confirmation.
- Core points:
  - `CompoundIdentity`: one compound is one Broad core id (BRD-X + 8 digits). Two records are the
    same compound if they share the core, or the InChIKey connectivity block when both have one.
    Salt forms therefore collapse, and a mismatched id is refused (`MALFORMED_IDENTITY`).
  - `AssayContext` names platform, readout, duration, dose count and cell format. A
    `PairMeasurement` is bound to one context, and `bind` refuses it in another
    (`CONTEXT_MISMATCH`), so a 5-day pooled screen value can never stand in for a 72 h arrayed
    confirmation.
  - `admit_curves` admits a compound's confirmation curves only above a line count; otherwise the
    status is `QC_FAILED` with `INSUFFICIENT_LINES`. Status values are the six-state
    `ScientificMeasurementStatus`, never a silent zero.
  - `TriageLedger` books confirmation curves, follow-up dose-responses and turnarounds against
    `CampaignBudget`s before execution (`BUDGET_EXCEEDED`).
  - `nominate` is order-invariant: ties break by a salted hash of (compound, line), never by input
    order, and there is a cap per compound.
  - `OutcomeSeal` releases sealed outcomes only after the freeze digests match and the choices are
    locked by digest (`FREEZE_MISMATCH`, `CHOICES_NOT_LOCKED`, `CHOICES_MISMATCH`).
    `assert_disjoint` refuses a split that shares a compound, connectivity block or family
    (`SPLIT_LEAK`).
- Interfaces: `CompoundIdentity`, `AssayContext`, `PairMeasurement`, `bind`, `admit_curves`, `TriageLedger`,
  `nominate`, `OutcomeSeal`, `assert_disjoint`.
- Depends on: maestro.campaign_budget, maestro.case_memory.
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from maestro.campaign_budget import CampaignBudget
from maestro.case_memory import ScientificMeasurementStatus

MALFORMED_IDENTITY, CONTEXT_MISMATCH, INSUFFICIENT_LINES = "MALFORMED_IDENTITY", "CONTEXT_MISMATCH", "INSUFFICIENT_LINES"
BUDGET_EXCEEDED, SPLIT_LEAK = "BUDGET_EXCEEDED", "SPLIT_LEAK"
FREEZE_MISMATCH, CHOICES_NOT_LOCKED, CHOICES_MISMATCH = "FREEZE_MISMATCH", "CHOICES_NOT_LOCKED", "CHOICES_MISMATCH"
_CORE = re.compile(r"^BRD-[A-Z]\d{8}$")
_CONNECTIVITY = re.compile(r"^[A-Z]{14}$")
_LINE = re.compile(r"^(ACH-\d{6}|[A-Z]+:\d+)$")


@dataclass(frozen=True)
class CompoundIdentity:
    core: str
    connectivity: str | None = None
    name: str = ""

    def __post_init__(self) -> None:
        if not _CORE.match(self.core) or (self.connectivity is not None and not _CONNECTIVITY.match(self.connectivity)):
            raise ValueError(MALFORMED_IDENTITY)

    @classmethod
    def from_broad_id(cls, broad_id: str, connectivity: str | None = None, name: str = "") -> "CompoundIdentity":
        return cls(str(broad_id).strip()[:13], connectivity, name)

    def same_compound(self, other: "CompoundIdentity") -> bool:
        return self.core == other.core or (self.connectivity is not None and self.connectivity == other.connectivity)


@dataclass(frozen=True)
class AssayContext:
    platform: str
    readout: str
    duration_hours: float
    doses: int
    cell_format: str
    source_sha256: str

    def __post_init__(self) -> None:
        if not (self.platform.strip() and self.readout.strip() and self.cell_format.strip()):
            raise ValueError("assay context needs platform, readout and cell format")
        if not (math.isfinite(self.duration_hours) and self.duration_hours > 0) or type(self.doses) is not int or self.doses < 1:
            raise ValueError("assay context needs a positive duration and dose count")
        if len(self.source_sha256) != 64:
            raise ValueError("assay context needs its source digest")

    @property
    def identifier(self) -> str:
        return f"{self.platform}:{self.readout}:{self.duration_hours:g}h:{self.doses}dose:{self.cell_format}"


@dataclass(frozen=True)
class PairMeasurement:
    compound: CompoundIdentity
    line: str
    context: AssayContext
    value: float
    status: ScientificMeasurementStatus
    experiments: int = 1

    def __post_init__(self) -> None:
        if not _LINE.match(self.line):
            raise ValueError(MALFORMED_IDENTITY)
        if self.status in (ScientificMeasurementStatus.QUALIFIED, ScientificMeasurementStatus.UNDETECTED) and not math.isfinite(self.value):
            raise ValueError("a qualified measurement needs a finite value")
        if type(self.experiments) is not int or self.experiments < 0:
            raise ValueError("experiment count must be a nonnegative integer")


def bind(measurement: PairMeasurement, context: AssayContext) -> PairMeasurement:
    """Return the measurement for use in ``context``, or refuse a value from another assay context."""

    if measurement.context.identifier != context.identifier or measurement.context.source_sha256 != context.source_sha256:
        raise ValueError(f"{CONTEXT_MISMATCH}:{measurement.context.identifier}->{context.identifier}")
    return measurement


def admit_curves(lines_with_curves: int, minimum: int) -> tuple[ScientificMeasurementStatus, str | None]:
    if type(lines_with_curves) is not int or lines_with_curves < 0 or type(minimum) is not int or minimum < 1:
        raise ValueError("line counts must be integers")
    if lines_with_curves == 0:
        return ScientificMeasurementStatus.PLANNED_MISSING, INSUFFICIENT_LINES
    if lines_with_curves < minimum:
        return ScientificMeasurementStatus.QC_FAILED, INSUFFICIENT_LINES
    return ScientificMeasurementStatus.QUALIFIED, None


@dataclass
class TriageLedger:
    """Separate budgets for confirmation curves and follow-up dose-responses, shared by every compared arm."""

    confirmation: CampaignBudget
    followup: CampaignBudget
    curves: int = 0
    followups: int = 0
    turnarounds: int = 0
    entries: list = field(default_factory=list)

    def book(self, *, curves: int = 0, followups: int = 0, turnarounds: int = 0, label: str = "") -> None:
        try:
            self.confirmation.require_feasible(self.curves + curves, self.turnarounds + turnarounds)
            self.followup.require_feasible(self.followups + followups, self.turnarounds + turnarounds)
        except ValueError as error:
            raise ValueError(f"{BUDGET_EXCEEDED}:{label}") from error
        self.curves, self.followups, self.turnarounds = self.curves + curves, self.followups + followups, self.turnarounds + turnarounds
        self.entries.append({"label": label, "curves": curves, "followups": followups, "turnarounds": turnarounds})


def _tie(salt: str, compound: str, line: str) -> float:
    return int(hashlib.sha256(f"{salt}:tie:{compound}:{line}".encode()).hexdigest()[:12], 16) / 16 ** 12


def nominate(scores: Sequence[float], compounds: Sequence[str], lines: Sequence[str], budget: int, *, cap: int = 3,
             salt: str) -> list[tuple[str, str]]:
    """Top ``budget`` (compound, line) pairs, at most ``cap`` per compound; non-finite scores are never nominated."""

    if type(budget) is not int or budget < 0 or type(cap) is not int or cap < 1:
        raise ValueError("budget and cap must be nonnegative integers")
    rows = sorted(((-float(s), _tie(salt, c, l), c, l) for s, c, l in zip(scores, compounds, lines) if math.isfinite(float(s))))
    out, taken = [], {}
    for _, _, c, l in rows:
        if len(out) >= budget:
            break
        if taken.get(c, 0) < cap:
            taken[c] = taken.get(c, 0) + 1
            out.append((c, l))
    return out


def _digest(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


@dataclass(frozen=True)
class OutcomeSeal:
    """Sealed outcomes open only for frozen code and locked choices."""

    frozen: Mapping[str, str]
    choices_sha256: str | None

    def release(self, files: Mapping[str, bytes], choices: bytes | None) -> str:
        for name, digest in self.frozen.items():
            if name not in files or _digest(files[name]) != digest:
                raise PermissionError(f"{FREEZE_MISMATCH}:{name}")
        if self.choices_sha256 is None or choices is None:
            raise PermissionError(CHOICES_NOT_LOCKED)
        if _digest(choices) != self.choices_sha256:
            raise PermissionError(CHOICES_MISMATCH)
        return hashlib.sha256((self.choices_sha256 + "".join(sorted(self.frozen.values()))).encode()).hexdigest()


def assert_disjoint(development: Sequence[CompoundIdentity], test: Sequence[CompoundIdentity], family: Mapping[str, str]) -> None:
    for d in development:
        for t in test:
            if d.same_compound(t):
                raise ValueError(f"{SPLIT_LEAK}:compound:{d.core}:{t.core}")
    shared = {family[d.core] for d in development} & {family[t.core] for t in test}
    if shared:
        raise ValueError(f"{SPLIT_LEAK}:family:{sorted(shared)[0]}")
