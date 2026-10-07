"""Read-only access contracts for the imported repeat feature catalog."""
import hashlib
import json
import sqlite3

import pytest

from tools.datasets.biological_knowledge import query_snapshot


@pytest.fixture
def catalog(tmp_path):
    path = tmp_path / "feature # catalog.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE cell_context(SIDM TEXT,pathway TEXT,activity REAL,evidence_kind TEXT);
        CREATE TABLE hotspot_mutation(SIDM TEXT,gene_identifier TEXT,hotspot REAL,
          evidence_kind TEXT,source_release TEXT);
        CREATE TABLE target_dependency(SIDM TEXT,gene TEXT,gene_effect REAL,
          evidence_kind TEXT,source_release TEXT);
        CREATE TABLE context_release(kind TEXT,source_url TEXT,source_sha256 TEXT,evidence_kind TEXT);
        CREATE TABLE dependency_source(doi TEXT,url TEXT,source_sha256 TEXT,derived_sha256 TEXT,license TEXT);
        INSERT INTO cell_context VALUES('SIDM1','MAPK',1.2,'derived basal RNA');
        INSERT INTO hotspot_mutation VALUES('SIDM1','KRAS',0,'hotspot call','release');
        INSERT INTO hotspot_mutation VALUES('SIDM1','TP53',NULL,'hotspot call','release');
        INSERT INTO target_dependency VALUES('SIDM1','KRAS',NULL,'CRISPR','release');
        INSERT INTO context_release VALUES('pathway','url','hash','derived basal RNA');
        INSERT INTO dependency_source VALUES('doi','url','source-hash','derived-hash','license');
        """)
    return path


def test_readonly_features_preserve_zero_missing_and_sources(catalog):
    before = hashlib.sha256(catalog.read_bytes()).hexdigest()
    result = query_snapshot(catalog, "repeat_features", sidm="SIDM1")
    modalities = result["modalities"]
    assert modalities["hotspot"]["features"][0]["hotspot"] == 0
    assert modalities["hotspot"]["features"][1]["hotspot"] is None
    assert modalities["hotspot"]["missing_values"] == 1
    assert modalities["dependency"]["features"][0]["gene_effect"] is None
    assert modalities["dependency"]["source"]["records"][0]["source_sha256"] == "source-hash"
    assert modalities["hotspot"]["source"]["status"] == "incomplete"
    assert "not verified wild type" in result["interpretation"]
    json.dumps(result, allow_nan=False)
    assert hashlib.sha256(catalog.read_bytes()).hexdigest() == before
    assert not list(catalog.parent.glob("*.sqlite-*"))


def test_exact_identity_and_missing_modality_are_visible(catalog):
    with sqlite3.connect(catalog) as db:
        db.execute("INSERT INTO cell_context VALUES('SIDM2','MAPK',0,'derived basal RNA')")
    result = query_snapshot(catalog, "repeat_features", sidm="SIDM2")
    assert result["status"] == "available"
    assert result["modalities"]["dependency"]["status"] == "unavailable"
    assert result["modalities"]["dependency"]["features"] == []
    assert query_snapshot(catalog, "repeat_features", sidm="' OR 1=1 --")["status"] == "unavailable"


def test_partial_source_schema_preserves_records_and_reports_gaps(catalog):
    with sqlite3.connect(catalog) as db:
        db.execute("DROP TABLE dependency_source")
        db.execute("CREATE TABLE dependency_source(doi TEXT)")
        db.execute("INSERT INTO dependency_source VALUES('known-doi')")
        db.execute("DROP TABLE context_release")
    result = query_snapshot(catalog, "repeat_features", sidm="SIDM1")["modalities"]
    assert result["dependency"]["source"]["status"] == "incomplete"
    assert result["dependency"]["source"]["records"] == [{"doi": "known-doi"}]
    assert "source_sha256" in result["dependency"]["source"]["missing_fields"]
    assert result["pathway"]["source"]["status"] == "unavailable"


def test_outcome_and_incompatible_databases_are_rejected(catalog):
    with sqlite3.connect(catalog) as db:
        db.execute("CREATE TABLE candidate_prediction(ranking_score REAL)")
    with pytest.raises(ValueError, match="not experimental evidence"):
        query_snapshot(catalog, "repeat_features", sidm="SIDM1")
    with sqlite3.connect(catalog) as db:
        db.execute("DROP TABLE candidate_prediction")
        db.execute("DROP TABLE hotspot_mutation")
    with pytest.raises(ValueError, match="Incompatible feature catalog"):
        query_snapshot(catalog, "repeat_features", sidm="SIDM1")
