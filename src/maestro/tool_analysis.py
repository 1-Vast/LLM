"""Structured, read-only analyses behind the registered local tool adapters."""
from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Mapping

from .composition import PlanComposer, rank_plans, unmet_prerequisites
from .models import (
    BiologicalQuantity, CompositionRule, EvidenceAction, FunctionalInterventionProfile,
    MechanismContrast, MechanismHypothesis,
)
from .acquisition import select_expected_coverage
from .tool_contracts import (
    TOOL_SCHEMA_VERSION, json_dumps, json_loads, json_value, nonempty_string,
    nonnegative_number, object_fields, string_list,
)


def _result(payload: dict[str, Any], observations: list[str], limitations: list[str]) -> dict[str, Any]:
    return json_value({"schema_version": TOOL_SCHEMA_VERSION, "payload": payload,
                       "observations": observations, "limitations": limitations, "artifacts": []})


def _source(path: Path) -> dict[str, Any]:
    return {"dataset": path.name, "provenance_verified": False}


def _table(path: Path):
    """Yield validated rows without accepting duplicate headers or ragged records."""
    if path.suffix.lower() not in {".csv", ".tsv"}:
        raise ValueError("Only CSV and TSV are supported.")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t" if path.suffix.lower() == ".tsv" else ",", strict=True)
        fields = reader.fieldnames or []
        if not fields or any(not field.strip() for field in fields) or len(fields) != len(set(fields)):
            raise ValueError("Table requires unique nonempty column names.")
        yield fields
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("Table row width does not match its header.")
            yield row


