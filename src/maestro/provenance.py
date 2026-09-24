"""Source clusters so repeated citations do not manufacture evidence strength.

File summary
- Path: src/maestro/provenance.py
- Purpose: Collapse citations of one experiment into a single evidence unit.
- Core points:
  - `SourceClusterIndex` maps any source id to the cluster that counts as one unit.
  - Repeated write-ups of one dataset are not three independent confirmations.
- Interfaces: `SourceClusterIndex`, `cluster_of`, `independent`, `build_index`, `SourceCluster`
- Depends on: (standard library only)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class SourceCluster:
    """One original experiment and the identifiers that refer to it."""

    cluster_id: str
    source_ids: frozenset[str]
    note: str = ""


class SourceClusterIndex:
    """Map any source identifier to the cluster that counts as one unit of evidence."""

    def __init__(self, clusters: Iterable[SourceCluster] = ()):
        self._clusters: dict[str, SourceCluster] = {}
        self._lookup: dict[str, str] = {}
        for cluster in clusters:
            self.register(cluster)

    def register(self, cluster: SourceCluster) -> SourceCluster:
        if not cluster.cluster_id.strip():
            raise ValueError("cluster_id is required.")
        self._clusters[cluster.cluster_id] = cluster
        for source_id in cluster.source_ids:
            self._lookup[source_id] = cluster.cluster_id
        self._lookup.setdefault(cluster.cluster_id, cluster.cluster_id)
        return cluster

    def cluster_of(self, source_id: str) -> str:
        return self._lookup.get(source_id, source_id)

    def independent(self, source_ids: Iterable[str]) -> frozenset[str]:
        return frozenset(self.cluster_of(item) for item in source_ids if item)

    def count_independent(self, source_ids: Iterable[str]) -> int:
        return len(self.independent(source_ids))

    @property
    def clusters(self) -> tuple[SourceCluster, ...]:
        return tuple(self._clusters.values())

    def cluster_members(self, cluster_id: str) -> frozenset[str]:
        cluster = self._clusters.get(cluster_id)
        return cluster.source_ids if cluster else frozenset()


def build_index(clusters: Sequence[Mapping[str, object]]) -> SourceClusterIndex:
    """Build an index from plain mappings such as parsed JSON or a manifest."""

    index = SourceClusterIndex()
    for entry in clusters:
        identifier = entry.get("cluster_id")
        sources = entry.get("source_ids") or ()
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("Each cluster mapping requires a non-empty cluster_id.")
        index.register(
            SourceCluster(
                cluster_id=identifier.strip(),
                source_ids=frozenset(str(item) for item in sources if str(item)),
                note=str(entry.get("note", "")),
            )
        )
    return index
