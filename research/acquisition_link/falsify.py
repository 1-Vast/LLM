"""Reproduce, with the repository's own code, each suspected break between prediction and measurement choice.

File summary
- Path: research/acquisition_link/falsify.py
- Purpose: Phase B of the 2026-09-26 acquisition-link audit. Every probe holds all inputs fixed
  except the one the suspected failure is about, runs the repository's selectors or controller,
  and records what they chose. It uses only interfaces that existed before the repair, so the same
  script documents the old behaviour (`--label before`) and the repaired one (`--label after`).
- Core points:
  - P1 wiring: with power-aware selection on (the production default of `from_workspace`, the CLI
    and the public loop), does swapping two actions' world-model predictions change the choice?
  - P2 information loss: a scenario card's branches reduced to one detection probability cannot
    separate equal correct-elimination odds with unequal wrong risk.
  - P3 magnitude trap and P4 late resolver: what the magnitude tie-break and the cost order choose.
  - P5 action space: which exposure time a per-action query states for a 72 h action.
  - P6 support: whether a one-reference card leaves its action in the selector's objective.
  - No probe reads a SciPlex3 outcome; the real-data counts are cited from the block-2 audit.
- Run: python research/acquisition_link/falsify.py --label before
- Depends on: maestro, agent, virtual_cell (repository code only)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agent.audit import RunLogger  # noqa: E402
from agent.context import ContextBuilder, TaskInterpreter  # noqa: E402
from agent.knowledge import EvidenceLedger  # noqa: E402
from agent.memory import MemoryStore  # noqa: E402
from agent.orchestrator import MAESTROOrchestrator  # noqa: E402
from agent.planner import MechanismContrastPlanner  # noqa: E402
from agent.template_client import TemplateCompleter  # noqa: E402
from agent.vision import VisualInspector  # noqa: E402
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent  # noqa: E402
from maestro.acquisition import select_expected_coverage  # noqa: E402
from maestro.selection import BudgetedEvidenceSelector  # noqa: E402
from virtual_cell import (  # noqa: E402
    ModelCapabilities,
    QueryAssessment,
    QuerySupport,
    StatePrediction,
    SystemContext,
    VirtualCellQueryTemplate,
)

OUT = ROOT / "outputs" / "acquisition_link_20260926"
LOW, HIGH = "[('drugA', 0.5, 'uM')]", "[('drugA', 5.0, 'uM')]"
REALISED, NOT_REALISED = "response_realised", "response_not_realised"
TRIAGE = {
    "task_type": "mechanism_diagnosis", "research_question": "Is the response of drugA realised?",
    "target_or_targets": ["TARGET_A"], "interventions": ["drugA"], "biological_context": "NCI-H596",
    "phenotype_endpoint": "transcriptome shift", "supplied_evidence": [], "constraints": [],
    "missing_information": [], "evidence_gaps": [], "needs_visual_review": False,
}
PLAN = {
    "identifier": "realisation-contrast",
    "hypotheses": [
        {"identifier": REALISED, "description": "The exposure perturbs the transcriptome.",
         "proposed_action": "continue", "causal_factor": "unresolved"},
        {"identifier": NOT_REALISED, "description": "The exposure does not perturb the transcriptome.",
         "proposed_action": "revise_intervention", "causal_factor": "incomplete_perturbation"},
    ],
    "differing_assumptions": ["whether the exposure changes RNA abundance"], "action_identifier": "measure_low",
    "outcome_categories": ["response_detected", "no_detectable_response"],
    "interpretation_boundaries": ["An RNA-level response does not establish engagement."],
}
NO_REPAIR = {"action_identifier": None, "modified_fields": [], "rationale": "none", "remaining_limitations": []}


class LabelWorldModel:
    """One fixed number per exact label; with ``served_time`` it refuses any other stated exposure."""

    name = "label_stub"

    def __init__(self, values, served_time=None):
        self.values, self.served_time, self.requests = values, served_time, []

    def capabilities(self):
        return ModelCapabilities("label_stub", "stub-1", "none", "label", ("drug",), True, False,
                                 self.served_time is not None, None)

    def _limits(self, request):
        t = request.intervention.time_hours
        return (f"time_not_supported:{t:g}h",) if self.served_time is not None and t is not None and t != self.served_time else ()

    def assess_query(self, request):
        self.requests.append(request)
        limits = self._limits(request)
        return QueryAssessment(QuerySupport.UNSUPPORTED if limits else QuerySupport.SUPPORTED, (), limits,
                               self.capabilities())

    def predict(self, request):
        return StatePrediction(True, {"embedding_delta_l2": self.values[request.intervention.identifier]}, None,
                               ("planning only",), request_id=request.request_id, model_version="stub-1",
                               in_distribution=True, uncertainty_components={"all": "fixture"})


def actions(late_time=None):
    common = dict(cost=1.0, distinguishes=(REALISED, NOT_REALISED), supplies=("realization:transcript_response",),
                  prediction_readout="embedding_delta_l2", prediction_relevance=1.0,
                  expected_outcomes={REALISED: "response_detected", NOT_REALISED: "no_detectable_response"})
    return (EvidenceAction("measure_low", "0.5 uM", time_hours=24.0, **common),
            EvidenceAction("measure_high", "5 uM", time_hours=late_time or 24.0, **common))


def controller(root: Path, world_model, power_aware: bool) -> MAESTROOrchestrator:
    client = TemplateCompleter({"task_triage": TRIAGE, "contrast_planner": PLAN, "repair_planner": NO_REPAIR})
    memory = MemoryStore(root / "memory.sqlite")
    return MAESTROOrchestrator(
        interpreter=TaskInterpreter(client), context_builder=ContextBuilder(EvidenceLedger(root / "evidence.sqlite"), memory),
        planner=MechanismContrastPlanner(client), visual_inspector=VisualInspector(client, "unused"), memory=memory,
        logger=RunLogger(root), controller=MAESTROAgent(), virtual_cell=world_model, power_aware_selection=power_aware)


def template(time_hours=None):
    return VirtualCellQueryTemplate(LOW, "drug", SystemContext("NCI-H596", "fixture", dataset_id="t", control_dataset_id="t"),
                                    ("embedding_delta_l2",), "stub-1",
                                    action_interventions={"measure_low": LOW, "measure_high": HIGH}, time_hours=time_hours)


def run(world_model, power_aware: bool, late_time=None, template_time=None):
    profile = FunctionalInterventionProfile(mode="inhibition", context_identifier="NCI-H596", time_hours=24.0)
    with tempfile.TemporaryDirectory() as folder:
        turn = controller(Path(folder), world_model, power_aware).run(
            "Which exposure first?", available_actions=actions(late_time), intervention_profile=profile,
            case_id="probe", budget=1.0, virtual_cell_template=template(template_time))
        events = [json.loads(line) for line in (Path(folder) / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    priorities = next(e for e in reversed(events) if e["kind"] == "budget_selection_completed")["payload"]["prediction_action_priorities"]
    return [a.identifier for a in turn.selected_actions], priorities


def probe_wiring() -> dict:
    out = {}
    for power_aware in (False, True):
        rows = {}
        for name, values in (("low_predicted_larger", {LOW: 5.0, HIGH: 1.0}), ("high_predicted_larger", {LOW: 1.0, HIGH: 5.0})):
            chosen, priorities = run(LabelWorldModel(values), power_aware)
            rows[name] = {"chosen": chosen, "priorities": priorities}
        rows["choice_changes_with_prediction"] = rows["low_predicted_larger"]["chosen"] != rows["high_predicted_larger"]["chosen"]
        out["power_aware" if power_aware else "budgeted"] = rows
    return out


def probe_information_loss() -> dict:
    profile = FunctionalInterventionProfile(mode="small_molecule")
    # Card branches (correct, wrong, unresolved, undetected) for two hypotheses, ten references each.
    cards = {"a-risky": (6, 3, 0, 1), "c-safe": (6, 0, 0, 4)}
    reduced = tuple(EvidenceAction(k, k, 1.0, ("h1", "h2"), detection_power=v[0] / sum(v)) for k, v in cards.items())
    plan = select_expected_coverage(frozenset({"h1", "h2"}), reduced, profile, 1.0)
    return {"cards": {k: dict(zip(("correct", "wrong", "unresolved", "undetected"), v)) for k, v in cards.items()},
            "detection_power_passed": {a.identifier: a.detection_power for a in reduced},
            "chosen": [a.identifier for a in plan.plan.actions],
            "expected_utility_per_card": {k: (v[0] - 2 * v[1]) / sum(v) for k, v in cards.items()},
            "note": "p_wrong has no field to travel in; equal detection power ties and the identifier decides"}


def probe_magnitude_and_time() -> dict:
    profile = FunctionalInterventionProfile(mode="small_molecule")
    loud, quiet = EvidenceAction("loud", "loud", 1.0, ("h1", "h2")), EvidenceAction("quiet", "quiet", 1.0, ("h1", "h2"))
    trap = BudgetedEvidenceSelector().select(frozenset({"h1", "h2"}), (loud, quiet), profile, 1.0,
                                             action_priorities={"loud": 50.0, "quiet": 1.0})
    early = EvidenceAction("A549|024h|10000nM", "24 h", 6.0, ("h1", "h2"), time_hours=24.0)
    late = EvidenceAction("A549|072h|10000nM", "72 h", 8.0, ("h1", "h2"), time_hours=72.0)
    budgeted = BudgetedEvidenceSelector().select(frozenset({"h1", "h2"}), (early, late), profile, 8.0,
                                                 action_priorities={"A549|072h|10000nM": 99.0})
    coverage = select_expected_coverage(frozenset({"h1", "h2"}), (early, late), profile, 8.0)
    return {"magnitude_trap_chosen": [a.identifier for a in trap.actions],
            "late_resolver": {"budgeted_with_a_large_72h_priority": [a.identifier for a in budgeted.actions],
                              "expected_coverage_without_declared_power": [a.identifier for a in coverage.plan.actions],
                              "note": "cost is compared before any prediction, so a 72 h action loses whenever a 24 h one declares the same coverage"}}


def probe_query_time() -> dict:
    world_model = LabelWorldModel({LOW: 1.0, HIGH: 5.0}, served_time=24.0)
    chosen, priorities = run(world_model, True, late_time=72.0, template_time=24.0)
    stated = {r.request_id.rsplit(".", 1)[-1]: r.intervention.time_hours for r in world_model.requests}
    return {"action_times": {"measure_low": 24.0, "measure_high": 72.0}, "request_times": stated,
            "priorities": priorities, "chosen": chosen,
            "borrowed_condition": stated.get("measure_high") != 72.0 and "measure_high" in priorities}


def probe_support() -> dict:
    """The registered card refuses a branch under two references; a refused card leaves the objective."""

    profile = FunctionalInterventionProfile(mode="small_molecule")
    # One reference of the small class, and it separated; ten references elsewhere never did.
    card_min2 = {"72h_one_reference": None, "24h_ten_references": 0.0}
    acts = tuple(EvidenceAction(k, k, 1.0, ("h1", "h2") if (p or 0) > 0 else (), detection_power=p if p else None)
                 for k, p in card_min2.items())
    plan = select_expected_coverage(frozenset({"h1", "h2"}), acts, profile, 8.0)
    return {"served_p_correct": card_min2, "chosen": [a.identifier for a in plan.plan.actions],
            "status": plan.status, "uncovered": sorted(plan.plan.uncovered),
            "block2_audit": {"tier_A_menu_actions_refused": 550, "of": 2616,
                             "realised_correct_rate_of_refused": 0.136,
                             "one_reference_shadow_ece": {"A": 0.089, "B": 0.053}, "served_ece": {"A": 0.154, "B": 0.101},
                             "source": "outputs/dynamic_world_model_20260926/card_audit/summary.json"}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, choices=("before", "after"))
    label = parser.parse_args().label
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--short", "--", "src"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    record = {"label": label, "head": commit, "src_uncommitted_changes": dirty.splitlines(),
              "P1_wiring": probe_wiring(), "P2_information_loss": probe_information_loss(),
              "P3_P4_magnitude_and_time": probe_magnitude_and_time(), "P5_query_time": probe_query_time(),
              "P6_support": probe_support()}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"falsification_{label}.json"
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()
