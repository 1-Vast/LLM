"""The LLM repair-proposal arm, compiled and scored under the admissible objective.

File summary
- Path: src/agent/llm_proposal_arm.py
- Purpose: measure what the agent contributes. A model is shown the public
  declarations of a decision problem -- the two explanations, the prior, the loss, the
  budget and the menu -- and asked for one repair from a two-operator language. The
  framework compiles the answer into a typed action, so the measurement is the model's
  *choice* (which premise, which operator, what cost, how reliable) and never its
  prose about outcome models.
- Core points:
  - The operators are the framework's own: `register_supplier` supplies a premise the
    menu cannot, `compose` returns a two-stage plan that shares a control. Anything
    else is refused by name and recorded as a refused proposal, not repaired.
  - Scoring is the exact admissible optimum over the menu plus the compiled proposal,
    compared against the menu-only bound, the declared repair catalogue and the rule
    arm, so "the model found it" and "the catalogue contained it" are different columns.
  - `endorses_unlicensed_attribution` records whether the model's own plan decides
    while two explanations are still supported -- the practice the framework's
    boundary forbids -- and `predicts_licensed` records whether it knew.
- Interfaces: `render_problem`, `compile_proposal`, `ProposalOutcome`, `run_family`,
  `run_arm`, `main`
- Depends on: agent.configuration, agent.llm, evaluation.adaptive_reference,
  evaluation.admissible, evaluation.contingent, evaluation.licensing_gap
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.admissible import admissible_repair_policy, solve_admissible_policy  # noqa: E402
from evaluation.adaptive_reference import (  # noqa: E402
    AdaptiveAction,
    DecisionProblem,
    evaluate_policy,
    optimal_policy,
)
from evaluation.contingent import ambiguity_aware_repair_policy, unsupported_attribution  # noqa: E402

PROPOSAL_SOURCE = "llm_proposal"
MENU_SOURCE = "menu"
TOLERANCE = 1e-6

SYSTEM_PROMPT = (
    "You are the repair operator of a scientific decision agent. You are given one "
    "decision problem: two competing explanations of an observation, the prior over "
    "them, the decisions and their losses, a budget, and the measurements the menu can "
    "already buy. You must propose exactly one repair that makes the decision reachable. "
    "\n\n"
    "The framework's rule, which you must respect: a decision that names a cause is only "
    "licensed when every explanation still compatible with what has been observed would "
    "have accepted that same decision. If two explanations are still compatible, the only "
    "honest actions are to buy the measurement that separates them or to defer. Deferral "
    "costs the deferral loss; a wrong decision costs the wrong-decision loss.\n\n"
    "You may propose exactly one of three operators:\n"
    '  {"operator": "register_supplier", "supplies": "<premise name>", "cost": <number>, '
    '"reliability": <number in (0,1]>, "predicts_licensed": <true|false>, "rationale": "<one sentence>"}\n'
    '  {"operator": "compose", "components": ["<menu action id>", "<menu action id>"], '
    '"cost": <number>, "reliability": <number in (0,1]>, "predicts_licensed": <true|false>, '
    '"rationale": "<one sentence>"}\n'
    '  {"operator": "register_supplier_and_bundle", "supplies": "<premise name>", '
    '"bundled_with": "<menu action id>", "cost": <supplier cost>, "saving": <number>, '
    '"reliability": <number in (0,1]>, "predicts_licensed": <true|false>, "rationale": "<one sentence>"}\n\n'
    "`register_supplier` registers a measurement of a premise. `compose` registers a "
    "single plan that runs the first component and then the second, sharing a control, so "
    "its cost may be lower than the sum. `register_supplier_and_bundle` registers a new "
    "measurement of a premise and the plan that runs it with the menu measurement it "
    "unlocks, so the pair may share a control: the plan costs the supplier cost plus the "
    "menu action's cost minus the saving. Return one JSON object and nothing else."
)


def render_problem(problem: DecisionProblem, *, missing_premises: Sequence[str] = ()) -> Mapping[str, object]:
    """The public declaration of a problem, as the model sees it."""

    return {
        "identifier": problem.identifier,
        "hypotheses": list(problem.hypotheses),
        "prior": {h: round(problem.prior[h], 6) for h in problem.hypotheses},
        "decisions": list(problem.decisions),
        "loss": {d: {h: problem.loss[d][h] for h in problem.hypotheses} for d in problem.decisions},
        "budget": problem.budget,
        "menu": [
            {
                "identifier": action.identifier,
                "cost": action.cost,
                "requires": list(action.prerequisites),
                "supplies_on_outcome": {o: list(f) for o, f in action.supplies.items()},
            }
            for action in problem.actions
            if action.source == "menu"
        ],
        # The repair catalogue is deliberately not rendered: the model proposes from the
        # menu and the missing premises alone, so "the model found it" and "the catalogue
        # contained it" stay separable after the fact.
        "missing_premises": list(missing_premises),
    }


def missing_premises(problem: DecisionProblem) -> tuple[str, ...]:
    """Premises the menu's own actions require and no menu action supplies."""

    menu_supplied = {
        field
        for action in problem.actions
        if action.source == "menu"
        for fields in action.supplies.values()
        for field in fields
    }
    required = {p for action in problem.actions if action.source == "menu" for p in action.prerequisites}
    return tuple(sorted(required - menu_supplied))


