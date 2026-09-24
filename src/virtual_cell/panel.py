"""Declared condition panels: invoke the weights to analyse, then rank and score.

File summary
- Path: src/virtual_cell/panel.py
- Purpose: give the world-model layer a first-class surface for *analytical* use of a
  weight-backed backend — run a declared panel of registered conditions, score the
  written artifacts, rank planning options, and issue a validation receipt only
  where a pre-declared criterion was met on a declared split.
- Core points:
  - A panel is a declared list of registered conditions against one context. The
    backend's own ``assess_query`` decides eligibility, so a panel cannot smuggle an
    unregistered label past the adapter; an abstention stays visible with its reason.
  - Every row keeps its artifact reference, digest and verification result, and is
    labelled ``model_prediction``. A panel never produces evidence, and its ranking
    never satisfies a prerequisite.
  - Gene-set analysis refuses an endpoint the output coordinates cannot express
    before scoring it, and the receipt refuses to grade itself unless the acceptance
    criterion, split and holdout status were declared by the caller.
- Interfaces: `PanelCondition`, `ConditionPanel`, `PanelRow`, `PanelRun`, `run_panel`,
  `read_artifact_values`, `score_panel_gene_sets`, `rank_conditions`,
  `score_panel_against_observations`, `PanelCriterion`, `KnowledgeAnnotation`,
  `load_panel_spec`, `execute_spec`.
- Depends on: interface.py, applicability.py, artifacts.py, calibration.py,
  pathway_readout.py, receipts.py, world_model.py
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .artifacts import vector_sha256
from .calibration import CalibrationPair, score as score_pairs
from .interface import (
    Interval,
    Intervention,
    PredictionRequest,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
    SystemContext,
    VirtualCellWorldModel,
)
from .pathway_readout import (
    BackgroundPool,
    ExpressivityAudit,
    GeneSet,
    expressivity_audit,
    score_gene_set,
    standardised_score,
)
from .receipts import ValidationReceipt
from .world_model import SimulationCostLedger


@dataclass(frozen=True)
class PanelCondition:
    """One registered condition to be queried, named by its exact backend label."""

    identifier: str
    dose: float | None = None
    time_hours: float | None = None


@dataclass(frozen=True)
class KnowledgeAnnotation:
    """A source-scoped biological statement that motivates a panel.

    The annotation says why these conditions and this endpoint were asked about. It is
    labelled ``retrieved_source`` in the report: a curated statement, with its source digest,
    that may motivate a query but can never satisfy a premise or discharge a prerequisite.
    An annotation without a source digest is refused, because an unsourced claim is
    indistinguishable from the caller's own belief.
    """

    statement: str
    source_id: str
    source_digest: str
    relation: str = "supports"
    quantity: str = "unspecified"

    def problems(self) -> tuple[str, ...]:
        issues: list[str] = []
        if not self.statement.strip():
            issues.append("annotation_statement_missing")
        if not self.source_id.strip():
            issues.append("annotation_source_missing")
        if not self.source_digest.strip():
            issues.append("annotation_source_digest_missing")
        return tuple(issues)


@dataclass(frozen=True)
class ConditionPanel:
    """A declared panel: one context, one model version, a bounded condition list."""

    panel_id: str
    context: SystemContext
    model_version: str
    conditions: tuple[PanelCondition, ...]
    readouts: tuple[str, ...]
    mode: str = "drug"
    intended_targets: tuple[str, ...] = ()
    annotations: tuple[KnowledgeAnnotation, ...] = ()

    def __post_init__(self) -> None:
        if not self.conditions:
            raise ValueError("A panel needs at least one condition.")
        if not self.readouts:
            raise ValueError("A panel needs at least one declared readout.")
        duplicates = len({item.identifier for item in self.conditions}) != len(self.conditions)
        if duplicates:
            raise ValueError("Panel condition labels must be unique.")
        for annotation in self.annotations:
            issues = annotation.problems()
            if issues:
                raise ValueError("Panel annotation is not usable: " + ", ".join(issues))

    def build_request(self, condition: PanelCondition, *, index: int) -> PredictionRequest:
        return PredictionRequest(
            request_id=f"{self.panel_id}.{index}",
            case_id=self.panel_id,
            contrast_id="panel",
            plan_version=1,
            intervention=Intervention(
                identifier=condition.identifier,
                mode=self.mode,
                intended_targets=self.intended_targets,
                dose=condition.dose,
                time_hours=condition.time_hours,
            ),
            context=self.context,
            readouts=self.readouts,
            model_version=self.model_version,
        )


@dataclass(frozen=True)
class PanelRow:
    """One condition's outcome: what was asked, what came back, where it was written."""

    condition: str
    request_id: str
    support: str
    applicable: bool
    in_distribution: bool | None
    validation_status: str
    values: Mapping[str, float] = field(default_factory=dict)
    intervals: Mapping[str, Interval] = field(default_factory=dict)
    abstain_reason: str | None = None
    limitations: tuple[str, ...] = ()
    artifact_ref: str | None = None
    artifact_sha256: str | None = None
    artifact_digest_verified: bool | None = None
    compute_cost: float = 0.0
    evidence_kind: str = "model_prediction"

    @property
    def planning_only(self) -> bool:
        return True

    def canonical(self) -> Mapping[str, object]:
        return {
            "condition": self.condition,
            "request_id": self.request_id,
            "support": self.support,
            "applicable": self.applicable,
            "abstain_reason": self.abstain_reason,
            "artifact_sha256": self.artifact_sha256,
            "values": {name: float(value) for name, value in sorted(self.values.items())},
        }


