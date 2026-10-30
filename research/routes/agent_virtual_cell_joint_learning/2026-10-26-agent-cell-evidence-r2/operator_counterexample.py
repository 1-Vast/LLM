"""Exact finite-set identity checks; no scientific data or performance experiment."""
from itertools import combinations


def leq(x, y):
    return all(a <= b for a, b in zip(x, y))


def cut_boundary(boundary, negative):
    return frozenset(x for x in boundary if not leq(negative, x))


def downsets(grid):
    for size in range(len(grid) + 1):
        for subset in combinations(grid, size):
            support = frozenset(subset)
            if all(not leq(x, y) or x in support for x in grid for y in support):
                yield support


def consistent(support, positives, negatives):
    return all(x in support for x in positives) and all(x not in support for x in negatives)


def set_union(sets):
    return frozenset().union(*sets)


def set_intersection(sets):
    if not sets:
        return None
    return frozenset.intersection(*sets)


def main():
    grid = tuple((i, j) for i in range(3) for j in range(3))
    hypotheses = tuple(downsets(grid))
    checks = 0
    for positive in grid:
        initial = tuple(h for h in hypotheses if positive in h)
        for negative in grid:
            feasible = tuple(h for h in initial if negative not in h)
            if not feasible:
                continue
            operator = cut_boundary(set_union(initial), negative)
            # A hierarchy with latent down-closed support and prior exp(|support|)
            # has exactly this MAP after the identical deterministic feedback.
            maps = tuple(h for h in feasible if len(h) == max(map(len, feasible)))
            assert maps == (operator,)
            assert set_union(feasible) == operator
            # Negative evidence adds no new unanimously permitted point.
            assert set_intersection(feasible) == frozenset(x for x in grid if leq(x, positive))
            checks += 1
    positive, negative = (0, 0), (1, 1)
    feasible = tuple(h for h in hypotheses if consistent(h, [positive], [negative]))
    maximal = set_union(feasible)
    minimal = set_intersection(feasible)
    assert (2, 0) in maximal and (2, 0) not in minimal
    assert not any(consistent(h, [(2, 2)], [(1, 1)]) for h in hypotheses)
    print({"kind": "exact mathematical identity, not empirical efficacy",
           "grid_points": len(grid), "down_closed_hypotheses": len(hypotheses),
           "consistent_positive_negative_checks": checks,
           "operator_equals_same_prior_hierarchical_MAP": True,
           "negative_adds_no_certified_positive": True,
           "maximal_support": sorted(maximal), "certified_support": sorted(minimal),
           "monotonicity_contradiction_detected": True})


if __name__ == "__main__":
    main()
