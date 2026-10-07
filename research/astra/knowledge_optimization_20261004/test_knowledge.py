"""Read-only retrieval and the supplied study's existing synthetic contracts."""
import hashlib
from pathlib import Path
import sqlite3

import pytest

from tools.datasets.biological_knowledge import query_snapshot
from research.astra.knowledge_transfer_20261004.check_invariants import Invariants
from research.astra.knowledge_transfer_20261004.context.check_context import Checks as ContextChecks
from research.astra.knowledge_transfer_20261004.interaction.check_interaction import Checks as InteractionChecks


@pytest.fixture
def snapshot(tmp_path):
    path = tmp_path / "public # snapshot.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE context_release(kind TEXT,method TEXT,source_sha256 TEXT);
        CREATE TABLE context_activity(sidm TEXT,kind TEXT,feature TEXT,value REAL);
        INSERT INTO context_release VALUES('pathway','derived RNA','source-hash');
        INSERT INTO context_activity VALUES('SIDM1','pathway','MAPK',1.2);
        CREATE TABLE drug(drug_id TEXT,name TEXT);
        CREATE TABLE drug_target_annotation(drug_id TEXT,raw_target TEXT,gene TEXT);
        CREATE TABLE drug_identity(drug_id TEXT,benchmark_structure_verified INTEGER);
        CREATE TABLE curated_drug_mechanism(id INTEGER,drug_id TEXT,target_chembl_id TEXT);
        CREATE TABLE chembl_target(target_chembl_id TEXT,name TEXT,entity_type TEXT,
          organism TEXT,component_metadata_json TEXT);
        INSERT INTO drug VALUES('1','Compound');
        INSERT INTO drug_identity VALUES('1',NULL);
        INSERT INTO curated_drug_mechanism VALUES(1,'1','TARGET');
        INSERT INTO chembl_target VALUES('TARGET','Complex','PROTEIN COMPLEX','human','["A","B"]');
        CREATE TABLE claim(id INTEGER, dataset TEXT,source_gene TEXT,target_gene TEXT,
          sign INTEGER,directed INTEGER,usable_before_gene_conflict_check INTEGER,
          species TEXT,tissue TEXT,cell_line TEXT,dose TEXT,time TEXT);
        INSERT INTO claim VALUES(1,'omnipath','A','B',1,1,1,'human',NULL,NULL,NULL,NULL);
        INSERT INTO claim VALUES(2,'collectri','A','B',-1,1,1,'human',NULL,NULL,NULL,NULL);
        INSERT INTO claim VALUES(3,'collectri','B','C',1,1,1,'human',NULL,NULL,NULL,NULL);
        INSERT INTO claim VALUES(4,'omnipath','X','Y',1,1,1,'human',NULL,NULL,NULL,NULL);
        INSERT INTO claim VALUES(5,'omnipath','X','Y',-1,1,1,'human',NULL,NULL,NULL,NULL);
        """)
    return path


def test_context_has_provenance_and_unavailable_is_not_zero(snapshot):
    before = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    result = query_snapshot(snapshot, "context", sidm="SIDM1", kind="pathway")
    assert result["features"] == [{"feature": "MAPK", "value": 1.2}]
    assert result["release"]["source_sha256"] == "source-hash"
    missing = query_snapshot(snapshot, "context", sidm="unknown", kind="pathway")
    assert missing["status"] == "unavailable" and missing["features"] == []
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == before


def test_complex_and_unknown_structure_are_preserved(snapshot):
    result = query_snapshot(snapshot, "drug", identifier="Compound")
    assert result["mechanisms"][0]["entity_type"] == "PROTEIN COMPLEX"
    assert result["chembl_identity"]["benchmark_structure_verified"] is None
    assert result["target_annotations"] == []
    assert result["applicability"]["engagement"] is None
    assert query_snapshot(snapshot, "drug", identifier="' OR 1=1 --")["status"] == "unavailable"
    with sqlite3.connect(snapshot) as db:
        db.execute("INSERT INTO drug VALUES('2','Compound')")
    assert query_snapshot(snapshot, "drug", identifier="Compound")["status"] == "ambiguous"


def test_opposite_signs_in_different_layers_are_not_conflicts(snapshot):
    result = query_snapshot(snapshot, "paths", source="A", target="B", hops=1, limit=10)
    assert {p[0]["dataset"] for p in result["paths"]} == {"omnipath", "collectri"}
    conflict = query_snapshot(snapshot, "paths", source="X", target="Y", hops=1, limit=10)
    assert conflict["paths"] == []
    composed = query_snapshot(snapshot, "paths", source="A", target="C", hops=2, limit=10)
    assert len(composed["paths"]) == 1
    assert [p["dataset"] for p in composed["paths"][0]] == ["omnipath", "collectri"]
    reverse = query_snapshot(snapshot, "paths", source="C", target="A", hops=2, limit=10)
    assert reverse["paths"] == []


def test_query_limits_and_missing_database_do_not_create_assets(snapshot, tmp_path):
    result = query_snapshot(snapshot, "paths", source="A", target="B", hops=1, limit=1)
    assert len(result["paths"]) == 1 and result["truncated"]
    with pytest.raises(ValueError):
        query_snapshot(snapshot, "paths", source="A", target="B", hops=1, limit=True)
    with pytest.raises(ValueError):
        query_snapshot(snapshot, "paths", source="A", target="B", hops=1.0, limit=1)
    missing = tmp_path / "missing.sqlite"
    with pytest.raises(FileNotFoundError):
        query_snapshot(missing, "context", sidm="SIDM1", kind="pathway")
    assert not missing.exists()
