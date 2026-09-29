"""Evidence cards: one statement, its epistemic class, and what it is allowed to change.

File summary
- Path: research/scientific_case_memory/evidence_cards.py
- Purpose: keep measured fact, qualified evidence, model prediction, historical analogy,
  mechanistic inference and speculation apart in the final answer, so a forecast or a precedent is
  never read as a measurement.
- Core points:
  - `EvidenceCard` names its class, its source, the action it came from, its measurement status,
    the independent units behind it, the registered interpretation rule (if any), whether the
    rule's premises were satisfied, and the limits that travel with it.
  - Only a real, QC-passed measurement whose reading a registered rule turned into an elimination
    is `qualified_evidence`. `classify` refuses to return that class for anything else, and
    `EvidenceLedger.add` raises `PromotionRefused` if a card claims it.
  - `card_from_step` maps a protocol-v2 runner step (measurement state, outcome, QC flag,
    elimination) to a card; a QC failure updates feasibility only, and a not-measured condition
    yields no card at all.
  - `EvidenceLedger.sections` groups cards by class for the answer's confidence section, and
    `abstention_reasons` lists why the ledger, as it stands, cannot support a terminal decision.
- Interfaces: `EvidenceCard`, `EvidenceLedger`, `PromotionRefused`, `classify`, `card_from_step`
- Depends on: case_schema.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from . import case_schema as S


class PromotionRefused(ValueError):
    """A card claimed a stronger class than its status permits."""


@dataclass(frozen=True)
class EvidenceCard:
    card_id: str
    evidence_class: S.EvidenceClass
    statement: str
    source: str
    action_id: str | None = None
    status: S.MeasurementStatus | None = None
    independent_units: int | None = None
    interpretation_rule: str | None = None
    premises_satisfied: bool | None = None
    eliminated: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


def classify(*, real_measurement: bool, qc_passed: bool | None, eliminated: bool, from_model: bool = False,
             from_case: bool = False, from_graph: bool = False) -> S.EvidenceClass:
    """The only place a class is chosen. Qualified evidence needs a real, QC-passed, eliminating reading."""
    if from_model:
        return S.EvidenceClass.MODEL_PREDICTION
    if from_case:
        return S.EvidenceClass.HISTORICAL_ANALOGY
    if from_graph:
        return S.EvidenceClass.MECHANISTIC_INFERENCE
    if real_measurement:
        if qc_passed is True and eliminated:
            return S.EvidenceClass.QUALIFIED_EVIDENCE
        return S.EvidenceClass.MEASURED_FACT
    return S.EvidenceClass.SPECULATION


def card_from_step(case_id: str, step: Mapping, contrast: tuple[str, str], index: int = 0) -> EvidenceCard | None:
    """A card for one executed runner step, or None when the condition was never measured."""
    state = step.get("state")
    if state == "not_measured":
        return None
    eliminated = tuple(step.get("eliminated") or ())
    qc = bool(step.get("qc"))
    if state == "quality_failed":
        return EvidenceCard(f"{case_id}:step{index}", S.EvidenceClass.MEASURED_FACT,
                            f"{step.get('action')} ran and failed its quality rule.", f"{case_id}",
                            step.get("action"), S.MeasurementStatus.QC_FAILED, 0, None, None, (),
                            ("A failed measurement updates detection feasibility only; it constrains no hypothesis.",))
    status = {"measured_undetected": S.MeasurementStatus.UNDETECTED, "measured_ambiguous": S.MeasurementStatus.AMBIGUOUS,
              "measured_eliminating": S.MeasurementStatus.QUALIFIED}[state]
    klass = classify(real_measurement=True, qc_passed=qc, eliminated=bool(eliminated))
    label = {"undetected": "no detectable response", "ambiguous": "a response that matched neither hypothesis"}.get(
        step.get("readout") or "", "a profile that removed a hypothesis" if eliminated else "a reading")
    return EvidenceCard(f"{case_id}:step{index}", klass, f"{step.get('action')} read {label}.", f"{case_id}",
                        step.get("action"), status, 1, "registered_validator", qc, eliminated,
                        ("One compound at one condition is one independent unit; it is not a replicate set.",))


@dataclass
class EvidenceLedger:
    cards: list[EvidenceCard] = field(default_factory=list)

    def add(self, card: EvidenceCard) -> EvidenceCard:
        if card.evidence_class is S.EvidenceClass.QUALIFIED_EVIDENCE:
            if card.status is not S.MeasurementStatus.QUALIFIED or not card.eliminated or card.premises_satisfied is not True:
                raise PromotionRefused(f"qualified_class_without_qualified_reading:{card.card_id}")
        if card.evidence_class in (S.EvidenceClass.MODEL_PREDICTION, S.EvidenceClass.HISTORICAL_ANALOGY,
                                   S.EvidenceClass.MECHANISTIC_INFERENCE, S.EvidenceClass.SPECULATION) and (
                card.status is not None and card.status.biological):
            raise PromotionRefused(f"non_measurement_with_measurement_status:{card.card_id}")
        self.cards.append(card)
        return card

    def sections(self) -> dict[str, list[EvidenceCard]]:
        out: dict[str, list[EvidenceCard]] = {c.value: [] for c in S.EvidenceClass}
        for card in self.cards:
            out[card.evidence_class.value].append(card)
        return out

    def qualified_eliminations(self) -> frozenset[str]:
        return frozenset(h for c in self.cards if c.evidence_class is S.EvidenceClass.QUALIFIED_EVIDENCE
                         for h in c.eliminated)

    def abstention_reasons(self, candidates: Sequence[str]) -> tuple[str, ...]:
        """Why the ledger cannot yet support a terminal decision (empty when one candidate survives)."""
        remaining = [c for c in candidates if c not in self.qualified_eliminations()]
        reasons: list[str] = []
        if len(remaining) > 1:
            reasons.append("more_than_one_hypothesis_compatible_with_qualified_evidence")
        if not remaining:
            reasons.append("every_registered_hypothesis_eliminated_explanation_set_insufficient")
        if not any(c.evidence_class is S.EvidenceClass.QUALIFIED_EVIDENCE for c in self.cards):
            reasons.append("no_qualified_evidence")
        return tuple(reasons)
