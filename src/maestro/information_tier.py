"""Information tiers for unseen-compound prediction: what a result may claim given what it read.

File summary
- Path: src/maestro/information_tier.py
- Purpose: make the visibility boundary between cold-start prediction, screen-informed triage and
  purchased measurement mechanical, so a T1 input can never support a T0 claim.
- Core points:
  - `Tier`:
    - T0, strict cold start: no observed perturbation response of the compound in any input;
      structure, curated annotations, cell-free measurements and the cell lines' own basal state
      are allowed;
    - T1: adds legal primary-screen or other already-observed responses of the compound, which
      still need independent confirmation;
    - T2: adds measurements bought during the campaign, each costed in wells and turnarounds.
  - `InputDeclaration` names one input, the lowest tier at which it may be visible, and whether it
    is outcome-proximal for the endpoint (for example a growth readout of the compound when the
    endpoint is viability). Outcome-proximal inputs are refused at every tier.
  - `admit(inputs, claimed)` refuses each input above the claimed tier (`TIER_VIOLATION`), each
    outcome-proximal input (`OUTCOME_PROXIMAL_INPUT`) and, with a registry, each input it does
    not know (`UNDECLARED_INPUT`).
  - `claimable_tier(inputs)` is the lowest tier a result built from these inputs may claim.
  - `cold_start_violations` lists, per compound, the sources that hold an observed response for
    it. A T0 evaluation set must come back empty.
- Interfaces: `Tier`, `InputDeclaration`, `Admission`, `TierViolation`, `admit`, `require`,
  `claimable_tier`, `cold_start_violations`.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Collection, Iterable, Mapping

TIER_VIOLATION = "TIER_VIOLATION"
OUTCOME_PROXIMAL_INPUT = "OUTCOME_PROXIMAL_INPUT"
UNDECLARED_INPUT = "UNDECLARED_INPUT"


class Tier(IntEnum):
    T0 = 0
    T1 = 1
    T2 = 2


@dataclass(frozen=True)
class InputDeclaration:
    name: str
    tier: Tier
    outcome_proximal: bool = False
    provenance: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("an input needs a name")
        if not isinstance(self.tier, Tier):
            raise TypeError("input tier must be a Tier")


@dataclass(frozen=True)
class Admission:
    claimed: Tier
    admitted: tuple[str, ...]
    refused: tuple[tuple[str, str], ...]

    @property
    def passed(self) -> bool:
        return not self.refused


class TierViolation(ValueError):
    def __init__(self, admission: Admission) -> None:
        self.admission = admission
        detail = ", ".join(f"{name}:{reason}" for name, reason in admission.refused)
        super().__init__(f"inputs not admissible at {admission.claimed.name}: {detail}")


def admit(inputs: Iterable[InputDeclaration], claimed: Tier,
          registry: Mapping[str, InputDeclaration] | None = None) -> Admission:
    """Admit each input at the claimed tier or refuse it with a named reason."""

    admitted, refused = [], []
    for item in inputs:
        if registry is not None and registry.get(item.name) != item:
            refused.append((item.name, UNDECLARED_INPUT))
        elif item.outcome_proximal:
            refused.append((item.name, OUTCOME_PROXIMAL_INPUT))
        elif item.tier > claimed:
            refused.append((item.name, TIER_VIOLATION))
        else:
            admitted.append(item.name)
    return Admission(Tier(claimed), tuple(admitted), tuple(refused))


def require(inputs: Iterable[InputDeclaration], claimed: Tier,
            registry: Mapping[str, InputDeclaration] | None = None) -> Admission:
    admission = admit(inputs, claimed, registry)
    if not admission.passed:
        raise TierViolation(admission)
    return admission


def claimable_tier(inputs: Iterable[InputDeclaration]) -> Tier:
    """The lowest tier a result read from these inputs may claim (T0 when it read none)."""

    items = list(inputs)
    for item in items:
        if item.outcome_proximal:
            raise TierViolation(Admission(Tier.T2, (), ((item.name, OUTCOME_PROXIMAL_INPUT),)))
    return Tier(max((int(i.tier) for i in items), default=0))


def cold_start_violations(compounds: Iterable[str],
                          observations: Mapping[str, Collection[str]]) -> dict[str, tuple[str, ...]]:
    """Per compound, the sources holding an observed perturbation response for it."""

    out = {}
    for c in compounds:
        hits = tuple(sorted(source for source, seen in observations.items() if c in seen))
        if hits:
            out[c] = hits
    return out
