import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location("knowledge_benchmark", Path(__file__).with_name("benchmark.py"))
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def fixture():
    records = [dict(drug=str(i), cid=str(i), smiles="C"*(i+1), kg_exact_identity=i < 3,
                    edges=[dict(gene="G", direction=direction, relation=direction, source_row=i)] if i < 3 else [])
               for i, direction in enumerate(["inhibit", "activate", "unknown", "bind", "bind", "bind", "bind"])]
    features = dict(molecule256=np.eye(7), knowledge1024=np.eye(7))
    records.append({**records[0], "drug": "dose_duplicate"})
    features = {key: np.concatenate([value, value[:1]]) for key, value in features.items()}
    return records, features


def test_direction_labels_remain_separate_and_unknown_is_not_negative():
    records, features = fixture()
    assert study.labels(records[0]) == ({"G"}, {("inhibit", "G")})
    assert study.labels(records[2]) == ({"G"}, set())
    result = study.benchmark(records, features)
    assert result["summary"]["knowledge1024"]["gene_queries"] == 3
    assert result["summary"]["knowledge1024"]["typed_queries"] == 2
    row = next(row for row in result["results"] if row["cid"] == "0" and row["arm"] == "knowledge1024")
    assert row["gene_known_hit_at5"] and not row["typed_known_hit_at5"]
    assert row["opposing_mode_gene_annotations"] == 1 and row["unlabeled_neighbors"] > 0
    agonist = {**records[0], "edges": [dict(gene="G", direction="agonist")]}
    assert study.labels(agonist)[1] == {("agonist", "G")}


def test_all_doses_exclude_self_and_full_unmapped_gallery_stays():
    records, features = fixture(); before = features["knowledge1024"].copy()
    result = study.benchmark(records, features)
    assert result["menu_rows"] == 8 and result["gallery_structures"] == 7
    for row in result["results"]:
        assert len(row["neighbors"]) == 5 and all(n["cid"] != row["cid"] for n in row["neighbors"])
    np.testing.assert_array_equal(features["knowledge1024"], before)
    features["knowledge1024"][-1, 0] += 1
    with pytest.raises(ValueError, match="dose_features"):
        study.benchmark(records, features)


def test_permutation_and_morgan_structure_baseline_are_deterministic():
    records, features = fixture()
    first, second = study.benchmark(records, features), study.benchmark(records, features)
    assert first["permutation"] == second["permutation"] and first["results"] == second["results"]
    assert "morgan2048" in first["summary"]
    assert any(n["cosine"] > 0 for row in first["results"] if row["arm"] == "morgan2048" for n in row["neighbors"])


def test_missing_label_sets_never_become_evaluation_negatives():
    records, features = fixture()
    for record in records:
        record["edges"] = []
    result = study.benchmark(records, features)
    assert result["results"] == [] and result["gallery_structures"] == 7
    assert result["summary"]["knowledge1024"]["gene_known_hit_at5"] is None


def test_audit_preserves_relation_modes_and_does_not_infer_assay_polarity():
    spec = importlib.util.spec_from_file_location("map_content_audit", Path(__file__).with_name("audit.py"))
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    assert audit.direction("functions as an inhibitor on the protein target") == "inhibit"
    assert audit.direction("functions as an agonist on the protein target") == "agonist"
    assert audit.direction("functions as an antagonist on the protein target") == "antagonist"
    assert audit.direction("binds to the protein target") == "bind"
    assert audit.direction("Inhibition of recombinant MMP2 after 30 mins; IC50") == "unknown"


def test_direction_predicates_and_source_row_lineage():
    spec = importlib.util.spec_from_file_location("knowledge_audit", Path(__file__).with_name("audit.py"))
    audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
    assert audit.direction("functions as an inhibitor on the protein target") == "inhibit"
    assert audit.direction("binds to the protein target") == "bind"
    assert audit.direction("functions as an agonist on the protein target") == "agonist"
    assert audit.direction("functions as an antagonist on the protein target") == "antagonist"
    assert audit.direction("Inhibition of human ERG assessed by patch clamp assay") == "unknown"
    assert audit.direction("Binding affinity IC50 against a target") == "unknown"
    records, features = fixture()
    result = study.benchmark(records, features)
    row = next(row for row in result["results"] if row["cid"] == "0" and row["arm"] == "knowledge1024")
    neighbor = next(n for n in row["neighbors"] if n["cid"] == "1")
    assert neighbor["annotation_source_rows"] == ["1"]
