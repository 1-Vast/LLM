import json

import pytest

from reserve_chemistry import group_records, write_once


def record(ident, smiles):
    return {"compound_id": ident, "identity_status": "KNOWN_SOURCE_STRUCTURE", "canonical_source_smiles": [smiles]}


def test_parent_salts_and_stereoisomers_never_cross_roles():
    rows, _ = group_records([record("a", "C[C@H](N)C(=O)O"), record("b", "C[C@@H](N)C(=O)O.[Na+]")])
    assert rows[0]["group_id"] == rows[1]["group_id"]
    assert rows[0]["role"] == rows[1]["role"]


def test_substitutions_with_same_ring_scaffold_stay_together():
    rows, _ = group_records([record("a", "Cc1ccccc1"), record("b", "Oc1ccccc1")])
    assert rows[0]["group_id"] == rows[1]["group_id"]


def test_input_order_cannot_change_group_or_reservation():
    data = [record("a", "CCO"), record("b", "c1ccncc1"), record("c", "C1CCCCC1")]
    assert group_records(data) == group_records(data[::-1])


def test_unknown_structure_is_retained_without_guessing():
    unknown = {"compound_id": "u", "identity_status": "QUARANTINE_STRUCTURE_MISSING", "canonical_source_smiles": []}
    rows, summary = group_records([record("a", "CCO"), unknown])
    assert len(rows) == 2
    assert rows[1]["compound_id"] == "u" and rows[1]["role"] == "quarantine"
    assert summary["role_label_counts"]["quarantine"] == 1


def test_conflicting_structure_cannot_become_development_data():
    conflict = {"compound_id": "c", "identity_status": "QUARANTINE_STRUCTURE_CONFLICT", "canonical_source_smiles": ["CCO", "CCN"]}
    rows, _ = group_records([record("a", "CCO"), conflict])
    assert rows[1]["role"] == "quarantine"


def test_existing_reservation_refuses_a_new_split(tmp_path):
    target = tmp_path / "reservation.json"
    assert write_once(target, {"role": "reserve"})
    assert not write_once(target, {"role": "reserve"})
    with pytest.raises(RuntimeError, match="refuse to overwrite"):
        write_once(target, {"role": "dev"})
    assert json.loads(target.read_text())["role"] == "reserve"
