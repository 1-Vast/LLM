"""Illustrative worked example for the report. Every number is invented for illustration."""
import numpy as np

names = ["prolif", "stress", "diff"]
W = np.diag([1.0, 2.0, 0.5])            # prespecified weights: stress is protected
g = np.array([-1.0, 0.0, 0.5])           # goal shift vs matched control
y_obs0 = np.array([-0.3, 0.6, 0.1])      # measured response of current action a0
y_hat = {                                 # cheap-model predictions (same basis)
    "a0 (current, 1 uM)": np.array([-0.5, 0.3, 0.1]),
    "a1 (same cpd, 0.3 uM)": np.array([-0.3, 0.1, 0.1]),
    "a2 (same class)": np.array([-0.9, 0.2, 0.1]),
    "a3 (other class)": np.array([-1.1, -0.1, 0.1]),
    "a4 (other class)": np.array([-0.6, 0.0, 0.1]),
}
kappa = {"a1 (same cpd, 0.3 uM)": 0.9, "a2 (same class)": 0.5, "a3 (other class)": 0.1, "a4 (other class)": 0.3}
unc = {"a1 (same cpd, 0.3 uM)": 0.02, "a2 (same class)": 0.05, "a3 (other class)": 0.40, "a4 (other class)": 0.08}

L = lambda v: float(v @ W @ v)
e0 = y_obs0 - y_hat["a0 (current, 1 uM)"]
r_meas = g - y_obs0
print("anchor residual e0 =", e0, " measured loss of a0 =", round(L(r_meas), 3))
print(f"{'action':24} {'nearest':>8} {'anchored':>9} {'kriged':>7} {'kriged+unc':>11} {'gain_meas':>9}")
for name, yh in y_hat.items():
    if name.startswith("a0"):
        continue
    near = L(g - yh)
    anch = L(g - (yh + e0))
    krig = L(g - (yh + kappa[name] * e0))
    delta = yh - y_hat["a0 (current, 1 uM)"]
    gain = 2 * r_meas @ W @ delta - L(delta)          # analytic gain with measured anchor
    print(f"{name:24} {near:8.3f} {anch:9.3f} {krig:7.3f} {krig + unc[name]:11.3f} {gain:9.3f}")

# Reachability certificate: every predicted delta has zero 'diff' component here, so the
# W-orthogonal complement of span{delta} contains the diff axis.
deltas = np.array([yh - y_hat["a0 (current, 1 uM)"] for n, yh in y_hat.items() if not n.startswith("a0")])
basis, _ = np.linalg.qr(deltas.T)
rank = np.linalg.matrix_rank(deltas)
S = basis[:, :rank]
P = S @ np.linalg.solve(S.T @ W @ S, S.T @ W)
perp_r = r_meas - P @ r_meas
max_perp_delta = max(np.sqrt(L(d - P @ d)) for d in deltas)
bound = max(0.0, np.sqrt(L(perp_r)) - max_perp_delta) ** 2
print("span rank of candidate deltas:", rank, " lower bound on achievable loss:", round(bound, 3))