@dataclass
class PanelRun:
    """The panel's rows, its compute ledger and a digest over the answers."""

    panel: ConditionPanel
    rows: tuple[PanelRow, ...]
    ledger: SimulationCostLedger

    def __post_init__(self) -> None:
        encoded = json.dumps(
            [row.canonical() for row in self.rows], sort_keys=True, ensure_ascii=True, allow_nan=False
        ).encode("utf-8")
        self.digest = hashlib.sha256(encoded).hexdigest()

    def rows_by_condition(self) -> Mapping[str, PanelRow]:
        return {row.condition: row for row in self.rows}

    def summary(self) -> Mapping[str, object]:
        abstentions: dict[str, int] = {}
        for row in self.rows:
            if not row.applicable:
                reason = row.abstain_reason or "unspecified"
                abstentions[reason] = abstentions.get(reason, 0) + 1
        return {
            "panel_id": self.panel.panel_id,
            "model_version": self.panel.model_version,
            "context_identifier": self.panel.context.identifier,
            "readouts": list(self.panel.readouts),
            "conditions": len(self.rows),
            "applicable": sum(1 for row in self.rows if row.applicable),
            "abstained": sum(1 for row in self.rows if not row.applicable),
            "abstain_reasons": abstentions,
            "artifacts_verified": sum(1 for row in self.rows if row.artifact_digest_verified),
            "compute": self.ledger.summary(),
            "panel_sha256": self.digest,
            "planning_only": True,
            "is_measurement": False,
        }