def _modal_outcome(action: AdaptiveAction, hypothesis: str) -> str:
    return max(action.outcome_model[hypothesis].items(), key=lambda item: (item[1], item[0]))[0]


def compile_proposal(
    problem: DecisionProblem, proposal: Mapping[str, object]
) -> tuple[tuple[AdaptiveAction, ...], str]:
    """Compile a model's proposal into typed actions, or refuse it by name.

    The model chooses; the framework decides what the choice means. Outcomes,
    prerequisites and supplies are read from the declared menu, so a proposal cannot
    invent an outcome model, and a refusal is reported with its reason instead of
    being repaired silently.
    """

    operator = str(proposal.get("operator", ""))
    try:
        reliability = float(proposal.get("reliability", 1.0))
        cost = float(proposal.get("cost", 0.0))
    except (TypeError, ValueError):
        return (), "cost_or_reliability_not_numeric"
    if not 0.0 < reliability <= 1.0:
        return (), "reliability_out_of_range"
    if cost < 0.0:
        return (), "negative_cost"

    def new_supplier(premise: str) -> AdaptiveAction:
        return AdaptiveAction(
            identifier=f"llm_supplier_of_{premise}",
            cost=cost,
            role="premise_supplier",
            source=PROPOSAL_SOURCE,
            outcome_model={
                hypothesis: {"ok": reliability, "failed": 1.0 - reliability}
                for hypothesis in problem.hypotheses
            },
            supplies={"ok": (premise,)},
        )

    if operator == "register_supplier":
        premise = proposal.get("supplies")
        if not isinstance(premise, str) or not premise:
            return (), "supplier_without_a_premise"
        if premise not in set(missing_premises(problem)):
            return (), f"premise_not_missing:{premise}"
        return (new_supplier(premise),), "compiled"

    if operator == "register_supplier_and_bundle":
        premise = proposal.get("supplies")
        if not isinstance(premise, str) or not premise:
            return (), "supplier_without_a_premise"
        if premise not in set(missing_premises(problem)):
            return (), f"premise_not_missing:{premise}"
        menu = {
            action.identifier: action
            for action in problem.actions
            if action.source == MENU_SOURCE
        }
        target = proposal.get("bundled_with")
        if not isinstance(target, str) or target not in menu:
            return (), f"bundled_action_not_in_the_menu:{target}"
        readout = menu[target]
        if premise not in readout.prerequisites:
            return (), f"bundled_action_does_not_need_the_premise:{premise}"
        try:
            saving = float(proposal.get("saving", 0.0))
        except (TypeError, ValueError):
            return (), "saving_not_numeric"
        if saving < 0.0:
            return (), "negative_saving"
        bundled_cost = cost + readout.cost - saving
        if bundled_cost < 0.0:
            return (), "bundled_cost_negative"
        supplier = new_supplier(premise)
        outcome_model: dict[str, dict[str, float]] = {}
        for hypothesis in problem.hypotheses:
            outcome_model[hypothesis] = {
                _modal_outcome(readout, hypothesis): reliability,
                "no_call": 1.0 - reliability,
            }
        return (
            supplier,
            AdaptiveAction(
                identifier="llm_bundled_plan",
                cost=bundled_cost,
                source=PROPOSAL_SOURCE,
                composed_from=(supplier.identifier, readout.identifier),
                prerequisites=tuple(p for p in readout.prerequisites if p != premise),
                outcome_model=outcome_model,
                supplies=readout.supplies,
            ),
        ), "compiled"

    if operator == "compose":
        components = proposal.get("components")
        if not isinstance(components, (list, tuple)) or len(components) != 2:
            return (), "compose_needs_two_components"
        # A composition is built from what the menu can already buy. An action that only a
        # repair could have proposed is not a component; composing it would smuggle the
        # catalogue back into the model's answer.
        identifiers = {
            action.identifier for action in problem.actions if action.source == MENU_SOURCE
        }
        for component in components:
            if str(component) not in identifiers:
                return (), f"component_not_in_the_menu:{component}"
        gate = problem.action(str(components[0]))
        readout = problem.action(str(components[1]))
        if not gate.supplies:
            return (), f"first_component_supplies_nothing:{gate.identifier}"
        if not set(readout.prerequisites) & {
            field for fields in gate.supplies.values() for field in fields
        }:
            return (), f"first_component_does_not_unlock_second:{gate.identifier}"
        outcome_model: dict[str, dict[str, float]] = {}
        for hypothesis in problem.hypotheses:
            outcome_model[hypothesis] = {
                _modal_outcome(readout, hypothesis): reliability,
                "no_call": 1.0 - reliability,
            }
        supplies = {
            _modal_outcome(readout, hypothesis): tuple(
                field for fields in gate.supplies.values() for field in fields
            )
            for hypothesis in problem.hypotheses
        }
        return (
            (
            AdaptiveAction(
                identifier="llm_composed_plan",
                cost=cost,
                source=PROPOSAL_SOURCE,
                composed_from=(gate.identifier, readout.identifier),
                prerequisites=gate.prerequisites,
                outcome_model=outcome_model,
                supplies=supplies,
            ),
            ),
            "compiled",
        )

    return (), f"unknown_operator:{operator or 'missing'}"


