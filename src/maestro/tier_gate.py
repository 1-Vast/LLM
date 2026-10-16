"""Strict information-tier admission: declarations are checked against a registry, provenance and the data.

File summary
- Path: src/maestro/tier_gate.py
- Purpose: close the gap in `maestro.information_tier.admit`, where the registry is optional and a declared
  tier is the caller's word, so a T1 input declared T0 is admitted. The historical module is unchanged
  (a frozen study hashes it); this is the versioned strict entry point.
- Core points:
  - `strict_admit` refuses a call without a registry (`REGISTRY_REQUIRED`), then applies the historical
    admission (`UNDECLARED_INPUT`, `OUTCOME_PROXIMAL_INPUT`, `TIER_VIOLATION`).
  - Each admitted input must also name provenance (`PROVENANCE_MISSING`) and, with a ledger, a registered
    source whose bytes still match (`PROVENANCE_UNVERIFIED:<code>`).
  - For a T0 claim, `compounds` and `observations` check the declaration against the data itself: a compound
    that appears in any source holding an observed response is refused (`COLD_START_VIOLATION:<source>`),
    whatever tier the inputs were declared at. Without `compounds` a T0 claim is `COLD_START_UNCHECKED`
    and is not admitted.
  - A declaration is still the registrant's assertion; what is checked is that it is registered, traceable to
    verified bytes, and consistent with the observed-response sets handed in.
- Interfaces: `POLICY_VERSION`, `strict_admit`, `strict_require`.
- Depends on: maestro.information_tier, maestro.evidence_registry.
"""
from __future__ import annotations

from typing import Collection, Iterable, Mapping

from maestro.evidence_registry import EvidenceLedger
from maestro.information_tier import Admission, InputDeclaration, Tier, TierViolation, admit, cold_start_violations

POLICY_VERSION = "tier-gate-1"
REGISTRY_REQUIRED = "REGISTRY_REQUIRED"
PROVENANCE_MISSING = "PROVENANCE_MISSING"
PROVENANCE_UNVERIFIED = "PROVENANCE_UNVERIFIED"
COLD_START_VIOLATION = "COLD_START_VIOLATION"
COLD_START_UNCHECKED = "COLD_START_UNCHECKED"


def strict_admit(inputs: Iterable[InputDeclaration], claimed: Tier, registry: Mapping[str, InputDeclaration] | None, *,
                 ledger: EvidenceLedger | None = None, compounds: Iterable[str] | None = None,
                 observations: Mapping[str, Collection[str]] | None = None) -> Admission:
    """Admit inputs at the claimed tier under `tier-gate-1`, or refuse each with a named reason."""

    items = list(inputs)
    if not registry:
        return Admission(Tier(claimed), (), tuple((item.name, REGISTRY_REQUIRED) for item in items) or (("*", REGISTRY_REQUIRED),))
    base = admit(items, claimed, registry)
    admitted, refused = [], list(base.refused)
    by_name = {item.name: item for item in items}
    for name in base.admitted:
        provenance = by_name[name].provenance.strip()
        if not provenance:
            refused.append((name, PROVENANCE_MISSING))
        elif ledger is not None:
            ok, why = ledger.verify_source(provenance)
            if ok:
                admitted.append(name)
            else:
                refused.append((name, f"{PROVENANCE_UNVERIFIED}:{why}"))
        else:
            admitted.append(name)
    if claimed == Tier.T0:
        if compounds is None or observations is None:
            refused.append(("*", COLD_START_UNCHECKED))
        else:
            for compound, sources in cold_start_violations(compounds, observations).items():
                refused.append((compound, f"{COLD_START_VIOLATION}:{','.join(sources)}"))
    return Admission(Tier(claimed), tuple(admitted), tuple(refused))


def strict_require(*args, **kwargs) -> Admission:
    admission = strict_admit(*args, **kwargs)
    if not admission.passed:
        raise TierViolation(admission)
    return admission
