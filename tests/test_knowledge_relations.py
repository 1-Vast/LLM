"""Typed relations, hybrid retrieval, and per-entity support in the evidence ledger.

File summary
- Path: tests/test_knowledge_relations.py
- Purpose: Pin the hybrid (lexical + structural) retrieval and support readout contracts.
- Core points:
  - Relations require a registered type and provenance; they re-rank, never fabricate.
  - The structural term covers query entities via declared mentions or one-hop neighbours.
  - `entity_support` counts distinct sources, so repeated citations are not replication.
- Interfaces: `test_*` functions
- Depends on: agent.knowledge
"""
from pathlib import Path

import pytest

from agent.knowledge import EvidenceLedger, EvidenceStatus


def _ledger(tmp_path: Path) -> EvidenceLedger:
    return EvidenceLedger(tmp_path / "evidence.sqlite")


def test_relation_requires_a_registered_type_and_provenance(tmp_path: Path):
    ledger = _ledger(tmp_path)
    with pytest.raises(ValueError, match="relation type"):
        ledger.add_relation("GENEX", "works_with", "GENEY", source="s", context="c")
    with pytest.raises(ValueError, match="source"):
        ledger.add_relation("GENEX", "inhibition", "GENEY", source=" ", context="c")
    with pytest.raises(ValueError, match="subject and an object"):
        ledger.add_relation(" ", "inhibition", "GENEY", source="s", context="c")

    record = ledger.add_relation("GENEX", "inhibition", "GENEY", source="paper-1", context="cell-a")
    assert record.relation_type == "inhibition"


def test_structural_term_reranks_without_fabricating_matches(tmp_path: Path):
    ledger = _ledger(tmp_path)
    lexical_only = ledger.add_evidence(
        "Combination screening readouts require matched conditions.",
        source="paper-lexical",
        context="review",
        status=EvidenceStatus.RETRIEVED,
    )
    structural_only = ledger.add_evidence(
        "A measured intervention effect was reported for the pair.",
        source="paper-structural",
        context="cell-a",
        status=EvidenceStatus.RETRIEVED,
        entities=("GENEX",),
    )
    ledger.add_relation("COMPOUNDY", "inhibition", "GENEX", source="paper-structural", context="cell-a")

    plain = ledger.retrieve("combination screening", limit=2)
    assert plain[0].identifier == lexical_only.identifier

    hybrid = ledger.retrieve("combination screening", entities=("COMPOUNDY",), limit=2)
    assert hybrid[0].identifier == structural_only.identifier

    no_entities = ledger.retrieve("combination screening", entities=(), limit=2)
    assert no_entities[0].identifier == lexical_only.identifier


def test_entity_support_counts_distinct_sources_and_flags_contradictions(tmp_path: Path):
    ledger = _ledger(tmp_path)
    for _ in range(3):
        ledger.add_evidence(
            "One experiment, three cited records.",
            source="same-source",
            context="cell-a",
            status=EvidenceStatus.RETRIEVED,
            entities=("GENEX",),
        )
    ledger.add_evidence(
        "An independent confirmation.",
        source="other-source",
        context="cell-a",
        status=EvidenceStatus.RETRIEVED,
        entities=("GENEX",),
    )
    ledger.add_relation("COMPOUNDY", "inhibition", "GENEX", source="same-source", context="cell-a")
    ledger.add_relation("COMPOUNDZ", "activation", "GENEX", source="other-source", context="cell-a")
    ledger.add_relation("GENEX", "contradicts", "GENEQ", source="review-1", context="cell-a")

    support = ledger.entity_support("GENEX")
    assert support.record_count == 4
    assert support.independent_sources == 2
    assert support.has_contradiction
    assert set(support.relation_types) == {"activation", "contradicts", "inhibition"}

    quiet = ledger.entity_support("UNSEEN")
    assert quiet.record_count == 0 and quiet.independent_sources == 0 and not quiet.has_contradiction


def test_retracting_evidence_invalidates_only_its_lineage(tmp_path: Path):
    ledger = _ledger(tmp_path)
    source = ledger.add_evidence(
        "Raw target engagement result.", source="experiment-a", context="cell-a",
        status=EvidenceStatus.MEASURED, entities=("EGFR",),
    )
    derived = ledger.add_evidence(
        "Derived mechanism interpretation.", source="analysis-a", context="cell-a",
        status=EvidenceStatus.DERIVED, lineage_ids=(source.identifier,), entities=("EGFR",),
    )
    independent = ledger.add_evidence(
        "Independent dose response result.", source="experiment-b", context="cell-a",
        status=EvidenceStatus.MEASURED,
    )

    assert set(ledger.retract_evidence(source.identifier)) == {source.identifier, derived.identifier}
    found = ledger.retrieve("target engagement mechanism dose response")

    assert tuple(record.identifier for record in found) == (independent.identifier,)
    assert ledger.entity_support("EGFR").record_count == 0