def canonical_repair_cost(problem: DecisionProblem, premise: str) -> float | None:
    """The cheapest declared cost of a registered repair that supplies this premise.

    A model's own cost declaration is a free parameter: nothing in the problem stops it
    from proposing a measurement at a tenth of the declared price, and a certificate
    computed from that number would credit the model for arithmetic rather than for
    judgement. This is the anchor the structure-only column is priced against.
    """

    costs = [
        action.cost
        for action in problem.actions
        if action.source != MENU_SOURCE
        and premise in {field for fields in action.supplies.values() for field in fields}
    ]
    return min(costs) if costs else None


def catalogue_saving(problem: DecisionProblem) -> float:
    """The shared-control saving the declared catalogue actually registers, if any.

    Like a cost, a saving is a declared laboratory quantity. A model that declares a
    large saving can make any plan look affordable, so the structure-only column prices
    the model's *structure* with the catalogue's own saving rather than the model's.
    """

    savings = []
    for action in problem.actions:
        if not action.is_composed:
            continue
        components = [problem.action(name) for name in action.composed_from]
        savings.append(sum(component.cost for component in components) - action.cost)
    return max(savings, default=0.0)


def structure_only_score(
    problem: DecisionProblem, proposal: Mapping[str, object]
) -> Mapping[str, object] | None:
    """Re-score the model's *structure* with the price fixed by the declared catalogue."""

    premise = proposal.get("supplies")
    if not isinstance(premise, str) or not premise:
        return None
    canonical = canonical_repair_cost(problem, premise)
    if canonical is None:
        return None
    adjusted = dict(proposal)
    adjusted["cost"] = canonical
    if "saving" in adjusted:
        adjusted["saving"] = catalogue_saving(problem)
    actions, reason = compile_proposal(problem, adjusted)
    if not actions:
        return None
    row = score_proposal(problem, actions, reason, adjusted).as_row()
    return {
        "canonical_cost": canonical,
        "declared_cost": proposal.get("cost"),
        "proposal_admissible": row["proposal_admissible"],
        "certified_value_of_the_proposal": row["certified_value_of_the_proposal"],
        "reaches_the_catalogue_value": row["reaches_the_catalogue_value"],
        "proposal_is_licensed": row["proposal_is_licensed"],
    }


