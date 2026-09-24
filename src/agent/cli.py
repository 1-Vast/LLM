"""Argparse entry point for a bounded MAESTRO turn or real-result feedback loop.

File summary
- Path: src/agent/cli.py
- Purpose: Parse inputs and run one auditable MAESTRO interaction from the command line.
- Core points:
  - Builds the action catalogue and intervention profile from JSON inputs, including each action's typed quantity.
  - `--planner-template` answers every structured agent call from a reviewed template, so the loop runs without a language model and without paid calls.
  - `--virtual-cell` selects the State checkpoint, the computed development-mean backend, or both behind one composite; predictions stay planning-only.
  - `main` runs one turn or a multi-round loop over sourced real measurement results and can write the full record as JSON.
  - `--hypotheses` registers the two explanations' definitions for every round, so a reworded model answer cannot end a loop.
  - A configuration, provider or planner-contract failure exits with status 2 and a one-line reason instead of a traceback.
- Interfaces: `main`
- Depends on: maestro.models, maestro.outcome, virtual_cell, agent.cases, agent.orchestrator, agent.template_client
"""
from __future__ import annotations

import argparse
import dataclasses
import enum
import json
import sys
from pathlib import Path
from typing import Any

from maestro.models import (
    BiologicalQuantity,
    DevelopmentAction,
    EvidenceAction,
    EvidenceActionKind,
    EvidenceKind,
    EvidenceScope,
    FunctionalInterventionProfile,
    MechanismHypothesis,
    MeasurementStatus,
    PremiseRequirement,
)
from maestro.outcome import InterpretationTable, OutcomeRule
from virtual_cell import (
    Intervention,
    PredictionRequest,
    SystemContext,
    VirtualCellQueryTemplate,
    build_backend,
)
from .cases import MeasurementResult
from .configuration import ConfigurationError
from .llm import LLMError
from .orchestrator import MAESTROOrchestrator
from .planner import PlannerContractError
from .template_client import TemplateCompleter, TemplateCompleterError


