import copy
import json

import pytest

from repair_archive import Archive, checked_evidence, digest, source_hash


def program(drug):
    return f"def choose(obs):\n    return {{'kind': 'f', 'drug': '{drug}'}}\n"


def results(drug, score=1, source=None):
    return [{"status": "ok", "error": None, "episode_id": "test-cell",
             "source_sha256": source_hash(source or program(drug)),
             "evaluation_context_sha256": digest("synthetic-fixed-episode-and-backend"),
             "yield": score, "trace": [{"kind": "f", "drug": drug}]}]


def test_inferior_branch_is_exploration_parent_and_has_winning_child():
    archive = Archive(min_gain=0.1)
    root = archive.add(program("a"), results("a", 2))["id"]
    assert archive.select_parent()["id"] == root
    inferior = archive.add(program("b"), results("b", 1), parent_id=root)["id"]
    assert not archive.promote(inferior, results("b", 1), results("a", 2))["accepted"]
    assert archive.deployed_id == root
    assert archive.select_parent()["id"] == inferior
    child = archive.add(program("c"), results("c", 3), parent_id=inferior)["id"]
    assert archive.promote(child, results("c", 3), results("a", 2))["accepted"]
    assert archive.lineage(child) == [root, inferior, child]
    assert archive.deployed_id == child
    assert archive.evaluation_count == archive.evaluated_candidates == 3


def test_restart_control_cannot_inherit_and_gate_rejects_ties():
    archive = Archive(mode="restart")
    root = archive.add(program("a"), results("a"))["id"]
    child = archive.add(program("b"), results("b"), parent_id=root)["id"]
    assert archive.select_parent()["id"] == root
    assert not archive.promote(child, results("b"), results("a"))["accepted"]
    with pytest.raises(ValueError, match="cannot inherit"):
        archive.add(program("c"), results("c", 2), parent_id=child)
    assert archive.evaluation_count == 2


@pytest.mark.parametrize("bad", [
    {"status": "error", "error": "timeout", "yield": None, "trace": []},
    {"status": "ok", "error": "runner failed", "yield": 0, "trace": []},
    {"status": "ok", "error": None, "yield": float("nan"), "trace": []},
    {"status": "ok", "error": None, "yield": -1, "trace": []},
    {"status": "ok", "error": None, "yield": True, "trace": []},
    {"status": "ok", "error": None, "yield": 1},
])
def test_invalid_never_enters_archive_or_proposer_evidence(bad):
    archive = Archive()
    with pytest.raises(ValueError):
        checked_evidence([bad])
    with pytest.raises(ValueError):
        archive.add(program("a"), [bad])
    assert not archive.nodes
    assert archive.evaluation_count == 1  # actual failed attempts still cost
    assert archive.attempts[0]["status"] == "invalid"


def test_source_and_behavior_duplicates_have_distinct_resource_accounting():
    archive = Archive()
    root = archive.add(program("a"), results("a"))["id"]
    assert not archive.needs_evaluation(program("a"))
    assert archive.add(program("a"), None)["status"] == "duplicate_source"
    assert archive.evaluation_count == 1
    with pytest.raises(ValueError, match="duplicate source"):
        archive.add(program("a"), results("a"))
    same_behavior = program("a") + "# syntactically different, same actions\n"
    answer = archive.add(same_behavior, results("a", source=same_behavior), parent_id=root)
    assert answer == {"status": "duplicate_behavior", "id": root, "accepted": False}
    assert archive.evaluation_count == 2
    assert len(archive.nodes) == 1


def test_evidence_is_copied_hashed_and_suite_checked():
    first = results("a")
    evidence = checked_evidence(first)
    first[0]["trace"][0]["drug"] = "tampered"
    assert evidence["episodes"][0]["trace"][0]["drug"] == "a"
    assert checked_evidence(results("a"))["sha256"] == evidence["sha256"]
    archive = Archive()
    root = archive.add(program("a"), results("a"))["id"]
    different = results("b")
    different[0]["episode_id"] = "another-cell"
    with pytest.raises(ValueError, match="same ordered episode"):
        archive.add(program("b"), different, parent_id=root)
    different[0]["source_sha256"] = source_hash(program("a"))
    with pytest.raises(ValueError, match="paired identical"):
        archive.promote(root, results("a"), different)


