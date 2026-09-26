"""Biological identity checks for expression feature labels.

File summary
- Path: src/virtual_cell/identity_markers.py
- Purpose: verify that a matrix's column labels name the genes whose counts the columns hold,
  using cell-line identity markers whose expression pattern a mislabelled column cannot fake.
- Core points:
  - A label table is trusted only when the declared markers peak in their expected context.
  - An offset between the label table and the columns is chosen by the markers, never assumed;
    when no offset, or more than one, passes, the check refuses by name.
  - The markers are literature facts about the lines, not results of any MAESTRO analysis.
  - The SciPlex3 release on Figshare (file 43381398) carries a stray header row as its first
    feature label, so column j holds the gene of label row j + 1. This module is how that was
    found and how a reader corrects it; nothing here hard-codes the offset.
- Interfaces: `IDENTITY_MARKERS`, `MarkerCheck`, `check_markers`, `resolve_label_offset`,
  `shift_labels`
- Depends on: numpy
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

# Context -> genes expressed there far above the other two contexts. K562 is an erythroleukemia
# line expressing embryonic and fetal globins with GATA1; MCF7 is a luminal, estrogen-receptor
# positive breast line; A549 carries a KEAP1 loss that keeps NRF2 targets constitutively high.
IDENTITY_MARKERS: Mapping[str, tuple[str, ...]] = {
    "K562": ("HBG1", "HBG2", "HBZ", "GATA1"),
    "MCF7": ("TFF1", "KRT19", "GATA3", "ESR1"),
    "A549": ("AKR1C1", "AKR1B10", "NQO1", "ALDH3A1"),
}


@dataclass(frozen=True)
class MarkerCheck:
    """How many declared markers peak in their expected context under one label offset."""

    offset: int
    tested: int
    peaked_in_expected_context: int
    untestable: tuple[str, ...]
    peaks: Mapping[str, str] = field(default_factory=dict)

    @property
    def fraction(self) -> float:
        return self.peaked_in_expected_context / self.tested if self.tested else 0.0

    def passed(self, *, minimum_fraction: float = 0.9, minimum_tested: int = 6) -> bool:
        return self.tested >= minimum_tested and self.fraction >= minimum_fraction

    def payload(self) -> dict[str, object]:
        return {"offset": self.offset, "tested": self.tested,
                "peaked_in_expected_context": self.peaked_in_expected_context,
                "untestable": list(self.untestable), "peaks": dict(self.peaks)}


def shift_labels(labels: Sequence[str | None], offset: int, columns: int) -> list[str | None]:
    """The label of each column under an offset: column j takes label row j + offset.

    A column whose label row falls outside the table is unlabelled (None), never borrowed.
    """

    return [labels[j + offset] if 0 <= j + offset < len(labels) else None for j in range(columns)]


def check_markers(
    means: Mapping[str, np.ndarray],
    labels: Sequence[str | None],
    *,
    offset: int = 0,
    markers: Mapping[str, Sequence[str]] = IDENTITY_MARKERS,
) -> MarkerCheck:
    """Test one offset: a marker passes when its column is highest in the marker's context.

    ``means`` maps a context to per-column mean expression; ``labels`` is the label table as
    published. A marker is untestable when its label is absent, when its column falls outside
    the matrix, when its context has no means, or when its column is zero everywhere.
    """

    contexts = [c for c in means]
    if not contexts:
        raise ValueError("marker_check_needs_context_means")
    columns = {len(np.asarray(v)) for v in means.values()}
    if len(columns) != 1:
        raise ValueError("marker_check_context_means_differ_in_length")
    width = columns.pop()
    row = {}
    for index, label in enumerate(labels):
        if label is not None:
            row.setdefault(label, index)
    tested = passed = 0
    untestable: list[str] = []
    peaks: dict[str, str] = {}
    for context, genes in markers.items():
        for gene in genes:
            column = row.get(gene, -1) - offset if gene in row else -1
            if context not in means or not 0 <= column < width:
                untestable.append(gene)
                continue
            values = {c: float(np.asarray(means[c])[column]) for c in contexts}
            if max(values.values()) <= 0.0:
                untestable.append(gene)
                continue
            winner = max(values, key=lambda c: (values[c], c))
            peaks[gene] = winner
            tested += 1
            passed += int(winner == context)
    return MarkerCheck(offset, tested, passed, tuple(untestable), peaks)


def resolve_label_offset(
    means: Mapping[str, np.ndarray],
    labels: Sequence[str | None],
    *,
    offsets: Sequence[int] = (-1, 0, 1),
    markers: Mapping[str, Sequence[str]] = IDENTITY_MARKERS,
    minimum_fraction: float = 0.9,
    minimum_tested: int = 6,
) -> tuple[int | None, tuple[MarkerCheck, ...], str | None]:
    """Choose the offset the markers support, or refuse by name.

    Returns ``(offset, checks, refusal)``. Exactly one passing offset is required: none means the
    labels cannot be trusted at any tested alignment, several means the markers cannot decide.
    """

    checks = tuple(check_markers(means, labels, offset=o, markers=markers) for o in offsets)
    passing = [c for c in checks if c.passed(minimum_fraction=minimum_fraction, minimum_tested=minimum_tested)]
    if not passing:
        return None, checks, "feature_labels_fail_identity_markers"
    if len(passing) > 1:
        return None, checks, "feature_label_offset_ambiguous"
    return passing[0].offset, checks, None
