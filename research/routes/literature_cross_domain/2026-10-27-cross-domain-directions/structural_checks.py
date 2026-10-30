"""Deterministic mathematical checks, not biological experiments or performance evidence."""
import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent


def contrast_values(values):
    return [values[i] - values[j] for i, j in itertools.combinations(range(len(values)), 2)]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def rho_ranks(predicted):
    n = len(predicted)
    return 1 - 6 * sum((i - p) ** 2 for i, p in enumerate(predicted, 1)) / (n * (n * n - 1))


def weighted_alignment(a, b, weights):
    numerator = sum(w * x * y for w, x, y in zip(weights, a, b))
    denominator = math.sqrt(sum(w * x*x for w, x in zip(weights, a)) *
                            sum(w * y*y for w, y in zip(weights, b)))
    return numerator / denominator


signed = contrast_values([1, -1, -1, 1])
recoded = contrast_values([1, 1, -1, -1])
assert median(signed) == 0 and median(recoded) == 2
screen_b = [1.9, 2.1, 0.2, -0.1, -1.8, -2.2]
weights = [1, 2, 3, 4, 5, 6]
flips = [1, -1, 1, -1, -1, 1]
alignment = weighted_alignment(signed, screen_b, weights)
alignment_flipped = weighted_alignment([x*s for x, s in zip(signed, flips)],
                                       [y*s for y, s in zip(screen_b, flips)], weights)
assert alignment == alignment_flipped

# A fully shared rank-one law can have zero condition/cell additive marginal means.
factor = [1.0, -1.0]
rank_one = [[a*b for b in factor] for a in factor]
assert all(sum(row) == 0 for row in rank_one)
assert all(sum(row[j] for row in rank_one) == 0 for j in range(2))
assert rank_one[0][0]*rank_one[1][1] == rank_one[0][1]*rank_one[1][0]

# Cov(Q_01,Q_02)=Var(e0) under independent equal-variance key errors.
# Mean of all lexically oriented cell contrasts has only O(n) independent noise.
dyadic_averaging = []
for n_cells in [4, 10, 30]:
    edge_count = n_cells*(n_cells-1)//2
    coefficients = [n_cells-1-2*i for i in range(n_cells)]
    true_variance = sum(a*a for a in coefficients)/(edge_count*edge_count)
    iid_edge_variance = 2/edge_count
    dyadic_averaging.append({'cells': n_cells, 'pairs': edge_count, 'key_error_variance': 1,
                            'actual_mean_contrast_variance': true_variance,
                            'independent_pair_formula_variance': iid_edge_variance})

# q2.py's weighted formula mixes first-power and squared weights; compare algebra only.
wy, ww = [1.0, 3.0], [2.0, 1.0]
w_sum = sum(ww)
w2_sum = sum(w*w for w in ww)
s_sum = sum(w*y for w,y in zip(ww,wy))
t_sum = sum(w*y*y for w,y in zip(ww,wy))
w_mu = s_sum/w_sum
reported_weighted_pair_moment = 0.5*((s_sum-w_mu*w_sum)**2-
    (t_sum-2*w_mu*s_sum+w_mu*w_mu*w2_sum))/(0.5*(w_sum*w_sum-w2_sum))
direct_weighted_pair_moment = (wy[0]-w_mu)*(wy[1]-w_mu)
assert abs(reported_weighted_pair_moment-direct_weighted_pair_moment) > 1

# K0=e1, P=diag(0,1), k1=e1+e2: edit and projected kernel coincide.
delta = 0.3
update = [0.0, delta]
old_key, new_key = [1.0, 0.0], [1.0, 1.0]
queries = [[1.0, t] for t in [-2.0, 0.0, 0.5, 1.0, 2.0]]
edit = [dot(update, k) for k in queries]
kernel = [delta * k[1] for k in queries]
assert edit == kernel and dot(update, old_key) == 0
small_q_norm = 1e-6
required_update_norm = abs(delta) / small_q_norm

# Screen-cell and screen-condition additive terms cancel in a double contrast.
cell, condition = [2, 7], [11, -3]
y = [[5 + c + p for p in condition] for c in cell]
q = (y[0][0] - y[0][1]) - (y[1][0] - y[1][1])
assert q == 0

# All times preserve N(0,I), despite different paths under a rotation.
angle = math.pi / 2
rotation = [[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]]
rrt = [[dot(row_i, row_j) for row_j in rotation] for row_i in rotation]
assert max(abs(rrt[i][j] - int(i == j)) for i in range(2) for j in range(2)) < 1e-14
stationary_path = [1.0, 0.0]
rotating_path = [row[0] for row in rotation]
assert abs(rotating_path[0] - stationary_path[0]) > 0.9

# Global rank association is neither necessary nor sufficient for top-1 utility.
zero_rho_correct_top = [4, 3, 2, 1, 5]
high_rho_wrong_top = list(range(1, 101))
high_rho_wrong_top[-2:] = [100, 99]
assert rho_ranks(zero_rho_correct_top) == 0
assert max(range(5), key=lambda i: zero_rho_correct_top[i]) == 4
assert max(range(100), key=lambda i: high_rho_wrong_top[i]) == 98

result = {
    "kind": "deterministic_mathematical_examples_not_biological_results",
    "signed_median": {"same_biological_values_different_id_order": True, "contrasts": signed,
                      "median": median(signed), "recoded_contrasts": recoded, "recoded_median": median(recoded)},
    "fixed_cycle_alignment": {"weighted_value": alignment, "same_cycles_synchronously_flipped": alignment_flipped,
                              "scope": "Algebra only; no independent-sample or calibrated-inference claim"},
    "shared_rank_one": {"matrix": rank_one, "condition_marginal_means": [0,0],
                        "cell_marginal_means": [0,0], "rank": 1,
                        "scope": "Zero additive condition share does not rule out a fully shared conditional law"},
    "dyadic_average_variance": dyadic_averaging,
    "q2_weighted_moment_formula": {"code_formula": reported_weighted_pair_moment,
                                    "direct_distinct_pair_formula": direct_weighted_pair_moment,
                                    "scope": "Illustration of weighted formula only, not re-estimation of biological data"},
    "local_edit": {"old_change": dot(update, old_key), "new_change": dot(update, new_key),
                   "query_changes": edit, "projected_kernel_changes": kernel,
                   "small_projected_key_norm": small_q_norm, "exact_edit_norm": required_update_norm,
                   "infeasible_case": "k_new=k_old and nonzero change, while old key is exactly preserved"},
    "additive_nuisance_double_contrast": q,
    "dynamic_ambiguity": {"rotation_times_transpose": rrt, "stationary_path_t": stationary_path,
                          "rotating_path_t": rotating_path,
                          "marginals": "both are N(0,I) for every t under isotropic initial Gaussian"},
    "decision_metric": {"zero_spearman_correct_top1": rho_ranks(zero_rho_correct_top),
                        "high_spearman_wrong_top1": rho_ranks(high_rho_wrong_top),
                        "high_rho_utility_regret_if_last_two_utilities_1_and_100": 99,
                        "scope": "No universal utility threshold follows from rank correlation alone"},
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
(ROOT / "structural_checks.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, ensure_ascii=False))