def main() -> int:
    """Run the MAESTRO CLI and return a process exit code."""

    parser = argparse.ArgumentParser(description="Run a bounded MAESTRO turn or explicit real-result feedback loop.")
    parser.add_argument("request", help="Natural-language scientific request.")
    parser.add_argument("--actions", type=Path, required=True, help="JSON evidence-action catalogue.")
    parser.add_argument("--profile", type=Path, required=True, help="JSON functional intervention profile.")
    parser.add_argument("--image", type=Path, action="append", default=[], help="Optional PNG/JPEG/GIF/WebP asset.")
    parser.add_argument(
        "--dataset",
        type=Path,
        action="append",
        default=[],
        help="Optional CSV, TSV, or JSON dataset for one registered local tool.",
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--case-id", help="Optional durable case identifier for resume and result import.")
    parser.add_argument("--budget", type=float, help="Optional total evidence budget for this case.")
    parser.add_argument(
        "--state-request",
        type=Path,
        help="Optional fully specified JSON prediction request for the registered State checkpoint and dataset.",
    )
    parser.add_argument(
        "--state-template",
        type=Path,
        help="Optional registered model inputs; MAESTRO binds them to the current case and contrast.",
    )
    parser.add_argument("--max-rounds", type=int, default=1, help="Maximum real-result feedback rounds; default is one planning turn.")
    parser.add_argument("--results", type=Path, help="JSON mapping from selected action identifiers to sourced real results.")
    parser.add_argument(
        "--planner-template",
        type=Path,
        help="Reviewed JSON answers for every structured agent call; runs the loop without a language model.",
    )
    parser.add_argument(
        "--virtual-cell",
        choices=("state", "development_mean", "composite", "none"),
        default="state",
        help="Prediction backend: the State checkpoint, the computed development-mean baseline, both, or none.",
    )
    parser.add_argument("--development-partition", type=Path, help="Declared development partition for the computed baseline.")
    parser.add_argument("--dataset-id", default="tahoe_c39", help="Registered dataset the computed baseline is fitted on.")
    parser.add_argument("--rules", type=Path, help="JSON list of reviewed outcome-interpretation rules.")
    parser.add_argument("--state-directory", type=Path, help="Directory for this run's memory, evidence, cases and event logs.")
    parser.add_argument("--artifact-directory", type=Path, help="Directory for virtual-cell prediction artifacts.")
    parser.add_argument("--trace", type=Path, help="Write the full turn or case-loop record as JSON.")
    parser.add_argument(
        "--hypotheses",
        type=Path,
        help="JSON list of exactly two registered hypotheses (identifier, description, proposed_action, causal_factor).",
    )
    arguments = parser.parse_args()
    try:
        return _run(arguments, parser)
    except (ConfigurationError, LLMError, PlannerContractError, TemplateCompleterError) as error:
        # An operational failure, not a defect: say what failed, without a traceback.
        print(f"maestro: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


def _run(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    actions_data = _read_json(arguments.actions)
    profile_data = _read_json(arguments.profile)
    if not isinstance(actions_data, list) or not isinstance(profile_data, dict):
        raise ValueError("Actions must be a JSON list and profile must be a JSON object.")
    actions = tuple(_action(item) for item in actions_data)
    prediction_request = _prediction_request(_read_json(arguments.state_request)) if arguments.state_request else None
    template = _query_template(_read_json(arguments.state_template)) if arguments.state_template else None
    if arguments.max_rounds < 1:
        parser.error("--max-rounds must be positive.")
    if arguments.max_rounds > 1 and not arguments.case_id:
        parser.error("--max-rounds requires --case-id so the loop can resume safely.")
    if prediction_request and template:
        parser.error("Use only one of --state-request and --state-template.")
    if arguments.virtual_cell in ("development_mean", "composite") and not arguments.development_partition:
        parser.error("--virtual-cell development_mean and composite require --development-partition.")
    hypotheses = _hypotheses(_read_json(arguments.hypotheses)) if arguments.hypotheses else ()
    profile = FunctionalInterventionProfile(
        mode=str(profile_data.get("mode", "")),
        nominal_dose=profile_data.get("nominal_dose"),
        functional_states={
            str(key): MeasurementStatus(value)
            for key, value in dict(profile_data.get("functional_states", {})).items()
        },
        protein_abundance=MeasurementStatus(profile_data.get("protein_abundance", "unknown")),
        activity_spectrum=tuple(profile_data.get("activity_spectrum", ())),
        time_hours=profile_data.get("time_hours"),
        context_identifier=profile_data.get("context_identifier"),
        source_ids=tuple(profile_data.get("source_ids", ())),
        measured_fields={
            str(key): MeasurementStatus(value)
            for key, value in dict(profile_data.get("measured_fields", {})).items()
        },
    )
    client = TemplateCompleter.from_file(arguments.planner_template) if arguments.planner_template else None
    controller = MAESTROOrchestrator.from_workspace(
        arguments.workspace,
        state_directory=arguments.state_directory,
        enable_virtual_cell=arguments.virtual_cell != "none",
        client=client,
        virtual_cell=_virtual_cell(arguments),
        interpretation_table=InterpretationTable(_rules(_read_json(arguments.rules))) if arguments.rules else None,
    )
    if arguments.max_rounds == 1:
        turn = controller.run(
            arguments.request,
            available_actions=actions,
            intervention_profile=profile,
            image_paths=tuple(arguments.image),
            dataset_paths=tuple(arguments.dataset),
            case_id=arguments.case_id,
            budget=arguments.budget,
            prediction_request=prediction_request,
            virtual_cell_template=template,
            expected_hypothesis_identifiers=tuple(item.identifier for item in hypotheses),
            expected_hypotheses=hypotheses,
        )
        print(turn.response)
        print(f"session_id={turn.session_id}")
        _write_trace(arguments.trace, turn, client)
        return 0

    results = _results(_read_json(arguments.results)) if arguments.results else {}
    loop = controller.run_case_loop(
        arguments.request,
        available_actions=actions,
        intervention_profile=profile,
        result_provider=lambda action, turn: results.get(action.identifier),
        case_id=arguments.case_id,
        budget=arguments.budget,
        max_rounds=arguments.max_rounds,
        image_paths=tuple(arguments.image),
        dataset_paths=tuple(arguments.dataset),
        prediction_request=prediction_request,
        virtual_cell_template=template,
        expected_hypotheses=hypotheses,
    )
    for index, turn in enumerate(loop.turns, start=1):
        print(f"round={index} session_id={turn.session_id}")
        print(turn.response)
    print(f"case_id={loop.case_id} stop_reason={loop.stop_reason} reflections={len(loop.reflections)}")
    _write_trace(arguments.trace, loop, client)
    return 0


def _virtual_cell(arguments: argparse.Namespace):
    """Build the requested backend from the workspace registry, or ``None``."""

    return build_backend(
        arguments.virtual_cell,
        workspace=arguments.workspace,
        dataset_id=arguments.dataset_id,
        development_partition=arguments.development_partition,
        artifact_directory=arguments.artifact_directory,
    )


def _json_default(value: Any) -> Any:
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=str)
    if isinstance(value, Path):
        return str(value)
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    return str(value)


def _write_trace(path: Path | None, record: Any, client: TemplateCompleter | None) -> None:
    if path is None:
        return
    payload = {
        "record": dataclasses.asdict(record),
        "planner": "reviewed_template" if client is not None else "configured_language_model",
        "template_sha256": getattr(client, "source_sha256", None),
        "template_calls": list(client.calls) if client is not None else None,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, default=_json_default) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _action(data: Any) -> EvidenceAction:
    if not isinstance(data, dict):
        raise ValueError("Each evidence action must be an object.")
    return EvidenceAction(
        identifier=str(data["identifier"]),
        description=str(data["description"]),
        cost=float(data["cost"]),
        distinguishes=tuple(data["distinguishes"]),
        kind=EvidenceActionKind(data.get("kind", "readout_measurement")),
        prerequisites=tuple(data.get("prerequisites", ())),
        readout=data.get("readout"),
        time_hours=data.get("time_hours"),
        expected_conditions={str(key): str(value) for key, value in dict(data.get("expected_conditions", {})).items()},
        prediction_readout=data.get("prediction_readout"),
        prediction_relevance=float(data.get("prediction_relevance", 0.0)),
        source_ids=tuple(data.get("source_ids", ())),
        requires_virtual_prediction=bool(data.get("requires_virtual_prediction", False)),
        expected_outcomes={str(key): str(value) for key, value in dict(data.get("expected_outcomes", {})).items()},
        supplies=tuple(str(item) for item in data.get("supplies", ())),
        execution_context=_optional_context(data.get("execution_context")),
        context_bound=_json_bool(data.get("context_bound", True), "context_bound"),
        quantity=BiologicalQuantity(data.get("quantity", BiologicalQuantity.UNSPECIFIED.value)),
        quantity_is_estimated=_json_bool(data.get("quantity_is_estimated", False), "quantity_is_estimated"),
        entity=data.get("entity"),
        site=data.get("site"),
        units=data.get("units"),
    )


def _hypotheses(data: Any) -> tuple[MechanismHypothesis, ...]:
    """Two registered explanations; their identifiers and meanings then hold for every round."""

    if not isinstance(data, list) or len(data) != 2:
        raise ValueError("--hypotheses must be a JSON list of exactly two hypothesis objects.")
    hypotheses = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Each hypothesis must be an object.")
        action = item.get("proposed_action")
        hypotheses.append(
            MechanismHypothesis(
                identifier=str(item["identifier"]),
                description=str(item["description"]),
                proposed_action=DevelopmentAction(action) if action is not None else None,
                causal_factor=str(item["causal_factor"]) if item.get("causal_factor") is not None else None,
            )
        )
    if hypotheses[0].identifier == hypotheses[1].identifier:
        raise ValueError("--hypotheses must name two distinct identifiers.")
    return tuple(hypotheses)


def _rules(data: Any) -> tuple[OutcomeRule, ...]:
    if not isinstance(data, list):
        raise ValueError("--rules must be a JSON list of rule objects.")
    rules = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Each rule must be an object.")
        rules.append(
            OutcomeRule(
                identifier=str(item["identifier"]),
                outcome_label=str(item["outcome_label"]),
                matched_fields=frozenset(str(value) for value in item.get("matched_fields", ())),
                forbidden_fields=frozenset(str(value) for value in item.get("forbidden_fields", ())),
                required_prefixes=frozenset(str(value) for value in item.get("required_prefixes", ())),
                eliminates=frozenset(str(value) for value in item.get("eliminates", ())),
                scope=EvidenceScope(item.get("scope", EvidenceScope.PLAN_LIMITATION.value)),
                action_identifier=item.get("action_identifier"),
                required_conditions=frozenset(str(value) for value in item.get("required_conditions", ())),
                requires_time_match=_json_bool(item.get("requires_time_match", False), "requires_time_match"),
                boundary=str(item.get("boundary", "")),
                allowed_action_kinds=frozenset(
                    EvidenceActionKind(value) for value in item.get("allowed_action_kinds", ())
                ),
                field_requirements=tuple(_premise_requirement(value) for value in item.get("field_requirements", ())),
                evidence_requirements=tuple(_premise_requirement(value) for value in item.get("evidence_requirements", ())),
                matched_condition_keys=tuple(str(value) for value in item.get("matched_condition_keys", ())),
                minimum_independent_units=_positive_int(
                    item.get("minimum_independent_units", 1), "minimum_independent_units"
                ),
                metric_bounds=_metric_bounds(item.get("metric_bounds", {})),
            )
        )
    return tuple(rules)


def _premise_requirement(data: Any) -> PremiseRequirement:
    if not isinstance(data, dict):
        raise ValueError("Each premise requirement must be an object.")
    return PremiseRequirement(
        field=str(data["field"]),
        quantity=BiologicalQuantity(data.get("quantity", BiologicalQuantity.UNSPECIFIED.value)),
        entity=data.get("entity"),
        site=data.get("site"),
        units=data.get("units"),
        context_identifier=data.get("context_identifier"),
        time_hours=data.get("time_hours"),
        time_tolerance_hours=data.get("time_tolerance_hours"),
        require_direct_measurement=_json_bool(
            data.get("require_direct_measurement", True), "require_direct_measurement"
        ),
        note=str(data.get("note", "")),
    )


def _metric_bounds(data: Any) -> dict[str, tuple[float | None, float | None]]:
    if not isinstance(data, dict):
        raise ValueError("metric_bounds must be an object.")
    result = {}
    for name, bounds in data.items():
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
            raise ValueError("Each metric_bounds entry must contain a lower and upper bound.")
        if any(
            value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)))
            for value in bounds
        ):
            raise ValueError("Metric bounds must be numbers or null.")
        lower, upper = bounds
        result[str(name)] = (
            float(lower) if lower is not None else None,
            float(upper) if upper is not None else None,
        )
    return result


