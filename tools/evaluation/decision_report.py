"""Paired terminal utility with explicit measurement and turnaround prices."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from math import isfinite
from pathlib import Path
from random import Random
import re
from typing import Sequence

from maestro.campaign_budget import CampaignBudget
from tools.evaluation.scoring import cluster_signflip_test


@dataclass(frozen=True)
class CampaignResult:
    campaign_id: str
    cluster_id: str
    arm: str
    endpoint: str
    problem_sha256: str
    measurement_budget: int
    terminal_utility: float
    measurements: int
    turnarounds: int
    other_resource_cost: float = 0.0
    other_utility_cost: float = 0.0

    def __post_init__(self) -> None:
        if any(not isinstance(v, str) or not v.strip()
               for v in (self.campaign_id, self.cluster_id, self.arm, self.endpoint)):
            raise ValueError("campaign identities and endpoint must be named")
        if not isinstance(self.problem_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", self.problem_sha256):
            raise ValueError("campaign problem requires a SHA256 identity")
        for value in (self.measurement_budget, self.measurements, self.turnarounds):
            if type(value) is not int or value < 0:
                raise ValueError("campaign budget and resource counts must be nonnegative integers")
        if self.measurements > self.measurement_budget:
            raise ValueError("campaign exceeds measurement budget")
        if (isinstance(self.terminal_utility, bool) or not isinstance(self.terminal_utility, (int, float))
                or not isfinite(self.terminal_utility)):
            raise ValueError("campaign utility must be finite")
        for value in (self.other_resource_cost, self.other_utility_cost):
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not isfinite(value) or value < 0):
                raise ValueError("other campaign costs must be finite and nonnegative")


def paired_campaign_report(rows: Sequence[CampaignResult], *, reference: str, candidate: str,
                           measurement_price: float, turnaround_price: float,
                           resamples: int = 2000, seed: int = 0,
                           resource_budget: CampaignBudget | None = None) -> dict:
    """Candidate minus reference, resampling and sign-flipping entire independent clusters.

    Prices must be declared in terminal utility units before comparing outcomes.
    A turnaround price is a scenario input, not a measured laboratory price.
    Problem identity must bind the library, population, conditions and budget.
    This validates paired declarations; it does not certify the underlying data.
    A common resource_budget enforces a hard total cap separately from utility
    pricing. Other costs (API, compute, overhead) must be declared in each unit;
    there is no automatic conversion between resource and terminal-utility units.
    """
    for value in (measurement_price, turnaround_price):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
            raise ValueError("resource prices must be finite nonnegative utility-unit values")
    if type(resamples) is not int or resamples < 2:
        raise ValueError("at least two bootstrap resamples are required")
    if reference == candidate:
        raise ValueError("two different arms are required")
    arms: dict[str, dict[str, CampaignResult]] = {reference: {}, candidate: {}}
    for row in rows:
        if row.arm not in arms:
            continue
        if row.campaign_id in arms[row.arm]:
            raise ValueError("duplicate campaign-arm result")
        arms[row.arm][row.campaign_id] = row
    if not arms[reference] or set(arms[reference]) != set(arms[candidate]):
        raise ValueError("paired arms must contain exactly the same nonempty campaigns")
    differences, raw, clusters, measurements, turnarounds, other_utility = [], [], [], [], [], []
    resource_costs: dict[str, list[float]] = {reference: [], candidate: []}
    endpoints = set()
    for name in sorted(arms[reference]):
        left, right = arms[reference][name], arms[candidate][name]
        if (left.cluster_id, left.endpoint, left.problem_sha256, left.measurement_budget) != (
                right.cluster_id, right.endpoint, right.problem_sha256, right.measurement_budget):
            raise ValueError("campaign comparison changes endpoint, problem, cluster or budget")
        endpoints.add(left.endpoint)
        # Validate each arm's complete declared utility cost even when equal
        # costs would cancel in the paired contrast.
        try:
            costs = [measurement_price * row.measurements + turnaround_price * row.turnarounds
                     + row.other_utility_cost for row in (left, right)]
        except OverflowError as exc:
            raise ValueError("derived campaign costs must be finite") from exc
        if not all(isfinite(value) for value in costs):
            raise ValueError("derived campaign costs must be finite")
        raw.append(right.terminal_utility - left.terminal_utility)
        measurements.append(right.measurements - left.measurements)
        turnarounds.append(right.turnarounds - left.turnarounds)
        other_utility.append(right.other_utility_cost - left.other_utility_cost)
        differences.append(raw[-1] - measurement_price * measurements[-1]
                           - turnaround_price * turnarounds[-1] - other_utility[-1])
        if not all(isfinite(value) for value in (raw[-1], differences[-1], other_utility[-1])):
            raise ValueError("derived campaign differences must be finite")
        if resource_budget is not None:
            for row in (left, right):
                resource_costs[row.arm].append(resource_budget.require_feasible(
                    row.measurements, row.turnarounds, other_cost=row.other_resource_cost))
        clusters.append(left.cluster_id)
    if len(endpoints) != 1:
        raise ValueError("pooled campaigns must share one endpoint and utility unit")
    # An absolute-sum bound also protects sign flips from intermediate overflow
    # when the observed signed sum happens to cancel to a finite value.
    for values in (raw, differences, measurements, turnarounds, other_utility, *resource_costs.values()):
        try:
            safe = isfinite(sum(abs(value) for value in values) * (1.0 + 1e-9))
        except OverflowError:
            safe = False
        if not safe:
            raise ValueError("campaign aggregation must remain finite")
    grouped: dict[str, list[float]] = {}
    for label, value in zip(clusters, differences):
        grouped.setdefault(label, []).append(value)
    names = sorted(grouped)
    if not isfinite(len(names) * max(sum(abs(value) for value in group) for group in grouped.values())):
        raise ValueError("bootstrap aggregation must remain finite")
    interval = None
    if len(names) >= 2:
        rng = Random(seed)
        draws = []
        for _ in range(resamples):
            sampled = [grouped[names[rng.randrange(len(names))]] for _ in names]
            draws.append(sum(sum(g) for g in sampled) / sum(len(g) for g in sampled))
        draws.sort()
        interval = [draws[int(0.025 * (resamples - 1))], draws[int(0.975 * (resamples - 1))]]
    count = len(differences)
    signflip = cluster_signflip_test(differences, clusters, seed=seed)
    if not signflip["exact"]:
        patterns = signflip["n_patterns"]
        for name in ("p_greater", "p_less", "p_two_sided"):
            signflip[name] = (round(signflip[name] * patterns) + 1) / (patterns + 1)
        signflip["monte_carlo_resolution"] = 1 / (patterns + 1)
        signflip["monte_carlo_correction"] = "plus one; a sampled test cannot report p=0"
    return {
        "schema": "maestro.paired_terminal_utility.v1", "reference": reference, "candidate": candidate,
        "campaigns": count, "independent_clusters": len(names),
        "raw_utility_increment": sum(raw) / count,
        "net_utility_increment": sum(differences) / count, "cluster_bootstrap_95": interval,
        "measurement_increment": sum(measurements) / count, "turnaround_increment": sum(turnarounds) / count,
        "other_utility_cost_increment": sum(other_utility) / count,
        "resource_budget": None if resource_budget is None else {
            **asdict(resource_budget),
            "mean_spend": {arm: sum(costs) / count for arm, costs in resource_costs.items()},
            "maximum_spend": {arm: max(costs) for arm, costs in resource_costs.items()},
            "basis": "common declared resource cap; prices and omitted costs are not authenticated",
        },
        "prices": {"measurement": measurement_price, "turnaround": turnaround_price,
                   "basis": "declared terminal-utility units; not authenticated monetary cost"},
        "signflip": signflip,
        "limitation": "Retrospective utility is scoped to the recorded endpoint and data. Multiple comparisons require a registered correction.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSON list of CampaignResult records")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--measurement-price", type=float, required=True)
    parser.add_argument("--turnaround-price", type=float, required=True)
    parser.add_argument("--resource-budget", type=Path,
                        help="JSON CampaignBudget with total, measurement_cost, turnaround_cost and unit")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [CampaignResult(**row) for row in json.loads(args.input.read_text(encoding="utf-8"))]
    report = paired_campaign_report(rows, reference=args.reference, candidate=args.candidate,
                                    measurement_price=args.measurement_price, turnaround_price=args.turnaround_price,
                                    resource_budget=None if args.resource_budget is None else CampaignBudget(
                                        **json.loads(args.resource_budget.read_text(encoding="utf-8"))))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("campaigns", "independent_clusters", "net_utility_increment")},
                     allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
