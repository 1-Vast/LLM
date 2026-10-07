"""Read public biological annotations from an explicitly supplied SQLite snapshot.

No experiment runner or research module is imported. Retrieved annotations and
derived basal RNA scores do not establish intervention efficacy or mechanism.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3


def context(db: sqlite3.Connection, sidm: str, kind: str) -> dict:
    if kind not in ("pathway", "tf"):
        raise ValueError("kind must be pathway or tf")
    release = db.execute("SELECT * FROM context_release WHERE kind=?", (kind,)).fetchone()
    rows = db.execute(
        "SELECT feature,value FROM context_activity WHERE sidm=? AND kind=? ORDER BY feature",
        (sidm, kind),
    ).fetchall()
    return {
        "sidm": sidm, "kind": kind, "status": "available" if rows else "unavailable",
        "features": [dict(row) for row in rows],
        "release": dict(release) if release else None,
        "interpretation": "Derived basal RNA activities; dynamic culture state and protein activity unverified",
    }


def drug(db: sqlite3.Connection, identifier: str) -> dict:
    rows = db.execute(
        "SELECT * FROM drug WHERE drug_id=? OR name=? ORDER BY drug_id",
        (identifier, identifier),
    ).fetchall()
    if len(rows) != 1:
        return {"query": identifier, "status": "ambiguous" if rows else "unavailable",
                "candidates": [dict(row) for row in rows]}
    identity = dict(rows[0])
    annotations = db.execute(
        "SELECT * FROM drug_target_annotation WHERE drug_id=? ORDER BY raw_target,gene",
        (identity["drug_id"],),
    ).fetchall()
    mechanisms = db.execute(
        """SELECT m.*,t.name AS target_name,t.entity_type,t.organism,
                  t.component_metadata_json
           FROM curated_drug_mechanism m LEFT JOIN chembl_target t USING(target_chembl_id)
           WHERE m.drug_id=? ORDER BY m.id""", (identity["drug_id"],),
    ).fetchall()
    chembl = db.execute("SELECT * FROM drug_identity WHERE drug_id=?", (identity["drug_id"],)).fetchone()
    return {
        "query": identifier, "status": "available", "drug": identity,
        "chembl_identity": dict(chembl) if chembl else None,
        "target_annotations": [dict(row) for row in annotations],
        "mechanisms": [dict(row) for row in mechanisms],
        "applicability": {key: None for key in ("cell", "dose", "time", "engagement")},
        "interpretation": "Curated target entities; complex components are not separate direct-binding claims",
    }


def repeat_features(db: sqlite3.Connection, sidm: str) -> dict:
    """Read the repeat study's feature catalog, never its outcome database."""
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    required = {
        "cell_context": {"SIDM", "pathway", "activity", "evidence_kind"},
        "hotspot_mutation": {"SIDM", "gene_identifier", "hotspot", "evidence_kind", "source_release"},
        "target_dependency": {"SIDM", "gene", "gene_effect", "evidence_kind", "source_release"},
    }
    if tables & {"measurement", "assay_condition", "candidate_prediction"}:
        raise ValueError("repeat_features requires a feature catalog, not experimental evidence")
    for table, columns in required.items():
        actual = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
        if not columns <= actual:
            raise ValueError(f"Incompatible feature catalog: {table} missing {sorted(columns - actual)}")
    result = {"sidm": sidm, "modalities": {}}
    for kind, table, identifier, value in (
        ("pathway", "cell_context", "pathway", "activity"),
        ("hotspot", "hotspot_mutation", "gene_identifier", "hotspot"),
        ("dependency", "target_dependency", "gene", "gene_effect"),
    ):
        rows = [dict(row) for row in db.execute(
            f"SELECT * FROM {table} WHERE SIDM=? ORDER BY {identifier}", (sidm,)
        )]
        result["modalities"][kind] = {
            "status": "available" if rows else "unavailable", "features": rows,
            "missing_values": sum(row[value] is None for row in rows),
        }
    for kind, table, expected in (
        ("pathway", "context_release", {"kind", "source_url", "source_sha256", "evidence_kind"}),
        ("dependency", "dependency_source", {"doi", "url", "source_sha256", "derived_sha256", "license"}),
    ):
        columns = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
        rows = []
        if table in tables:
            query = f"SELECT * FROM {table}"
            if kind == "pathway" and "kind" in columns:
                query += " WHERE kind='pathway'"
            rows = [dict(row) for row in db.execute(query)]
        result["modalities"][kind]["source"] = {
            "status": "available" if rows and expected <= columns else "incomplete" if rows else "unavailable",
            "records": rows, "missing_fields": sorted(expected - columns),
        }
    result["modalities"]["hotspot"]["source"] = {
        "status": "incomplete", "records": [],
        "note": "Rows preserve release labels; acquisition URL/hash/license are in the separate source receipt",
    }
    result["status"] = "available" if any(m["features"] for m in result["modalities"].values()) else "unavailable"
    result["interpretation"] = (
        "Basal pathway scores are derived; hotspot zero is not verified wild type; "
        "missing dependency is not zero effect; CRISPR knockout is not pharmacologic inhibition"
    )
    return result


