"""Report the complete development frontier, per-context harm and exact flag sets."""
from __future__ import annotations

import csv
import json

from verify_direction import HERE, STUDY, sha


def main():
    path = STUDY / "budget_frontier1/FRONTIER.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        points = list(csv.DictReader(handle))
    contexts = ("PANC-1", "HepG2/C3A")
    grouped = {}
    for point in points:
        key = (point["model"], point["policy"], int(point["screens"]))
        grouped.setdefault(key, {})[point["context"]] = point
    baseline = {context: grouped[("M0", "knowledge_gradient", 8)][context] for context in contexts}
    chosen = grouped[("M2", "fixed_top_prior", 5)]
    per_context = {}
    for context in contexts:
        reference, candidate = baseline[context], chosen[context]
        reference_flags, candidate_flags = json.loads(reference["flags"]), json.loads(candidate["flags"])
        assert set(reference_flags) == set(candidate_flags)
        assert float(reference["utility"]) == float(candidate["utility"])
        same_k = grouped[("M0", "knowledge_gradient", 5)][context]
        per_context[context] = {
            "STATE_K5_flags": candidate_flags,
            "simple_KG8_flags": reference_flags,
            "identical_flag_sets": True,
            "STATE_K5_utility": float(candidate["utility"]),
            "simple_KG8_utility": float(reference["utility"]),
            "STATE_K5_minus_simple_KG5": float(candidate["utility"]) - float(same_k["utility"]),
        }
    ordered = sorted(grouped, key=lambda key: (key[2], key[0], key[1]))
    pareto = []
    for key in ordered:
        u = [float(grouped[key][context]["utility"]) for context in contexts]
        dominated = False
        for other in ordered:
            v = [float(grouped[other][context]["utility"]) for context in contexts]
            if other[2] <= key[2] and all(b >= a - 1e-12 for a, b in zip(u, v)):
                if other[2] < key[2] or any(b > a + 1e-12 for a, b in zip(u, v)):
                    dominated = True
                    break
        if not dominated:
            pareto.append({"model": key[0], "policy": key[1], "screens": key[2],
                           "counterfactual_total_profiles": key[2] + 5,
                           "per_context_utility": dict(zip(contexts, u))})
    harm = []
    for policy in ("fixed_top_prior", "knowledge_gradient"):
        for count in range(9):
            differences = {
                context: float(grouped[("M2", policy, count)][context]["utility"])
                - float(grouped[("M0", policy, count)][context]["utility"])
                for context in contexts
            }
            harm.append({"policy": policy, "screens": count, "STATE_minus_same_policy_empirical": differences})
    result = {
        "status": "Independently verified posthoc development frontier; no confirmatory cost claim",
        "source_sha256": sha(path),
        "parent_verification_sha256": sha(HERE / "FOLLOWUP_VERIFICATION.json"),
        "chosen_point_for_future_protocol_only": "M2 fixed_top_prior K5 versus M0 knowledge_gradient K8",
        "counterfactual_profile_totals": {"STATE_K5": 10, "simple_KG8": 13},
        "counterfactual_total_profile_reduction": 3 / 13,
        "counterfactual_first_well_reduction": 3 / 8,
        "same_cap_unused_STATE_K5": 3,
        "actual_new_purchases": 0,
        "per_context": per_context,
        "all_same_policy_harm_comparisons": harm,
        "undominated_observed_points": pareto,
        "selection_limit": "K5 chosen after examining all K0..8 and both exposed contexts; freeze for new independent units before calling benefit validated",
        "not_a_stopping_rule": "Outcome frontier does not supply an implementable target-blind adaptive stopping threshold",
    }
    with (HERE / "FRONTIER_DETAIL.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "all_same_policy_harm_comparisons"}, indent=2))


if __name__ == "__main__":
    main()