def _json_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a JSON boolean.")
    return value


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def _prediction_request(data: Any) -> PredictionRequest:
    if not isinstance(data, dict):
        raise ValueError("State request must be a JSON object.")
    intervention = data.get("intervention")
    context = data.get("context")
    if not isinstance(intervention, dict) or not isinstance(context, dict):
        raise ValueError("State request requires intervention and context objects.")
    return PredictionRequest(
        request_id=str(data["request_id"]),
        case_id=str(data["case_id"]),
        contrast_id=str(data["contrast_id"]),
        plan_version=int(data["plan_version"]),
        intervention=Intervention(
            identifier=str(intervention["identifier"]),
            mode=str(intervention["mode"]),
            intended_targets=tuple(str(item) for item in intervention.get("intended_targets", ())),
            dose=intervention.get("dose"),
            dose_unit=intervention.get("dose_unit"),
            time_hours=intervention.get("time_hours"),
        ),
        context=SystemContext(
            identifier=str(context["identifier"]),
            description=str(context["description"]),
            dataset_id=context.get("dataset_id"),
            control_dataset_id=context.get("control_dataset_id"),
            species=context.get("species"),
            replicate_unit=context.get("replicate_unit"),
        ),
        readouts=tuple(str(item) for item in data.get("readouts", ())),
        model_version=str(data["model_version"]),
    )