def test_saved_archive_restores_programs_lineages_counters_and_next_parent(tmp_path):
    archive = Archive(suite_id="synthetic-regression")
    root = archive.add(program("a"), results("a", 2))["id"]
    archive.select_parent()
    child = archive.add(program("b"), results("b", 1), parent_id=root)["id"]
    archive.promote(child, results("b", 1), results("a", 2))
    path = tmp_path / "archive.json"
    archive.save(path)
    restored = Archive.load(path)
    assert restored.__dict__ == archive.__dict__
    assert restored.select_parent() == archive.select_parent()
    assert restored.lineage(child) == [root, child]
    selected = restored.select_parent()
    selected["evidence"]["episodes"][0]["trace"] = []
    assert restored.nodes[selected["id"]]["evidence"]["episodes"][0]["trace"]


def test_behavior_ignores_model_versions_but_evidence_keeps_them():
    archive = Archive()
    original = results("a")
    original[0]["trace"][0]["model_before"] = "v1"
    root = archive.add(program("a"), original)["id"]
    second = copy.deepcopy(original)
    second[0]["trace"][0]["model_before"] = "v2"
    assert checked_evidence(second)["sha256"] != checked_evidence(original)["sha256"]
    source = program("a") + "# same policy\n"
    second[0]["source_sha256"] = source_hash(source)
    assert archive.add(source, second,
                       parent_id=root)["status"] == "duplicate_behavior"


def test_scores_cannot_be_attributed_to_a_different_program():
    archive = Archive()
    root = archive.add(program("a"), results("a"))["id"]
    with pytest.raises(ValueError, match="source does not match"):
        archive.add(program("b"), results("c", 3), parent_id=root)
    child = archive.add(program("d"), results("d", 2), parent_id=root)["id"]
    with pytest.raises(ValueError, match="source does not match"):
        archive.promote(child, results("c", 3), results("a"))
    with pytest.raises(ValueError, match="source does not match"):
        archive.promote(child, results("d", 2), results("c", 0))
    assert archive.deployed_id == root


def test_same_episode_ids_with_changed_backend_or_budget_cannot_be_compared():
    archive = Archive()
    root = archive.add(program("a"), results("a"))["id"]
    different = results("b")
    different[0]["evaluation_context_sha256"] = digest("different-budget")
    with pytest.raises(ValueError, match="same evaluation contexts"):
        archive.add(program("b"), different, parent_id=root)
    child = archive.add(program("c"), results("c", 2), parent_id=root)["id"]
    wrong_comparator = results("a")
    wrong_comparator[0]["evaluation_context_sha256"] = digest("different-backend")
    with pytest.raises(ValueError, match="identical evaluation contexts"):
        archive.promote(child, results("c", 2), wrong_comparator)


@pytest.mark.parametrize("corruption", ["evidence", "behavior", "parent", "generation", "score", "source"])
def test_archive_load_rejects_corrupted_records(tmp_path, corruption):
    archive = Archive()
    root = archive.add(program("a"), results("a"))["id"]
    child = archive.add(program("b"), results("b", 2), parent_id=root)["id"]
    path = tmp_path / "archive.json"
    archive.save(path)
    payload = json.loads(path.read_text())
    node = payload["nodes"][child]
    if corruption == "evidence":
        node["evidence"]["episodes"][0]["yield"] = 99
    elif corruption == "behavior":
        node["behavior_sha256"] = "0" * 64
    elif corruption == "parent":
        node["parent_id"] = child
    elif corruption == "generation":
        node["generation"] = 99
    elif corruption == "score":
        node["mean_yield"] = 99
    else:
        node["source"] = program("tampered")
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="corrupt"):
        Archive.load(path)


def test_malformed_result_mapping_and_empty_error_are_rejected():
    with pytest.raises(ValueError, match="must be an object"):
        checked_evidence([None])
    bad = results("a")
    bad[0]["error"] = ""
    with pytest.raises(ValueError, match="invalid evaluation"):
        checked_evidence(bad)
