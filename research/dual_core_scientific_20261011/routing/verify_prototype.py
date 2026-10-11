"""Finite permutation and shift checks before promoting the routing contract."""
from dataclasses import replace
from itertools import permutations
import json
from pathlib import Path

from virtual_cell.interface import Intervention, PredictionRequest, SystemContext
from routing_contract import BackendPreference, BackendRoutingPolicy


def main():
    request = PredictionRequest("q", "case", "contrast", 1,
                                Intervention("drug", "drug", (), 1.0, "uM", 24.0),
                                SystemContext("cell", "cell", dataset_id="platform"), ("rna",), "v1")
    base = BackendPreference("a", "v1", "cell", "platform", ("rna",), "drug", 1.0, "uM", 24.0,
                             "calibration-v1", 50, 1.0)
    rules = (base, replace(base, backend="b", reference_units=60, compute_cost=2.0),
             replace(base, backend="c", reference_units=60, compute_cost=0.5))
    policies = [BackendRoutingPolicy("reference-policy", "1" * 64, order) for order in permutations(rules)]
    assert {p.ranked(request, {"a", "b", "c"})[0].backend for p in policies} == {"c"}
    assert len({p.identity for p in policies}) == 1
    shifts = (replace(request, context=replace(request.context, dataset_id="shifted")),
              replace(request, intervention=replace(request.intervention, time_hours=48.0)),
              replace(request, intervention=replace(request.intervention, dose=2.0)),
              replace(request, readouts=("viability",)))
    assert all(not policies[0].ranked(q, {"a", "b", "c"}) for q in shifts)
    report = {"status": "VERIFIED_ENGINEERING_ONLY", "permutations": len(policies),
              "refused_scope_shifts": len(shifts), "selected": "c",
              "scientific_benefit": "NOT_EVALUATED"}
    Path(__file__).with_name("prototype_result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
