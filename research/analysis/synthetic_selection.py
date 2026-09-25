"""Synthetic property check: when does a measured anchor help candidate selection?

SYNTHETIC. Nothing here is biological evidence. The generative model is chosen to expose
one mechanism: prediction errors that are partly shared across candidates in the same
context (the "systematic variation" Systema describes) versus candidate-specific errors.

World (per task): true effects y(a) = B z(a) + idiosyncratic noise, rank-k in d dims.
Predictions: y_hat(a) = y(a) + sigma_e * (sqrt(w) * s + sqrt(1 - w) * u_a), with s shared by
all candidates in the task and u_a independent. The current candidate a0 is measured:
y_obs(a0) = y(a0) + sigma_m * m. Goal g = response of a hidden reference action (not in the
menu) plus an optional component outside the true effect span.

Rules compared (all single-shot, K = 0 extra queries):
  nearest   argmin ||g - y_hat(a)||            (== analytic gain with a predicted anchor)
  anchored  argmin ||g - (y_hat(a) + e0)||      e0 = y_obs(a0) - y_hat(a0)  (ASRG, measured anchor)
  kriged    argmin ||g - (y_hat(a) + k * e0)||  k = w_hat s_e^2 / (s_e^2 + s_m^2), w_hat estimated
            on separate calibration tasks (the out-of-fold analogue)
  random    uniform over the menu
Regret = true loss of the chosen action minus the best true loss in the menu.

Second experiment: K measured queries. Each measurement also updates the estimate of the
shared error (a Gaussian posterior on s), which is the mechanism behind "calibration anchors".
"""
from __future__ import annotations

import json
import numpy as np

D, K_RANK, N_MENU = 30, 6, 60


def make_world(rng):
    basis, _ = np.linalg.qr(rng.normal(size=(D, K_RANK)))
    return basis


def task(rng, basis, w, sigma_e, sigma_m, off_span):
    z = rng.normal(size=(N_MENU + 1, K_RANK)) * np.array([3, 2.5, 2, 1.5, 1, 0.7])
    y = z @ basis.T + 0.05 * rng.normal(size=(N_MENU + 1, D))
    reference, y = y[0], y[1:]
    perp = rng.normal(size=D); perp -= basis @ (basis.T @ perp); perp /= np.linalg.norm(perp)
    g = reference + off_span * perp
    shared = rng.normal(size=D)
    err = sigma_e * (np.sqrt(w) * shared[None, :] + np.sqrt(1 - w) * rng.normal(size=(N_MENU, D)))
    y_hat = y + err
    a0 = int(rng.integers(N_MENU))
    y_obs0 = y[a0] + sigma_m * rng.normal(size=D)
    return g, y, y_hat, a0, y_obs0


def true_loss(g, y):
    return ((g - y) ** 2).sum(-1)


def choose(g, y_hat, a0, y_obs0, rule, kappa=0.0, rng=None):
    if rule == "random":
        return int(rng.integers(len(y_hat)))
    e0 = y_obs0 - y_hat[a0]
    offset = {"nearest": 0.0, "anchored": 1.0, "kriged": kappa}[rule]
    scores = true_loss(g, y_hat + offset * e0)
    scores[a0] = true_loss(g, y_obs0)  # the anchor itself is known from its measurement
    return int(np.argmin(scores))


def estimate_w(rng, basis, w, sigma_e, sigma_m, n_cal=40):
    """Method-of-moments estimate of the shared-error fraction from calibration tasks.

    In a real study this is the out-of-fold residual covariance between candidates in the
    same context; here each calibration task reveals two measured candidates.
    """
    cov, var = [], []
    for _ in range(n_cal):
        g, y, y_hat, a0, _ = task(rng, basis, w, sigma_e, sigma_m, 0.0)
        a, b = rng.choice(N_MENU, 2, replace=False)
        ra = (y[a] + sigma_m * rng.normal(size=D)) - y_hat[a]
        rb = (y[b] + sigma_m * rng.normal(size=D)) - y_hat[b]
        cov.append(np.mean(ra * rb)); var.append(0.5 * (np.mean(ra * ra) + np.mean(rb * rb)))
    total = np.mean(var)
    return float(np.clip(np.mean(cov) / max(total - sigma_m ** 2, 1e-9), 0, 1))