def _query_template(data: Any) -> VirtualCellQueryTemplate:
    if not isinstance(data, dict) or not isinstance(data.get("context"), dict):
        raise ValueError("State template requires a context object.")
    context = data["context"]
    return VirtualCellQueryTemplate(
        intervention_identifier=str(data["intervention_identifier"]),
        intervention_mode=str(data["intervention_mode"]),
        context=SystemContext(
            identifier=str(context["identifier"]),
            description=str(context["description"]),
            dataset_id=context.get("dataset_id"),
            control_dataset_id=context.get("control_dataset_id"),
            species=context.get("species"),
            replicate_unit=context.get("replicate_unit"),
        ),
        readouts=tuple(str(item) for item in data.get("readouts", ())),
        model_version=str(data["model_version"]),
        action_interventions={str(key): str(value) for key, value in dict(data.get("action_interventions", {})).items()},
    )


def _results(data: Any) -> dict[str, MeasurementResult]:
    if not isinstance(data, dict):
        raise ValueError("--results must be a JSON object keyed by action identifier.")
    results: dict[str, MeasurementResult] = {}
    for action_id, value in data.items():
        if not isinstance(value, dict):
            raise ValueError("Each --results entry must be an object.")
        units = value.get("independent_units")
        replicates = value.get("biological_replicates")
        results[str(action_id)] = MeasurementResult(
            action_identifier=str(action_id),
            statement=str(value["statement"]),
            source_id=str(value["source_id"]),
            context_identifier=value.get("context_identifier"),
            time_hours=value.get("time_hours"),
            independent_units=_positive_int(units, "independent_units") if units is not None else None,
            quality_passed=_json_bool(value["quality_passed"], "quality_passed"),
            conditions={str(key): str(item) for key, item in dict(value.get("conditions", {})).items()},
            metrics={str(key): str(item) for key, item in dict(value.get("metrics", {})).items()},
            record_count=_positive_int(value.get("record_count", 1), "record_count"),
            biological_replicates=_positive_int(replicates, "biological_replicates") if replicates is not None else None,
            evidence_kind=EvidenceKind(value.get("evidence_kind", EvidenceKind.REAL_MEASUREMENT.value)),
            interpretation_fields=tuple(str(item) for item in value.get("interpretation_fields", ())),
            limitations=tuple(str(item) for item in value.get("limitations", ())),
            result_id=value.get("result_id"),
        )
    return results


def _optional_context(value: object) -> str | None:
    """An action's declared execution context; absent means the case's own context."""

    return value.strip() if isinstance(value, str) and value.strip() else None


if __name__ == "__main__":
    raise SystemExit(main())
