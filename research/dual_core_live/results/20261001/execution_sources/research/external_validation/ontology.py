"""Development-frozen mechanism ontology and truth-free external episodes.

The ontology is part of the development freeze.  An external study may provide
compound and assay metadata, but it must not provide mechanism labels while an
episode menu or a hypothesis contrast is being constructed.  Labels are read
only by the evaluator after an arm has finished.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from types import MappingProxyType


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifests" / "hypothesis_ontology.json"
_FORBIDDEN = frozenset({
    "truth", "hidden_truth", "ground_truth", "klass", "mechanism",
    "mechanism_label", "annotation", "outcome", "outcomes",
})


@dataclass(frozen=True)
class ExternalEpisode:
    """An episode candidate with no evaluator label attached."""

    episode_id: str
    dataset: str
    tier: str
    fold: int
    compound: str
    h1: str
    h2: str
    unit: str

    def as_manifest_record(self) -> dict[str, str]:
        return {
            "episode_id": self.episode_id,
            "compound": self.compound,
            "h1": self.h1,
            "h2": self.h2,
            "unit": self.unit,
        }


@dataclass(frozen=True)
class HypothesisOntology:
    """Immutable, tiered hypothesis identifiers frozen during development."""

    version: str
    source: str
    pools: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("ontology version must be non-empty")
        normalized: dict[str, tuple[str, ...]] = {}
        for tier, values in self.pools.items():
            if not isinstance(tier, str) or not tier.strip():
                raise ValueError("ontology tier must be non-empty")
            labels = tuple(str(value).strip() for value in values)
            if not labels or any(not value for value in labels):
                raise ValueError(f"ontology pool {tier!r} must be non-empty")
            if len(set(labels)) != len(labels):
                raise ValueError(f"ontology pool {tier!r} contains duplicate hypotheses")
            normalized[tier] = tuple(sorted(labels))
        if not normalized:
            raise ValueError("ontology must contain at least one tier")
        object.__setattr__(self, "pools", MappingProxyType(normalized))

    def pool(self, tier: str) -> tuple[str, ...]:
        try:
            return self.pools[tier]
        except KeyError as exc:
            raise ValueError(f"tier {tier!r} is not in the frozen hypothesis ontology") from exc

    def contrasts(self, tier: str) -> tuple[tuple[str, str], ...]:
        return tuple(itertools.combinations(self.pool(tier), 2))

    @property
    def sha256(self) -> str:
        payload = {"version": self.version, "source": self.source,
                   "pools": {k: list(v) for k, v in sorted(self.pools.items())}}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(path: Path = MANIFEST) -> HypothesisOntology:
    """Load and validate the checked-in development ontology manifest."""

    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(value) != {"manifest_version", "source", "pools"}:
        raise ValueError("hypothesis ontology manifest has unexpected fields")
    if value["manifest_version"] != "1":
        raise ValueError("unsupported hypothesis ontology manifest version")
    if not isinstance(value["pools"], dict):
        raise ValueError("hypothesis ontology pools must be an object")
    return HypothesisOntology("1", str(value["source"]),
                             {tier: tuple(labels) for tier, labels in value["pools"].items()})


def _metadata_compounds(compounds: Iterable[str | Mapping]) -> tuple[tuple[str, str], ...]:
    """Normalize metadata records and reject attempts to smuggle labels."""

    out = []
    for item in compounds:
        if isinstance(item, Mapping):
            bad = {str(key).strip().lower() for key in item} & _FORBIDDEN
            if bad:
                raise ValueError(f"external metadata contains evaluator-only fields: {sorted(bad)}")
            if "compound" not in item:
                raise ValueError("external metadata records require compound")
            compound, unit = item["compound"], item.get("unit", item["compound"])
        else:
            compound, unit = item, item
        compound, unit = str(compound).strip(), str(unit).strip()
        if not compound:
            raise ValueError("external metadata compound must be non-empty")
        out.append((compound, unit or compound))
    unique = dict(sorted(out))
    return tuple(unique.items())


def build_truth_free_episodes(*, dataset: str, tier: str, fold: int,
                              compounds: Iterable[str | Mapping],
                              ontology: HypothesisOntology | None = None) -> tuple[ExternalEpisode, ...]:
    """Build all registered contrasts from metadata and the frozen ontology.

    There is intentionally no ``truth`` parameter.  Every pair in the frozen
    pool is offered for every metadata compound; scoring can attach a label only
    after the arm returns.
    """

    ontology = ontology or load()
    pairs = ontology.contrasts(tier)
    if not pairs:
        raise ValueError(f"ontology tier {tier!r} has fewer than two hypotheses")
    records = []
    for compound, unit in _metadata_compounds(compounds):
        for h1, h2 in pairs:
            episode_id = f"{dataset}|{tier}|{int(fold)}|{compound}|{h1}|{h2}"
            records.append(ExternalEpisode(episode_id, dataset, tier, int(fold), compound, h1, h2, unit))
    return tuple(records)


def build_episode_manifest(*, dataset: str, tier: str, fold: int,
                           compounds: Iterable[str | Mapping], setting: Mapping,
                           ontology: HypothesisOntology | None = None) -> dict:
    """Serialize a truth-free episode manifest suitable for schema validation."""

    episodes = build_truth_free_episodes(dataset=dataset, tier=tier, fold=fold,
                                         compounds=compounds, ontology=ontology)
    return {"manifest_version": "1", "dataset": dataset, "tier": tier, "fold": int(fold),
            "setting": dict(setting), "episodes": [episode.as_manifest_record() for episode in episodes]}


__all__ = ["ExternalEpisode", "HypothesisOntology", "build_episode_manifest",
           "build_truth_free_episodes", "load"]
