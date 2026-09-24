"""Gene-set pathway readouts, and whether a backend can represent them at all.

File summary
- Path: src/virtual_cell/pathway_readout.py
- Purpose: turn a declared set of genes into a typed transcriptional readout, and
  answer the separate question of whether a model's output coordinates can
  express that readout.
- Core points:
  - A gene set is identified by its resolved members, so a definition that
    changes silently is a different endpoint with a different digest.
  - Scoring refuses a set whose members are not all present: dropping members is
    a restriction the caller must declare, because the average over survivors is
    a different quantity.
  - The score is RNA abundance of a gene set. It is a proxy for pathway activity
    and the typing never lets it discharge a premise for proximal activity.
  - Expressivity is answerable before any prediction: a coordinate space that
    omits the genes an endpoint is made of cannot represent it, whatever the
    model's accuracy on other endpoints.
- Interfaces: `GeneSet`, `score_gene_set`, `BackgroundPool`, `StandardisedScore`,
  `standardised_score`, `load_background_pool`, `pathway_observable`,
  `ExpressivityAudit`, `expressivity_audit`
- Depends on: maestro.models, virtual_cell.biology
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, replace
from pathlib import Path
from statistics import fmean, pstdev
from typing import Iterable, Mapping, Sequence

from maestro.models import BiologicalQuantity

from .biology import MeasurementModel, Observable


@dataclass(frozen=True)
class GeneSet:
    """A declared set of genes, identified by what it actually contains.

    ``source`` and ``source_sha256`` record where membership came from, so a
    Reactome-derived set and a hand-frozen panel are distinguishable, and a
    later release cannot change an endpoint without changing its digest.
    """

    identifier: str
    members: tuple[str, ...]
    source: str
    source_sha256: str
    rule: str
    restricted_from: str | None = None

    @property
    def digest(self) -> str:
        """SHA-256 over the identifier and the sorted membership.

        Order is not part of the definition, so two spellings of one set agree;
        a restriction drops members and therefore changes the digest, which is
        what makes a restricted endpoint visibly different from the declared one.
        """

        payload = self.identifier + "\n" + "\n".join(sorted(self.members))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @property
    def size(self) -> int:
        return len(self.members)

    def restricted_to(self, available: Mapping[str, float] | Iterable[str]) -> tuple["GeneSet", tuple[str, ...]]:
        """Return the set restricted to available genes, plus the dropped members."""

        names = set(available)
        present = tuple(member for member in self.members if member in names)
        missing = tuple(member for member in self.members if member not in names)
        return replace(self, members=present, restricted_from=self.digest), missing


def score_gene_set(values: Mapping[str, float], gene_set: GeneSet) -> float:
    """Mean value over the set's members, refusing an undeclared restriction."""

    if not gene_set.members:
        raise ValueError(f"gene set '{gene_set.identifier}' has no members to score")
    missing = [member for member in gene_set.members if member not in values]
    if missing:
        raise ValueError(
            f"gene set '{gene_set.identifier}' has {len(missing)} member(s) absent from the supplied values "
            f"({', '.join(missing[:5])}); call restricted_to() to declare the restriction explicitly"
        )
    return float(fmean(float(values[member]) for member in gene_set.members))


@dataclass(frozen=True)
class BackgroundPool:
    """The declared gene pool a size-matched background is drawn from.

    The pool decides the answer. Drawing from whatever genes happen to be present in
    the supplied values makes a declared set containing undetected members *not*
    size-matched against its own background, and the resulting z is then a function of
    an undeclared sampling choice rather than of the data. So the pool is a first-class
    artefact with its own digest: two runs that disagree must disagree visibly.
    """

    identifier: str
    members: tuple[str, ...]
    source: str
    source_sha256: str
    rule: str

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("A background pool needs an identifier.")
        if not self.members:
            raise ValueError(f"Background pool '{self.identifier}' has no members.")
        if not self.source.strip() or not self.source_sha256.strip():
            raise ValueError(
                f"Background pool '{self.identifier}' must name its source and that source's digest; "
                "an undeclared pool is indistinguishable from the caller's own choice."
            )

    @property
    def digest(self) -> str:
        """SHA-256 over the identifier and the sorted membership, as for a gene set."""

        payload = self.identifier + "\n" + "\n".join(sorted(self.members))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @property
    def size(self) -> int:
        return len(self.members)

    def usable_for(self, values: Mapping[str, float], gene_set: GeneSet) -> tuple[str, ...]:
        """Why this pool cannot supply a background here, named individually."""

        problems: list[str] = []
        available = [member for member in self.members if member in values]
        if len(available) < gene_set.size:
            problems.append(
                f"background_pool_smaller_than_the_gene_set:{len(available)}<{gene_set.size}"
            )
        absent = self.size - len(available)
        if absent:
            problems.append(f"background_members_absent_from_the_values:{absent}_of_{self.size}")
        return tuple(problems)


@dataclass(frozen=True)
class StandardisedScore:
    """A set score beside the background of size-matched random sets."""

    raw: float
    z: float
    background_mean: float
    background_sd: float
    background_draws: int
    gene_set_digest: str
    background_pool_size: int
    background_pool_id: str = ""
    background_pool_digest: str = ""
    background_members_absent_from_the_values: int = 0