@dataclass(frozen=True)
class ProposalOutcome:
    """One family's proposal, its compiled action space and its exact scores."""

    identifier: str
    compiled: bool
    refusal: str
    novel_in_action_space: bool
    predicts_licensed: bool | None
    proposal_is_licensed: bool
    menu_only_admissible: float
    catalogue_admissible: float
    proposal_admissible: float
    certified_value_of_the_proposal: float
    reaches_the_catalogue_value: bool
    rule_arm_loss: float
    rule_arm_endorses_unlicensed_attribution: float
    proposal_endorses_unlicensed_attribution: float
    rationale: str

    def as_row(self) -> Mapping[str, object]:
        return {
            "identifier": self.identifier,
            "compiled": self.compiled,
            "refusal": self.refusal,
            "novel_in_action_space": self.novel_in_action_space,
            "predicts_licensed": self.predicts_licensed,
            "proposal_is_licensed": self.proposal_is_licensed,
            "menu_only_admissible": round(self.menu_only_admissible, 6),
            "catalogue_admissible": round(self.catalogue_admissible, 6),
            "proposal_admissible": round(self.proposal_admissible, 6),
            "certified_value_of_the_proposal": round(self.certified_value_of_the_proposal, 6),
            "reaches_the_catalogue_value": self.reaches_the_catalogue_value,
            "rule_arm_loss": round(self.rule_arm_loss, 6),
            "rule_arm_endorses_unlicensed_attribution": round(
                self.rule_arm_endorses_unlicensed_attribution, 6
            ),
            "proposal_endorses_unlicensed_attribution": round(
                self.proposal_endorses_unlicensed_attribution, 6
            ),
            "rationale": self.rationale,
        }


