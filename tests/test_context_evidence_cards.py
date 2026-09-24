from pathlib import Path

from agent.context import ContextBuilder, TaskIntent
from agent.knowledge import EvidenceLedger, EvidenceStatus
from agent.memory import MemoryStore


def _intent() -> TaskIntent:
    return TaskIntent(
        "mechanism_diagnosis", "Resolve the EGFR discrepancy.", ("EGFR",), ("drug-x",),
        "cell-a", "viability", (), (), (), False,
    )


def test_context_packs_complete_evidence_cards_or_omits_them(tmp_path: Path):
    ledger = EvidenceLedger(tmp_path / "evidence.sqlite")
    retained = ledger.add_evidence(
        "EGFR activity changed.", source="paper-a", context="cell-a; limitations: one time point.",
        status=EvidenceStatus.RETRIEVED, entities=("EGFR",),
    )
    omitted = ledger.add_evidence(
        "A long unrelated observation " * 20, source="paper-b",
        context="cell-b; limitations: unrelated context.", status=EvidenceStatus.RETRIEVED,
    )
    builder = ContextBuilder(ledger, MemoryStore(tmp_path / "memory.sqlite"), max_characters=300)

    packet = builder.build(_intent())

    assert retained.identifier in packet.included_record_ids
    assert omitted.identifier in packet.omitted_record_ids
    assert "SOURCE: paper-a" in packet.rendered
    assert "limitations: one time point" in packet.rendered
    assert omitted.statement not in packet.rendered
    assert packet.omission_reasons == (f"{omitted.identifier}: insufficient_context_budget",)


def test_context_returns_an_explicit_error_when_mandatory_task_state_does_not_fit(tmp_path: Path):
    builder = ContextBuilder(EvidenceLedger(tmp_path / "evidence.sqlite"), MemoryStore(tmp_path / "memory.sqlite"), max_characters=12)

    packet = builder.build(_intent())

    assert packet.budget_error == "mandatory_task_state_exceeds_context_budget"
    assert packet.rendered.startswith("CONTEXT_BUDGET_INSUFFICIENT")


def test_context_build_activates_entity_aware_retrieval(tmp_path: Path):
    ledger = EvidenceLedger(tmp_path / "evidence.sqlite")
    record = ledger.add_evidence(
        "A structurally linked observation.", source="paper-a", context="cell-a",
        status=EvidenceStatus.RETRIEVED, entities=("GENE-X",),
    )
    ledger.add_relation("EGFR", "inhibition", "GENE-X", source="paper-a", context="cell-a")
    builder = ContextBuilder(ledger, MemoryStore(tmp_path / "memory.sqlite"))

    packet = builder.build(_intent())

    assert record.identifier in packet.included_record_ids
