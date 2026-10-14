"""Miniature ledgers for the strict decision and evidence-registry contracts.

File summary
- Path: tests/fixtures/strict_evidence.py
- Purpose: build a ledger over real temporary files, so every authentication test reads actual bytes.
- Interfaces: `PROTOCOL`, `CONTEXT`, `Lab`.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from maestro.case_memory import ScientificMeasurementStatus as S
from maestro.evidence_registry import EvidenceLedger, EvidenceReceipt, RegisteredSource
from maestro.models import EvidenceKind as K

PROTOCOL = "study-v1"
CONTEXT = "A549:cetsa:1h"


class Lab:
    """A directory of source files, a registry over them and helpers that add receipts."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.sources: list[RegisteredSource] = []
        self.ledger = EvidenceLedger(self.root, [])

    def source(self, source_id: str, body: str, *, experiment: str | None = None, publication: str | None = None,
               rule: str = "raw") -> RegisteredSource:
        path = self.root / f"{source_id}.csv"
        path.write_bytes(body.encode("utf-8"))
        src = RegisteredSource(source_id, path.name, hashlib.sha256(body.encode("utf-8")).hexdigest(), rule, experiment, publication)
        self.ledger._sources[source_id] = src
        return src

    def receipt(self, rid: str, source_id: str, observable: str, value: float, *, unit: str = "z", kind=K.REAL_MEASUREMENT,
                status=S.QUALIFIED, context: str = CONTEXT, rule: str | None = None, parents: tuple[str, ...] = (),
                protocol: str = PROTOCOL) -> EvidenceReceipt:
        src = self.ledger.source(source_id)
        receipt = EvidenceReceipt(rid, source_id, src.sha256, observable, value, unit, "plate-median", context, status,
                                  "qc/plate-report-1", rule or observable, protocol, kind, parents)
        self.ledger.add(receipt)
        return receipt