def experiment_single_shot(seed=1, tasks=1500):
    rng = np.random.default_rng(seed)
    basis = make_world(rng)
    rows = []
    for sigma_e in (0.5, 1.0):
        for w in (0.0, 0.25, 0.5, 0.75, 0.95):
            sigma_m = 0.2
            w_hat = estimate_w(rng, basis, w, sigma_e, sigma_m)
            kappa = w_hat * sigma_e ** 2 / (sigma_e ** 2 + sigma_m ** 2)
            regrets = {r: [] for r in ("nearest", "anchored", "kriged", "random")}
            for _ in range(tasks):
                g, y, y_hat, a0, y_obs0 = task(rng, basis, w, sigma_e, sigma_m, off_span=1.0)
                losses = true_loss(g, y); best = losses.min()
                for rule in regrets:
                    regrets[rule].append(losses[choose(g, y_hat, a0, y_obs0, rule, kappa, rng)] - best)
            summary = {r: (float(np.mean(v)), float(1.96 * np.std(v) / np.sqrt(len(v)))) for r, v in regrets.items()}
            rows.append({"sigma_e": sigma_e, "w_true": w, "w_hat": round(w_hat, 3), "kappa": round(kappa, 3), **summary})
    return rows


def experiment_budget(seed=2, tasks=600, w=0.6, sigma_e=1.0, sigma_m=0.2):
    """K measured queries, selected greedily by current predicted loss or at random.

    'shared-update' uses every measured residual to update the posterior mean of the shared
    error s (conjugate Gaussian), then re-predicts all unmeasured candidates.
    """
    rng = np.random.default_rng(seed)
    basis = make_world(rng)
    tau2 = w * sigma_e ** 2          # prior variance of the shared error per coordinate
    nug2 = (1 - w) * sigma_e ** 2 + sigma_m ** 2  # candidate-specific + measurement variance
    out = {}
    for K in (0, 1, 2, 4, 8):
        res = {"greedy_no_update": [], "greedy_shared_update": [], "random_shared_update": []}
        for _ in range(tasks):
            g, y, y_hat, a0, y_obs0 = task(rng, basis, w, sigma_e, sigma_m, off_span=1.0)
            losses = true_loss(g, y); best = losses.min()
            for policy in res:
                measured = {a0: y_obs0}
                for _step in range(K):
                    if policy.endswith("shared_update"):
                        resid = np.array([measured[a] - y_hat[a] for a in measured])
                        n = len(resid)
                        s_mean = resid.sum(0) * tau2 / (nug2 + n * tau2)
                    else:
                        s_mean = np.zeros(D)
                    pred = y_hat + s_mean
                    for a, v in measured.items():
                        pred[a] = v
                    remaining = [a for a in range(N_MENU) if a not in measured]
                    if policy.startswith("random"):
                        pick = int(rng.choice(remaining))
                    else:
                        pick = min(remaining, key=lambda a: true_loss(g, pred[a]))
                    measured[pick] = y[pick] + sigma_m * rng.normal(size=D)
                # final choice: best measured, or best predicted if that is predicted better
                resid = np.array([measured[a] - y_hat[a] for a in measured]); n = len(resid)
                s_mean = resid.sum(0) * tau2 / (nug2 + n * tau2) if policy.endswith("shared_update") else np.zeros(D)
                pred = y_hat + s_mean
                for a, v in measured.items():
                    pred[a] = v
                choice = int(np.argmin(true_loss(g, pred)))
                res[policy].append(losses[choice] - best)
        out[K] = {p: (float(np.mean(v)), float(1.96 * np.std(v) / np.sqrt(len(v)))) for p, v in res.items()}
    return out


if __name__ == "__main__":
    single = experiment_single_shot()
    print("SINGLE-SHOT (K=0) mean regret +/- 95% half-width; lower is better. SYNTHETIC.")
    print(f"{'sigma_e':>7} {'w':>5} {'w_hat':>6} {'kappa':>6} | {'nearest':>14} {'anchored':>14} {'kriged':>14} {'random':>14}")
    for r in single:
        fmt = lambda k: f"{r[k][0]:7.2f}±{r[k][1]:5.2f}"
        print(f"{r['sigma_e']:7.1f} {r['w_true']:5.2f} {r['w_hat']:6.3f} {r['kappa']:6.3f} | "
              f"{fmt('nearest'):>14} {fmt('anchored'):>14} {fmt('kriged'):>14} {fmt('random'):>14}")
    budget = experiment_budget()
    print("\nQUERY BUDGET (w=0.6, sigma_e=1.0): mean regret +/- 95% half-width. SYNTHETIC.")
    for K, v in budget.items():
        print(f"K={K}: " + "  ".join(f"{p}={m:6.2f}±{h:4.2f}" for p, (m, h) in v.items()))
    with open("synthetic_results.json", "w") as f:
        json.dump({"single_shot": single, "budget": {str(k): v for k, v in budget.items()},
                   "note": "synthetic property check; not biological evidence"}, f, indent=1)