def run_panel(
    backend: VirtualCellWorldModel,
    panel: ConditionPanel,
    *,
    ledger: SimulationCostLedger | None = None,
) -> PanelRun:
    """Query every declared condition; an abstention is a row, not an exception."""

    books = ledger or SimulationCostLedger()
    name = getattr(backend, "name", type(backend).__name__)
    rows: list[PanelRow] = []
    for index, condition in enumerate(panel.conditions):
        request = panel.build_request(condition, index=index)
        assessment: QueryAssessment = backend.assess_query(request)
        if assessment.support is not QuerySupport.SUPPORTED:
            books.record(name, abstained=True, violation=False)
            limitations = assessment.limitations + tuple(
                f"missing_input:{item}" for item in assessment.missing_inputs
            )
            rows.append(
                PanelRow(
                    condition=condition.identifier,
                    request_id=request.request_id,
                    support=assessment.support.value,
                    applicable=False,
                    in_distribution=False,
                    validation_status=assessment.validation_status.value,
                    abstain_reason=", ".join(limitations) or assessment.support.value,
                    limitations=limitations,
                    compute_cost=0.0,
                )
            )
            continue
        prediction: StatePrediction = backend.predict(request)
        violation = not prediction.contract_valid
        books.record(name, abstained=not prediction.applicable, violation=violation)
        verified: bool | None = None
        if prediction.artifact_ref and Path(prediction.artifact_ref).is_file():
            verified = (
                prediction.artifact_sha256 is not None
                and _file_sha256(Path(prediction.artifact_ref)) == prediction.artifact_sha256
            )
        rows.append(
            PanelRow(
                condition=condition.identifier,
                request_id=request.request_id,
                support=assessment.support.value,
                applicable=prediction.applicable,
                in_distribution=prediction.in_distribution,
                validation_status=assessment.validation_status.value,
                values=dict(prediction.state_change or {}),
                intervals=dict(prediction.intervals),
                abstain_reason=prediction.abstain_reason,
                limitations=prediction.limitations,
                artifact_ref=prediction.artifact_ref,
                artifact_sha256=prediction.artifact_sha256,
                artifact_digest_verified=verified,
                compute_cost=prediction.compute_cost,
            )
        )
    return PanelRun(panel=panel, rows=tuple(rows), ledger=books)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def read_artifact_values(path: Path | str) -> tuple[Mapping[str, float], Mapping[str, object]]:
    """Read one shift artifact as named coordinates, refusing an unverified vector.

    The artifact records the digest of the float64 bytes it wrote. Recomputing it
    here is what makes an analysis reproducible from the file alone: a vector that
    does not match its own digest is refused rather than scored. Calibrated values
    are returned when the artifact carries them, because that is the summary the
    adapter reported; the choice is named in the second element.
    """

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    block = payload.get("calibrated") or payload.get("raw")
    if not isinstance(block, dict):
        raise ValueError(f"Artifact {path} carries neither a calibrated nor a raw vector.")
    values = [float(value) for value in block.get("values", ())]
    recorded = block.get("sha256_float64")
    if recorded is not None and vector_sha256(values) != recorded:
        raise ValueError(f"Artifact {path} does not match its recorded vector digest.")
    names = payload.get("feature_names")
    if not isinstance(names, list) or len(names) != len(values):
        raise ValueError(f"Artifact {path} does not name one coordinate per value.")
    named = {str(name): value for name, value in zip(names, values) if name}
    what = payload.get("calibrated") and "calibrated" or "raw"
    return named, {"source": what, "endpoint": payload.get("endpoint"), "resolved": len(named)}


@dataclass(frozen=True)
class PanelGeneSetScore:
    """One declared endpoint scored per condition, or the named reason it was not."""

    condition: str
    gene_set_id: str
    gene_set_digest: str
    audit: ExpressivityAudit | None
    raw: float | None = None
    z: float | None = None
    background_mean: float | None = None
    background_sd: float | None = None
    background_pool_id: str = ""
    background_pool_digest: str = ""
    refused_reason: str | None = None
    values_source: str = ""

    @property
    def scored(self) -> bool:
        return self.raw is not None