def score_proposal(
    problem: DecisionProblem,
    compiled: Sequence[AdaptiveAction],
    refusal: str,
    proposal: Mapping[str, object],
) -> ProposalOutcome:
    """Exact scores for one compiled proposal, against the menu-only bound and the rule arm."""

    # The bound is taken over the shipped menu alone: both the declared repair catalogue
    # and any earlier proposal are removed, so the comparison is against what the menu
    # could already do and not against a rival repair.
    menu_only = problem.restricted_to(
        (MENU_SOURCE,), identifier=f"{problem.identifier}[menu_only]"
    )
    menu_only_admissible = solve_admissible_policy(menu_only).expected_loss
    catalogue_admissible = solve_admissible_policy(problem).expected_loss
    rule_arm = evaluate_policy(admissible_repair_policy, problem)
    recorded_arm_endorses = unsupported_attribution(ambiguity_aware_repair_policy, problem)
    if not compiled:
        return ProposalOutcome(
            identifier=problem.identifier,
            compiled=False,
            refusal=refusal,
            novel_in_action_space=False,
            predicts_licensed=proposal.get("predicts_licensed")
            if isinstance(proposal.get("predicts_licensed"), bool)
            else None,
            proposal_is_licensed=False,
            menu_only_admissible=menu_only_admissible,
            catalogue_admissible=catalogue_admissible,
            proposal_admissible=menu_only_admissible,
            certified_value_of_the_proposal=0.0,
            reaches_the_catalogue_value=False,
            rule_arm_loss=rule_arm.expected_loss,
            rule_arm_endorses_unlicensed_attribution=recorded_arm_endorses,
            proposal_endorses_unlicensed_attribution=0.0,
            rationale=str(proposal.get("rationale", ""))[:400],
        )
    extended = DecisionProblem(
        identifier=f"{problem.identifier}[with_llm_proposal]",
        hypotheses=problem.hypotheses,
        prior=problem.prior,
        # The declared repair catalogue is removed: a proposal is scored on what it adds
        # to the shipped menu, so a dear or unreliable proposal cannot borrow the
        # catalogue's cheap route to look effective.
        actions=tuple(menu_only.actions) + tuple(compiled),
        budget=problem.budget,
        decisions=problem.decisions,
        loss=problem.loss,
        family=problem.family,
        note="the shipped menu plus one model-proposed action",
    )
    problems = extended.validate()
    if problems:
        return score_proposal(problem, None, f"invalid_problem:{','.join(problems)}", proposal)
    proposal_admissible = solve_admissible_policy(extended).expected_loss
    catalogue_identifiers = {action.identifier for action in problem.actions}
    novel = any(action.identifier not in catalogue_identifiers for action in compiled)
    return ProposalOutcome(
        identifier=problem.identifier,
        compiled=True,
        refusal="",
        novel_in_action_space=novel,
        predicts_licensed=proposal.get("predicts_licensed")
        if isinstance(proposal.get("predicts_licensed"), bool)
        else None,
        proposal_is_licensed=proposal_admissible < menu_only_admissible - TOLERANCE,
        menu_only_admissible=menu_only_admissible,
        catalogue_admissible=catalogue_admissible,
        proposal_admissible=proposal_admissible,
        certified_value_of_the_proposal=max(0.0, menu_only_admissible - proposal_admissible),
        reaches_the_catalogue_value=proposal_admissible <= catalogue_admissible + TOLERANCE,
        rule_arm_loss=rule_arm.expected_loss,
        rule_arm_endorses_unlicensed_attribution=recorded_arm_endorses,
        proposal_endorses_unlicensed_attribution=unsupported_attribution(
            optimal_policy(extended), extended
        ),
        rationale=str(proposal.get("rationale", ""))[:400],
    )


def run_family(problem: DecisionProblem, client) -> tuple[ProposalOutcome, Mapping[str, object]]:
    """Ask the model for one repair and score the compiled result.

    The configured model reasons before it answers, so the completion budget has to
    cover the reasoning as well as the JSON object: a 600-token budget returns
    `finish_reason=length` with empty content, which the arm records as a provider
    failure rather than scoring as a wrong proposal. One retry is allowed on a
    protocol failure, and the retry is reported with the run.
    """

    statement = render_problem(problem, missing_premises=missing_premises(problem))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(statement, ensure_ascii=False, sort_keys=True)},
    ]
    attempts = 0
    while True:
        attempts += 1
        try:
            payload, response = client.complete_json(messages, max_tokens=4_000)
            break
        except Exception:
            if attempts >= 2:
                raise
    outcome = score_proposal(problem, *compile_proposal(problem, payload), payload)
    transcript = {
        "identifier": problem.identifier,
        "problem": statement,
        "response": payload,
        "model": response.model,
        "usage": dict(response.usage),
        "finish_reason": response.finish_reason,
        "attempts": attempts,
    }
    return outcome, transcript


