"""Does putting reachability in the state change what the typed model recommends?

File summary
- Path: research/local_verification/topology_ablation.py
- Purpose: the 12-repeat probe of 2026-09-25 selected a non-executable action in all twelve
  calls - `orthogonal_rescue` seven times, whose premise nothing supplies, `proximal_activity`
  four times and `engagement_shift` once, three and two supplier steps away - while the only
  executable decisive action, `rna_low`, drew a reported probability of 0.03 and was never
  chosen. The same question inside the critic, whose state carries the supplier topology and
  the deterministic check, returned `rna_low`. Two different states, so nothing is established:
  this script runs the comparison properly, changing one thing.
- Core points:
  - One contrast, one action menu, one question set. The only difference between the arms is
    whether the state carries the topology block.
  - Each arm is repeated, so the arms are compared on distributions rather than on one draw of
    a source already known to be irreproducible.
  - The outcome measured is the share of selections that the agent could actually execute, plus
    the agreement in each arm. A change in *what* is recommended and a change in *how stably*
    are different findings and are reported separately.
- Interfaces: `main()`
- Depends on: agent.decision_critic, agent.typesafe, maestro

Every call is paid. `--repeats 12` in two arms is 24 evaluations.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agent.decision_critic import TypedDecisionCritic  # noqa: E402
from agent.typesafe import TypeSafeJevClient, TypeSafeSettings  # noqa: E402
from maestro import EvidenceAction, FunctionalInterventionProfile, MAESTROAgent  # noqa: E402
from maestro.models import DevelopmentAction, MechanismContrast, MechanismHypothesis  # noqa: E402
from maestro.topology import ActionTopology  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
EXECUTABLE = {"rna_low", "rna_high"}


def load_actions() -> tuple[EvidenceAction, ...]:
    data = json.loads((FIXTURES / "actions.json").read_text(encoding="utf-8"))
    return tuple(
        EvidenceAction(
            identifier=item["identifier"],
            description=item["description"],
            cost=float(item["cost"]),
            distinguishes=tuple(item["distinguishes"]),
            prerequisites=tuple(item.get("prerequisites", ())),
            supplies=tuple(item.get("supplies", ())),
            time_hours=item.get("time_hours"),
            expected_outcomes=dict(item.get("expected_outcomes", {})),
            source_ids=tuple(item.get("source_ids", ())),
        )
        for item in data
    )


def build_contrast(actions) -> MechanismContrast:
    hypotheses = json.loads((FIXTURES / "hypotheses.json").read_text(encoding="utf-8"))
    return MechanismContrast(
        identifier="realisation-contrast",
        hypotheses=tuple(
            MechanismHypothesis(
                item["identifier"], item["description"],
                DevelopmentAction(item["proposed_action"]), item["causal_factor"],
            )
            for item in hypotheses
        ),
        differing_assumptions=("whether the exposure changes RNA abundance at 24 h",),
        plan=next(a for a in actions if a.identifier == "rna_low"),
        outcome_categories=("response_detected", "no_detectable_response"),
        interpretation_boundaries=(
            "An RNA-level response does not establish target engagement, pathway activity or viability.",
        ),
    )


def arm(critic, contrast, actions, profile, topology, repeats: int, label: str) -> dict:
    outcome = critic.review_plan(
        contrast, actions,
        check=MAESTROAgent().check_contrast(contrast, profile),
        topology=topology,
        context_identifier=profile.context_identifier,
        repeats=repeats,
    )
    rows = [r for r in outcome.stability if r.get("question_id") == "best_separating_action"]
    row = rows[0] if rows else {}
    counts = Counter(row.get("value_counts", {}))
    total = sum(counts.values()) or 1
    executable = sum(count for name, count in counts.items() if name in EXECUTABLE)
    return {
        "arm": label,
        "topology_in_state": topology is not None,
        "repeats": repeats,
        "selections": dict(counts),
        "executable_share": executable / total,
        "agreement": row.get("agreement"),
        "verdict": row.get("verdict"),
        "refusals": list(outcome.refusals),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare the typed model with and without reachability in its state.")
    parser.add_argument("--workspace", type=Path, default=ROOT)
    parser.add_argument("--repeats", type=int, default=12, help="Calls per arm; 12 is where the stability gate has power.")
    parser.add_argument("--report", type=Path)
    arguments = parser.parse_args()

    settings = TypeSafeSettings.from_workspace(arguments.workspace)
    if settings is None:
        print("typesafe: not configured in this workspace; nothing to compare.")
        return 3

    actions = load_actions()
    contrast = build_contrast(actions)
    profile = FunctionalInterventionProfile(
        mode="inhibition", context_identifier="NCI-H596", time_hours=24.0,
    )
    # The same object the agent loop puts in front of the model each round, built the same way.
    topology = ActionTopology.build(actions, profile).summary()

    print(f"model {settings.model!r}, {arguments.repeats} calls per arm, 2 arms\n")
    results = []
    for label, block in (("with_topology", topology), ("without_topology", None)):
        critic = TypedDecisionCritic(TypeSafeJevClient(settings))
        result = arm(critic, contrast, actions, profile, block, arguments.repeats, label)
        results.append(result)
        share = result["executable_share"]
        agreement = result["agreement"]
        print(f"{label:<18} executable share {share:>5.0%}"
              f"  agreement {agreement if agreement is None else round(agreement, 3)}"
              f"  verdict {result['verdict']}")
        print(f"{'':<18} selections {result['selections']}")

    with_block, without_block = results
    print()
    print("What changed, and what it does and does not show:")
    print(f"  executable share  {without_block['executable_share']:.0%} -> {with_block['executable_share']:.0%}")
    print(f"  agreement         {without_block['agreement']} -> {with_block['agreement']}")
    print("  One thing differed between the arms, so a difference here is attributable to the")
    print("  topology block. It says nothing about whether the recommendation is biologically")
    print("  right: an executable action is one the agent can run, not one worth running.")

    if arguments.report:
        arguments.report.parent.mkdir(parents=True, exist_ok=True)
        arguments.report.write_text(json.dumps({"model": settings.model, "arms": results}, indent=1) + "\n",
                                    encoding="utf-8")
        print(f"\nreport written to {arguments.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