def standardised_score(
    values: Mapping[str, float],
    gene_set: GeneSet,
    *,
    draws: int = 1000,
    seed: int = 0,
    background: "BackgroundPool | Sequence[str] | None" = None,
) -> StandardisedScore:
    """Score a set against size-matched random sets drawn from a **declared** pool.

    Standardising against random sets of the same size is what keeps a large set, or a
    set of highly expressed genes, from producing an effect by construction. The pool is
    required, not optional: falling back to the supplied values was a silent sampling
    choice, and a declared set containing undetected members was then compared against a
    background that could not contain them. A caller with no pool is refused by name.
    """

    raw = score_gene_set(values, gene_set)
    if background is None:
        # Fail closed. A guard that passes when nothing is declared is not a guard.
        raise ValueError(
            f"background_pool_not_declared: gene set '{gene_set.identifier}' cannot be "
            "standardised without a declared background pool; pass a BackgroundPool so the "
            "sampling frame is auditable and carries a digest."
        )
    pool_id = ""
    pool_digest = ""
    absent = 0
    if isinstance(background, BackgroundPool):
        problems = background.usable_for(values, gene_set)
        blocking = [item for item in problems if item.startswith("background_pool_smaller")]
        if blocking:
            raise ValueError(
                f"background pool '{background.identifier}' cannot supply size-matched sets: "
                + ", ".join(problems)
            )
        pool_id, pool_digest = background.identifier, background.digest
        absent = background.size - len([item for item in background.members if item in values])
        members: Sequence[str] = [item for item in background.members if item in values]
    else:
        members = background
    pool = sorted(members)
    if len(pool) < gene_set.size:
        raise ValueError(
            f"background pool of {len(pool)} genes cannot supply size-matched sets of {gene_set.size}"
        )
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        chosen = rng.sample(pool, gene_set.size)
        samples.append(fmean(float(values[name]) for name in chosen))
    mean = float(fmean(samples))
    spread = float(pstdev(samples))
    z = 0.0 if spread == 0.0 else (raw - mean) / spread
    return StandardisedScore(
        raw=raw,
        z=float(z),
        background_mean=mean,
        background_sd=spread,
        background_draws=draws,
        gene_set_digest=gene_set.digest,
        background_pool_size=len(pool),
        # The sampling frame travels with the z. Without these three fields a reader
        # cannot tell which declared pool produced the number, and the pool digest is
        # what makes two disagreeing runs visibly disagree.
        background_pool_id=pool_id,
        background_pool_digest=pool_digest,
        background_members_absent_from_the_values=absent,
    )


def load_background_pool(path: Path | str) -> BackgroundPool:
    """Read a digested background-pool artefact, refusing one that does not match itself.

    The artefact is the form a pool travels in between runs: it carries its own digest
    over the sorted membership, so a pool that was edited after declaration is refused
    by name rather than silently re-standardising every endpoint its consumer scores.
    """

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "maestro.background_pool.v1":
        raise ValueError(
            f"background_pool_not_declared: {path} is not a maestro.background_pool.v1 artefact"
        )
    members = payload.get("members")
    if not isinstance(members, list) or not members:
        raise ValueError(f"background pool artefact {path} does not list its members")
    pool = BackgroundPool(
        identifier=str(payload.get("identifier", "")),
        members=tuple(str(member) for member in members),
        source=str(payload.get("source", "")),
        source_sha256=str(payload.get("source_sha256", "")),
        rule=str(payload.get("rule", "")),
    )
    recorded = str(payload.get("digest", ""))
    if recorded != pool.digest:
        raise ValueError(
            f"background pool artefact {path} does not match its recorded digest "
            f"(recorded {recorded}, observed {pool.digest})"
        )
    return pool


def pathway_observable(
    gene_set: GeneSet,
    *,
    context_identifier: str | None,
    time_hours: float | None,
    measured: bool = True,
    units: str = "log1p_normalised_count_shift",
    assay: str = "scrnaseq_pseudobulk",
) -> Observable:
    """Type a gene-set score as what it is: RNA abundance of a declared set."""

    return Observable(
        name=f"pathway_shift:{gene_set.identifier}",
        quantity=BiologicalQuantity.RNA_ABUNDANCE,
        entity=f"gene_set:{gene_set.identifier}",
        units=units,
        assay=assay,
        measurement_model=MeasurementModel(
            observation="mean over member genes of the condition mean minus the vehicle mean",
            noise="normal",
            aggregation="mean over declared gene-set members",
        ),
        context_identifier=context_identifier,
        time_hours=time_hours,
        measured=measured,
        limitations=(
            "transcriptional proxy for pathway activity, not a phosphorylation or enzymatic measurement",
            f"gene_set_digest:{gene_set.digest}",
        ),
    )


@dataclass(frozen=True)
class ExpressivityAudit:
    """Whether an output coordinate space can represent a declared endpoint."""

    gene_set_id: str
    gene_set_digest: str
    total_members: int
    representable: int
    missing_members: tuple[str, ...]
    coordinate_space: str = ""

    @property
    def fraction(self) -> float:
        return 0.0 if self.total_members == 0 else self.representable / self.total_members

    @property
    def verdict(self) -> str:
        if self.total_members and self.representable == self.total_members:
            return "expressible"
        if self.representable == 0:
            return "not_expressible"
        return "partially_expressible"

    @property
    def applicability_reason(self) -> str | None:
        """A named reason a backend cannot serve this endpoint, or None."""

        if self.verdict == "expressible":
            return None
        return f"endpoint_not_representable_in_output_space:{self.gene_set_id}"


def expressivity_audit(
    gene_set: GeneSet, coordinate_names: Iterable[str], *, coordinate_space: str = ""
) -> ExpressivityAudit:
    """Compare a declared endpoint with the coordinates a backend actually emits."""

    names = {name for name in coordinate_names if name}
    representable = [member for member in gene_set.members if member in names]
    missing = tuple(member for member in gene_set.members if member not in names)
    return ExpressivityAudit(
        gene_set_id=gene_set.identifier,
        gene_set_digest=gene_set.digest,
        total_members=gene_set.size,
        representable=len(representable),
        missing_members=missing,
        coordinate_space=coordinate_space,
    )
