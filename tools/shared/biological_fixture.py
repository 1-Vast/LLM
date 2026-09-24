"""Constructed multi-assay fixtures for software verification, never biological data.

File summary
- Path: tools/shared/biological_fixture.py
- Purpose: Exercise the production chain with separate engagement, function and phenotype records.
- Core points: thresholds, values and assay capabilities are declared synthetic test inputs.
- Interfaces: contract, results, orchestrator, run_chain
- Depends on: agent, maestro, tools.shared.stub_client
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable

from agent.audit import RunLogger
from agent.cases import CaseStore, MeasurementResult
from agent.context import ContextBuilder, TaskInterpreter
from agent.knowledge import EvidenceLedger
from agent.memory import MemoryStore
from agent.orchestrator import MAESTROOrchestrator
from agent.planner import MechanismContrastPlanner
from agent.vision import VisualInspector
from maestro import (
    EvidenceAction, EvidenceActionKind, EvidenceScope, FunctionalInterventionProfile,
    InterpretationTable, MODE_COMPARATOR_FIELD, MODE_DIFFERENCE_FIELD,
    SUFFICIENT_FUNCTION_FIELD, OutcomeRule,
)
from maestro.models import BiologicalQuantity, PremiseRequirement
from tools.shared.stub_client import StubClient

ENGAGEMENT = "engagement:target:measured"
PHENOTYPE = "phenotype:viability:unaffected"
CONDITIONS = {"intervention": "fixture_compound", "exposure": "fixture_level", "sample_id": "fixture_batch_1"}
TASK = {
    "task_type": "mechanism_diagnosis", "research_question": "Test the constructed mechanistic chain.",
    "target_or_targets": ["TARGET"], "interventions": ["fixture_compound"],
    "biological_context": "fixture_cells", "phenotype_endpoint": "viability",
    "supplied_evidence": [], "constraints": [], "missing_information": [], "needs_visual_review": False,
}
PLAN = {
    "identifier": "typed-chain", "hypotheses": [
        {"identifier": "incomplete", "description": "Incomplete functional realization.",
         "causal_factor": "incomplete_perturbation", "proposed_action": "revise_intervention"},
        {"identifier": "mode", "description": "Non-equivalent intervention modes.",
         "causal_factor": "mode_non_equivalence", "proposed_action": "change_intervention_mode"},
    ],
    "differing_assumptions": ["functional realization"], "action_identifier": "comparator",
    "outcome_categories": ["concordant", "discordant"],
    "interpretation_boundaries": ["Constructed contract fixture; no biological validation."],
}


def contract():
    common = dict(execution_context="fixture_cells", expected_conditions=CONDITIONS)
    engagement = EvidenceAction(
        "engagement", "Constructed direct target-occupancy assay.", 1.0, ("incomplete",),
        quantity=BiologicalQuantity.TARGET_OCCUPANCY, entity="TARGET", units="fraction",
        time_hours=1.0, supplies=(ENGAGEMENT,), **common,
    )
    function = EvidenceAction(
        "function", "Constructed proximal-function assay.", 1.0, ("incomplete",),
        kind=EvidenceActionKind.FUNCTIONAL_MEASUREMENT, quantity=BiologicalQuantity.PROXIMAL_ACTIVITY,
        entity="TARGET", units="fraction_of_control", time_hours=1.0,
        supplies=(SUFFICIENT_FUNCTION_FIELD,), prerequisites=(ENGAGEMENT,), **common,
    )
    comparator = EvidenceAction(
        "comparator", "Constructed matched-mode viability comparator.", 1.0, ("incomplete", "mode"),
        kind=EvidenceActionKind.MODE_MATCHED_COMPARATOR, quantity=BiologicalQuantity.VIABILITY,
        entity="fixture_cells", units="fraction_of_control", time_hours=48.0,
        prerequisites=(ENGAGEMENT, SUFFICIENT_FUNCTION_FIELD),
        supplies=(MODE_COMPARATOR_FIELD, MODE_DIFFERENCE_FIELD, PHENOTYPE),
        expected_outcomes={"incomplete": "concordant", "mode": "discordant"}, **common,
    )
    occupancy = PremiseRequirement(
        ENGAGEMENT, BiologicalQuantity.TARGET_OCCUPANCY, entity="TARGET", units="fraction",
        context_identifier="fixture_cells", time_hours=1.0,
    )
    proximal = PremiseRequirement(
        SUFFICIENT_FUNCTION_FIELD, BiologicalQuantity.PROXIMAL_ACTIVITY, entity="TARGET",
        units="fraction_of_control", context_identifier="fixture_cells", time_hours=1.0,
    )
    table = InterpretationTable((
        OutcomeRule(
            "occupancy", "registered_occupancy_range", frozenset({ENGAGEMENT}),
            scope=EvidenceScope.INTERVENTION_IMPLEMENTATION, action_identifier="engagement",
            field_requirements=(occupancy,), metric_bounds={"occupancy": (0.8, 1.0)},
            requires_time_match=True,
        ),
        OutcomeRule(
            "proximal", "registered_function_range", frozenset({SUFFICIENT_FUNCTION_FIELD}),
            scope=EvidenceScope.INTERVENTION_IMPLEMENTATION, action_identifier="function",
            field_requirements=(proximal,), evidence_requirements=(occupancy,),
            matched_condition_keys=tuple(CONDITIONS), metric_bounds={"residual_activity": (0.0, 0.2)},
            requires_time_match=True,
        ),
        OutcomeRule(
            "mode_difference", "discordant", frozenset({MODE_COMPARATOR_FIELD, MODE_DIFFERENCE_FIELD, PHENOTYPE}),
            eliminates=frozenset({"incomplete"}), scope=EvidenceScope.MECHANISM_CONTRAST,
            action_identifier="comparator", allowed_action_kinds=frozenset({EvidenceActionKind.MODE_MATCHED_COMPARATOR}),
            field_requirements=(PremiseRequirement(MODE_COMPARATOR_FIELD, BiologicalQuantity.VIABILITY,
                                entity="fixture_cells", units="fraction_of_control"),),
            evidence_requirements=(occupancy, proximal), matched_condition_keys=tuple(CONDITIONS),
            metric_bounds={"inhibitor_viability": (0.8, 1.0), "comparator_viability": (0.0, 0.4)},
            minimum_independent_units=3, requires_time_match=True,
            boundary="Predeclared fixture trajectory links 1h proximal measurements to a 48h comparator; not a validated biological bridge.",
        ),
    ))
    return (engagement, function, comparator), table, FunctionalInterventionProfile(
        mode="drug", context_identifier="fixture_cells"
    )


def results():
    """Synthetic values are intentionally explicit and must not be called measurements of biology."""
    entries = {}
    actions, _, _ = contract()
    metrics = {
        "engagement": {"occupancy": "0.9"}, "function": {"residual_activity": "0.1"},
        "comparator": {"inhibitor_viability": "0.9", "comparator_viability": "0.3"},
    }
    for action in actions:
        entries[action.identifier] = MeasurementResult(
            action.identifier, "Constructed software-contract observation, not experimental biology.",
            f"fixture_source_{action.identifier}", "fixture_cells", action.time_hours, 3, True,
            conditions=dict(CONDITIONS), metrics=metrics[action.identifier],
            interpretation_fields=action.supplies, result_id=f"fixture_result_{action.identifier}",
            limitations=("Synthetic test input.",),
        )
    return entries


def orchestrator(root: Path, *, table=None, rounds: int = 4, plans=None):
    registered_plans = plans if plans is not None else [PLAN] * rounds
    client = StubClient([value for plan in registered_plans for value in (TASK, plan)])
    memory = MemoryStore(root / "memory.sqlite")
    return MAESTROOrchestrator(
        interpreter=TaskInterpreter(client), context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client), visual_inspector=VisualInspector(client, "unused"),
        memory=memory, logger=RunLogger(root), case_store=CaseStore(root / "cases.sqlite"),
        interpretation_table=table,
    )


def run_chain(root: Path, *, transform: Callable | None = None, maximum_rounds: int = 4):
    actions, table, profile = contract()
    supplied = results()
    if transform is not None:
        supplied = transform(supplied)
    agent = orchestrator(root, table=table, rounds=maximum_rounds)
    loop = agent.run_case_loop(
        "Execute the constructed biological evidence contract.", available_actions=actions,
        intervention_profile=profile, result_provider=lambda action, turn: supplied.get(action.identifier),
        case_id="constructed_chain", budget=5.0, max_rounds=maximum_rounds,
    )
    return agent, loop
