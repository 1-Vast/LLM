"""Score the frozen real package under the admissible objective, and say why it is null.

File summary
- Path: src/evaluation/real_admissible.py
- Purpose: put the admissible certificate on the 58 frozen cases so the repair's value
  is measured under the objective the framework claims, not only under the loss
  convention it shipped. The 2026-09-14 record measured 0.000 in 58 of 58 under the
  shipped objective; this module recomputes both and reports the conditions that make
  the difference, so the null is explained rather than restated.
- Core points:
  - Each case is the declared decision problem of `real_contingent.case_problem`, in
    both the as-shipped and the retyped-counterfactual world, so the four optima are
    comparable to the recorded numbers.
  - `binding_diagnostics` reports *why* the admissible constraint does or does not
    bind: the prior, whether the root decision is licensed, and how many single actions
    separate the contrast on their own. A uniform prior with a unit-cost decisive
    action can never test the boundary, and that is a property of the package.
  - Nothing here is biological evidence. Every outcome model is a case author's
    declaration made determinate, and the package defect this module certifies is a
    defect of the declaration, not of the biology.
- Interfaces: `measure_case`, `measure_package`, `main`
- Depends on: evaluation.cases, evaluation.real_contingent, evaluation.admissible,
  evaluation.contingent
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.admissible import (  # noqa: E402
    admissible_certificate,
    binding_diagnostics,
    price_of_admissibility,
)
from evaluation.cases import CaseRepository  # noqa: E402
from evaluation.real_contingent import (  # noqa: E402
    DEFAULT_REPAIR_PREMIUM,
    REPAIR_SOURCE,
    case_problem,
)


def _median(values: Sequence[float]) -> float | None:
    finite = sorted(value for value in values if value is not None)
    if not finite:
        return None
    middle = len(finite) // 2
    if len(finite) % 2:
        return float(finite[middle])
    return float((finite[middle - 1] + finite[middle]) / 2)


def measure_case(case, *, repair_premium: float = DEFAULT_REPAIR_PREMIUM) -> Mapping[str, object]:
    declared, _ = case_problem(case, repair_premium=repair_premium, retype_matched_supplier=False)
    counterfactual, repair = case_problem(
        case, repair_premium=repair_premium, retype_matched_supplier=True
    )
    diagnostics = binding_diagnostics(declared)
    declared_price = price_of_admissibility(declared)
    retyped_price = price_of_admissibility(counterfactual)
    declared_certificate = admissible_certificate(declared, catalogue_source=REPAIR_SOURCE)
    retyped_certificate = admissible_certificate(counterfactual, catalogue_source=REPAIR_SOURCE)
    return {
        "case": case.identifier,
        "needs_a_typed_repair": bool(repair),
        "as_declared_unconstrained": declared_certificate["menu_only_unconstrained"],
        "as_declared_admissible": declared_certificate["menu_only_admissible"],
        "retyped_unconstrained_menu_only": retyped_certificate["menu_only_unconstrained"],
        "retyped_unconstrained_closed": retyped_certificate["closed_unconstrained"],
        "retyped_admissible_menu_only": retyped_certificate["menu_only_admissible"],
        "retyped_admissible_closed": retyped_certificate["closed_admissible"],
        "value_of_the_repair_catalogue_unconstrained": retyped_certificate[
            "value_of_the_repair_catalogue_unconstrained"
        ],
        "value_of_the_repair_catalogue_admissible": retyped_certificate[
            "value_of_the_repair_catalogue_admissible"
        ],
        "price_of_admissibility_as_declared": declared_price["price_of_admissibility"],
        "price_of_admissibility_retyped": retyped_price["price_of_admissibility"],
        "root_licensed": diagnostics["root_licensed"],
        "root_bayes_decision": diagnostics["root_bayes_decision"],
        "prior_is_uniform": diagnostics["prior_is_uniform"],
        "prior_max": diagnostics["prior_max"],
        "individually_decisive_actions": diagnostics["individually_decisive_actions"],
        "cheapest_decisive_cost": diagnostics["cheapest_decisive_cost"],
        "unsupported_attribution_of_the_unconstrained_reference": diagnostics[
            "unsupported_attribution_of_the_unconstrained_reference"
        ],
        "complete": bool(
            declared_certificate["complete"] and retyped_certificate["complete"]
        ),
    }


def measure_package(
    directory: Path, *, repair_premium: float = DEFAULT_REPAIR_PREMIUM
) -> Mapping[str, object]:
    root = Path(directory)
    repository = CaseRepository(root / "public", root / "private")
    rows = [
        measure_case(case.public, repair_premium=repair_premium) for case, _ in repository.load()
    ]
    certified = [row for row in rows if row["complete"]]
    needing = [row for row in certified if row["needs_a_typed_repair"]]
    return {
        "package": root.as_posix(),
        "repair_premium": repair_premium,
        "cases": len(rows),
        "certified": len(certified),
        "cases_needing_a_typed_repair": len(needing),
        "cases_where_the_repair_is_worth_something": sum(
            1 for row in needing if (row["value_of_the_repair_catalogue_unconstrained"] or 0) > 0
        ),
        "cases_where_the_repair_is_worth_something_under_admissibility": sum(
            1 for row in needing if (row["value_of_the_repair_catalogue_admissible"] or 0) > 0
        ),
        "cases_where_the_boundary_binds": sum(
            1 for row in certified if (row["price_of_admissibility_as_declared"] or 0) > 0
        ),
        "cases_with_a_uniform_prior": sum(1 for row in certified if row["prior_is_uniform"]),
        "cases_whose_root_decision_is_licensed": sum(
            1 for row in certified if row["root_licensed"]
        ),
        "cases_where_the_root_decision_attributes_without_a_licence": sum(
            1 for row in certified if not row["root_licensed"]
        ),
        "median_unsupported_attribution_of_the_unconstrained_reference": _median(
            [float(row["unsupported_attribution_of_the_unconstrained_reference"]) for row in certified]
        ),
        "median_individually_decisive_actions": _median(
            [float(row["individually_decisive_actions"]) for row in certified]
        ),
        "median_cheapest_decisive_cost": _median(
            [
                float(row["cheapest_decisive_cost"])
                for row in certified
                if row["cheapest_decisive_cost"] is not None
            ]
        ),
        "rows": rows,
        "reading": (
            "Both certificates are computed from the case author's declared outcomes. The "
            "admissible column is the same package scored under the framework's own "
            "licensing rule as a constraint. A zero in both columns means the package "
            "cannot express the decision the boundary creates, and the diagnostics say "
            "which declaration is responsible."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    directory = Path(argv[0]) if argv else Path("data/evaluation/cases/real_v3")
    out = Path(argv[1]) if len(argv) > 1 else Path("real_v3_admissible.json")
    payload = measure_package(directory)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{payload['package']}: cases={payload['cases']} certified={payload['certified']} "
        f"needing_a_typed_repair={payload['cases_needing_a_typed_repair']} "
        f"repair_worth_something_unconstrained={payload['cases_where_the_repair_is_worth_something']} "
        f"repair_worth_something_admissible="
        f"{payload['cases_where_the_repair_is_worth_something_under_admissibility']} "
        f"boundary_binds={payload['cases_where_the_boundary_binds']} "
        f"uniform_prior={payload['cases_with_a_uniform_prior']}"
    )
    print(f"written: {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
