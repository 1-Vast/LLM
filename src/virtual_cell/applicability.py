"""Applicability domain, support level and extrapolation rejection.

File summary
- Path: src/virtual_cell/applicability.py
- Purpose: decide, before inference, whether a query lies inside the domain the
  model was fitted on, and say separately what is known about how well it does
  there.
- Core points:
  - Support is registered as *joint* condition slices; a domain derived from a
    table never becomes the cross product of its marginal ranges.
  - Four different facts are kept apart: can the model represent the query, was
    the exact slice observed, was performance evaluated on it against a declared
    acceptance criterion, and is its uncertainty calibrated.
  - A table of observed or training rows yields observed support, never
    validation: validation needs an identifiable receipt with an endpoint, a
    split, an acceptance criterion and a verified holdout.
- Interfaces: `SupportRecord`, `SupportRegistry`, `ApplicabilityVerdict`,
  `SupportLevel`, `SupportRegistry.from_table`.
- Depends on: virtual_cell/receipts.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Iterable, Mapping, Sequence

from .receipts import ValidationReceipt


class SupportLevel(str, Enum):
    """How much the registered evidence says about one query.

    The distinction a single boolean could not draw is between a query the
    model has been *validated* on, one whose exact conditions were merely
    *observed*, and one it can only *execute*. Only the first is a statement
    about whether the answer will be right, and it requires a receipt whose
    holdout was verified rather than assumed.
    """

    VALIDATED = "validated"
    RETROSPECTIVE_UNVERIFIED_HOLDOUT = "retrospective_unverified_holdout"
    EVALUATED_BELOW_ACCEPTANCE = "evaluated_below_acceptance"
    OBSERVED_SUPPORT = "observed_support"
    EXECUTABLE_UNCALIBRATED = "executable_uncalibrated"
    UNKNOWN = "unknown"
    INCOMPATIBLE = "incompatible"


# Gaps that mean the model cannot represent the query at all, as opposed to
# gaps that mean it was never validated there.
_STRUCTURAL_GAPS = frozenset({"mode_unregistered", "readout_unsupported"})
_IDENTITY_GAPS = frozenset({"perturbation_unregistered"})

# Levels a covering record can reach, best first.
_COVERED_ORDER = (
    SupportLevel.VALIDATED,
    SupportLevel.RETROSPECTIVE_UNVERIFIED_HOLDOUT,
    SupportLevel.EVALUATED_BELOW_ACCEPTANCE,
    SupportLevel.OBSERVED_SUPPORT,
)


@dataclass(frozen=True)
class SupportRecord:
    """One registered slice of the domain a model was fitted or validated on.

    A record with ``dose_range`` or ``time_range`` is an *interpolation claim*:
    it asserts that every value between the endpoints is supported, jointly
    with this record's other attributes. ``evaluations`` and ``calibration``
    are what lift a slice above observed support; ``origin`` records whether
    the slice came from training rows, from observed data, or from a hand
    declaration.
    """

    context_id: str
    perturbations: frozenset[str]
    modes: frozenset[str] = frozenset()
    readouts: frozenset[str] = frozenset()
    dose_range: tuple[float, float] | None = None
    time_range: tuple[float, float] | None = None
    observations: int = 0
    source: str = ""
    justification: str = ""
    origin: str = "declared"
    evaluations: tuple[ValidationReceipt, ...] = field(default_factory=tuple)
    calibration: ValidationReceipt | None = None

    def covers(
        self,
        *,
        perturbation: str,
        mode: str,
        dose: float | None,
        time_hours: float | None,
        readouts: Sequence[str],
    ) -> tuple[str, ...]:
        """Return the reasons this record does not cover the query."""

        gaps: list[str] = []
        if perturbation not in self.perturbations:
            gaps.append("perturbation_unregistered")
        if self.modes and mode not in self.modes:
            gaps.append("mode_unregistered")
        if self.readouts and not set(readouts).issubset(self.readouts):
            gaps.append("readout_unsupported")
        if self.dose_range is not None:
            if dose is None:
                gaps.append("dose_unspecified")
            elif not (self.dose_range[0] <= dose <= self.dose_range[1]):
                gaps.append("dose_out_of_range")
        if self.time_range is not None:
            if time_hours is None:
                gaps.append("time_unspecified")
            elif not (self.time_range[0] <= time_hours <= self.time_range[1]):
                gaps.append("time_out_of_range")
        return tuple(gaps)


@dataclass(frozen=True)
class ApplicabilityVerdict:
    """Whether the query is in domain, at what level, and if not, exactly why."""

    in_distribution: bool
    reasons: tuple[str, ...]
    matched: SupportRecord | None = None
    level: SupportLevel = SupportLevel.UNKNOWN
    receipt_problems: tuple[str, ...] = ()
    calibrated_uncertainty: bool = False

    @property
    def abstain_reason(self) -> str | None:
        return ", ".join(self.reasons) if self.reasons else None

    @property
    def validated(self) -> bool:
        """Only an accepted receipt on a verified holdout counts as validation."""

        return self.level is SupportLevel.VALIDATED

    @property
    def evaluated(self) -> bool:
        return self.level in {
            SupportLevel.VALIDATED,
            SupportLevel.RETROSPECTIVE_UNVERIFIED_HOLDOUT,
            SupportLevel.EVALUATED_BELOW_ACCEPTANCE,
        }


def receipt_level(
    receipts: Sequence[ValidationReceipt],
    *,
    endpoints: Sequence[str],
    context_identifier: str | None = None,
    model_version: str | None = None,
) -> tuple[SupportLevel, tuple[str, ...]]:
    """Best level any of these receipts supports, with the problems of the rest."""

    wanted = tuple(endpoints)
    problems: list[str] = []
    best = SupportLevel.OBSERVED_SUPPORT
    for receipt in receipts:
        issues = receipt.problems(
            endpoints=wanted or None,
            context_identifier=context_identifier,
            model_version=model_version,
        )
        if issues:
            problems.extend(issues)
            continue
        if receipt.passed is True:
            level = (
                SupportLevel.VALIDATED
                if receipt.holdout_verified
                else SupportLevel.RETROSPECTIVE_UNVERIFIED_HOLDOUT
            )
        elif receipt.passed is False:
            level = SupportLevel.EVALUATED_BELOW_ACCEPTANCE
        else:  # pragma: no cover - problems() already names this case
            continue
        if _COVERED_ORDER.index(level) < _COVERED_ORDER.index(best):
            best = level
    return best, tuple(dict.fromkeys(problems))


class SupportRegistry:
    """Registered support slices; an unregistered query is out of domain."""

    def __init__(self, records: Iterable[SupportRecord] = ()):
        self._records: list[SupportRecord] = []
        self._by_context: dict[str, list[SupportRecord]] = {}
        for record in records:
            self.register(record)

    def register(self, record: SupportRecord) -> SupportRecord:
        self._records.append(record)
        self._by_context.setdefault(record.context_id, []).append(record)
        return record

    @property
    def records(self) -> tuple[SupportRecord, ...]:
        return tuple(self._records)

    def contexts(self) -> tuple[str, ...]:
        return tuple(self._by_context)

    def _representable(
        self, candidates: Sequence[SupportRecord], *, mode: str, readouts: Sequence[str], perturbation: str
    ) -> tuple[bool, bool, bool]:
        """Whether mode, readouts and perturbation appear anywhere in this context."""

        modes = {value for record in candidates for value in record.modes}
        available = {value for record in candidates for value in record.readouts}
        perturbations = {value for record in candidates for value in record.perturbations}
        return (
            not modes or mode in modes,
            not available or set(readouts).issubset(available),
            perturbation in perturbations,
        )

    def assess(
        self,
        *,
        context_id: str,
        perturbation: str,
        mode: str,
        dose: float | None = None,
        time_hours: float | None = None,
        readouts: Sequence[str] = (),
        model_version: str | None = None,
    ) -> ApplicabilityVerdict:
        """Classify one query against every registered slice of this context.

        The query must be covered by a *single* record. Satisfying one attribute
        from one slice and another from a different slice is exactly the
        cross-product error: two observations at different doses, times and
        readouts say nothing about the combination neither of them measured.
        """

        candidates = self._by_context.get(context_id)
        if not candidates:
            return ApplicabilityVerdict(False, ("context_unregistered",), None, SupportLevel.UNKNOWN)

        best: tuple[int, SupportRecord, tuple[str, ...]] | None = None
        for record in candidates:
            gaps = record.covers(
                perturbation=perturbation,
                mode=mode,
                dose=dose,
                time_hours=time_hours,
                readouts=readouts,
            )
            if best is None or len(gaps) < best[0]:
                best = (len(gaps), record, gaps)
                if not gaps:
                    break
        assert best is not None
        _, record, gaps = best
        if not gaps:
            level, problems = receipt_level(
                record.evaluations,
                endpoints=tuple(readouts),
                context_identifier=context_id,
                model_version=model_version,
            )
            calibrated = record.calibration is not None and record.calibration.accepted
            return ApplicabilityVerdict(True, (), record, level, problems, calibrated)

        mode_ok, readouts_ok, perturbation_ok = self._representable(
            candidates, mode=mode, readouts=readouts, perturbation=perturbation
        )
        if not mode_ok or not readouts_ok:
            # The model has no representation for what was asked. More data at
            # other conditions would not help; this is a different failure from
            # being uncalibrated.
            structural = tuple(reason for reason in gaps if reason in _STRUCTURAL_GAPS) or gaps
            return ApplicabilityVerdict(False, structural, None, SupportLevel.INCOMPATIBLE)
        if not perturbation_ok:
            return ApplicabilityVerdict(
                False,
                tuple(reason for reason in gaps if reason in _IDENTITY_GAPS) or gaps,
                None,
                SupportLevel.UNKNOWN,
            )
        # Every axis is individually representable, but no single registered
        # slice covers the combination. The model will run; nothing says the
        # answer is calibrated here.
        return ApplicabilityVerdict(False, gaps, record, SupportLevel.EXECUTABLE_UNCALIBRATED)

    @classmethod
    def from_table(
        cls,
        rows: Sequence[Mapping[str, object]],
        *,
        context_column: str = "context_id",
        perturbation_column: str = "perturbation",
        mode_column: str = "mode",
        dose_column: str = "dose",
        time_column: str = "time_hours",
        readout_column: str = "readout",
        default_mode: str = "drug",
        source: str = "table",
        origin: str = "observed_rows",
        interpolate_over: Sequence[str] = (),
    ) -> "SupportRegistry":
        """Derive a domain from observed rows, one joint slice per observed cell.

        Each distinct (context, perturbation, mode, readout, dose, time) that
        actually occurs becomes its own record. Nothing is merged across axes,
        so a query can only be covered by a combination that was measured, and
        being covered means *observed*, not validated: no held-out error was
        measured by writing a table down.

        ``interpolate_over`` names axes on which the caller claims validated
        interpolation, for example ``("dose",)`` for a fitted dose-response
        model. Rows are then merged into a range *only* along those axes, and
        only among rows identical on every other axis. The claim is recorded in
        each record's ``justification`` so it can be audited rather than
        assumed.
        """

        axes = {str(name) for name in interpolate_over}
        unknown = axes - {"dose", "time"}
        if unknown:
            raise ValueError(f"Interpolation is not defined for axes {sorted(unknown)}.")

        grouped: dict[tuple, dict[str, object]] = {}
        for row in rows:
            context = str(row.get(context_column, ""))
            if not context:
                continue
            perturbation = row.get(perturbation_column)
            mode = row.get(mode_column)
            readout = row.get(readout_column)
            dose = row.get(dose_column)
            time_hours = row.get(time_column)
            dose_value = float(dose) if isinstance(dose, (int, float)) and isfinite(float(dose)) else None
            time_value = (
                float(time_hours)
                if isinstance(time_hours, (int, float)) and isfinite(float(time_hours))
                else None
            )
            key = (
                context,
                str(perturbation) if perturbation is not None else "",
                str(mode) if mode is not None else default_mode,
                str(readout) if readout is not None else "",
                None if "dose" in axes else dose_value,
                None if "time" in axes else time_value,
            )
            bucket = grouped.setdefault(key, {"doses": [], "times": [], "n": 0})
            if dose_value is not None:
                bucket["doses"].append(dose_value)
            if time_value is not None:
                bucket["times"].append(time_value)
            bucket["n"] = int(bucket["n"]) + 1

        justification = (
            f"observed joint slices; interpolation claimed on {sorted(axes)}"
            if axes
            else "observed joint slices only; no interpolation claimed"
        )
        registry = cls()
        for key, bucket in sorted(grouped.items(), key=lambda entry: str(entry[0])):
            context, perturbation, mode, readout, _, _ = key
            doses = bucket["doses"]
            times = bucket["times"]
            registry.register(
                SupportRecord(
                    context_id=context,
                    perturbations=frozenset({perturbation}) if perturbation else frozenset(),
                    modes=frozenset({mode}),
                    readouts=frozenset({readout}) if readout else frozenset(),
                    dose_range=(min(doses), max(doses)) if doses else None,
                    time_range=(min(times), max(times)) if times else None,
                    observations=int(bucket["n"]),
                    source=source,
                    justification=justification,
                    origin=origin,
                )
            )
        return registry
