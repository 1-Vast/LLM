"""Evaluation contract v2: pre-outcome eligibility, training-side normalisation, identity, units and QC.

File summary
- Path: src/maestro/evaluation_contract.py
- Purpose: the executable form of evaluator-audit findings E1-E7 / corrections C1-C7
  (`research/evaluator_audit_20261013`) for a future evaluator. The frozen evaluator
  `research/knowledge_reality_20261013/confirm.py` is not changed and was never run; this is a new
  version, not an edit of a protocol.
- Core points:
  - C1 `eligible_units` reads metadata rows only and has no outcome argument, so eligibility cannot
    depend on outcome missingness. Missingness is QC loss, reported by `settle`.
  - C2 `nominate_wells` takes scores and a frozen candidate set, never outcomes. `settle` books a
    nominated well that failed QC or is missing as consumed, with no hit.
  - C3/C4 `TrainNormaliser` fits only on rows its authorised training ids contain
    (`NORMALISER_ROW_NOT_AUTHORISED`). `hit_labels` is row-local, so another test compound cannot
    change a label.
  - C5 `resolve_identity` refuses duplicated identifiers, a core present in more than one screen
    (`REP.1M` and `REP1M` are one spelling), and more than one row per core in a screen. Unmapped
    requested cores are listed and refused unless the caller declares a loss allowance.
  - C6 `PinnedInputs` reads a file only if its sha256 is in the manifest and matches.
  - C7 `settle` applies the same QC and unit rules to every readout, secondary ones included.
  - Viability units are declared, never guessed. Percent converts to a fraction by division, and
    `viability_hit` compares with a boundary tolerance so 50 percent and 0.5 fraction classify alike.
- Interfaces: `eligible_units`, `nominate_wells`, `settle`, `TrainNormaliser`, `hit_labels`,
  `resolve_identity`, `PinnedInputs`, `viability_fraction`, `viability_hit`.
- Depends on: numpy, maestro.evidence_registry.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Collection, Iterable, Mapping, Sequence

import numpy as np

from maestro.evidence_registry import holds

UNIT_UNDECLARED, UNIT_RANGE_SUSPECT = "UNIT_UNDECLARED", "UNIT_RANGE_SUSPECT"
NORMALISER_ROW_NOT_AUTHORISED, IDENTITY_REFUSED = "NORMALISER_ROW_NOT_AUTHORISED", "IDENTITY_REFUSED"
UNPINNED_INPUT, PINNED_MISSING, PINNED_DIGEST_MISMATCH = "UNPINNED_INPUT", "PINNED_MISSING", "PINNED_DIGEST_MISMATCH"
NOMINATION_OUTSIDE_FROZEN_SET, BUDGET_EXCEEDED = "NOMINATION_OUTSIDE_FROZEN_SET", "BUDGET_EXCEEDED"
_CORE_LENGTH = 13


def viability_fraction(values, unit: str | None) -> np.ndarray:
    """Viability as a fraction. The unit must be declared; values that contradict it are refused."""

    array = np.asarray(values, dtype=float)
    finite = array[np.isfinite(array)]
    if unit == "fraction":
        if finite.size and finite.max() > 5.0:
            raise ValueError(f"{UNIT_RANGE_SUSPECT}: declared fraction but maximum {finite.max():g}")
        return array
    if unit == "percent":
        if finite.size >= 20 and finite.max() <= 3.0:
            raise ValueError(f"{UNIT_RANGE_SUSPECT}: declared percent but maximum {finite.max():g}")
        return array / 100.0
    raise ValueError(f"{UNIT_UNDECLARED}: {unit!r}")


def viability_hit(values, unit: str | None, threshold_fraction: float, *, inclusive: bool) -> np.ndarray:
    """Hit when viability is below (or at, when ``inclusive``) the threshold. NaN is never a hit."""

    fraction = viability_fraction(values, unit)
    relation = "<=" if inclusive else "<"
    return np.array([bool(np.isfinite(v)) and holds(float(v), relation, float(threshold_fraction)) for v in fraction.ravel()],
                    dtype=bool).reshape(fraction.shape)


def _screen(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", name.upper())


def eligible_units(metadata: Iterable[Mapping[str, str]], *, screen: str, perturbation_type: str, min_lines: int,
                   unit_field: str = "unit", screen_field: str = "screen", type_field: str = "pert_type",
                   line_field: str = "line") -> tuple[str, ...]:
    """Units the protocol freezes as scored, from metadata alone. There is no outcome argument by design."""

    lines: dict[str, set[str]] = {}
    for row in metadata:
        if _screen(row[screen_field]) == _screen(screen) and row[type_field] == perturbation_type:
            lines.setdefault(row[unit_field], set()).add(row[line_field])
    return tuple(sorted(u for u, seen in lines.items() if len(seen) >= min_lines))


@dataclass(frozen=True)
class Resolution:
    mapping: Mapping[str, str]
    unmapped: tuple[str, ...]


class IdentityRefused(ValueError):
    def __init__(self, refusals: Sequence[str]) -> None:
        self.refusals = tuple(refusals)
        super().__init__(f"{IDENTITY_REFUSED}: " + "; ".join(self.refusals))


def resolve_identity(requested_cores: Iterable[str], id_rows: Sequence[Mapping[str, str]], *, max_unmapped: int = 0) -> Resolution:
    """Map each requested compound core to exactly one identifier in exactly one screen, or refuse."""

    refusals, seen_ids = [], set()
    by_core: dict[str, list[tuple[str, str]]] = {}
    for row in id_rows:
        ident, screen = row["id"], _screen(row["screen"])
        if ident in seen_ids:
            refusals.append(f"DUPLICATE_ID:{ident}")
        seen_ids.add(ident)
        by_core.setdefault(ident[:_CORE_LENGTH], []).append((ident, screen))
    requested = list(dict.fromkeys(requested_cores))
    mapping, unmapped = {}, []
    for core in requested:
        entries = by_core.get(core)
        if not entries:
            unmapped.append(core)
            continue
        if len({screen for _, screen in entries}) > 1:
            refusals.append(f"CROSS_SCREEN_COLLISION:{core}")
        elif len({ident for ident, _ in entries}) > 1:
            refusals.append(f"AMBIGUOUS_DUPLICATE_ROWS:{core}")
        else:
            mapping[core] = entries[0][0]
    if len(unmapped) > max_unmapped:
        refusals.append(f"UNMAPPED_CORES_EXCEED_ALLOWANCE:{len(unmapped)}>{max_unmapped}:{','.join(sorted(unmapped)[:5])}")
    if refusals:
        raise IdentityRefused(sorted(set(refusals)))
    return Resolution(dict(sorted(mapping.items())), tuple(sorted(unmapped)))


class TrainNormaliser:
    """Median profile estimated on authorised training rows only; applied unchanged to truth and predictions."""

    def __init__(self, authorised_ids: Collection[str]) -> None:
        self._authorised = frozenset(authorised_ids)
        self.median: np.ndarray | None = None

    def fit(self, matrix, row_ids: Sequence[str]) -> "TrainNormaliser":
        outside = [r for r in row_ids if r not in self._authorised]
        if outside:
            raise ValueError(f"{NORMALISER_ROW_NOT_AUTHORISED}: {outside[:3]}")
        self.median = np.nanmedian(np.asarray(matrix, dtype=float), axis=0)
        return self

    def residualise(self, matrix) -> np.ndarray:
        if self.median is None:
            raise RuntimeError("normaliser is not fitted")
        return np.asarray(matrix, dtype=float) - self.median


def hit_labels(matrix, normaliser: TrainNormaliser, z_threshold: float) -> np.ndarray:
    """Row-local robust-z hits on the training-residualised matrix: one row never reads another."""

    residual = normaliser.residualise(matrix)
    centre = np.nanmedian(residual, axis=1, keepdims=True)
    mad = np.nanmedian(np.abs(residual - centre), axis=1, keepdims=True) * 1.4826
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (residual - centre) / mad
    return np.isfinite(z) & (z <= -abs(z_threshold))


def _tie(well: tuple[str, str], salt: str) -> str:
    return hashlib.sha256(f"{salt}|{well[0]}|{well[1]}".encode("utf-8")).hexdigest()


def nominate_wells(scores: Mapping[tuple[str, str], float], frozen_candidates: Collection[tuple[str, str]], budget_wells: int,
                   *, salt: str) -> tuple[tuple[str, str], ...]:
    """Top predicted wells inside the frozen candidate set. Outcomes are not an argument; ties break by salted hash."""

    if type(budget_wells) is not int or budget_wells < 0:
        raise ValueError("budget must be a nonnegative integer number of wells")
    outside = [w for w in scores if w not in frozen_candidates]
    if outside:
        raise ValueError(f"{NOMINATION_OUTSIDE_FROZEN_SET}: {outside[:3]}")
    ranked = sorted((w for w in scores if np.isfinite(scores[w])), key=lambda w: (-scores[w], _tie(w, salt)))
    return tuple(ranked[:budget_wells])


@dataclass(frozen=True)
class Readout:
    name: str
    unit: str
    values: Mapping[tuple[str, str], float]
    qc_ok: Mapping[tuple[str, str], bool]


@dataclass(frozen=True)
class Settlement:
    wells_consumed: int
    hits: Mapping[str, int]
    qc_failed: Mapping[str, int]
    missing: Mapping[str, int]


def settle(nominated: Sequence[tuple[str, str]], readouts: Sequence[Readout], threshold_fraction: float, *,
           inclusive: bool = False) -> Settlement:
    """Book every nominated well, then score each readout (primary and secondary alike) by the same rules."""

    hits, qc_failed, missing = {}, {}, {}
    for readout in readouts:
        n_hit = n_fail = n_missing = 0
        for well in nominated:
            if well not in readout.values or not np.isfinite(readout.values[well]):
                n_missing += 1
                continue
            if not readout.qc_ok.get(well, False):
                n_fail += 1
                continue
            n_hit += int(viability_hit([readout.values[well]], readout.unit, threshold_fraction, inclusive=inclusive)[0])
        hits[readout.name], qc_failed[readout.name], missing[readout.name] = n_hit, n_fail, n_missing
    return Settlement(len(nominated), hits, qc_failed, missing)


class PinnedInputs:
    """A file may be read only when the manifest pins its sha256 and the bytes still match."""

    def __init__(self, root: Path, manifest: Mapping[str, str]) -> None:
        self.root, self.manifest = Path(root), dict(manifest)

    def read_bytes(self, relative: str) -> bytes:
        if relative not in self.manifest:
            raise PermissionError(f"{UNPINNED_INPUT}: {relative}")
        path = self.root / relative
        if not path.is_file():
            raise FileNotFoundError(f"{PINNED_MISSING}: {relative}")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != self.manifest[relative]:
            raise ValueError(f"{PINNED_DIGEST_MISMATCH}: {relative}")
        return data

    def problems(self) -> list[str]:
        out = []
        for relative in sorted(self.manifest):
            try:
                self.read_bytes(relative)
            except (FileNotFoundError, ValueError) as error:
                out.append(str(error))
        return out
