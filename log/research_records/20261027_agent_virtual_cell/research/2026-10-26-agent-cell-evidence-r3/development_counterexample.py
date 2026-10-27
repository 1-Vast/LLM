"""Pure arithmetic checks for the ordinal candidate; no scientific data loaded."""
from itertools import permutations
import json


def monotone_interpolate(xs, ys, x):
    for i in range(1, len(xs)):
        if x <= xs[i]:
            t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    raise ValueError(x)


# End-point controls can agree while interior response curves differ.
xs = [0.0, 1 / 3, 2 / 3, 1.0]
rows = [[0.0, 0.1, 0.2, 1.0], [0.0, 0.7, 0.9, 1.0]]
for ys in rows:
    assert all(a < b for a, b in zip(ys, ys[1:]))
    for x, y in zip(xs, ys):
        assert abs(monotone_interpolate(xs, ys, x) - y) < 1e-12

# With no ties, a common scalar latent axis exists iff row orders agree.
checked = 0
for a in permutations(range(3)):
    for b in permutations(range(3)):
        same_order = a == b
        no_crossing = all((a[i] - a[j]) * (b[i] - b[j]) > 0
                          for i in range(3) for j in range(i))
        assert same_order == no_crossing
        checked += 1

# Rejection does not select an extension: two completions reverse an unseen choice.
observed = {"T": {"a": 0.1, "b": 0.8}, "N": {"a": 0.9, "b": 0.2}}
assert ((observed["T"]["a"] - observed["T"]["b"]) *
        (observed["N"]["a"] - observed["N"]["b"])) < 0
w1 = {"p": (0.1, 0.9), "q": (0.8, 0.9)}
w2 = {"p": (0.8, 0.9), "q": (0.1, 0.9)}
def winner(world):
    return max(world, key=lambda k: world[k][1] - world[k][0])
assert winner(w1) == "p" and winner(w2) == "q"
print(json.dumps({"kind": "synthetic_arithmetic_only", "rank_cases": checked,
                  "control_anchored_nonlinearity": True,
                  "observed_crossing": True,
                  "same_observation_opposite_unseen_winner": True}))
