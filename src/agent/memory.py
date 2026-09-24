"""Persistent working, episodic, and semantic memory with explicit epistemic status.

File summary
- Path: src/agent/memory.py
- Purpose: Store and retrieve experience while keeping each entry's epistemic status.
- Core points:
  - `MemoryStore` retrieves experience without upgrading it to a real measurement result.
  - Each entry keeps its `EpistemicStatus` so proposals are not mistaken for evidence.
- Interfaces: `MemoryStore`, `remember`, `search`, `MemoryEntry`, `MemoryKind`, `EpistemicStatus`
- Depends on: (standard library only)
"""
from __future__ import annotations

import re
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping


class MemoryKind(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class EpistemicStatus(str, Enum):
    PROPOSED = "proposed"
    RETRIEVED = "retrieved"
    MEASURED = "measured"
    VERIFIED = "verified"
    DERIVED = "derived"


@dataclass(frozen=True)
class MemoryScope:
    """Access boundary applied before ranking stored experience."""

    case_id: str | None = None
    task_type: str | None = None
    dataset_partitions: tuple[str, ...] = ()
    biological_context: str | None = None
    allowed_origins: tuple[str, ...] = ()
    created_after: str | None = None
    created_before: str | None = None
    allow_cross_case: bool = False


@dataclass(frozen=True)
class MemoryEntry:
    """One stored memory record with its kind, content, and epistemic status."""

    identifier: str
    kind: MemoryKind
    content: str
    status: EpistemicStatus
    provenance: str
    session_id: str
    created_at: str
    scope: MemoryScope = MemoryScope()
    parent_ids: tuple[str, ...] = ()
    retracted: bool = False


class MemoryStore:
    """SQLite-backed memory designed to retrieve experience without upgrading it to fact."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def remember(
        self,
        content: str,
        *,
        kind: MemoryKind,
        status: EpistemicStatus,
        provenance: str,
        session_id: str,
        scope: MemoryScope | None = None,
        parent_ids: tuple[str, ...] = (),
    ) -> MemoryEntry:
        entry = MemoryEntry(
            identifier=str(uuid.uuid4()),
            kind=kind,
            content=content.strip(),
            status=status,
            provenance=provenance.strip(),
            session_id=session_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            scope=scope or MemoryScope(),
            parent_ids=tuple(parent_ids),
        )
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO memories(
                    id, kind, content, status, provenance, session_id, created_at, scope_json, parent_ids, retracted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    entry.identifier,
                    entry.kind.value,
                    entry.content,
                    entry.status.value,
                    entry.provenance,
                    entry.session_id,
                    entry.created_at,
                    _scope_json(entry.scope),
                    ",".join(entry.parent_ids),
                ),
            )
        return entry

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        kinds: Iterable[MemoryKind] | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[MemoryEntry, ...]:
        """Retrieve lexical matches deterministically; callers retain the recorded status."""

        allowed = tuple(kind.value for kind in kinds) if kinds else ()
        sql = "SELECT id, kind, content, status, provenance, session_id, created_at, scope_json, parent_ids, retracted FROM memories"
        arguments: list[str] = []
        clauses = ["retracted = 0"]
        if allowed:
            clauses.append("kind IN (" + ",".join("?" for _ in allowed) + ")")
            arguments.extend(allowed)
        sql += " WHERE " + " AND ".join(clauses)
        with self._connection() as connection:
            rows = connection.execute(sql, arguments).fetchall()
        query_terms = set(_terms(query))
        ranked = sorted(
            (
                (_lexical_score(query_terms, row[2]), row)
                for row in rows
                if _scope_matches(_scope_from_json(row[7]), scope, row[4], row[6])
                and _lexical_score(query_terms, row[2]) > 0
            ),
            key=lambda item: (item[0], item[1][6]),
            reverse=True,
        )[:limit]
        return tuple(_row_to_entry(row) for _, row in ranked)

    def retract(self, identifier: str) -> tuple[str, ...]:
        """Mark a memory and its derived descendants inactive without deleting history."""

        with self._connection() as connection:
            rows = connection.execute("SELECT id, parent_ids FROM memories WHERE retracted = 0").fetchall()
            known = {row[0]: tuple(item for item in row[1].split(",") if item) for row in rows}
            if identifier not in known:
                raise ValueError(f"Unknown active memory: {identifier}")
            affected = {identifier}
            changed = True
            while changed:
                changed = False
                for child, parents in known.items():
                    if child not in affected and any(parent in affected for parent in parents):
                        affected.add(child)
                        changed = True
            connection.executemany("UPDATE memories SET retracted = 1 WHERE id = ?", ((item,) for item in affected))
        return tuple(sorted(affected))

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    scope_json TEXT NOT NULL DEFAULT '{}',
                    parent_ids TEXT NOT NULL DEFAULT '',
                    retracted INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(memories)").fetchall()}
            for name, definition in (
                ("scope_json", "TEXT NOT NULL DEFAULT '{}" + "'"),
                ("parent_ids", "TEXT NOT NULL DEFAULT ''"),
                ("retracted", "INTEGER NOT NULL DEFAULT 0"),
            ):
                if name not in columns:
                    connection.execute(f"ALTER TABLE memories ADD COLUMN {name} {definition}")

    def _connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)


def _terms(text: str) -> tuple[str, ...]:
    """Return conservative lexical units for Latin identifiers and CJK requests.

    Whole CJK runs are intentionally retained rather than guessed into words.  This
    supports an exact bilingual query without introducing a tokenizer dependency or
    silently translating scientific identifiers.
    """

    return tuple(re.findall(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", text.lower()))


def _lexical_score(query_terms: set[str], text: str) -> float:
    if not query_terms:
        return 0.0
    content_terms = set(_terms(text))
    return len(query_terms & content_terms) / len(query_terms)


def _row_to_entry(row: tuple[str, str, str, str, str, str, str, str, str, int]) -> MemoryEntry:
    return MemoryEntry(
        identifier=row[0],
        kind=MemoryKind(row[1]),
        content=row[2],
        status=EpistemicStatus(row[3]),
        provenance=row[4],
        session_id=row[5],
        created_at=row[6],
        scope=_scope_from_json(row[7]),
        parent_ids=tuple(item for item in row[8].split(",") if item),
        retracted=bool(row[9]),
    )


def _scope_json(scope: MemoryScope) -> str:
    return json.dumps(
        {
            "case_id": scope.case_id,
            "task_type": scope.task_type,
            "dataset_partitions": scope.dataset_partitions,
            "biological_context": scope.biological_context,
            "allowed_origins": scope.allowed_origins,
            "created_after": scope.created_after,
            "created_before": scope.created_before,
            "allow_cross_case": scope.allow_cross_case,
        },
        ensure_ascii=True,
        sort_keys=True,
    )


def _scope_from_json(value: str) -> MemoryScope:
    try:
        data = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, Mapping):
        data = {}
    return MemoryScope(
        case_id=data.get("case_id") if isinstance(data.get("case_id"), str) else None,
        task_type=data.get("task_type") if isinstance(data.get("task_type"), str) else None,
        dataset_partitions=tuple(item for item in data.get("dataset_partitions", ()) if isinstance(item, str)),
        biological_context=data.get("biological_context") if isinstance(data.get("biological_context"), str) else None,
        allowed_origins=tuple(item for item in data.get("allowed_origins", ()) if isinstance(item, str)),
        created_after=data.get("created_after") if isinstance(data.get("created_after"), str) else None,
        created_before=data.get("created_before") if isinstance(data.get("created_before"), str) else None,
        allow_cross_case=bool(data.get("allow_cross_case", False)),
    )


def _scope_matches(
    entry: MemoryScope,
    requested: MemoryScope | None,
    provenance: str,
    created_at: str,
) -> bool:
    if requested is None:
        return True
    if requested.allowed_origins and provenance not in requested.allowed_origins:
        return False
    if requested.case_id:
        if entry.case_id is None:
            return requested.allow_cross_case
        if entry.case_id != requested.case_id and not (requested.allow_cross_case and entry.allow_cross_case):
            return False
    if requested.task_type and entry.task_type and entry.task_type != requested.task_type:
        return False
    if requested.biological_context and entry.biological_context and entry.biological_context != requested.biological_context:
        return False
    if requested.dataset_partitions and entry.dataset_partitions and not set(requested.dataset_partitions).intersection(entry.dataset_partitions):
        return False
    if requested.created_after and created_at < requested.created_after:
        return False
    if requested.created_before and created_at > requested.created_before:
        return False
    return True