def paths(db: sqlite3.Connection, source: str, target: str, hops: int, limit: int) -> dict:
    if isinstance(hops, bool) or not isinstance(hops, int) or hops not in (1, 2):
        raise ValueError("hops must be 1 or 2")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 to 100")
    # Use one bounded query instead of fetching each neighbour's outgoing edges.
    eligible = """WITH eligible AS (
        SELECT c.* FROM claim c WHERE c.usable_before_gene_conflict_check=1
        AND c.directed=1 AND c.sign IN (-1,1)
        AND NOT EXISTS (SELECT 1 FROM claim x
          WHERE x.source_gene=c.source_gene AND x.target_gene=c.target_gene
            AND x.dataset=c.dataset AND x.species IS c.species
            AND x.tissue IS c.tissue AND x.cell_line IS c.cell_line
            AND x.dose IS c.dose AND x.time IS c.time
            AND x.sign=-c.sign AND x.usable_before_gene_conflict_check=1)
    )"""
    query = """ SELECT id AS first_id,NULL AS second_id FROM eligible
                 WHERE source_gene=? AND target_gene=?"""
    parameters: list = [source, target]
    if hops == 2:
        query += """ UNION ALL SELECT a.id,b.id FROM eligible a JOIN eligible b
                     ON a.target_gene=b.source_gene
                     WHERE a.source_gene=? AND b.target_gene=? AND a.dataset='omnipath'
                       AND a.target_gene!=? AND a.source_gene!=b.target_gene"""
        parameters += [source, target, target]
    query += " ORDER BY first_id,second_id LIMIT ?"
    rows = db.execute(eligible + query, parameters + [limit + 1]).fetchall()
    result = []
    for row in rows[:limit]:
        ids = [row["first_id"]] + ([row["second_id"]] if row["second_id"] is not None else [])
        result.append([dict(db.execute("SELECT * FROM claim WHERE id=?", (i,)).fetchone()) for i in ids])
    return {
        "source": source, "target": target, "paths": result, "truncated": len(rows) > limit,
        "applicability": {key: None for key in ("cell", "dose", "time")},
        "interpretation": "Directed literature paths; no inferred drug effect or independent-evidence count",
    }


def query_snapshot(database: Path, operation: str, **arguments) -> dict:
    database = Path(database).resolve(strict=True)
    db = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA query_only=ON")
        if operation == "context":
            result = context(db, **arguments)
        elif operation == "drug":
            result = drug(db, **arguments)
        elif operation == "paths":
            result = paths(db, **arguments)
        elif operation == "repeat_features":
            result = repeat_features(db, **arguments)
        else:
            raise ValueError("operation must be context, drug, paths or repeat_features")
        result["database"] = str(database)
        return result
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    sub = parser.add_subparsers(dest="operation", required=True)
    ctx = sub.add_parser("context")
    ctx.add_argument("sidm")
    ctx.add_argument("--kind", choices=("pathway", "tf"), default="pathway")
    molecule = sub.add_parser("drug")
    molecule.add_argument("identifier")
    repeat = sub.add_parser("repeat_features", help="Read feature_catalog.sqlite; drug/paths need the earlier knowledge schema")
    repeat.add_argument("sidm")
    network = sub.add_parser("paths")
    network.add_argument("source")
    network.add_argument("target")
    network.add_argument("--hops", type=int, choices=(1, 2), default=2)
    network.add_argument("--limit", type=int, default=10)
    args = vars(parser.parse_args())
    database, operation = args.pop("database"), args.pop("operation")
    print(json.dumps(query_snapshot(database, operation, **args), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
