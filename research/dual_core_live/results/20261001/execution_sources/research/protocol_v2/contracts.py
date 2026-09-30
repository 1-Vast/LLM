"""Truth and data-boundary contracts: what a policy may see, what a measurement state means, how scoring fails.

File summary
- Path: research/protocol_v2/contracts.py
- Purpose: separate truth-free policy execution from truth-bearing post-hoc scoring. Name the
  five measurement states. Build the minimal public view an arm receives, by whitelist.
- Core points:
  - Measurement states. `not_measured` (the design never ran the condition for this compound),
    `quality_failed` (it ran and failed QC), `measured_undetected`, `measured_ambiguous` and
    `measured_eliminating`. Only the last three are biological readings. Protocol v1's executor
    turned `not_measured` into `quality_failed` and charged it as an assay (56 of 729 QC-false
    steps in the registered SciPlex3 replay). Here a not-measured condition is never offered, and
    choosing one raises `NotMeasured`.
  - Scoring. `score(trace, truth)` is the only place a truth meets a trace. It refuses a missing
    truth or a truth outside the contrast (`TruthMissing`), so an unscorable episode can never be
    counted as correct, wrong or deferred.
  - Public view. `PublicContext` holds exactly five fields: training-only reference tables
    (`ft`), the validator calibration fitted on them (`params`), the menu and pool (`tier`, with
    no label-derived eligibility list), structures and unit identifiers (`data.compounds`, with
    no annotation column), the metadata availability map (`data.availability`), and per-fold
    caches (`extra`). An arm that reaches for anything else (profiles, QC fields, detection
    flags, labels, the condition index) gets an `AttributeError`. This replaces protocol v1's
    blacklist seal for v2 arms.
  - Truth-free episodes. The pool comes from reference compounds (`reference_pool`), and every
    pair of pool classes is offered for every metadata-eligible compound
    (`truth_free_episodes`). The mechanism endpoint keeps, at scoring time, the episodes whose
    pair contains the compound's label (`mechanism_endpoint`).
  - Protocol v2.1 (`protocol_v2_1.json`) adds three boundary fixes without changing any v2
    default. `Lifecycle` separates what happened to a condition (not planned, planned and not
    measured, measured valid, measured and QC-failed, unknown) from what a valid measurement read
    (`readout`); `v2_state` maps the pair back to `MeasurementState` losslessly.
    `design_availability` builds the menu from the frozen study design (`design.py`), so a
    held-out outcome cannot remove a condition. `fold_pools` rebuilds the L1000 hypothesis pool
    from each fold's training compounds only, replacing a pool counted over every compound
    before the split.
- Interfaces: `MeasurementState`, `measurement_state`, `NotMeasured`, `TruthMissing`,
  `require_truth`, `score`, `reference_pool`, `truth_free_episodes`, `mechanism_endpoint`,
  `PublicContext`, `PublicData`, `public_view`, `public_view_problems`, `PUBLIC_COLUMNS`,
  `Lifecycle`, `lifecycle_state`, `readout`, `v2_state`, `design_availability`, `fold_pools`
- Depends on: research/dynamic_world_model/common.py (Tier), numpy, pandas
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

import pandas as pd

from research.belief_planning import tasks as T

C = T.C


class MeasurementState(str, Enum):
    NOT_MEASURED = "not_measured"
    QUALITY_FAILED = "quality_failed"
    MEASURED_UNDETECTED = "measured_undetected"
    MEASURED_AMBIGUOUS = "measured_ambiguous"
    MEASURED_ELIMINATING = "measured_eliminating"

    @property
    def biological(self) -> bool:
        """Whether the state is a biological reading (and may enter an outcome distribution)."""
        return self in (MeasurementState.MEASURED_UNDETECTED, MeasurementState.MEASURED_AMBIGUOUS,
                        MeasurementState.MEASURED_ELIMINATING)


_BY_OUTCOME = {"undetected": MeasurementState.MEASURED_UNDETECTED,
               "ambiguous": MeasurementState.MEASURED_AMBIGUOUS,
               "eliminate_a": MeasurementState.MEASURED_ELIMINATING,
               "eliminate_b": MeasurementState.MEASURED_ELIMINATING}


class NotMeasured(RuntimeError):
    """An arm chose a condition the study design never ran for this compound."""


class TruthMissing(ValueError):
    """Scoring was asked to score an episode without a usable truth."""


def measurement_state(result: Mapping) -> MeasurementState:
    """The state of one executor result (`episodes.execute`'s dict)."""
    if result.get("row") is None:
        return MeasurementState.NOT_MEASURED
    if not result.get("qc"):
        return MeasurementState.QUALITY_FAILED
    outcome = result.get("outcome")
    if outcome not in _BY_OUTCOME:
        raise ValueError(f"unknown_measured_outcome:{outcome!r}")
    return _BY_OUTCOME[outcome]


class Lifecycle(str, Enum):
    """What happened to a condition for a compound. Separate from what a valid measurement read."""
    NOT_PLANNED = "not_planned"
    PLANNED_NOT_MEASURED = "planned_not_measured"
    MEASURED_VALID = "measured_valid"
    MEASURED_QC_FAILED = "measured_qc_failed"
    MISSING_OR_UNKNOWN = "missing_or_unknown"


def lifecycle_state(planned: bool | None, result: Mapping | None) -> Lifecycle:
    """The lifecycle of one condition: `planned` from the design, `result` from the executor (or None).

    A planned condition whose prepared row is absent ran and failed a QC rule (for SciPlex3, fewer
    than 20 cells per replicate group), so it is MEASURED_QC_FAILED, not a missing design entry.
    """
    if planned is None:
        return Lifecycle.MISSING_OR_UNKNOWN
    if not planned:
        return Lifecycle.NOT_PLANNED
    if result is None:
        return Lifecycle.PLANNED_NOT_MEASURED
    if result.get("row") is None or not result.get("qc"):
        return Lifecycle.MEASURED_QC_FAILED
    return Lifecycle.MEASURED_VALID


def readout(result: Mapping | None) -> str | None:
    """The biological reading of a valid measurement (undetected, ambiguous, eliminating), else None."""
    if not result or result.get("row") is None or not result.get("qc"):
        return None
    state = _BY_OUTCOME.get(result.get("outcome"))
    if state is None:
        raise ValueError(f"unknown_measured_outcome:{result.get('outcome')!r}")
    return state.value.replace("measured_", "")


def v2_state(lifecycle: Lifecycle, reading: str | None) -> MeasurementState:
    """Lossless map from (lifecycle, readout) to protocol v2's `MeasurementState`."""
    if lifecycle is Lifecycle.MEASURED_VALID:
        if reading is None:
            raise ValueError("valid_measurement_without_readout")
        return MeasurementState(f"measured_{reading}")
    if reading is not None:
        raise ValueError(f"readout_without_valid_measurement:{lifecycle.value}")
    if lifecycle is Lifecycle.MEASURED_QC_FAILED:
        return MeasurementState.QUALITY_FAILED
    return MeasurementState.NOT_MEASURED


def design_availability(design: Mapping, keys, compounds) -> dict:
    """Which of `keys` the study design planned for each compound (`design.py` tables; no outcome read)."""
    wanted = [tuple(k) for k in keys]
    return {c: frozenset(k for k in wanted if k in design.get(c, frozenset())) for c in compounds}


def fold_pools(klass: Mapping[str, str], identity: Mapping[str, str], training, complete, detected_at: Mapping,
               *, min_identities: int, min_detected: int) -> tuple:
    """The L1000 pool rule applied to one fold's training compounds only.

    A class enters when its training compounds planned at every tier condition (`complete`) have at
    least `min_identities` distinct identities, of which at least `min_detected` were detected at a
    tier condition (`detected_at`: compound -> keys detected; training compounds only). Held-out
    compounds contribute nothing, so their labels and detection outcomes cannot move the pool.
    """
    identities: dict[str, set] = {}
    detected: dict[str, set] = {}
    for compound in training:
        label = klass.get(compound)
        if _missing(label) or compound not in complete:
            continue
        identities.setdefault(label, set()).add(identity.get(compound, compound))
        if detected_at.get(compound):
            detected.setdefault(label, set()).add(identity.get(compound, compound))
    return tuple(sorted(k for k, v in identities.items()
                        if len(v) >= min_identities and len(detected.get(k, ())) >= min_detected))


def _missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or (isinstance(value, str) and not value)


def require_truth(truth, h1, h2) -> None:
    if _missing(truth):
        raise TruthMissing(f"scoring_truth_missing: {h1!r} vs {h2!r}")
    if truth not in (h1, h2):
        raise TruthMissing(f"scoring_truth_outside_contrast: {truth!r} not in ({h1!r}, {h2!r})")


FINAL_UTILITY = {"correct": 1, "wrong": -2, "exhausted": -2, "undetermined": 0, "deferred": 0}


def score(trace: Mapping, truth) -> dict:
    """Join a truth to a truth-free trace. The only function in protocol v2 that reads a truth."""
    h1, h2 = trace["h1"], trace["h2"]
    require_truth(truth, h1, h2)
    if "truth" in trace:
        raise ValueError("trace_carries_truth: execution traces must be truth-free")
    other = h2 if truth == h1 else h1
    remaining = frozenset(trace["remaining"])
    if not trace["steps"]:
        final = "deferred"
    elif remaining == frozenset({truth}):
        final = "correct"
    elif remaining == frozenset({other}):
        final = "wrong"
    elif not remaining:
        final = "exhausted"
    else:
        final = "undetermined"
    return {"truth": truth, "final": final, "utility": FINAL_UTILITY[final],
            "correct": float(final == "correct"), "wrong": float(final in ("wrong", "exhausted")),
            "decided": float(final in ("correct", "wrong", "exhausted")), "deferred": float(final == "deferred")}


# ------------------------------------------------------------------------------ truth-free episodes
def reference_pool(reference_labels: Mapping[str, str], *, min_units: int, unit_of: Mapping[str, str] | None = None) -> tuple:
    """The hypothesis pool from reference compounds only: classes with at least `min_units` units.

    `reference_labels` must hold reference (training) compounds only; a held-out or external test
    label has no place here. Protocol v1 counted held-out labels into development pools.
    """
    units: dict[str, set] = {}
    for compound, label in reference_labels.items():
        if _missing(label):
            continue
        units.setdefault(str(label), set()).add((unit_of or {}).get(compound, compound))
    return tuple(sorted(k for k, v in units.items() if len(v) >= min_units))


def truth_free_episodes(*, dataset: str, tier: str, fold: int, compounds, pool, unit_of=None):
    """Every pair of pool classes for every metadata-eligible compound. No truth, no label filter.

    Reuses `research/external_validation/ontology.py`'s tested builder with a pool derived from
    reference compounds (`reference_pool`), not from the development ontology file. Offering
    every pair, rather than each compound's own class against each decoy, also removes a
    structural leak of the forced-choice design: there, the true class is the one class common to
    all of a compound's contrasts.
    """
    from research.external_validation.ontology import HypothesisOntology, build_truth_free_episodes
    ontology = HypothesisOntology("reference", f"{dataset} reference compounds", {tier: tuple(pool)})
    records = [{"compound": c, "unit": (unit_of or {}).get(c, c)} for c in compounds]
    return build_truth_free_episodes(dataset=dataset, tier=tier, fold=fold, compounds=records, ontology=ontology)


def mechanism_endpoint(episodes, truth_of: Mapping[str, str]) -> tuple[list, list]:
    """Scoring side only: episodes whose contrast contains the compound's post-hoc label, and the rest.

    The acquisition endpoint uses every episode; the mechanism endpoint only the first list.
    """
    scorable, unscorable = [], []
    for e in episodes:
        truth = truth_of.get(e.compound)
        (scorable if not _missing(truth) and truth in (e.h1, e.h2) else unscorable).append(e)
    return scorable, unscorable


# ------------------------------------------------------------------------------ public view
PUBLIC_COLUMNS = ("compound", "smiles", "component", "skeleton", "identity", "scaffold")
"""Compound columns an arm may read: identity, structure and independent-unit keys. No annotation."""

PUBLIC_FIELDS = ("ft", "params", "tier", "data", "extra")


@dataclass(frozen=True)
class PublicData:
    compounds: pd.DataFrame
    availability: Mapping[str, frozenset]
    """compound -> condition keys the study design ran for it (plate-map metadata, not outcomes)."""


@dataclass(frozen=True)
class PublicContext:
    ft: object
    params: Mapping
    tier: object
    data: PublicData
    extra: dict = field(default_factory=dict)


def availability(real_ctx, keys, compounds) -> dict:
    """Which of `keys` the design ran for each compound. Reads only whether a condition row exists."""
    index = real_ctx.data.index
    return {c: frozenset(k for k in keys if c in index.get(tuple(k), {})) for c in compounds}


def public_view(real_ctx, heldout, *, training_compounds, extra=None, design=None) -> PublicContext:
    """The whitelist projection an arm receives for one fold.

    With `design` (protocol v2.1: compound -> planned keys), availability is the study design;
    without it (protocol v2), availability is whether a prepared row exists.
    """
    comp = real_ctx.data.compounds.drop_duplicates("compound")
    columns = [c for c in PUBLIC_COLUMNS if c in comp.columns]
    compounds = comp[columns].reset_index(drop=True).copy()
    tier = real_ctx.tier
    public_tier = C.Tier(tier.name, tuple(tier.keys), tuple(tier.pool), ())
    params = MappingProxyType({k: v for k, v in real_ctx.params.items()})
    avail = (availability(real_ctx, tier.keys, sorted(heldout)) if design is None
             else design_availability(design, tier.keys, sorted(heldout)))
    base = {"training_compounds": tuple(training_compounds)}
    base.update(extra or {})
    return PublicContext(real_ctx.ft, params, public_tier, PublicData(compounds, MappingProxyType(avail)), base)


def public_view_problems(view, heldout) -> list[str]:
    """Independent check of the whitelist: fields, columns, reference tables and eligibility."""
    problems = []
    names = set(vars(view)) if hasattr(view, "__dict__") else {f for f in PUBLIC_FIELDS if hasattr(view, f)}
    extra_fields = names - set(PUBLIC_FIELDS)
    if extra_fields:
        problems.append(f"unexpected_fields:{sorted(extra_fields)}")
    columns = set(view.data.compounds.columns)
    if columns - set(PUBLIC_COLUMNS):
        problems.append(f"non_public_columns:{sorted(columns - set(PUBLIC_COLUMNS))}")
    for key, table in view.ft.tables.items():
        if set(heldout) & set(table.names):
            problems.append(f"heldout_compound_in_reference_table:{C.action_id(key)}")
    if tuple(view.tier.compounds):
        problems.append("label_derived_eligibility_visible")
    for attr in ("index", "shift", "conditions", "rep1", "rep2", "agreement", "wells", "well_mean"):
        if hasattr(view.data, attr):
            problems.append(f"measurement_field_visible:{attr}")
    if "truth" in view.extra or "klass" in view.extra:
        problems.append("truth_in_extra")
    return problems
