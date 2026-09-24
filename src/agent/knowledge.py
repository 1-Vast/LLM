"""SQLite evidence ledger with source provenance, scope and retraction lineage."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from maestro.models import EvidenceKind
from .memory import MemoryScope, _lexical_score, _terms


class EvidenceStatus(str, Enum):
    RETRIEVED = "retrieved"
    MEASURED = "measured"
    DERIVED = "derived"
    PREDICTED = "predicted"
    UNVERIFIED = "unverified"


class ClaimVerdict(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    REFUTED = "refuted"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SourceRecord:
    identifier: str
    url: str
    locator: str
    cluster: str
    access_level: str
    hash: str
    access_note: str = ""
    case_id: str | None = None
    partition: str = "knowledge"
    retracted: bool = False


@dataclass(frozen=True)
class EvidenceRecord:
    identifier: str
    statement: str
    source: str
    context: str
    status: EvidenceStatus
    created_at: str
    evidence_kind: EvidenceKind
    lineage_ids: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()
    retracted: bool = False
    case_id: str | None = None
    partition: str = "unscoped"
    source_lineage_ids: tuple[str, ...] = ()
    payload: Mapping[str, Any] = field(default_factory=dict)


RELATION_TYPES: frozenset[str] = frozenset({
    "coexpression", "functional_similarity", "physical_binding", "inhibition",
    "activation", "complex_membership", "measured_intervention_effect", "contradicts",
})


@dataclass(frozen=True)
class RelationRecord:
    identifier: str
    subject: str
    relation_type: str
    object: str
    source: str
    context: str
    created_at: str
    case_id: str | None = None
    partition: str = "unscoped"


@dataclass(frozen=True)
class EntitySupport:
    entity: str
    record_count: int
    independent_sources: int
    relation_types: tuple[str, ...]
    relation_count: int
    has_contradiction: bool


@dataclass(frozen=True)
class ClaimRecord:
    identifier: str
    statement: str
    verdict: ClaimVerdict
    evidence_ids: tuple[str, ...]
    rationale: str
    case_id: str | None = None
    partition: str = "unscoped"


def status_for_kind(kind: EvidenceKind) -> EvidenceStatus:
    if kind is EvidenceKind.REAL_MEASUREMENT:
        return EvidenceStatus.MEASURED
    if kind in {EvidenceKind.MODEL_PREDICTION, EvidenceKind.PREDICTION_DERIVED_ANALYSIS}:
        return EvidenceStatus.PREDICTED
    if kind is EvidenceKind.DERIVED_ANALYSIS:
        return EvidenceStatus.DERIVED
    if kind is EvidenceKind.RETRIEVED_SOURCE:
        return EvidenceStatus.RETRIEVED
    return EvidenceStatus.UNVERIFIED


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def _ids(value: str) -> tuple[str, ...]:
    # Read legacy comma-separated fields; JSON preserves commas inside new identifiers.
    return tuple(json.loads(value)) if value.startswith("[") else tuple(filter(None, value.split(",")))


def _boundary(case_id: str | None, partition: str | None) -> tuple[str | None, str]:
    if case_id is not None and not case_id.strip():
        raise ValueError("case_id must not be blank.")
    case_id = case_id.strip() if case_id is not None else None
    partition = partition if partition is not None else ("case" if case_id else "unscoped")
    if not partition or partition != partition.strip():
        raise ValueError("partition must be a nonempty canonical identifier.")
    if partition == "knowledge" and case_id is not None:
        raise ValueError("Knowledge must not belong to a case.")
    if partition not in {"knowledge", "unscoped", "private"} and case_id is None:
        raise ValueError("A dataset partition requires case_id.")
    return case_id, partition


def _visible(case_id: str | None, partition: str, scope: MemoryScope | None) -> bool:
    # Evidence isolation is independent of allow_cross_case; register general knowledge explicitly.
    if partition == "private":
        return False
    if partition == "knowledge":
        return case_id is None
    if case_id is None:
        return scope is None or (scope.case_id is None and not scope.dataset_partitions)
    if scope is None or scope.case_id != case_id:
        return False
    return partition == "case" or partition in scope.dataset_partitions


def _evidence(row: sqlite3.Row) -> EvidenceRecord:
    return EvidenceRecord(
        row["id"], row["statement"], row["source"], row["context"], EvidenceStatus(row["status"]),
        row["created_at"], EvidenceKind(row["evidence_kind"]), _ids(row["lineage_ids"]),
        _ids(row["entities"]), bool(row["retracted"]), row["case_id"], row["partition"],
        _ids(row["source_lineage_ids"]), json.loads(row["payload_json"]),
    )


def _source(row: sqlite3.Row) -> SourceRecord:
    data = dict(row)
    data["identifier"] = data.pop("id")
    data["retracted"] = bool(data["retracted"])
    return SourceRecord(**data)


class EvidenceLedger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def register_source(
        self, identifier: str, *, url: str, locator: str, cluster: str,
        access_level: str, hash: str, access_note: str = "",
        case_id: str | None = None, partition: str = "knowledge",
    ) -> SourceRecord:
        """Source identities are immutable; hashes identify declared material, not fetched remote text."""
        case_id, partition = _boundary(case_id, partition)
        record = SourceRecord(identifier, url, locator, cluster, access_level, hash,
                              access_note, case_id, partition)
        with self._connection() as connection:
            return self._register_source(connection, record)

    def _register_source(self, connection: sqlite3.Connection, record: SourceRecord) -> SourceRecord:
        for name in ("identifier", "url", "locator", "cluster", "access_level", "hash"):
            value = getattr(record, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Source {name} is required.")
        if len(record.hash) != 64 or any(c not in "0123456789abcdef" for c in record.hash):
            raise ValueError("Source hash must be a lowercase SHA-256 digest.")
        existing = connection.execute("SELECT * FROM sources WHERE id = ?", (record.identifier,)).fetchone()
        if existing:
            old = _source(existing)
            if asdict(old) | {"retracted": False} != asdict(record):
                raise ValueError(f"Source identifier conflict: {record.identifier}")
            return old
        data = asdict(record)
        data["id"] = data.pop("identifier")
        connection.execute(
            f"INSERT INTO sources ({','.join(data)}) VALUES ({','.join('?' for _ in data)})",
            tuple(data.values()),
        )
        return record

    def get_source(self, identifier: str, *, scope: MemoryScope | None = None) -> SourceRecord | None:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM sources WHERE id = ?", (identifier,)).fetchone()
        if row and not row["retracted"] and row["access_level"] != "private" and _visible(row["case_id"], row["partition"], scope):
            return _source(row)
        return None

    def add_evidence(
        self, statement: str, *, source: str, context: str, status: EvidenceStatus,
        evidence_kind: EvidenceKind | None = None, lineage_ids: tuple[str, ...] = (),
        entities: tuple[str, ...] = (), case_id: str | None = None, partition: str | None = None,
        source_lineage_ids: tuple[str, ...] = (), payload: Mapping[str, Any] | None = None,
        identifier: str | None = None,
    ) -> EvidenceRecord:
        """Explicit kind must match status; legacy callers retain their declared status."""
        status = EvidenceStatus(status)
        if evidence_kind is None:
            evidence_kind = {
                EvidenceStatus.RETRIEVED: EvidenceKind.RETRIEVED_SOURCE,
                EvidenceStatus.MEASURED: EvidenceKind.REAL_MEASUREMENT,
                EvidenceStatus.DERIVED: EvidenceKind.DERIVED_ANALYSIS,
                EvidenceStatus.PREDICTED: EvidenceKind.MODEL_PREDICTION,
                EvidenceStatus.UNVERIFIED: EvidenceKind.LEGACY_UNCLASSIFIED,
            }[status]
        evidence_kind = EvidenceKind(evidence_kind)
        if status != status_for_kind(evidence_kind):
            raise ValueError("Evidence status must match evidence_kind.")
        case_id, partition = _boundary(case_id, partition)
        if partition == "knowledge" and evidence_kind is not EvidenceKind.RETRIEVED_SOURCE:
            raise ValueError("Knowledge must remain retrieved_source, never a case measurement.")
        record = EvidenceRecord(
            identifier or str(uuid.uuid4()), statement.strip(), source.strip(), context.strip(), status,
            datetime.now(timezone.utc).isoformat(), evidence_kind, tuple(dict.fromkeys(lineage_ids)),
            tuple(dict.fromkeys(e.strip() for e in entities if e.strip())), False, case_id, partition,
            tuple(dict.fromkeys(source_lineage_ids)), json.loads(_json(dict(payload or {}))),
        )
        with self._connection() as connection:
            return self._insert_evidence(connection, record)

    def _insert_evidence(self, connection: sqlite3.Connection, record: EvidenceRecord) -> EvidenceRecord:
        if not record.statement or not record.source:
            raise ValueError("Evidence records require a statement and source identifier.")
        existing = connection.execute("SELECT * FROM evidence WHERE id = ?", (record.identifier,)).fetchone()
        if existing:
            old = _evidence(existing)
            if asdict(old) | {"created_at": record.created_at, "retracted": False} != asdict(record):
                raise ValueError(f"Evidence identifier conflict: {record.identifier}")
            return old
        for parent_id in record.lineage_ids:
            row = connection.execute("SELECT * FROM evidence WHERE id = ?", (parent_id,)).fetchone()
            if row is None or row["retracted"]:
                raise ValueError(f"Unknown or retracted evidence lineage: {parent_id}")
            self._check_parent(record, row)
            if record.evidence_kind is EvidenceKind.REAL_MEASUREMENT and row["evidence_kind"] != EvidenceKind.REAL_MEASUREMENT.value:
                raise ValueError("Non-measured lineage cannot become a real measurement.")
            if record.evidence_kind is EvidenceKind.DERIVED_ANALYSIS and status_for_kind(EvidenceKind(row["evidence_kind"])) is EvidenceStatus.PREDICTED:
                raise ValueError("Prediction lineage requires prediction_derived_analysis.")
        for source_id in dict.fromkeys((record.source, *record.source_lineage_ids)):
            row = connection.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
            if row is None:
                if source_id in record.source_lineage_ids:
                    raise ValueError(f"Unknown source lineage: {source_id}")
                continue
            if row["retracted"]:
                raise ValueError(f"Retracted source: {source_id}")
            self._check_parent(record, row)
            if row["access_level"] == "private" and record.partition != "private":
                raise ValueError("Private source cannot enter agent evidence.")
            if row["partition"] == "knowledge" and record.evidence_kind is EvidenceKind.REAL_MEASUREMENT:
                raise ValueError("Literature cannot become a case measurement.")
        connection.execute(
            """INSERT INTO evidence(id, statement, source, context, status, created_at, evidence_kind,
               lineage_ids, entities, retracted, case_id, partition, source_lineage_ids, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record.identifier, record.statement, record.source, record.context, record.status.value,
             record.created_at, record.evidence_kind.value, _json(record.lineage_ids), _json(record.entities),
             record.retracted, record.case_id, record.partition, _json(record.source_lineage_ids), _json(record.payload)),
        )
        return record

    @staticmethod
    def _check_parent(record: EvidenceRecord, parent: sqlite3.Row) -> None:
        if parent["partition"] == "knowledge":
            return
        if parent["case_id"] != record.case_id or parent["partition"] != record.partition:
            raise ValueError("Lineage cannot cross case or partition boundaries.")

    def load_knowledge_package(self, path: Path) -> tuple[EvidenceRecord, ...]:
        """Load a local JSON package atomically and idempotently; changed contents need a new package_id."""
        package = json.loads(Path(path).read_text(encoding="utf-8"))
        if package.get("schema_version") != "1.0" or not package.get("package_id"):
            raise ValueError("Knowledge package requires schema_version 1.0 and package_id.")
        digest = hashlib.sha256(_json(package).encode()).hexdigest()
        records = []
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            old = connection.execute("SELECT hash FROM knowledge_packages WHERE id = ?", (package["package_id"],)).fetchone()
            if old and old["hash"] != digest:
                raise ValueError("Knowledge package identifier conflict; use a new version.")
            source_ids = set()
            source_details = {}
            for item in package["sources"]:
                source = SourceRecord(**item)
                _boundary(source.case_id, source.partition)
                if source.case_id is not None or source.partition not in {"knowledge", "private"} or source.retracted:
                    raise ValueError("Knowledge package cannot import case sources.")
                if source.identifier in source_ids:
                    raise ValueError("Duplicate source identifier in knowledge package.")
                source_ids.add(source.identifier)
                source_details[source.identifier] = asdict(source)
                self._register_source(connection, source)
            entry_ids = set()
            for item in package["constraints"]:
                if item["id"] in entry_ids:
                    raise ValueError("Duplicate constraint identifier in knowledge package.")
                entry_ids.add(item["id"])
                refs = tuple(item["source_ids"])
                if not refs or not set(refs).issubset(source_ids):
                    raise ValueError("Constraint requires registered package source lineage.")
                if item.get("evidence_kind", "retrieved_source") != "retrieved_source" or item.get("status", "retrieved") != "retrieved":
                    raise ValueError("Knowledge constraints must remain retrieved_source.")
                if item.get("case_id") is not None or item.get("partition", "knowledge") != "knowledge":
                    raise ValueError("Knowledge constraints cannot carry case scope.")
                record = EvidenceRecord(
                    "knowledge:" + str(uuid.uuid5(uuid.NAMESPACE_URL, _json([package["package_id"], item["id"]]))),
                    item["statement"].strip(), refs[0],
                    "General literature constraint; not a measurement of this case. " + item["limitations"],
                    EvidenceStatus.RETRIEVED, datetime.now(timezone.utc).isoformat(), EvidenceKind.RETRIEVED_SOURCE,
                    entities=tuple(item.get("entities", ())), partition="knowledge", source_lineage_ids=refs,
                    payload={"package_id": package["package_id"], "constraint": item,
                             "sources": [source_details[ref] for ref in refs]},
                )
                records.append(self._insert_evidence(connection, record))
            connection.execute("INSERT OR IGNORE INTO knowledge_packages(id, hash) VALUES (?, ?)", (package["package_id"], digest))
        return tuple(records)

    def _visible_evidence(self, connection: sqlite3.Connection, scope: MemoryScope | None) -> dict[str, EvidenceRecord]:
        sources = {row["id"]: row for row in connection.execute("SELECT * FROM sources")}
        records = {}
        for row in connection.execute("SELECT * FROM evidence WHERE retracted = 0"):
            record = _evidence(row)
            if not _visible(record.case_id, record.partition, scope):
                continue
            if any(ref in sources and (sources[ref]["retracted"] or sources[ref]["access_level"] == "private"
                   or not _visible(sources[ref]["case_id"], sources[ref]["partition"], scope))
                   for ref in (record.source, *record.source_lineage_ids)):
                continue
            if any(ref not in sources for ref in record.source_lineage_ids):
                continue
            records[record.identifier] = record
        # Filter unverifiable or out-of-scope legacy lineage on reads as well.
        while True:
            invalid = [key for key, record in records.items() if any(parent not in records for parent in record.lineage_ids)]
            if not invalid:
                return records
            for key in invalid:
                del records[key]

    def get_evidence(self, identifier: str, *, scope: MemoryScope | None = None) -> EvidenceRecord | None:
        with self._connection() as connection:
            return self._visible_evidence(connection, scope).get(identifier)

    def retrieve(
        self, query: str, *, entities: tuple[str, ...] = (), structural_weight: float = 1.0,
        limit: int = 8, scope: MemoryScope | None = None,
    ) -> tuple[EvidenceRecord, ...]:
        with self._connection() as connection:
            records = self._visible_evidence(connection, scope).values()
            edges = self._visible_relations(connection, scope)
        neighbours: dict[str, set[str]] = {}
        for edge in edges:
            neighbours.setdefault(edge["subject"], set()).add(edge["object"])
            neighbours.setdefault(edge["object"], set()).add(edge["subject"])
        terms = set(_terms(query))
        query_entities = {entity.strip() for entity in entities if entity.strip()}
        scored = []
        for record in records:
            score = _lexical_score(terms, record.statement + " " + record.context)
            score += structural_weight * _structural_score(query_entities, set(record.entities), neighbours)
            if score > 0:
                scored.append((score, record))
        scored.sort(key=lambda item: (item[0], item[1].created_at, item[1].identifier), reverse=True)
        return tuple(record for _, record in scored[:max(0, limit)])

    def retract_evidence(self, identifier: str) -> tuple[str, ...]:
        with self._connection() as connection:
            if not connection.execute("SELECT id FROM evidence WHERE id = ?", (identifier,)).fetchone():
                raise ValueError(f"Unknown evidence: {identifier}")
            return self._retract(connection, {identifier})

    def retract_source(self, identifier: str) -> tuple[str, ...]:
        with self._connection() as connection:
            if not connection.execute("SELECT id FROM sources WHERE id = ?", (identifier,)).fetchone():
                raise ValueError(f"Unknown source: {identifier}")
            connection.execute("UPDATE sources SET retracted = 1 WHERE id = ?", (identifier,))
            seeds = {row["id"] for row in connection.execute("SELECT * FROM evidence")
                     if identifier in (row["source"], *_ids(row["source_lineage_ids"]))}
            return self._retract(connection, seeds)

    @staticmethod
    def _retract(connection: sqlite3.Connection, affected: set[str]) -> tuple[str, ...]:
        rows = connection.execute("SELECT id, lineage_ids FROM evidence").fetchall()
        while True:
            children = {row["id"] for row in rows if set(_ids(row["lineage_ids"])) & affected}
            if children <= affected:
                break
            affected |= children
        connection.executemany("UPDATE evidence SET retracted = 1 WHERE id = ?", ((key,) for key in affected))
        for row in connection.execute("SELECT * FROM claims").fetchall():
            if set(_ids(row["evidence_ids"])) & affected and row["verdict"] != ClaimVerdict.UNKNOWN.value:
                connection.execute("UPDATE claims SET verdict = ?, rationale = ? WHERE id = ?",
                                   (ClaimVerdict.UNKNOWN.value, row["rationale"] + " [Evidence retracted; reassessment required.]", row["id"]))
        return tuple(sorted(affected))

    def add_relation(
        self, subject: str, relation_type: str, object_: str, *, source: str, context: str,
        case_id: str | None = None, partition: str | None = None,
    ) -> RelationRecord:
        if not subject.strip() or not object_.strip():
            raise ValueError("Relation records require both a subject and an object.")
        if relation_type not in RELATION_TYPES:
            raise ValueError(f"Unregistered relation type: {relation_type}")
        if not source.strip():
            raise ValueError("Relation records require a source identifier.")
        case_id, partition = _boundary(case_id, partition)
        record = RelationRecord(str(uuid.uuid4()), subject.strip(), relation_type, object_.strip(),
                                source.strip(), context.strip(), datetime.now(timezone.utc).isoformat(), case_id, partition)
        with self._connection() as connection:
            connection.execute("INSERT INTO relations(id, subject, relation_type, object, source, context, created_at, case_id, partition) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(asdict(record).values()))
        return record

    def _visible_relations(self, connection: sqlite3.Connection, scope: MemoryScope | None) -> list[sqlite3.Row]:
        sources = {row["id"]: row for row in connection.execute("SELECT * FROM sources")}
        evidence_ids = {row["id"] for row in connection.execute("SELECT id FROM evidence")}
        active = self._visible_evidence(connection, scope)
        return [row for row in connection.execute("SELECT * FROM relations")
                if _visible(row["case_id"], row["partition"], scope)
                and (row["source"] not in evidence_ids or row["source"] in active)
                and (row["source"] not in sources or (
                    not sources[row["source"]]["retracted"] and sources[row["source"]]["access_level"] != "private"
                    and _visible(sources[row["source"]]["case_id"], sources[row["source"]]["partition"], scope)))]

    def entity_support(self, entity: str, *, scope: MemoryScope | None = None) -> EntitySupport:
        """Deduplicate source clusters; their count is not a validated biological replicate count."""
        entity = entity.strip()
        with self._connection() as connection:
            records = [r for r in self._visible_evidence(connection, scope).values() if entity in r.entities]
            edges = [r for r in self._visible_relations(connection, scope) if entity in (r["subject"], r["object"])]
            clusters = {r["id"]: r["cluster"] for r in connection.execute("SELECT id, cluster FROM sources")}
        pairs: dict[tuple[str, str], set[str]] = {}
        for edge in edges:
            pairs.setdefault((edge["subject"], edge["object"]), set()).add(edge["relation_type"])
        types = {row["relation_type"] for row in edges}
        return EntitySupport(entity, len(records), len({clusters.get(r.source, r.source) for r in records}),
                             tuple(sorted(types)), len(edges), "contradicts" in types or any(
                                 {"inhibition", "activation"} <= values for values in pairs.values()))

    def ingest_text(
        self, text: str, *, source: str, context: str, status: EvidenceStatus = EvidenceStatus.RETRIEVED,
        chunk_size: int = 1_200, case_id: str | None = None, partition: str | None = None,
    ) -> tuple[EvidenceRecord, ...]:
        if chunk_size < 200:
            raise ValueError("chunk_size must be at least 200 characters.")
        if status != EvidenceStatus.RETRIEVED:
            raise ValueError("Ingested text must remain retrieved_source.")
        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            candidate = (current + "\n\n" + paragraph).strip() if current else paragraph
            if len(candidate) <= chunk_size:
                current = candidate
                continue
            if current:
                chunks.append(current)
            while len(paragraph) > chunk_size:
                chunks.append(paragraph[:chunk_size])
                paragraph = paragraph[chunk_size:]
            current = paragraph
        if current:
            chunks.append(current)
        return tuple(self.add_evidence(chunk, source=source, context=f"{context} [chunk {index}/{len(chunks)}]",
                                       status=status, evidence_kind=EvidenceKind.RETRIEVED_SOURCE,
                                       case_id=case_id, partition=partition)
                     for index, chunk in enumerate(chunks, start=1))

    def record_claim(
        self, statement: str, *, verdict: ClaimVerdict, evidence_ids: tuple[str, ...], rationale: str,
        case_id: str | None = None, partition: str | None = None,
    ) -> ClaimRecord:
        case_id, partition = _boundary(case_id, partition)
        verdict = ClaimVerdict(verdict)
        scope = MemoryScope(case_id=case_id, dataset_partitions=(partition,)) if case_id else None
        with self._connection() as connection:
            visible = self._visible_evidence(connection, scope)
            if any(key not in visible for key in evidence_ids):
                raise ValueError("Claim requires active evidence within its scope.")
            if verdict is not ClaimVerdict.UNKNOWN and not evidence_ids:
                raise ValueError("A non-unknown verdict requires evidence.")
            for key in evidence_ids:
                parent = visible[key]
                if parent.partition != "knowledge" and (parent.case_id, parent.partition) != (case_id, partition):
                    raise ValueError("Claim cannot cross case or partition boundaries.")
            record = ClaimRecord(str(uuid.uuid4()), statement.strip(), verdict, tuple(dict.fromkeys(evidence_ids)), rationale.strip(), case_id, partition)
            connection.execute("INSERT INTO claims(id, statement, verdict, evidence_ids, rationale, case_id, partition) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (record.identifier, record.statement, verdict.value, _json(record.evidence_ids), record.rationale, case_id, partition))
        return record

    def get_claim(self, identifier: str, *, scope: MemoryScope | None = None) -> ClaimRecord | None:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM claims WHERE id = ?", (identifier,)).fetchone()
            if row is None or not _visible(row["case_id"], row["partition"], scope):
                return None
            refs = _ids(row["evidence_ids"])
            visible = self._visible_evidence(connection, scope)
            # Retain retracted references for audit; hide unauthorized references and their claims.
            for key in refs:
                parent = connection.execute("SELECT * FROM evidence WHERE id = ?", (key,)).fetchone()
                if parent is None or not _visible(parent["case_id"], parent["partition"], scope):
                    return None
            verdict = ClaimVerdict(row["verdict"]) if all(key in visible for key in refs) else ClaimVerdict.UNKNOWN
            return ClaimRecord(row["id"], row["statement"], verdict, refs, row["rationale"], row["case_id"], row["partition"])

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY, statement TEXT NOT NULL, source TEXT NOT NULL,
                context TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL)""")
            connection.execute("""CREATE TABLE IF NOT EXISTS relations (
                id TEXT PRIMARY KEY, subject TEXT NOT NULL, relation_type TEXT NOT NULL,
                object TEXT NOT NULL, source TEXT NOT NULL, context TEXT NOT NULL, created_at TEXT NOT NULL)""")
            connection.execute("""CREATE TABLE IF NOT EXISTS claims (
                id TEXT PRIMARY KEY, statement TEXT NOT NULL, verdict TEXT NOT NULL,
                evidence_ids TEXT NOT NULL, rationale TEXT NOT NULL)""")
            additions = {
                "evidence": {"evidence_kind": "TEXT NOT NULL DEFAULT 'legacy_unclassified'",
                             "lineage_ids": "TEXT NOT NULL DEFAULT ''", "entities": "TEXT NOT NULL DEFAULT ''",
                             "retracted": "INTEGER NOT NULL DEFAULT 0", "source_lineage_ids": "TEXT NOT NULL DEFAULT '[]'",
                             "payload_json": "TEXT NOT NULL DEFAULT '{}'"},
                "relations": {}, "claims": {},
            }
            for table, fields in additions.items():
                columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
                for name, definition in (fields | {"case_id": "TEXT", "partition": "TEXT NOT NULL DEFAULT 'unscoped'"}).items():
                    if name not in columns:
                        connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
            connection.execute("""CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY, url TEXT NOT NULL, locator TEXT NOT NULL, cluster TEXT NOT NULL,
                access_level TEXT NOT NULL, hash TEXT NOT NULL, access_note TEXT NOT NULL DEFAULT '',
                case_id TEXT, partition TEXT NOT NULL DEFAULT 'knowledge', retracted INTEGER NOT NULL DEFAULT 0)""")
            connection.execute("CREATE TABLE IF NOT EXISTS knowledge_packages (id TEXT PRIMARY KEY, hash TEXT NOT NULL)")
            for kind in EvidenceKind:
                connection.execute("UPDATE evidence SET status = ? WHERE evidence_kind = ? AND status != ?",
                                   (status_for_kind(kind).value, kind.value, status_for_kind(kind).value))

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection


KnowledgeBase = EvidenceLedger


def _structural_score(query_entities: set[str], record_entities: set[str], neighbours: Mapping[str, set[str]]) -> float:
    if not query_entities:
        return 0.0
    return sum(entity in record_entities or bool(record_entities & neighbours.get(entity, set()))
               for entity in query_entities) / len(query_entities)
