"""What a proposed repair is worth on a real case, under two readings of the licence.

File summary
- Path: src/evaluation/repair_certificate.py
- Purpose: price the capability a policy proposes against the best any policy restricted to
  the menu could do. The certificate is the difference between two exact optima, so it bounds
  every selection policy at any search depth, and it is reported under both licence readings
  the package declares: the recorded exclusion tolerance, under which only a determinate
  observation can license an attribution, and the package's own measured error budget.
- Core points:
  - Menu actions keep determinate declared outcomes, because their records are retrievals of
    released values. The engagement repairs carry the measured error rate of the call, so the
    second reading prices a repair that can be wrong at a rate the package measured.
  - Under the exclusion tolerance a noisy measurement excludes nothing, so a repair priced
    with a measured error is worth exactly zero there. That is a property of the tolerance,
    not of the repair, and both numbers are printed side by side rather than one of them.
  - A gate premise is declared optimistically by the package - the plan's bet that the
    comparator engages - exactly as planning-time declarations are everywhere else in the
    framework. The certificate therefore prices the declaration, and the replay run is what
    prices the record.
- Interfaces: `case_problem`, `certificate`, `measure_package`, `main`
- Depends on: evaluation.admissible, evaluation.adaptive_reference, evaluation.capabilities,
  evaluation.cases, evaluation.repair_replay
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.adaptive_reference import DEFER, AdaptiveAction, DecisionProblem  # noqa: E402
from evaluation.admissible import admissible_certificate, binding_diagnostics  # noqa: E402
from evaluation.capabilities import CompiledRepair, load_capability_registry  # noqa: E402
from evaluation.cases import CaseRepository, ReplayCase  # noqa: E402
from evaluation.repair_replay import compilable_repairs  # noqa: E402

CATALOGUE_SOURCE = "repair_catalogue"
MENU_SOURCE = "menu"
# The framework's recorded loss convention, unchanged from the frozen-package certificate:
# a correct decision costs nothing, a wrong one ten, deferral four, plus every action's cost.
WRONG_DECISION_LOSS = 10.0
DEFERRAL_LOSS = 4.0
UNINTERPRETABLE = "uninterpretable"
RECORDED_EXCLUSION_TOLERANCE = 1e-9


def case_problem(
    case: ReplayCase,
    repairs: Sequence[CompiledRepair] = (),
    *,
    error_rate: float = 0.0,
) -> DecisionProblem:
    """One case as a declared decision problem, with the repairs a registry could supply.

    ``error_rate`` is the measured probability that an engagement call reports the wrong
    state. At zero the repair's declared outcome is determinate, which is the reading the
    frozen packages use; above zero the same action is a noisy measurement.
    """

    hypotheses = tuple(str(item["identifier"]) for item in case.public.hypotheses)
    proposed = {str(item["identifier"]): str(item["development_action"]) for item in case.public.hypotheses}
    decisions = tuple(dict.fromkeys((*proposed.values(), DEFER)))
    loss = {
        decision: {name: (0.0 if proposed[name] == decision else WRONG_DECISION_LOSS) for name in hypotheses}
        for decision in decisions
    }
    loss[DEFER] = {name: DEFERRAL_LOSS for name in hypotheses}

    actions: list[AdaptiveAction] = []
    for item in case.public.actions:
        action = item.action
        if not item.available:
            continue
        if not set(hypotheses).issubset(action.expected_outcomes):
            continue
        outcomes = {name: action.expected_outcomes[name] for name in hypotheses}
        supplies = {outcome: tuple(action.supplies) for outcome in set(outcomes.values())}
        gate = action.interpretation_gate
        actions.append(
            AdaptiveAction(
                identifier=action.identifier,
                cost=float(action.cost),
                outcome_model={name: {outcomes[name]: 1.0} for name in hypotheses},
                prerequisites=tuple(action.prerequisites),
                supplies=supplies,
                role="premise_supplier" if action.supplies else "readout",
                source=MENU_SOURCE,
                interpretation_gate=gate,
                # Without its gate the assay runs, passes its own check and moves no belief.
                uninterpretable_model=(
                    {name: {UNINTERPRETABLE: 1.0} for name in hypotheses} if gate is not None else None
                ),
            )
        )

    templates = case.public.repair_outcome_templates or {}
    for repair in repairs:
        template = templates.get(repair.premise)
        if not template or not set(hypotheses).issubset(template):
            continue
        labels = {name: str(template[name]) for name in hypotheses}
        distinct = sorted(set(labels.values()))
        model: dict[str, dict[str, float]] = {}
        for name in hypotheses:
            declared = labels[name]
            if error_rate <= 0.0 or len(distinct) < 2:
                model[name] = {declared: 1.0}
                continue
            others = [label for label in distinct if label != declared]
            model[name] = {declared: 1.0 - error_rate}
            for label in others:
                model[name][label] = error_rate / len(others)
        actions.append(
            AdaptiveAction(
                identifier=repair.identifier,
                cost=float(repair.action.cost),
                outcome_model=model,
                supplies={outcome: (repair.premise,) for outcome in distinct},
                role="premise_supplier",
                source=CATALOGUE_SOURCE,
            )
        )

    problem = DecisionProblem(
        identifier=case.public.identifier,
        hypotheses=hypotheses,
        prior={name: 1.0 / len(hypotheses) for name in hypotheses},
        actions=tuple(actions),
        budget=float(case.public.budget),
        decisions=decisions,
        loss=loss,
        family="engagement repair package",
        note=(
            "declared outcome models; menu retrievals are determinate and engagement repairs "
            f"carry a measured call error of {error_rate:.6f}"
        ),
    )
    problems = problem.validate()
    if problems:
        raise ValueError(f"{case.public.identifier}: {', '.join(problems)}")
    return problem


def certificate(
    case: ReplayCase,
    repairs: Sequence[CompiledRepair],
    *,
    error_rate: float,
) -> Mapping[str, object]:
    """The repair's certified value under both licence readings, with the diagnostics."""

    determinate = case_problem(case, repairs, error_rate=0.0)
    measured = case_problem(case, repairs, error_rate=error_rate)
    return {
        "case": case.public.identifier,
        "repairs": [repair.identifier for repair in repairs],
        "menu_actions": sum(1 for action in determinate.actions if action.source == MENU_SOURCE),
        "declared_outcomes_exclusion_tolerance": admissible_certificate(
            determinate, catalogue_source=CATALOGUE_SOURCE, tolerance=RECORDED_EXCLUSION_TOLERANCE
        ),
        "measured_error_exclusion_tolerance": admissible_certificate(
            measured, catalogue_source=CATALOGUE_SOURCE, tolerance=RECORDED_EXCLUSION_TOLERANCE
        ),
        "measured_error_measured_tolerance": admissible_certificate(
            measured, catalogue_source=CATALOGUE_SOURCE, tolerance=error_rate
        ),
        "binding_diagnostics": binding_diagnostics(determinate),
    }


