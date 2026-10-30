from pathlib import Path
import json
import random

import pytest

from agent.knowledge import ClaimVerdict, EvidenceLedger, EvidenceStatus
from agent.memory import EpistemicStatus, MemoryKind, MemoryScope, MemoryStore


def test_memory_scope_excludes_other_cases_and_unknown_legacy_scope(tmp_path: Path):
    memory = MemoryStore(tmp_path / "memory.sqlite")
    current = memory.remember(
        "EGFR functional calibration in cell-a.",
        kind=MemoryKind.EPISODIC,
        status=EpistemicStatus.MEASURED,
        provenance="result_import",
        session_id="s1",
        scope=MemoryScope(case_id="case-a", task_type="mechanism_diagnosis", dataset_partitions=("train",)),
    )
    memory.remember(
        "EGFR answer from a held-out case.",
        kind=MemoryKind.EPISODIC,
        status=EpistemicStatus.MEASURED,
        provenance="result_import",
        session_id="s2",
        scope=MemoryScope(case_id="case-b", task_type="mechanism_diagnosis", dataset_partitions=("test",)),
    )
    memory.remember(
        "EGFR legacy answer without a case boundary.",
        kind=MemoryKind.EPISODIC,
        status=EpistemicStatus.MEASURED,
        provenance="result_import",
        session_id="s3",
    )

    found = memory.search(
        "EGFR calibration",
        scope=MemoryScope(case_id="case-a", task_type="mechanism_diagnosis", dataset_partitions=("train",)),
    )

    assert tuple(item.identifier for item in found) == (current.identifier,)


def test_memory_retraction_propagates_to_derived_memories_only(tmp_path: Path):
    memory = MemoryStore(tmp_path / "memory.sqlite")
    source = memory.remember(
        "Observed target engagement.", kind=MemoryKind.EPISODIC, status=EpistemicStatus.MEASURED,
        provenance="result_import", session_id="s1",
    )
    derived = memory.remember(
        "Reflection: engagement removes one uncertainty.", kind=MemoryKind.EPISODIC,
        status=EpistemicStatus.DERIVED, provenance="reflection", session_id="s1", parent_ids=(source.identifier,),
    )
    unrelated = memory.remember(
        "Independent dose response.", kind=MemoryKind.EPISODIC, status=EpistemicStatus.MEASURED,
        provenance="result_import", session_id="s1",
    )

    assert set(memory.retract(source.identifier)) == {source.identifier, derived.identifier}
    found = memory.search("engagement dose response")

    assert tuple(item.identifier for item in found) == (unrelated.identifier,)


def test_memory_search_preserves_cjk_queries_and_origin_filters(tmp_path: Path):
    memory = MemoryStore(tmp_path / "memory.sqlite")
    chinese_query = "\u68c0\u67e5 EGFR \u529f\u80fd\u6d4b\u91cf"
    matching = memory.remember(
        chinese_query, kind=MemoryKind.SEMANTIC, status=EpistemicStatus.RETRIEVED,
        provenance="literature", session_id="s1",
    )
    memory.remember(
        chinese_query, kind=MemoryKind.SEMANTIC, status=EpistemicStatus.RETRIEVED,
        provenance="untrusted_test", session_id="s1",
    )

    found = memory.search(chinese_query, scope=MemoryScope(allowed_origins=("literature",)))

    assert tuple(item.identifier for item in found) == (matching.identifier,)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_graph_retraction_preserves_closure_for_cycles_and_multiple_parents(tmp_path, seed):
    memory = MemoryStore(tmp_path / "memory.sqlite")
    ledger = EvidenceLedger(tmp_path / "evidence.sqlite")
    generator = random.Random(seed)
    parents = {str(i): generator.sample([str(j) for j in range(30)], generator.randrange(4))
               for i in range(30)}
    # Legacy cycles and forward references are seeded directly, never qualified
    # through the public evidence ingress. Isolated records must remain active.
    parents["30"] = []
    for key in parents:
        entry = memory.remember("fixture", kind=MemoryKind.EPISODIC, status=EpistemicStatus.DERIVED,
                                provenance="fixture", session_id="s")
        with memory._connection() as connection:
            connection.execute("UPDATE memories SET id=?, parent_ids=? WHERE id=?",
                               (key, ",".join(parents[key]), entry.identifier))
        ledger.add_evidence("fixture", identifier=key, source="fixture", context="fixture",
                            status=EvidenceStatus.RETRIEVED)
    with ledger._connection() as connection:
        connection.executemany("UPDATE evidence SET lineage_ids=? WHERE id=?",
                               ((json.dumps(value), key) for key, value in parents.items()))
        connection.execute("INSERT INTO claims(id, statement, verdict, evidence_ids, rationale) "
                           "VALUES ('claim', 'fixture', ?, '[\"0\"]', 'original')",
                           (ClaimVerdict.SUPPORTED.value,))
    expected = {"0"}
    while True:
        expanded = expected | {key for key, values in parents.items() if expected.intersection(values)}
        if expanded == expected:
            break
        expected = expanded
    assert memory.retract("0") == ledger.retract_evidence("0") == tuple(sorted(expected))
    assert "30" not in expected
    with pytest.raises(ValueError, match="Unknown active memory"):
        memory.retract("0")
    assert ledger.retract_evidence("0") == tuple(sorted(expected))
    with ledger._connection() as connection:
        row = connection.execute("SELECT verdict, rationale FROM claims WHERE id='claim'").fetchone()
        assert row["verdict"] == "unknown" and row["rationale"].count("reassessment required") == 1