def score_panel_gene_sets(
    run: PanelRun,
    gene_sets: Sequence[GeneSet],
    *,
    draws: int = 1000,
    seed: int = 0,
    background: BackgroundPool | Sequence[str] | None = None,
) -> tuple[PanelGeneSetScore, ...]:
    """Score declared gene-set endpoints over a panel's artifacts.

    An endpoint whose members are not all present in the artifact's coordinates is
    refused with its audit attached, because a score over surviving members is a
    different quantity from the one that was declared. An endpoint that is expressible
    still needs a **declared** sampling frame before it can be standardised: with no
    pool the row is refused by name rather than standardised against the artifact's own
    coordinates, which was the undeclared sampling choice `standardised_score` fails
    closed on. The pool's identifier and digest travel with every scored row.
    """

    scores: list[PanelGeneSetScore] = []
    for row in run.rows:
        if not row.artifact_ref or not Path(row.artifact_ref).is_file():
            for gene_set in gene_sets:
                scores.append(
                    PanelGeneSetScore(
                        condition=row.condition,
                        gene_set_id=gene_set.identifier,
                        gene_set_digest=gene_set.digest,
                        audit=None,
                        refused_reason="artifact_unavailable",
                    )
                )
            continue
        values, meta = read_artifact_values(row.artifact_ref)
        for gene_set in gene_sets:
            audit = expressivity_audit(gene_set, values.keys(), coordinate_space=str(meta.get("endpoint") or ""))
            if audit.verdict != "expressible":
                scores.append(
                    PanelGeneSetScore(
                        condition=row.condition,
                        gene_set_id=gene_set.identifier,
                        gene_set_digest=gene_set.digest,
                        audit=audit,
                        refused_reason=audit.applicability_reason,
                        values_source=str(meta.get("source", "")),
                    )
                )
                continue
            raw = score_gene_set(values, gene_set)
            if background is None:
                scores.append(
                    PanelGeneSetScore(
                        condition=row.condition,
                        gene_set_id=gene_set.identifier,
                        gene_set_digest=gene_set.digest,
                        audit=audit,
                        refused_reason="background_pool_not_declared",
                        values_source=str(meta.get("source", "")),
                    )
                )
                continue
            if isinstance(background, BackgroundPool):
                blocking = [
                    item
                    for item in background.usable_for(values, gene_set)
                    if item.startswith("background_pool_smaller")
                ]
                if blocking:
                    scores.append(
                        PanelGeneSetScore(
                            condition=row.condition,
                            gene_set_id=gene_set.identifier,
                            gene_set_digest=gene_set.digest,
                            audit=audit,
                            refused_reason=", ".join(blocking),
                            values_source=str(meta.get("source", "")),
                        )
                    )
                    continue
            standard = standardised_score(values, gene_set, draws=draws, seed=seed, background=background)
            scores.append(
                PanelGeneSetScore(
                    condition=row.condition,
                    gene_set_id=gene_set.identifier,
                    gene_set_digest=gene_set.digest,
                    audit=audit,
                    raw=raw,
                    z=standard.z,
                    background_mean=standard.background_mean,
                    background_sd=standard.background_sd,
                    background_pool_id=standard.background_pool_id,
                    background_pool_digest=standard.background_pool_digest,
                    values_source=str(meta.get("source", "")),
                )
            )
    return tuple(scores)


@dataclass(frozen=True)
class PanelRankingEntry:
    condition: str
    value: float
    weight: float
    priority: float
    rank: int


@dataclass(frozen=True)
class PanelNotRanked:
    """A condition the order does not contain, with the reason it is absent."""

    condition: str
    reason: str


@dataclass(frozen=True)
class PanelRanking:
    """A planning order over conditions, with refusals kept beside it."""

    readout: str
    entries: tuple[PanelRankingEntry, ...]
    not_ranked: tuple[PanelNotRanked, ...]
    rule: str = (
        "abs(predicted value) x declared weight, ties broken by condition label; "
        "this ranks what to measure next and never licenses a mechanism claim"
    )


