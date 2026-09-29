"""Adaptation: what it costs to transfer a precedent onto a different condition, and whether that has worked.

File summary
- Path: research/scientific_case_memory/adaptation_model.py
- Purpose: separate similarity from transferability. Two cases can look alike and still not transfer;
  this module records each attempted transfer as a source, a target, the differences between them
  and whether the source's reading matched the target's, and prices a new transfer from that record.
- Core points:
  - A difference signature is a small discrete key: does the dataset or assay differ, does the cell
    line differ, is the time the same, near or far, is the dose the same, near or far, does the batch
    differ. Continuous gaps are binned by fold change (`NEAR_FOLD`), so the table has few cells and
    each can be counted.
  - `AdaptationTable` counts successes and trials per signature. A transfer succeeded when the
    source's reading at its condition equals the target's reading at the target condition, for two
    compounds of the same hypothesis class and different independent units.
  - Cost is relative to what transfer achieves at zero difference. With `s0` the zero-difference
    success rate and `chance` the rate expected if readings were independent draws from the pooled
    distribution, a signature with success rate `s` costs `clip((s0 - s) / (s0 - chance), 0, 1)`:
    0 when it transfers as well as a same-condition class-mate, 1 when it is no better than chance.
  - A signature with fewer than `MIN_TRIALS` recorded transfers has no historical support. It is
    priced from the declared prior, `PRIOR_COST_PER_DIFFERENCE` for each differing attribute, and
    flagged `supported=False`; its uncertainty is the widest allowed. The prior is a declared
    convention fixed before any result, not an estimate.
  - `transition_matrix` estimates, from training pairs only, how a source reading maps to a target
    reading between two conditions, so a reference missing its reading at the target condition can
    contribute a soft reading instead of nothing (`Jeffreys` smoothed).
  - Nothing here reads a held-out label: the table and the matrices are built from training
    references and their own leave-unit-out readings.
- Interfaces: `NEAR_FOLD`, `MIN_TRIALS`, `PRIOR_COST_PER_DIFFERENCE`, `Context`, `differences`,
  `signature`, `operations_for`, `AdaptationCost`, `AdaptationTable`, `transition_matrix`
- Depends on: case_schema.py, numpy
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

import numpy as np

from . import case_schema as S

NEAR_FOLD = 4.0
"""Two times or doses within this fold change (either direction) are `near`; the same value is `same`."""
MIN_TRIALS = 20
"""Fewest recorded transfers of one signature before its success rate may price a new transfer."""
PRIOR_COST_PER_DIFFERENCE = 0.25
"""Declared prior cost per differing attribute, used only where a signature has no historical support."""
JEFFREYS = 0.5


@dataclass(frozen=True)
class Context:
    """Where a reading was made (or is to be made)."""

    dataset: str
    assay: str
    cell_line: str | None = None
    time_h: float | None = None
    dose_nM: float | None = None
    batch: str | None = None


def _gap(a: float | None, b: float | None) -> str:
    if a is None or b is None:
        return "unknown"
    if a == b:
        return "same"
    if a <= 0 or b <= 0:
        return "far"
    return "near" if max(a / b, b / a) <= NEAR_FOLD else "far"


def differences(source: Context, target: Context) -> dict[str, object]:
    """The explicit differences between two contexts, as attributes a report can print."""
    return {
        "dataset": source.dataset != target.dataset,
        "assay": source.assay != target.assay,
        "cell_line": (source.cell_line != target.cell_line) if (source.cell_line and target.cell_line) else None,
        "time": _gap(source.time_h, target.time_h),
        "dose": _gap(source.dose_nM, target.dose_nM),
        "batch": (source.batch != target.batch) if (source.batch and target.batch) else None,
    }


def signature(diff: Mapping[str, object]) -> tuple:
    """The discrete key under which a transfer is counted."""
    return (bool(diff["dataset"] or diff["assay"]), diff["cell_line"], diff["time"], diff["dose"], bool(diff["batch"]))


def differing_attributes(diff: Mapping[str, object]) -> int:
    n = int(bool(diff["dataset"] or diff["assay"]))
    n += int(diff["cell_line"] is True)
    n += int(diff["time"] in ("near", "far"))
    n += int(diff["dose"] in ("near", "far"))
    n += int(diff["batch"] is True)
    n += int(diff["time"] == "unknown") + int(diff["dose"] == "unknown")
    return n


def operations_for(diff: Mapping[str, object]) -> tuple[str, ...]:
    ops = []
    if diff["dataset"] or diff["assay"]:
        ops.append("cross_assay_transfer")
    if diff["cell_line"] is True:
        ops.append("cross_cell_line_transfer")
    if diff["time"] in ("near", "far"):
        ops.append("cross_time_transfer")
    if diff["dose"] in ("near", "far"):
        ops.append("cross_dose_transfer")
    if diff["batch"] is True:
        ops.append("batch_correction_assumed")
    return tuple(ops) or ("same_condition_transfer",)


@dataclass(frozen=True)
class AdaptationCost:
    cost: float
    supported: bool
    trials: int
    success_rate: float | None
    uncertainty: float
    reason: str


class AdaptationTable:
    """Counts of adaptation successes per difference signature, plus the chance rate."""

    def __init__(self, chance: float = 0.25):
        self.counts: dict[tuple, list[int]] = {}
        self.chance = float(chance)

    def add(self, sig: tuple, success: bool, n: int = 1) -> None:
        cell = self.counts.setdefault(sig, [0, 0])
        cell[0] += int(success) * n
        cell[1] += n

    def add_bulk(self, sig: tuple, successes: int, trials: int) -> None:
        cell = self.counts.setdefault(sig, [0, 0])
        cell[0] += int(successes)
        cell[1] += int(trials)

    def stats(self, sig: tuple) -> tuple[int, int]:
        s, n = self.counts.get(sig, [0, 0])
        return s, n

    def _rate(self, sig: tuple) -> tuple[float, float, int]:
        s, n = self.stats(sig)
        a, b = s + JEFFREYS, n - s + JEFFREYS
        mean = a / (a + b)
        sd = math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1)))
        return mean, sd, n

    @property
    def zero_signature(self) -> tuple:
        return (False, False, "same", "same", False)

    def baseline(self) -> tuple[float, int]:
        mean, _, n = self._rate(self.zero_signature)
        return mean, n

    def cost(self, diff: Mapping[str, object]) -> AdaptationCost:
        sig = signature(diff)
        mean, sd, n = self._rate(sig)
        s0, n0 = self.baseline()
        if n >= MIN_TRIALS and n0 >= MIN_TRIALS:
            room = max(s0 - self.chance, 1e-9)
            rel = min(1.0, max(0.0, (s0 - mean) / room))
            return AdaptationCost(rel, True, n, mean, sd, "historical")
        k = differing_attributes(diff)
        return AdaptationCost(min(1.0, PRIOR_COST_PER_DIFFERENCE * k), False, n, None if n == 0 else mean,
                              0.5 if n == 0 else max(sd, 0.25), "declared_prior_no_historical_support")

    def valid_when(self, margin: float = 0.05) -> tuple[str, ...]:
        """Signatures with support whose success rate is within `margin` of the zero-difference rate."""
        s0, _ = self.baseline()
        return tuple(sorted(_sig_text(sig) for sig in self.counts
                            if self.stats(sig)[1] >= MIN_TRIALS and self._rate(sig)[0] >= s0 - margin))

    def failed_when(self, margin: float = 0.05) -> tuple[str, ...]:
        """Signatures with support whose success rate is within `margin` of chance or below."""
        return tuple(sorted(_sig_text(sig) for sig in self.counts
                            if self.stats(sig)[1] >= MIN_TRIALS and self._rate(sig)[0] <= self.chance + margin))

    def rows(self) -> list[dict]:
        out = []
        for sig, (s, n) in sorted(self.counts.items(), key=lambda kv: str(kv[0])):
            mean, sd, _ = self._rate(sig)
            out.append({"signature": _sig_text(sig), "successes": s, "trials": n, "success_rate": mean, "sd": sd,
                        "supported": n >= MIN_TRIALS})
        return out


def _sig_text(sig: tuple) -> str:
    cross, cell, time, dose, batch = sig
    return (f"assay_change={cross};cell_line_change={cell};time={time};dose={dose};batch_change={batch}")


def make_link(source_case: str, target_case: str, source: Context, target: Context, table: AdaptationTable,
              success: bool | None) -> S.AdaptationLink:
    """One recorded transfer, priced from the table as it stood."""
    diff = differences(source, target)
    priced = table.cost(diff)
    return S.AdaptationLink(source_case, target_case, {k: v for k, v in diff.items()}, operations_for(diff),
                            round(priced.cost, 6), success, table.valid_when(), table.failed_when())


def transition_matrix(source_codes: np.ndarray, target_codes: np.ndarray, n_codes: int = 4,
                      prior: np.ndarray | None = None, strength: float = 4.0) -> np.ndarray:
    """P(target code | source code), rows summing to 1, from references measured at both conditions.

    Codes below zero mean not measured or not scored and are ignored. Each row is shrunk to `prior`
    (the pooled target distribution) with pseudo-count `strength`, so a code never seen in the source
    falls back to the pooled rate rather than to zero.
    """
    counts = np.zeros((n_codes, n_codes))
    ok = (source_codes >= 0) & (target_codes >= 0)
    np.add.at(counts, (source_codes[ok], target_codes[ok]), 1.0)
    if prior is None:
        prior = counts.sum(0) + JEFFREYS
    prior = np.asarray(prior, dtype=float)
    prior = prior / prior.sum()
    rows = counts + strength * prior[None, :]
    return rows / rows.sum(1, keepdims=True)