def measure_package(
    *,
    public_directory: Path,
    private_directory: Path,
    registry_path: Path,
    error_rate: float | None = None,
) -> Mapping[str, object]:
    """Certify every case in a package, with and without its measured call error."""

    registry = load_capability_registry(registry_path)
    payload = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    measured = (
        error_rate
        if error_rate is not None
        else float(payload.get("null_model", {}).get("holdout_false_positive_rate_upper_95", 0.0))
    )
    rows: list[Mapping[str, object]] = []
    for case, _outcomes in CaseRepository(public_directory, private_directory).load():
        repairs = compilable_repairs(case, registry)
        rows.append(certificate(case, repairs, error_rate=measured))
    positive_declared = sum(
        1
        for row in rows
        if (row["declared_outcomes_exclusion_tolerance"]["value_of_the_repair_catalogue_admissible"] or 0) > 0
    )
    positive_measured = sum(
        1
        for row in rows
        if (row["measured_error_measured_tolerance"]["value_of_the_repair_catalogue_admissible"] or 0) > 0
    )
    positive_measured_strict = sum(
        1
        for row in rows
        if (row["measured_error_exclusion_tolerance"]["value_of_the_repair_catalogue_admissible"] or 0) > 0
    )
    return {
        "package": public_directory.parent.as_posix(),
        "registry": {"identifier": registry.identifier, "sha256": registry.sha256},
        "measured_call_error_rate": measured,
        "cases": len(rows),
        "cases_with_a_compilable_repair": sum(1 for row in rows if row["repairs"]),
        "cases_where_the_repair_is_worth_something_declared": positive_declared,
        "cases_where_the_repair_is_worth_something_measured_error_measured_tolerance": positive_measured,
        "cases_where_the_repair_is_worth_something_measured_error_exclusion_tolerance": positive_measured_strict,
        "rows": rows,
        "reading": (
            "Three columns, three claims. The declared column prices the package's own "
            "determinate declarations. The measured-error columns price the same repair as a "
            "measurement that can be wrong at the rate this package measured on held-out "
            "vehicle channels: under the recorded exclusion tolerance such a measurement "
            "excludes nothing, and under the measured tolerance it licenses at that error rate. "
            "None of the three is a biological result; each is a statement about a declared "
            "finite model."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Certify the value of a proposed repair on a real package.")
    parser.add_argument("--public-cases", type=Path, default=Path("data/evaluation/cases/engagement_v1/public"))
    parser.add_argument("--private-results", type=Path, default=Path("data/evaluation/cases/engagement_v1/private"))
    parser.add_argument(
        "--capabilities", type=Path, default=Path("data/evaluation/capabilities/engagement_capabilities_v1.json")
    )
    parser.add_argument("--error-rate", type=float, help="Override the package's measured call error rate.")
    parser.add_argument("--output", type=Path, help="Where to write the certificate JSON.")
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    payload = measure_package(
        public_directory=arguments.public_cases,
        private_directory=arguments.private_results,
        registry_path=arguments.capabilities,
        error_rate=arguments.error_rate,
    )
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"cases={payload['cases']} with_repair={payload['cases_with_a_compilable_repair']} "
        f"error_rate={payload['measured_call_error_rate']:.6f}"
    )
    for row in payload["rows"]:
        declared = row["declared_outcomes_exclusion_tolerance"]
        strict = row["measured_error_exclusion_tolerance"]
        measured = row["measured_error_measured_tolerance"]
        print(
            f"  {row['case']:34s} repairs={len(row['repairs'])} "
            f"menu_only={declared['menu_only_admissible']:.3f} closed={declared['closed_admissible']:.3f} "
            f"declared_value={declared['value_of_the_repair_catalogue_admissible']} "
            f"measured_strict={strict['value_of_the_repair_catalogue_admissible']} "
            f"measured_tolerant={measured['value_of_the_repair_catalogue_admissible']}"
        )
    if arguments.output is not None:
        print(f"written: {arguments.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