def rank_conditions(
    run: PanelRun,
    readout: str,
    *,
    weight_of: Callable[[str], float] | None = None,
) -> PanelRanking:
    """Order the conditions a model can answer, keeping the ones it cannot visible.

    The magnitude is used rather than the sign, matching the controller's own
    tie-break convention: a direction would be a biological claim the panel cannot
    make from a planning-only prediction. A revoked readout enters through
    ``weight_of`` and is reported as weighted out rather than quietly dropped.
    """

    scored: list[tuple[str, float, float]] = []
    not_ranked: list[PanelNotRanked] = []
    for row in run.rows:
        if not row.applicable or readout not in row.values:
            not_ranked.append(PanelNotRanked(row.condition, row.abstain_reason or "readout_not_returned"))
            continue
        weight = 1.0 if weight_of is None else float(weight_of(row.condition))
        if weight <= 0.0:
            not_ranked.append(PanelNotRanked(row.condition, "weighted_out_by_reliability"))
            continue
        value = float(row.values[readout])
        scored.append((row.condition, value, weight))
    ordered = sorted(scored, key=lambda item: (-abs(item[1]) * item[2], item[0]))
    entries = tuple(
        PanelRankingEntry(
            condition=condition,
            value=value,
            weight=weight,
            priority=abs(value) * weight,
            rank=index,
        )
        for index, (condition, value, weight) in enumerate(ordered, start=1)
    )
    return PanelRanking(readout=readout, entries=entries, not_ranked=tuple(not_ranked))


@dataclass(frozen=True)
class PanelCriterion:
    """What the panel's predictions must achieve, declared before they are scored."""

    endpoint: str
    metric: str
    direction: str
    threshold: float
    minimum_pairs: int
    split: str
    acceptance_criterion: str
    holdout_verified: bool = False
    nominal_level: float = 0.9
    receipt_id: str | None = None

    def __post_init__(self) -> None:
        if self.metric not in {"mean_absolute_error", "interval_coverage"}:
            raise ValueError("metric must be 'mean_absolute_error' or 'interval_coverage'.")
        if self.direction not in {"below", "above"}:
            raise ValueError("direction must be 'below' or 'above'.")
        if self.minimum_pairs < 1:
            raise ValueError("A criterion needs at least one scored pair.")
        if not self.split.strip() or not self.acceptance_criterion.strip():
            raise ValueError("A criterion must name its split and its acceptance criterion.")


def score_panel_against_observations(
    run: PanelRun,
    observations: Mapping[str, float],
    criterion: PanelCriterion,
) -> ValidationReceipt:
    """Compare declared predictions with later real values and issue a receipt.

    The receipt is honest about what it is: ``passed`` is ``None`` when fewer pairs
    than the declared minimum could be scored, ``holdout_verified`` is exactly what
    the caller declared (and defaults to false), and the exit conditions are carried
    as caveats rather than folded into the verdict.
    """

    rows = run.rows_by_condition()
    pairs: list[CalibrationPair] = []
    for condition, observed in sorted(observations.items()):
        row = rows.get(condition)
        if row is None or not row.applicable or criterion.endpoint not in row.values:
            continue
        band = row.intervals.get(criterion.endpoint)
        low = band.low if band is not None else row.values[criterion.endpoint]
        high = band.high if band is not None else row.values[criterion.endpoint]
        pairs.append(
            CalibrationPair(
                predicted=float(row.values[criterion.endpoint]),
                low=float(low),
                high=float(high),
                observed=float(observed),
                strata={"condition": condition},
            )
        )
    report = score_pairs(pairs, nominal_level=criterion.nominal_level)
    metric_value = (
        report.mean_absolute_error if criterion.metric == "mean_absolute_error" else report.interval_coverage
    )
    if len(pairs) < criterion.minimum_pairs or metric_value is None:
        caveats = (f"only {len(pairs)} of {criterion.minimum_pairs} declared pairs were scorable",)
        return ValidationReceipt(
            receipt_id=criterion.receipt_id or f"{run.panel.panel_id}-{criterion.split}-unscored",
            endpoint=criterion.endpoint,
            split=criterion.split,
            acceptance_criterion=criterion.acceptance_criterion,
            metric=criterion.metric,
            value=None,
            threshold=criterion.threshold,
            passed=None,
            holdout_verified=False,
            context_identifier=run.panel.context.identifier,
            model_version=run.panel.model_version,
            independent_units=len(pairs),
            artifact_sha256=run.digest,
            caveats=caveats,
        )
    met = metric_value <= criterion.threshold if criterion.direction == "below" else metric_value >= criterion.threshold
    caveats = [
        f"{criterion.metric}={metric_value:.6g} against threshold {criterion.threshold:g} ({criterion.direction})",
        f"interval coverage {report.interval_coverage} at nominal level {criterion.nominal_level}",
    ]
    if not criterion.holdout_verified:
        caveats.append(
            "the caller did not verify that these observations lie outside the model's training data; "
            "this receipt is not a generalisation result"
        )
    return ValidationReceipt(
        receipt_id=criterion.receipt_id or f"{run.panel.panel_id}-{criterion.split}",
        endpoint=criterion.endpoint,
        split=criterion.split,
        acceptance_criterion=criterion.acceptance_criterion,
        metric=criterion.metric,
        value=float(metric_value),
        threshold=float(criterion.threshold),
        passed=bool(met),
        holdout_verified=criterion.holdout_verified,
        context_identifier=run.panel.context.identifier,
        model_version=run.panel.model_version,
        independent_units=len(pairs),
        artifact_sha256=run.digest,
        caveats=tuple(caveats),
    )