@pytest.mark.parametrize("bad_ancestor", ["missing", "private", "other_case", "retracted"])
def test_invisible_ancestor_excludes_all_descendants_but_not_independent_evidence(tmp_path, bad_ancestor):
    ledger = EvidenceLedger(tmp_path / "evidence.sqlite")
    ledger.add_evidence("fixture", identifier="root", source="fixture", context="fixture",
                        status=EvidenceStatus.RETRIEVED, partition="knowledge")
    for key, parent in (("child", "root"), ("grandchild", "child"), ("safe", None)):
        ledger.add_evidence("fixture", identifier=key, source="fixture", context="fixture",
                            status=EvidenceStatus.RETRIEVED, partition="knowledge",
                            lineage_ids=(parent,) if parent else ())
    with ledger._connection() as connection:
        if bad_ancestor == "missing":
            connection.execute("UPDATE evidence SET lineage_ids='[\"unknown\"]' WHERE id='root'")
        elif bad_ancestor == "private":
            connection.execute("INSERT INTO sources(id,url,locator,cluster,access_level,hash,access_note,case_id,partition,retracted) "
                               "VALUES ('private','fixture','fixture','fixture','private','hash','',NULL,'knowledge',0)")
            connection.execute("UPDATE evidence SET source='private' WHERE id='root'")
        elif bad_ancestor == "other_case":
            connection.execute("UPDATE evidence SET case_id='other', partition='train' WHERE id='root'")
        else:
            connection.execute("UPDATE evidence SET retracted=1 WHERE id='root'")
        visible = ledger._visible_evidence(connection, MemoryScope(case_id="case", dataset_partitions=("train",)))
    assert tuple(visible) == ("safe",)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_legacy_visibility_matches_fixed_point_with_cycles_and_multiple_parents(tmp_path, seed):
    ledger = EvidenceLedger(tmp_path / "evidence.sqlite")
    generator = random.Random(seed)
    parents = {str(i): generator.sample([str(j) for j in range(30)] + ["missing"], generator.randrange(4))
               for i in range(30)}
    # Existing read semantics retain closed legacy cycles. This parity test does
    # not certify them as scientific evidence or permit new cycles at ingress.
    parents.update({"closed-a": ["closed-b"], "closed-b": ["closed-a"]})
    for key in parents:
        ledger.add_evidence("fixture", identifier=key, source="fixture", context="fixture",
                            status=EvidenceStatus.RETRIEVED)
    with ledger._connection() as connection:
        connection.executemany("UPDATE evidence SET lineage_ids=? WHERE id=?",
                               ((json.dumps(value), key) for key, value in parents.items()))
        visible = ledger._visible_evidence(connection, None)
    expected = set(parents)
    while True:
        filtered = {key for key in expected if set(parents[key]) <= expected}
        if filtered == expected:
            break
        expected = filtered
    assert set(visible) == expected
    assert {"closed-a", "closed-b"} <= expected