def run_arm(problems: Mapping[str, DecisionProblem], client) -> Mapping[str, object]:
    """Run the whole arm and aggregate the rates the claim needs."""

    rows: list[Mapping[str, object]] = []
    transcripts: list[Mapping[str, object]] = []
    tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for name, problem in problems.items():
        try:
            outcome, transcript = run_family(problem, client)
        except Exception as error:  # a provider failure is data, not a crash
            rows.append(
                {
                    "identifier": name,
                    "compiled": False,
                    "refusal": f"provider_failure:{type(error).__name__}",
                    "novel_in_action_space": False,
                    "predicts_licensed": None,
                    "proposal_is_licensed": False,
                    "menu_only_admissible": None,
                    "catalogue_admissible": None,
                    "proposal_admissible": None,
                    "certified_value_of_the_proposal": 0.0,
                    "reaches_the_catalogue_value": False,
                    "rule_arm_loss": None,
                    "rule_arm_endorses_unlicensed_attribution": None,
                    "proposal_endorses_unlicensed_attribution": None,
                    "rationale": "",
                    "error": str(error)[:200],
                }
            )
            continue
        row = dict(outcome.as_row())
        if row["compiled"]:
            structure = structure_only_score(problem, transcript["response"])
            if structure is not None:
                row["structure_only"] = structure
        rows.append(row)
        transcripts.append(transcript)
        for key in tokens:
            tokens[key] += int(transcript["usage"].get(key, 0))
    compiled = [row for row in rows if row["compiled"]]
    structure_rows = [row["structure_only"] for row in compiled if "structure_only" in row]
    missing_ids = {problem.identifier for problem in problems.values() if missing_premises(problem)}
    rows_with_missing = [row for row in rows if row["identifier"] in missing_ids]
    compiled_with_missing = [row for row in rows_with_missing if row["compiled"]]
    return {
        "scope": (
            "One model call per declared decision problem. Scores are exact optima over the "
            "declared finite model plus the compiled proposal; they are statements about "
            "algorithm behaviour on declared models, not about biology."
        ),
        "problems": len(rows),
        "compiled_proposals": len(compiled),
        "admissible_proposal_rate": round(len(compiled) / len(rows), 6) if rows else None,
        "problems_where_a_premise_is_missing": len(rows_with_missing),
        "admissible_proposal_rate_where_a_premise_is_missing": (
            round(len(compiled_with_missing) / len(rows_with_missing), 6)
            if rows_with_missing
            else None
        ),
        "novel_proposal_rate_among_compiled": (
            round(sum(1 for row in compiled if row["novel_in_action_space"]) / len(compiled), 6)
            if compiled
            else None
        ),
        "reaches_the_catalogue_value_rate_among_compiled": (
            round(sum(1 for row in compiled if row["reaches_the_catalogue_value"]) / len(compiled), 6)
            if compiled
            else None
        ),
        "certified_value_total": round(
            sum(float(row["certified_value_of_the_proposal"]) for row in compiled), 6
        ),
        "structure_only_rows": len(structure_rows),
        "structure_only_certified_value_total": round(
            sum(float(entry["certified_value_of_the_proposal"]) for entry in structure_rows), 6
        ),
        "structure_only_reaches_the_catalogue_value": sum(
            1 for entry in structure_rows if entry["reaches_the_catalogue_value"]
        ),
        "licensed_predictions_correct": sum(
            1 for row in compiled if row["predicts_licensed"] == row["proposal_is_licensed"]
        ),
        "licensed_predictions_recorded": sum(
            1 for row in compiled if row["predicts_licensed"] is not None
        ),
        "rule_arm_endorses_unlicensed_attribution_total": round(
            sum(
                float(row["rule_arm_endorses_unlicensed_attribution"] or 0.0) for row in compiled
            ),
            6,
        ),
        "tokens": tokens,
        "rows": rows,
        "transcripts": transcripts,
    }