def load_panel_spec(path: Path | str) -> tuple[ConditionPanel, tuple[GeneSet, ...], Mapping[str, float], PanelCriterion | None]:
    """Read one panel specification: the panel, its endpoints, observations and criterion."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("A panel spec must be a JSON object.")
    context = data.get("context")
    if not isinstance(context, dict):
        raise ValueError("A panel spec needs a context object.")
    panel = ConditionPanel(
        panel_id=str(data["panel_id"]),
        context=SystemContext(
            identifier=str(context["identifier"]),
            description=str(context.get("description", "")),
            dataset_id=context.get("dataset_id"),
            control_dataset_id=context.get("control_dataset_id"),
            species=context.get("species"),
            replicate_unit=context.get("replicate_unit"),
        ),
        model_version=str(data["model_version"]),
        conditions=tuple(
            PanelCondition(
                identifier=str(item["identifier"]),
                dose=item.get("dose"),
                time_hours=item.get("time_hours"),
            )
            for item in data["conditions"]
        ),
        readouts=tuple(str(item) for item in data["readouts"]),
        mode=str(data.get("mode", "drug")),
        intended_targets=tuple(str(item) for item in data.get("intended_targets", ())),
        annotations=tuple(
            KnowledgeAnnotation(
                statement=str(item["statement"]),
                source_id=str(item["source_id"]),
                source_digest=str(item["source_digest"]),
                relation=str(item.get("relation", "supports")),
                quantity=str(item.get("quantity", "unspecified")),
            )
            for item in data.get("annotations", ())
        ),
    )
    gene_sets = tuple(
        GeneSet(
            identifier=str(item["identifier"]),
            members=tuple(str(member) for member in item["members"]),
            source=str(item.get("source", "")),
            source_sha256=str(item.get("source_sha256", "")),
            rule=str(item.get("rule", "")),
        )
        for item in data.get("gene_sets", ())
    )
    observations = {str(key): float(value) for key, value in dict(data.get("observations", {})).items()}
    criterion = None
    if data.get("criterion") is not None:
        payload = dict(data["criterion"])
        criterion = PanelCriterion(
            endpoint=str(payload["endpoint"]),
            metric=str(payload["metric"]),
            direction=str(payload["direction"]),
            threshold=float(payload["threshold"]),
            minimum_pairs=int(payload["minimum_pairs"]),
            split=str(payload["split"]),
            acceptance_criterion=str(payload["acceptance_criterion"]),
            holdout_verified=bool(payload.get("holdout_verified", False)),
            nominal_level=float(payload.get("nominal_level", 0.9)),
            receipt_id=payload.get("receipt_id"),
        )
    if observations and criterion is None:
        raise ValueError("Observations were supplied without the criterion that grades them.")
    return panel, gene_sets, observations, criterion


def execute_spec(
    backend: VirtualCellWorldModel,
    spec_path: Path | str,
    *,
    ledger: SimulationCostLedger | None = None,
    draws: int = 1000,
    seed: int = 0,
    background_pool: BackgroundPool | None = None,
) -> Mapping[str, object]:
    """Run one spec end to end and return the JSON-serialisable report.

    ``background_pool`` is the declared sampling frame gene-set endpoints are
    standardised against. It is a parameter rather than a default because the frame
    decides the answer: a caller with none gets refused rows that name the reason,
    never a z drawn from whatever coordinates the artifact happened to carry.
    """

    panel, gene_sets, observations, criterion = load_panel_spec(spec_path)
    run = run_panel(backend, panel, ledger=ledger)
    payload: dict[str, Any] = {
        "schema": "maestro.virtual_cell.panel.v1",
        "planning_only": True,
        "is_measurement": False,
        "summary": run.summary(),
        "knowledge_annotations": [
            {
                "statement": annotation.statement,
                "source_id": annotation.source_id,
                "source_digest": annotation.source_digest,
                "relation": annotation.relation,
                "quantity": annotation.quantity,
                "evidence_kind": "retrieved_source",
                "can_satisfy_a_premise": False,
            }
            for annotation in panel.annotations
        ],
        "rows": [
            {
                **dict(row.canonical()),
                "in_distribution": row.in_distribution,
                "validation_status": row.validation_status,
                "limitations": list(row.limitations),
                "artifact_ref": row.artifact_ref,
                "artifact_digest_verified": row.artifact_digest_verified,
                "compute_cost": row.compute_cost,
                "evidence_kind": row.evidence_kind,
            }
            for row in run.rows
        ],
    }
    if gene_sets:
        if background_pool is not None:
            payload["background_pool"] = {
                "identifier": background_pool.identifier,
                "digest": background_pool.digest,
                "size": background_pool.size,
                "source": background_pool.source,
                "source_sha256": background_pool.source_sha256,
                "rule": background_pool.rule,
            }
        payload["gene_set_scores"] = [
            {
                "condition": item.condition,
                "gene_set_id": item.gene_set_id,
                "gene_set_digest": item.gene_set_digest,
                "verdict": None if item.audit is None else item.audit.verdict,
                "fraction_representable": None if item.audit is None else item.audit.fraction,
                "raw": item.raw,
                "z": item.z,
                "background_pool_id": item.background_pool_id,
                "background_pool_digest": item.background_pool_digest,
                "refused_reason": item.refused_reason,
                "values_source": item.values_source,
            }
            for item in score_panel_gene_sets(
                run, gene_sets, draws=draws, seed=seed, background=background_pool
            )
        ]
    ranking = rank_conditions(run, panel.readouts[0])
    payload["ranking"] = {
        "readout": ranking.readout,
        "rule": ranking.rule,
        "entries": [
            {"rank": entry.rank, "condition": entry.condition, "value": entry.value, "priority": entry.priority}
            for entry in ranking.entries
        ],
        "not_ranked": [
            {"condition": item.condition, "reason": item.reason} for item in ranking.not_ranked
        ],
    }
    if criterion is not None:
        receipt = score_panel_against_observations(run, observations, criterion)
        payload["receipt"] = {
            "receipt_id": receipt.receipt_id,
            "endpoint": receipt.endpoint,
            "split": receipt.split,
            "acceptance_criterion": receipt.acceptance_criterion,
            "metric": receipt.metric,
            "value": receipt.value,
            "threshold": receipt.threshold,
            "passed": receipt.passed,
            "holdout_verified": receipt.holdout_verified,
            "independent_units": receipt.independent_units,
            "artifact_sha256": receipt.artifact_sha256,
            "caveats": list(receipt.caveats),
        }
    return payload
