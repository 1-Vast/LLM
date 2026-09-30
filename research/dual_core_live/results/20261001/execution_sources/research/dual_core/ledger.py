"""Purchased-measurement ledger: the only route by which a measured response becomes an in-context prompt.

File summary
- Path: research/dual_core/ledger.py
- Purpose: the agent-side contract for using acquired measurements as context. The executor records
  every purchase. A planner may read a prompt only through `PurchaseLedger.prompts`, which re-checks
  it against the steps the runner actually executed.
- Core points:
  - A `Prompt` is bound to:
    - the compound;
    - the dataset and assay;
    - the condition (line, time, dose);
    - the acquisition step and its cost in days;
    - the condition row, batch, measured replicate quality, detection flag, and a SHA-256 of the
      shift.
  - `record` accepts only an executor result whose row exists, passed QC, and belongs to this
    compound at this condition. Otherwise it logs a refusal and returns None:
    - `no_row` (nothing was measured);
    - `qc_failed`;
    - `identity_mismatch` (the row is another compound's, or another condition's).
  - `prompts(target, executed)` returns prompts only for conditions that appear, QC-passed, among
    the executed steps before the decision point. It refuses:
    - `target_outcome_leakage` (the target condition itself);
    - `future_measurement` (a purchase after the decision point);
    - `unpurchased` (a condition requested that was never bought).
  - Refusals are recorded, never silently dropped. The ledger never returns a predicted profile: a
    `Prompt` can only be built from an executor result.
- Interfaces: `Prompt`, `PurchaseLedger`, `LedgerRefusal`
- Depends on: numpy, pandas
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np


class LedgerRefusal(ValueError):
    """A request for a prompt that the ledger may not serve."""


@dataclass(frozen=True)
class Prompt:
    compound: str
    dataset: str
    assay: str
    condition: tuple
    step: int
    cost_days: float
    row: int
    batch: str
    quality: float
    detected: bool
    digest: str
    shift: np.ndarray = field(repr=False, compare=False)

    def __array__(self, dtype=None, copy=None):
        return np.asarray(self.shift, dtype=dtype)

    def provenance(self) -> dict:
        return {"compound": self.compound, "dataset": self.dataset, "assay": self.assay,
                "condition": list(self.condition), "step": self.step, "cost_days": self.cost_days, "row": self.row,
                "batch": self.batch, "quality": self.quality, "detected": self.detected, "sha256": self.digest}


class PurchaseLedger:
    """One per episode: what the executor returned for this compound, in acquisition order."""

    def __init__(self, compound: str, *, dataset: str, assay: str, conditions, shift, quality, detected, batch,
                 cost_days):
        self.compound = compound
        self.dataset, self.assay = dataset, assay
        self._conditions, self._shift = conditions, shift
        self._quality, self._detected, self._batch = quality, detected, batch
        self._cost = cost_days
        self.purchases: list = []          # (step, condition, Prompt | None)
        self.refusals: list = []           # (step, condition, reason)

    def record(self, key, result: dict) -> Prompt | None:
        """Called by the executor after every purchase, in order."""
        key = (str(key[0]), float(key[1]), float(key[2]))
        step = len(self.purchases)
        row = result.get("row")
        reason = None
        if row is None:
            reason = "no_row"
        elif not result.get("qc"):
            reason = "qc_failed"
        else:
            r = self._conditions.iloc[int(row)]
            if (str(r.compound).strip() != self.compound or str(r.cell_line) != key[0]
                    or float(r.time) != key[1] or float(r.dose) != key[2]):
                reason = "identity_mismatch"
        if reason is not None:
            self.purchases.append((step, key, None))
            self.refusals.append((step, key, reason))
            return None
        shift = np.asarray(self._shift[int(row)], dtype=np.float64)
        prompt = Prompt(self.compound, self.dataset, self.assay, key, step, float(self._cost(key)), int(row),
                        str(self._batch[int(row)]), float(np.clip(np.nan_to_num(self._quality[int(row)]), 0.0, 1.0)),
                        bool(self._detected[int(row)]), hashlib.sha256(shift.tobytes()).hexdigest(), shift)
        self.purchases.append((step, key, prompt))
        return prompt

    def prompts(self, *, target, executed) -> dict:
        """Prompts usable for a forecast at `target`, given the runner's executed (public) steps so far."""
        target = (str(target[0]), float(target[1]), float(target[2]))
        decision_point = len(executed)
        out = {}
        for i, step in enumerate(executed):
            key = (str(step["key"][0]), float(step["key"][1]), float(step["key"][2]))
            if i >= len(self.purchases) or self.purchases[i][1] != key:
                raise LedgerRefusal(f"executed step {i} {key} is not the ledger's purchase {i}")
            prompt = self.purchases[i][2]
            if prompt is None or not step.get("qc"):
                continue
            if key == target:
                self.refusals.append((decision_point, key, "target_outcome_leakage"))
                continue
            out[key] = prompt
        return out

    def get(self, key, *, decision_point: int) -> Prompt:
        """A single prompt by condition; refuses future and unpurchased requests."""
        key = (str(key[0]), float(key[1]), float(key[2]))
        for step, k, prompt in self.purchases:
            if k == key and prompt is not None:
                if step >= decision_point:
                    self.refusals.append((decision_point, key, "future_measurement"))
                    raise LedgerRefusal(f"{key} was bought at step {step}, after decision point {decision_point}")
                return prompt
        self.refusals.append((decision_point, key, "unpurchased"))
        raise LedgerRefusal(f"{key} was never bought (or failed QC) for {self.compound}")