def aggregate_with_structure(
    payload: Mapping[str, object], problems: Mapping[str, DecisionProblem]
) -> Mapping[str, object]:
    """Recompute the arm's aggregates from a recorded run, adding the structure-only column.

    The paid part of this arm is the model call. Everything here is arithmetic over the
    recorded proposals, so a correction to how a proposal is priced never requires
    buying the answers again, and the corrected table can be reproduced offline.
    """

    rows: list[Mapping[str, object]] = []
    for row in payload.get("rows", []):  # type: ignore[union-attr]
        updated = dict(row)  # type: ignore[arg-type]
        transcript = next(
            (
                entry
                for entry in payload.get("transcripts", ())  # type: ignore[union-attr]
                if entry["identifier"] == updated["identifier"]
            ),
            None,
        )
        # Rows are keyed by the problem's own identifier, which is not always the family
        # key it was built from, so the lookup is by identifier rather than by key.
        problem = next(
            (
                candidate
                for candidate in problems.values()
                if candidate.identifier == str(updated["identifier"])
            ),
            None,
        )
        if updated.get("compiled") and transcript is not None and problem is not None:
            structure = structure_only_score(problem, transcript["response"])
            if structure is not None:
                updated["structure_only"] = structure
        rows.append(updated)
    compiled = [row for row in rows if row["compiled"]]
    structure_rows = [row["structure_only"] for row in compiled if "structure_only" in row]
    updated_payload = dict(payload)
    updated_payload["rows"] = rows
    updated_payload["compiled_proposals"] = len(compiled)
    updated_payload["structure_only_rows"] = len(structure_rows)
    updated_payload["structure_only_certified_value_total"] = round(
        sum(float(entry["certified_value_of_the_proposal"]) for entry in structure_rows), 6
    )
    updated_payload["structure_only_reaches_the_catalogue_value"] = sum(
        1 for entry in structure_rows if entry["reaches_the_catalogue_value"]
    )
    missing_ids = {problem.identifier for problem in problems.values() if missing_premises(problem)}
    rows_with_missing = [row for row in rows if row["identifier"] in missing_ids]
    updated_payload["problems_where_a_premise_is_missing"] = len(rows_with_missing)
    updated_payload["admissible_proposal_rate_where_a_premise_is_missing"] = (
        round(sum(1 for row in rows_with_missing if row["compiled"]) / len(rows_with_missing), 6)
        if rows_with_missing
        else None
    )
    return updated_payload


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    workspace = Path(__file__).resolve().parents[2]
    # Default output is scratch, not a day folder: `log/` is the dated record and holds one
    # `README.md` per working day, so a runner writes its intermediate result under `tmp/`.
    out = Path(argv[0]) if argv else workspace / "tmp" / "llm_proposal_arm" / "llm_proposal_arm.json"

    from agent.configuration import MAESTROSettings  # noqa: E402
    from agent.llm import DeepSeekChatClient  # noqa: E402
    from evaluation.contingent_suite import FAMILIES as RECORDED  # noqa: E402
    from evaluation.licensing_gap import FAMILIES as GAP  # noqa: E402

    problems: dict[str, DecisionProblem] = {
        name: build() for name, build in {**GAP, **RECORDED}.items()
    }
    client = DeepSeekChatClient(MAESTROSettings.from_workspace(workspace))
    payload = run_arm(problems, client)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    transcript_dir = out.parent / "transcript"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir.joinpath("transcripts.json").write_text(
        json.dumps(payload["transcripts"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"problems={payload['problems']} compiled={payload['compiled_proposals']} "
        f"admissible_rate={payload['admissible_proposal_rate']} "
        f"novel_rate={payload['novel_proposal_rate_among_compiled']} "
        f"reaches_catalogue_rate={payload['reaches_the_catalogue_value_rate_among_compiled']} "
        f"certified_value_total={payload['certified_value_total']} "
        f"tokens={payload['tokens']['total_tokens']}"
    )
    print(f"written: {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
