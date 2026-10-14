"""Verified evidence registry: receipts bound to real source bytes, with lineage and independence groups.

File summary
- Path: src/maestro/evidence_registry.py
- Purpose: authenticate the evidence a strict decision rests on. `maestro.decision_review.EvidenceItem`
  only checks that a digest has 64 characters and trusts a caller-supplied `independent` flag. This
  module is the versioned replacement for strict use; the historical module is unchanged.
- Core points:
  - `RegisteredSource` names a file, its sha256 and the experiment or publication it came from.
    `EvidenceLedger.verify_source` re-reads the bytes on every call, so a modified or absent file
    is refused (`SOURCE_DIGEST_MISMATCH`, `SOURCE_MISSING`) and the refusal is not cached.
  - `EvidenceReceipt` binds one value to its source, observable, unit, normalisation, assay context,
    QC status, predefined decision rule, study protocol version and parent receipts.
  - Lineage follows PROV-O's `wasDerivedFrom`. A derived analysis must name parents that exist and
    authenticate. If any ancestor is a model prediction, the receipt is tainted and is never decisive
    (`PREDICTION_IN_LINEAGE`), so relabelling a prediction as an analysis does not admit it.
  - Independence is computed, never declared. Every decisive receipt maps to the set of upstream
    groups of its measured ancestors (experiment id, else publication id, else one shared
    `UNATTRIBUTED` group). Duplicated, reordered or repackaged records of one experiment or one
    publication stay one group, so they cannot raise an independent-support count.
  - `withdraw` removes a receipt. Anything that depended on it must re-verify (`binding_problems`).
  - Units convert to one canonical unit per dimension by division, so a boundary value (50 percent
    against 0.5 fraction) classifies identically and nothing is rounded through a product.
- Interfaces: `RegisteredSource`, `EvidenceReceipt`, `EvidenceLedger`, `canonical_value`, `holds`.
- Depends on: maestro.case_memory, maestro.claim_audit, maestro.models.
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from maestro.case_memory import ScientificMeasurementStatus
from maestro.models import EvidenceKind

SOURCE_UNREGISTERED, SOURCE_MISSING, SOURCE_DIGEST_MISMATCH = "SOURCE_UNREGISTERED", "SOURCE_MISSING", "SOURCE_DIGEST_MISMATCH"
RECEIPT_UNKNOWN, RECEIPT_WITHDRAWN = "RECEIPT_UNKNOWN", "RECEIPT_WITHDRAWN"
NO_LINEAGE, PARENT_REFUSED, LINEAGE_CYCLE = "NO_LINEAGE", "PARENT_REFUSED", "LINEAGE_CYCLE"
PREDICTION_IN_LINEAGE, KIND_NOT_MEASURED = "PREDICTION_IN_LINEAGE", "KIND_NOT_MEASURED"
STATUS_NOT_ADMITTED, CONTEXT_MISMATCH, PROTOCOL_MISMATCH = "STATUS_NOT_ADMITTED", "CONTEXT_MISMATCH", "PROTOCOL_MISMATCH"
UNIT_UNKNOWN, UNIT_DIMENSION_MISMATCH, NON_FINITE_VALUE = "UNIT_UNKNOWN", "UNIT_DIMENSION_MISMATCH", "NON_FINITE_VALUE"
NO_MEASURED_ROOT = "NO_MEASURED_ROOT"
UNATTRIBUTED = "UNATTRIBUTED"
MEASURED_KINDS = frozenset({EvidenceKind.REAL_MEASUREMENT, EvidenceKind.DERIVED_ANALYSIS})
PREDICTED_KINDS = frozenset({EvidenceKind.MODEL_PREDICTION, EvidenceKind.PREDICTION_DERIVED_ANALYSIS})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
RELATIONS = {"<=": lambda v, t: v <= t, ">=": lambda v, t: v >= t, "<": lambda v, t: v < t, ">": lambda v, t: v > t}

# unit -> (dimension, divisor to the dimension's canonical unit). Division only: 29 percent / 100 is
# the double nearest 0.29, whereas 0.29 * 100 is not 29.
UNITS: Mapping[str, tuple[str, float]] = {
    "fraction": ("viability_fraction", 1.0), "percent": ("viability_fraction", 100.0),
    "z": ("z_score", 1.0), "log2_fold_change": ("log2_fold_change", 1.0),
    "unitless": ("unitless", 1.0), "count": ("count", 1.0),
}


def canonical_value(value: float, unit: str) -> tuple[str, float]:
    if unit not in UNITS:
        raise ValueError(f"{UNIT_UNKNOWN}:{unit}")
    dimension, divisor = UNITS[unit]
    return dimension, float(value) / divisor


def holds(value: float, relation: str, threshold: float) -> bool:
    """Compare with a relative tolerance of 1e-12 at the boundary, so a unit round trip cannot flip a class."""

    if relation not in RELATIONS:
        raise ValueError(f"unknown relation {relation}")
    tie = math.isclose(value, threshold, rel_tol=1e-12, abs_tol=1e-15)
    if relation == "<=":
        return value <= threshold or tie
    if relation == ">=":
        return value >= threshold or tie
    return RELATIONS[relation](value, threshold) and not tie


@dataclass(frozen=True)
class RegisteredSource:
    source_id: str
    relative_path: str
    sha256: str
    digest_rule: str = "raw"
    experiment_id: str | None = None
    publication_id: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.relative_path.strip():
            raise ValueError("a source needs an identifier and a path")
        if not _SHA256.match(self.sha256):
            raise ValueError("source digest must be 64 lowercase hex characters")
        if self.digest_rule not in ("raw", "lf_normalised"):
            raise ValueError("digest rule must be raw or lf_normalised")

    @property
    def group(self) -> str:
        return self.experiment_id or self.publication_id or UNATTRIBUTED


@dataclass(frozen=True)
class EvidenceReceipt:
    receipt_id: str
    source_id: str
    source_sha256: str
    observable: str
    value: float
    unit: str
    normalisation: str
    context: str
    qc_status: ScientificMeasurementStatus
    qc_reference: str
    rule_id: str
    protocol_version: str
    kind: EvidenceKind
    derived_from: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("receipt_id", "source_id", "observable", "unit", "normalisation", "context", "qc_reference",
                     "rule_id", "protocol_version"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"receipt field {name} is required")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise TypeError("receipt value must be a number")
        if not isinstance(self.kind, EvidenceKind) or not isinstance(self.qc_status, ScientificMeasurementStatus):
            raise TypeError("receipt kind and QC status must be the registered enums")
        if not _SHA256.match(self.source_sha256):
            raise ValueError("receipt source digest must be 64 lowercase hex characters")


class EvidenceLedger:
    """Receipts and the registered sources behind them. Every question is answered from current bytes."""

    def __init__(self, root: Path, sources: Iterable[RegisteredSource], receipts: Iterable[EvidenceReceipt] = ()) -> None:
        self.root = Path(root)
        self._sources: dict[str, RegisteredSource] = {}
        for source in sources:
            if source.source_id in self._sources:
                raise ValueError(f"duplicate source {source.source_id}")
            self._sources[source.source_id] = source
        self._receipts: dict[str, EvidenceReceipt] = {}
        self._withdrawn: dict[str, str] = {}
        for receipt in receipts:
            self.add(receipt)

    def add(self, receipt: EvidenceReceipt) -> None:
        if receipt.receipt_id in self._receipts:
            raise ValueError(f"duplicate receipt {receipt.receipt_id}")
        self._receipts[receipt.receipt_id] = receipt

    def withdraw(self, receipt_id: str, reason: str) -> None:
        if receipt_id not in self._receipts:
            raise KeyError(RECEIPT_UNKNOWN)
        if not reason.strip():
            raise ValueError("a withdrawal must state why")
        self._withdrawn[receipt_id] = reason

    def receipt(self, receipt_id: str) -> EvidenceReceipt:
        return self._receipts[receipt_id]

    def receipt_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._receipts))

    def source(self, source_id: str) -> RegisteredSource | None:
        return self._sources.get(source_id)

    def verify_source(self, source_id: str) -> tuple[bool, str]:
        source = self._sources.get(source_id)
        if source is None:
            return False, SOURCE_UNREGISTERED
        path = (self.root / source.relative_path).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():
            return False, SOURCE_MISSING
        data = path.read_bytes()
        if source.digest_rule == "lf_normalised":
            data = data.replace(b"\r\n", b"\n")
        if hashlib.sha256(data).hexdigest() != source.sha256:
            return False, SOURCE_DIGEST_MISMATCH
        return True, "verified"

    def authenticate(self, receipt_id: str, _stack: tuple[str, ...] = ()) -> tuple[bool, str]:
        """Bytes, declared digest, withdrawal and parent integrity. It does not decide admissibility."""

        receipt = self._receipts.get(receipt_id)
        if receipt is None:
            return False, RECEIPT_UNKNOWN
        if receipt_id in self._withdrawn:
            return False, RECEIPT_WITHDRAWN
        if receipt_id in _stack:
            return False, LINEAGE_CYCLE
        ok, why = self.verify_source(receipt.source_id)
        if not ok:
            return False, why
        if self._sources[receipt.source_id].sha256 != receipt.source_sha256:
            return False, SOURCE_DIGEST_MISMATCH
        if receipt.kind == EvidenceKind.DERIVED_ANALYSIS and not receipt.derived_from:
            return False, NO_LINEAGE
        for parent in receipt.derived_from:
            ok, why = self.authenticate(parent, _stack + (receipt_id,))
            if not ok:
                return False, f"{PARENT_REFUSED}:{parent}:{why}"
        return True, "authenticated"

    def lineage(self, receipt_id: str) -> tuple[frozenset[str], bool]:
        """(upstream independence groups of measured ancestors, whether any ancestor is a model prediction)."""

        receipt = self._receipts[receipt_id]
        groups, predicted = set(), receipt.kind in PREDICTED_KINDS
        if receipt.kind == EvidenceKind.REAL_MEASUREMENT:
            groups.add(self._sources[receipt.source_id].group)
        for parent in receipt.derived_from:
            sub_groups, sub_predicted = self.lineage(parent)
            groups |= sub_groups
            predicted = predicted or sub_predicted
        return frozenset(groups), predicted

    def admit(self, receipt_id: str, context: str, protocol_version: str, *, allow_undetected: bool = False) -> tuple[bool, str]:
        """Whether this receipt may decide a prediction made in ``context`` under ``protocol_version``."""

        ok, why = self.authenticate(receipt_id)
        if not ok:
            return False, why
        receipt = self._receipts[receipt_id]
        if receipt.kind not in MEASURED_KINDS:
            return False, f"{KIND_NOT_MEASURED}:{receipt.kind.value}"
        groups, predicted = self.lineage(receipt_id)
        if predicted:
            return False, PREDICTION_IN_LINEAGE
        if not groups:
            return False, NO_MEASURED_ROOT
        allowed = {ScientificMeasurementStatus.QUALIFIED} | ({ScientificMeasurementStatus.UNDETECTED} if allow_undetected else set())
        if receipt.qc_status not in allowed:
            return False, f"{STATUS_NOT_ADMITTED}:{receipt.qc_status.value}"
        if not math.isfinite(float(receipt.value)):
            return False, NON_FINITE_VALUE
        if receipt.context != context:
            return False, f"{CONTEXT_MISMATCH}:{receipt.context}"
        if receipt.protocol_version != protocol_version:
            return False, f"{PROTOCOL_MISMATCH}:{receipt.protocol_version}"
        if receipt.unit not in UNITS:
            return False, f"{UNIT_UNKNOWN}:{receipt.unit}"
        return True, "admitted"

    def independent_groups(self, receipt_ids: Iterable[str]) -> frozenset[str]:
        groups: set[str] = set()
        for receipt_id in receipt_ids:
            groups |= self.lineage(receipt_id)[0]
        return frozenset(groups)

    def binding(self, receipt_ids: Iterable[str]) -> dict[str, str]:
        """receipt id -> declared source digest, as recorded in a certificate."""

        return {rid: self._receipts[rid].source_sha256 for rid in sorted(set(receipt_ids))}

    def binding_problems(self, binding: Mapping[str, str]) -> list[str]:
        """Receipts a certificate rests on that no longer authenticate (withdrawn, modified, missing)."""

        problems = []
        for receipt_id, digest in sorted(binding.items()):
            ok, why = self.authenticate(receipt_id)
            if not ok:
                problems.append(f"{receipt_id}:{why}")
            elif self._receipts[receipt_id].source_sha256 != digest:
                problems.append(f"{receipt_id}:{SOURCE_DIGEST_MISMATCH}")
        return problems
