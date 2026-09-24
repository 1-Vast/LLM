from pathlib import Path

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
