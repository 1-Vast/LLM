from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

from agent.context import ContextBuilder, TaskIntent
from agent.knowledge import EvidenceLedger, EvidenceStatus
from agent.memory import MemoryStore
from agent.planner import MechanismContrastPlanner
from agent.tool_runtime import ToolRouter
from agent.vision import VisualInspection


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
    # Reserve space for the complete task and one atomic evidence card.
    builder = ContextBuilder(ledger, MemoryStore(tmp_path / "memory.sqlite"), max_characters=700)

    packet = builder.build(_intent())

    assert retained.identifier in packet.included_record_ids
    assert omitted.identifier in packet.omitted_record_ids
    assert "SOURCE: paper-a" in packet.rendered
    assert "limitations: one time point" in packet.rendered
    assert omitted.statement not in packet.rendered
    assert packet.omission_reasons == (f"{omitted.identifier}: insufficient_context_budget",)
    assert len(packet.rendered) <= 700


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


def test_structured_task_state_reaches_planner_and_tool_router(tmp_path: Path):
    intent = replace(
        _intent(), biological_context=None, phenotype_endpoint='viability at 48 h',
        constraints=('Public data only; no new measurements.', 'Preserve label "\u7ec6\u80de-A".'),
        evidence_gaps=('Target engagement is unmeasured.',),
        missing_information=('biological_context',), needs_visual_review=True,
    )
    packet = ContextBuilder(EvidenceLedger(tmp_path / 'e.sqlite'), MemoryStore(tmp_path / 'm.sqlite')).build(intent)

    class CaptureClient:
        def complete_json(self, messages):
            self.messages = messages
            raise RuntimeError('captured before provider call')

    client = CaptureClient()
    with pytest.raises(RuntimeError, match='captured before provider call'):
        MechanismContrastPlanner(client).propose(packet, ())
    tool_messages = ToolRouter._selection_messages(packet, (), {})
    for messages in (client.messages, tool_messages):
        rendered = messages[1]['content']
        details = json.JSONDecoder().raw_decode(rendered.split('TASK DETAILS (requested state; not measured evidence)\n', 1)[1])[0]
        assert {**details, 'research_question': intent.research_question,
                'supplied_evidence': list(intent.supplied_evidence)} == json.loads(json.dumps(asdict(intent)))
    assert intent.constraints[0] in packet.rendered
    assert '\u7ec6\u80de-A' in packet.rendered
    assert packet.evidence == ()


def test_large_constraint_refuses_instead_of_silently_disappearing(tmp_path: Path):
    intent = replace(_intent(), constraints=('Do not acquire new experimental data. ' * 40,))
    packet = ContextBuilder(EvidenceLedger(tmp_path / 'e.sqlite'), MemoryStore(tmp_path / 'm.sqlite'),
                            max_characters=1000).build(intent)
    assert packet.budget_error == 'mandatory_task_state_exceeds_context_budget'
    assert packet.rendered.startswith('CONTEXT_BUDGET_INSUFFICIENT')


def test_feedback_retains_unknowns_and_unmeasured_evidence_gaps(tmp_path: Path):
    builder = ContextBuilder(EvidenceLedger(tmp_path / 'e.sqlite'), MemoryStore(tmp_path / 'm.sqlite'))
    intent = replace(_intent(), constraints=('Public data only.',),
                     evidence_gaps=('Activity has not been measured.',))
    packet = builder.build(intent)
    updated = builder.add_visual_reviews(packet, (
        VisualInspection(Path('plot.png'), ('A trend is visible.',), (), 'Planning only.', ('Not an assay.',)),
    ))
    assert packet.rendered in updated.rendered
    assert intent.constraints[0] in updated.rendered
    assert intent.evidence_gaps[0] in updated.rendered
    assert '"needs_visual_review":false' in updated.rendered
    assert updated.evidence == ()