def data_profile(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Describe supplied file structure, not biological validity or independence."""
    parameters = json_value(parameters)
    path = Path(parameters["dataset_path"])
    sample_rows = parameters.get("sample_rows", 5)
    if type(sample_rows) is not int or not 1 <= sample_rows <= 25:
        raise ValueError("sample_rows must be an integer between 1 and 25.")
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        reader = _table(path)
        fields = next(reader)
        rows, missing, count = [], dict.fromkeys(fields, 0), 0
        for row in reader:
            count += 1
            for field in fields:
                if not row[field].strip():
                    missing[field] += 1
            if len(rows) < sample_rows:
                rows.append(row)
        payload = {"format": suffix.lstrip("."), "row_count": count, "columns": fields,
                   "sample_rows": rows, "missing_counts": missing, "sample_truncated": count > len(rows)}
        observations = [f"Dataset {path.name} has {count} data rows and {len(fields)} columns.",
                        "Columns: " + ", ".join(fields) + ".", "Sample rows: " + json_dumps(rows),
                        "Missing-value counts: " + json_dumps(missing) + "."]
    elif suffix == ".json":
        data = json_loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            sample = data[:sample_rows]
            keys = sorted({key for item in sample if isinstance(item, dict) for key in item})
            payload = {"format": "json", "shape": "array", "item_count": len(data), "sample_items": sample,
                       "sampled_fields": keys, "sample_truncated": len(data) > len(sample)}
            observations = [f"Dataset {path.name} is a JSON array with {len(data)} top-level items.",
                            "Fields visible in sampled objects: " + ", ".join(keys) + ".",
                            "Sample items: " + json_dumps(sample)]
        elif isinstance(data, dict):
            payload = {"format": "json", "shape": "object", "keys": sorted(data), "key_count": len(data)}
            observations = [f"Dataset {path.name} is a JSON object with {len(data)} top-level keys.",
                            "Top-level keys: " + ", ".join(sorted(data)) + "."]
        else:
            payload = {"format": "json", "shape": "scalar", "value": data}
            observations = [f"Dataset {path.name} contains a top-level JSON scalar."]
    else:
        raise ValueError(f"Unsupported dataset type: {suffix}")
    payload.update({"analysis": "data_profile", "source": _source(path), "independent_unit_count": None})
    return _result(payload, observations, [
        "The profile describes supplied file values, not biological validity or causal interpretation.",
        "Source provenance and independent units are not established by row counts.",
        "JSON keys are sampled at the top level; nested data require a task-specific adapter.",
    ])


def column_summary(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize one numeric column without treating rows as independent samples."""
    parameters = json_value(parameters)
    path = Path(parameters["dataset_path"])
    column = nonempty_string(parameters["column"], "column")
    reader = _table(path)
    if column not in next(reader):
        raise ValueError(f"Column '{column}' was not found in {path.name}.")
    values, missing, non_numeric = [], 0, 0
    for row in reader:
        raw = row[column].strip()
        if not raw:
            missing += 1
            continue
        try:
            value = float(raw)
        except ValueError:
            non_numeric += 1
            continue
        if not math.isfinite(value):
            raise ValueError(f"Non-finite numeric value in column {column}.")
        values.append(value)
    if not values:
        raise ValueError(f"Column '{column}' contains no parseable numeric values.")
    stats = {"count": len(values), "minimum": min(values), "maximum": max(values),
             "mean": statistics.fmean(values), "median": statistics.median(values),
             "sample_standard_deviation": statistics.stdev(values) if len(values) > 1 else None}
    if any(value is not None and not math.isfinite(value) for value in stats.values()):
        raise ValueError("Summary overflowed finite numeric range.")
    observations = [f"Column {column} in {path.name}: n={len(values)}, missing_or_non_numeric={missing + non_numeric}.",
                    f"Minimum={stats['minimum']:.6g}; maximum={stats['maximum']:.6g}; mean={stats['mean']:.6g}; median={stats['median']:.6g}."]
    if len(values) > 1:
        observations.append(f"Sample standard deviation={stats['sample_standard_deviation']:.6g}.")
    return _result({"analysis": "column_summary", "source": _source(path), "column": column, "statistics": stats,
                    "missing_count": missing, "non_numeric_count": non_numeric,
                    "row_count": len(values) + missing + non_numeric, "independent_unit_count": None}, observations, [
        "The summary is descriptive and does not test a biological hypothesis or control confounding.",
        "Missing and non-numeric values are reported separately; source provenance and independence remain unknown.",
    ])


def table_filter(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Apply one declarative condition and return a bounded matching-row sample."""
    parameters = json_value(parameters)
    path = Path(parameters["dataset_path"])
    column = nonempty_string(parameters["column"], "column")
    operator = nonempty_string(parameters["operator"], "operator")
    raw_value = parameters["value"]
    if type(raw_value) not in (str, int, float):
        raise ValueError("value must be a string or finite number.")
    value, max_rows = str(raw_value), parameters.get("max_rows", 10)
    if type(max_rows) is not int or not 1 <= max_rows <= 100:
        raise ValueError("max_rows must be an integer between 1 and 100.")
    if operator not in {"equals", "contains", "greater_than", "less_than"}:
        raise ValueError(f"Unsupported operator: {operator}")
    threshold = None
    if operator in {"greater_than", "less_than"}:
        threshold = float(value)
        if not math.isfinite(threshold):
            raise ValueError("Non-finite numeric filter threshold.")
    reader = _table(path)
    if column not in next(reader):
        raise ValueError(f"Column '{column}' was not found in {path.name}.")
    matches = []
    count = missing = non_numeric = row_count = 0
    for row in reader:
        row_count += 1
        candidate = row[column].strip()
        if not candidate:
            missing += 1
            continue
        if threshold is not None:
            try:
                number = float(candidate)
            except ValueError:
                non_numeric += 1
                continue
            if not math.isfinite(number):
                raise ValueError("Non-finite numeric filter input.")
            matched = number > threshold if operator == "greater_than" else number < threshold
        else:
            matched = candidate == value if operator == "equals" else value.lower() in candidate.lower()
        if matched:
            count += 1
            if len(matches) < max_rows:
                matches.append(row)
    return _result({"analysis": "table_filter", "source": _source(path),
                    "condition": {"column": column, "operator": operator, "value": raw_value},
                    "matched_count": count, "sample_rows": matches, "sample_truncated": count > len(matches),
                    "row_count": row_count, "missing_count": missing, "non_numeric_count": non_numeric,
                    "independent_unit_count": None}, [
        f"Filter {column} {operator} {value!r} matched {count} rows in {path.name}.",
        "Bounded matching-row sample: " + json_dumps(matches),
    ], ["Filtering does not establish enrichment, association, causality, or independent sample size.",
        f"At most {max_rows} matching rows are returned; missing or invalid numeric values are not matched."])


def _sources(items: Any, *, allow_unknown: bool = False) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list) or (not items and not allow_unknown):
        raise ValueError("sources must declare source provenance as an array.")
    sources = {}
    for item in items:
        source = object_fields(item, {"id", "independence_group"}, set(), "source")
        identifier = nonempty_string(source["id"], "source.id")
        if identifier in sources:
            raise ValueError("Duplicate source id.")
        if source["independence_group"] is not None or not allow_unknown:
            nonempty_string(source["independence_group"], "source.independence_group")
        sources[identifier] = source
    return sources


def _unique_strings(value: Any, field: str) -> list[str]:
    result = string_list(value, field)
    if len(result) != len(set(result)):
        raise ValueError(f"Duplicate {field}.")
    return result


def evidence_bundle_optimize(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Exactly select a fixed declared menu; optionally rank gated plans separately."""
    path = Path(parameters["dataset_path"])
    data = object_fields(json_loads(path.read_text(encoding="utf-8-sig")),
                         {"schema_version", "budget", "cost_unit", "context", "time_hours", "required", "sources", "actions"},
                         {"weights", "composition"}, "evidence bundle")
    if data["schema_version"] != TOOL_SCHEMA_VERSION:
        raise ValueError("Unknown evidence bundle schema_version.")
    budget = nonnegative_number(data["budget"], "budget")
    cost_unit = nonempty_string(data["cost_unit"], "cost_unit")
    context = nonempty_string(data["context"], "context")
    time = nonnegative_number(data["time_hours"], "time_hours")
    required = _unique_strings(data["required"], "required")
    if not required:
        raise ValueError("required must contain unique named requirements.")
    sources = _sources(data["sources"])
    records = data["actions"]
    if not isinstance(records, list) or len(records) > 16:
        raise ValueError("exact_candidate_limit_exceeded: actions must be an array of at most 16 candidates.")
    actions, seen = [], set()
    for item in records:
        object_fields(item, {"id", "cost", "cost_unit", "distinguishes", "source_ids", "context", "time_hours",
                             "independent_unit", "quantity"},
                      {"prerequisites", "description", "supplies", "interpretation_gate", "expected_outcomes", "detection_power"}, "action")
        identifier = nonempty_string(item["id"], "action.id")
        if identifier in seen:
            raise ValueError("Duplicate action id.")
        seen.add(identifier)
        cost = nonnegative_number(item["cost"], "action.cost")
        if item["cost_unit"] != cost_unit:
            raise ValueError("Action cost_unit mismatch; no implicit cost conversion.")
        if item["context"] != context or nonnegative_number(item["time_hours"], "action.time_hours") != time:
            raise ValueError("Action context/time mismatch.")
        nonempty_string(item["independent_unit"], "action.independent_unit")
        source_ids = _unique_strings(item["source_ids"], "action.source_ids")
        if not source_ids or set(source_ids) - sources.keys():
            raise ValueError("Action has missing or unknown source_ids.")
        quantity = BiologicalQuantity(item["quantity"])
        if quantity is BiologicalQuantity.UNSPECIFIED:
            raise ValueError("Action quantity must be known; unspecified is not a measurement capability.")
        distinguishes = _unique_strings(item["distinguishes"], "action.distinguishes")
        if set(distinguishes) - set(required):
            raise ValueError("Action distinguishes must refer to declared requirements.")
        prerequisites = _unique_strings(item.get("prerequisites", []), "action.prerequisites")
        supplies = _unique_strings(item.get("supplies", []), "action.supplies")
        gate = item.get("interpretation_gate")
        if gate is not None:
            nonempty_string(gate, "action.interpretation_gate")
        outcomes = item.get("expected_outcomes", {})
        if not isinstance(outcomes, dict) or set(outcomes) - set(required):
            raise ValueError("expected_outcomes must refer only to declared requirements.")
        for value in outcomes.values():
            nonempty_string(value, "expected_outcome")
        actions.append(EvidenceAction(
            identifier=identifier, description=nonempty_string(item.get("description", identifier), "action.description"),
            cost=cost, distinguishes=tuple(distinguishes), prerequisites=tuple(prerequisites),
            source_ids=tuple(source_ids), quantity=quantity, execution_context=context, time_hours=time,
            supplies=tuple(supplies), interpretation_gate=gate, expected_outcomes=outcomes,
            detection_power=item.get("detection_power"),
        ))
    nonnegative_number(sum(action.cost for action in actions), "aggregate candidate cost")
    weights = data.get("weights", {})
    if not isinstance(weights, dict) or set(weights) - set(required):
        raise ValueError("weights must refer only to declared requirements.")
    weights = {key: nonnegative_number(value, f"weight.{key}") for key, value in weights.items()}
    nonnegative_number(sum(weights.get(key, 1.0) for key in required), "aggregate weight")
    profile = FunctionalInterventionProfile(mode="declared_plan", context_identifier=context, time_hours=time)
    ungated = sorted((action for action in actions if action.interpretation_gate is None), key=lambda action: action.identifier)
    expected = select_expected_coverage(frozenset(required), ungated, profile, budget, weights=weights,
                                       source_groups={key: value["independence_group"] for key, value in sources.items()})
    plan = expected.plan
    selected = [action.identifier for action in plan.actions]
    payload = {
        "analysis": "evidence_bundle_optimize", "solver": "select_expected_coverage", "exact": True,
        "exact_scope": "fixed_ungated_executable_menu_only", "source": _source(path),
        "objective_order": ["maximize_declared_weighted_expected_coverage", "minimize_cost", "minimize_action_count", "identifier"],
        "coverage_probability": dict(expected.coverage_probability),
        "expected_coverage": expected.expected_coverage,
        "assumptions": list(expected.assumptions), "dependence_groups": dict(expected.dependence_groups),
        "rejected": [asdict(item) for item in expected.rejected],
        "selected_action_ids": selected, "selected_declarations": [item for item in records if item["id"] in selected],
        "covered": sorted(plan.covered), "uncovered": sorted(plan.uncovered),
        "coverage_score": sum(weights.get(key, 1.0) for key in sorted(plan.covered)),
        "total_cost": plan.total_cost, "budget": budget, "cost_unit": cost_unit, "context": context, "time_hours": time,
        "waiting_for_prerequisites": list(plan.waiting_for_prerequisites),
        "missing_prerequisites": sorted({key for action in actions for key in action.prerequisites}),
        "blocked_interpretation_gates": [{"action_id": action.identifier, "premise": action.interpretation_gate}
                                         for action in actions if action.interpretation_gate is not None],
        "sources": list(sources.values()), "independent_measurement_count": None,
        "composition": _composition_report(data.get("composition"), required, actions, records, profile, budget),
    }
    return _result(payload, [f"Selected {len(selected)} declared actions covering {len(plan.covered)}/{len(required)} requirements at cost {plan.total_cost:g}."], [
        "Exact only for the supplied executable ungated menu of at most 16 candidates and declared additive costs/coverage; not global research utility.",
        "Costs, quantity capabilities, coverage and provenance are declarations, not verified purchases or experimental results.",
        "Prerequisites and interpretation gates remain unknown; selection never certifies measured premises or independent replication.",
        "Shared sources or independent units do not earn extra coverage; overlapping requirements are counted once.",
        "Exact refers to exhaustive subset enumeration with Python floating-point comparisons, not exact rational arithmetic.",
        "Optional two-stage compositions are ranked separately by declared worst-case residual then cost, not jointly optimized with the set cover; no probabilities or discounts are inferred.",
    ])


def _composition_report(spec, required, actions, records, profile, budget) -> dict[str, Any] | None:
    """Use the existing composer on a bounded declared two-hypothesis closure."""
    if spec is None:
        return None
    object_fields(spec, {"id", "shared_control_saving"}, set(), "composition")
    if len(required) != 2:
        raise ValueError("Composition requires exactly two declared hypothesis identifiers.")
    rule = CompositionRule(nonempty_string(spec["id"], "composition.id"),
                           nonnegative_number(spec["shared_control_saving"], "shared_control_saving"))
    contrast = MechanismContrast("declared_bundle", tuple(MechanismHypothesis(key, key) for key in required), (), None)
    missing = unmet_prerequisites(actions, profile)
    units = {item["id"]: item["independent_unit"] for item in records}
    plans, rejected = [], []
    for gate in actions:
        for readout in actions:
            if gate is readout or readout.interpretation_gate not in gate.supplies:
                continue
            pair = {"gate_id": gate.identifier, "readout_id": readout.identifier}
            reason = None
            if units[gate.identifier] != units[readout.identifier]:
                reason = "independent_unit_mismatch"
            elif rule.shared_control_saving >= min(readout.cost, gate.cost):
                reason = "saving_must_be_less_than_each_component_cost"
            elif set(readout.expected_outcomes) != set(required):
                reason = "incomplete_expected_outcomes"
            if reason is not None:
                rejected.append({**pair, "reason": reason})
                continue
            composed = PlanComposer(rule).compose(contrast, (gate, readout), missing)
            composed = tuple(plan for plan in composed if plan.gate.identifier == gate.identifier)
            if not composed:
                rejected.append({**pair, "reason": "composition_contract_not_satisfied"})
            plans.extend(composed)
    ranked = rank_plans(plans, contrast)
    candidates = []
    for evaluation in ranked:
        plan = evaluation.plan
        candidates.append({
            "id": plan.identifier, "gate_id": plan.gate.identifier, "readout_id": plan.readout.identifier,
            "premise": plan.authorization().premise, "premise_status": "unknown",
            "continue_only_if_gate_passes": True, "total_cost_if_gate_passes": plan.cost,
            "gate_cost": plan.gate_cost, "cost_if_gate_fails": plan.gate_cost,
            "within_budget": plan.cost <= budget and plan.gate_cost <= budget,
            "worst_declared_case_residual": evaluation.worst_case_residual,
            "objective": evaluation.objective, "confirmed": False,
        })
    affordable = [item for item in candidates if item["within_budget"]]
    return {"solver": "PlanComposer/rank_plans", "joint_set_cover_optimization": False,
            "rule": spec, "constraints": ["two_declared_hypotheses", "same_context_time_and_independent_unit",
                                         "gate_executable_now", "gate_supplies_interpretation_premise",
                                         "complete_declared_outcomes", "saving_less_than_each_component_cost",
                                         "gate_and_pass_branch_within_budget"],
            "objective_order": ["minimize_worst_declared_case_residual", "minimize_residual_plus_0.25_cost", "identifier"],
            "ranked_candidates": candidates, "rejected": rejected,
            "preferred_plan_id": affordable[0]["id"] if affordable else None}


_QUANTITIES = {"transcript": "rna_abundance", "protein": "protein_abundance", "occupancy": "target_occupancy",
               "activity": "proximal_activity", "morphology": "morphology_feature"}
_SCOPE = ("pair_id", "context", "time_hours", "independent_unit", "replicate", "entity", "contrast_id")


@dataclass(frozen=True)
class ModalityRecord:
    """One declared scalar record with explicit pairing, provenance and quantity."""
    id: str
    pair_id: str | None
    modality: str
    source_id: str | None
    context: str | None
    time_hours: float | None
    independent_unit: str | None
    replicate: str | None
    quantity: str | None
    entity: str | None
    contrast_id: str | None
    feature: str | None
    unit: str | None
    value: float | None
    reference_value: float | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModalityRecord:
        """Reject untyped substitutions, non-finite values and undeclared fields."""
        fields = set(cls.__dataclass_fields__)
        object_fields(data, fields, set(), "modality record")
        nonempty_string(data["id"], "record.id")
        modality = nonempty_string(data["modality"], "record.modality")
        if modality not in _QUANTITIES:
            raise ValueError("Unknown modality.")
        if data["quantity"] is not None and data["quantity"] != _QUANTITIES[modality]:
            raise ValueError("Modality/quantity mismatch; RNA, occupancy, activity and morphology are distinct.")
        for key in fields - {"time_hours", "value", "reference_value"}:
            if data[key] is not None:
                nonempty_string(data[key], f"record.{key}")
        if data["time_hours"] is not None:
            nonnegative_number(data["time_hours"], "record.time_hours")
        for key in ("value", "reference_value"):
            value = data[key]
            try:
                valid = value is None or (type(value) in (int, float) and math.isfinite(value))
            except OverflowError:
                valid = False
            if not valid:
                raise ValueError(f"record.{key} must be a finite numeric value or null.")
        return cls(**data)


def multimodal_alignment(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Report pairing QC and scoped directional review candidates, never inference."""
    path = Path(parameters["dataset_path"])
    data = object_fields(json_loads(path.read_text(encoding="utf-8-sig")),
                         {"schema_version", "sources", "records"}, {"visibility"}, "paired modality dataset")
    if data["schema_version"] != TOOL_SCHEMA_VERSION:
        raise ValueError("Unknown paired modality schema_version.")
    sources = _sources(data["sources"], allow_unknown=True)
    if not isinstance(data["records"], list) or not 1 <= len(data["records"]) <= 128:
        raise ValueError("records must be an array of 1 to 128 paired modality records.")
    raw_records = data["records"]
    visibility = data.get("visibility")
    if visibility is None:
        visibility = {"stage": "retrospective", "acquisition_cost": None, "cost_unit": None,
                      "withheld_record_ids": [], "decision_use": "retrospective_qc_only"}
    else:
        visibility = dict(object_fields(visibility, {"stage", "available_record_ids", "acquisition_cost", "cost_unit"}, set(), "visibility"))
        if visibility["stage"] not in {"pre_experiment", "post_acquisition", "retrospective"}:
            raise ValueError("unknown_visibility_stage")
        nonnegative_number(visibility["acquisition_cost"], "visibility.acquisition_cost")
        nonempty_string(visibility["cost_unit"], "visibility.cost_unit")
        available = set(_unique_strings(visibility["available_record_ids"], "visibility.available_record_ids"))
        identifiers = [nonempty_string(item.get("id"), "record.id") for item in raw_records]
        if len(set(identifiers)) != len(identifiers) or available - set(identifiers):
            raise ValueError("visibility_record_identity_mismatch")
        visibility["withheld_record_ids"] = sorted(set(identifiers) - available)
        visibility["decision_use"] = "declared_visible_inputs_only_not_verified_acquisition"
        # Filter before measurement parsing, pairing, direction checks or prompt serialization.
        raw_records = [item for item in raw_records if item["id"] in available]
    records = [asdict(ModalityRecord.from_dict(item)) for item in raw_records]
    seen, eligible, missing = set(), [], []
    for record in records:
        identifier, source_id = record["id"], record["source_id"]
        if identifier in seen:
            raise ValueError("Duplicate modality record id.")
        seen.add(identifier)
        if source_id is not None and source_id not in sources:
            raise ValueError("Unknown record source_id.")
        missing_fields = sorted(key for key, value in record.items() if value is None)
        if source_id in sources and sources[source_id]["independence_group"] is None:
            missing_fields.append("source_independence_group")
        if missing_fields:
            missing.append({"record_id": identifier, "missing_fields": missing_fields})
        if not set(missing_fields) - {"reference_value", "value"}:
            eligible.append(record)
    groups = defaultdict(list)
    for record in eligible:
        groups[tuple(record[key] for key in _SCOPE)].append(record)
    mismatches = []
    for left, right in combinations(eligible, 2):
        if left["pair_id"] == right["pair_id"]:
            differences = [key for key in _SCOPE[1:] if left[key] != right[key]]
            if differences:
                mismatches.append({"record_ids": [left["id"], right["id"]], "fields": differences})
    aligned, ambiguous, unpaired, candidates = [], [], [], []
    for key, group in groups.items():
        modalities = [item["modality"] for item in group]
        scope = dict(zip(_SCOPE, key))
        info = {**scope, "record_ids": [item["id"] for item in group], "modalities": sorted(set(modalities)),
                "missing_modalities": sorted(set(_QUANTITIES) - set(modalities)),
                "source_ids": sorted({item["source_id"] for item in group}),
                "source_independence_groups": sorted({sources[item["source_id"]]["independence_group"] for item in group}),
                "declared_independent_unit_count": 1}
        if len(modalities) != len(set(modalities)):
            ambiguous.append({**info, "reason": "duplicate_modality_in_same_replicate"})
            continue
        if len(group) < 2:
            unpaired.extend(item["id"] for item in group)
            continue
        aligned.append(info)
        for left, right in combinations(group, 2):
            if {left["modality"], right["modality"]} & {"morphology", "occupancy"}:
                continue
            directions = [_direction(item) for item in (left, right)]
            if None not in directions and set(directions) == {"increase", "decrease"}:
                candidates.append({
                    **scope, "record_ids": [left["id"], right["id"]], "directions": directions,
                    "quantities": [left["quantity"], right["quantity"]],
                    "source_ids": [left["source_id"], right["source_id"]],
                    "kind": "cross_quantity_direction_discordance", "requires_review": True,
                    "expected_direction_relation": "not_assumed", "declared_independent_unit_count": 1,
                })
    return _result({
        "analysis": "multimodal_alignment", "source": _source(path), "visibility": visibility,
        "alignment_qc": {"record_count": len(records), "aligned_groups": aligned, "mismatches": mismatches,
                         "missing": missing, "ambiguous_groups": ambiguous, "unpaired_record_ids": unpaired,
                         "excluded_record_ids": [item["id"] for item in records if item not in eligible],
                         "declared_independent_unit_count": len({item["independent_unit"] for item in eligible}),
                         "verified_independent_measurement_count": None},
        "contradiction_candidates": candidates, "records": records, "sources": list(sources.values()),
    }, [f"Alignment QC: {len(aligned)} paired groups, {len(mismatches)} scope mismatches, {len(candidates)} direction-discordance candidates."], [
        "Only supplied paired scalar records are inspected; no embeddings, image inference, significance tests, or causal conclusions are generated.",
        "RNA abundance, protein abundance, target occupancy, proximal activity and morphology are distinct quantities, not interchangeable measurements.",
        "Opposite within-record directions against supplied references are review candidates, not established contradictions or calibrated effect comparisons; equal directions do not prove agreement.",
        "Occupancy and morphology participate only in pairing QC, not activity-direction inference.",
        "Source identities, references, replicates and independent units are declarations, not verified provenance; multiple modalities or technical replicates on one unit are not independent replications.",
        "Exact context, time, replicate, entity, contrast and independent-unit matching is required; missing quantities stay missing and no imputation is performed.",
        "Visibility and acquisition costs are caller declarations, not verified receipts; retrospective QC is not a pre-experiment risk predictor.",
    ])


def _direction(record: Mapping[str, Any]) -> str | None:
    value, reference = record["value"], record["reference_value"]
    if value is None or reference is None:
        return None
    if value == reference:
        return "unchanged"
    return "increase" if value > reference else "decrease"
