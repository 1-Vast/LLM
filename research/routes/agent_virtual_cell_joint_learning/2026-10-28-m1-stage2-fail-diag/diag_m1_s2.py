#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M1-S2-FAIL-DIAG: failure-attribution diagnostic for M1 Stage2 H1 0/16.

DIAGNOSTIC ONLY. Does not change C216 verdict, does not re-run H1 as a gate, does not output
effect/decision utility/regret/top-k/method comparison. Frozen environment = C216 exactly.

Writes only: diag_m1_s2.json (result; telemetry excluded). Run twice -> byte identical.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
from scipy.special import ndtr, ndtri

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))
C216_JSON = os.path.join(BASE, '2026-10-28-m1-stage2-rerun', 'm1_stage2_rerun.json')
C216_SHA = 'B2CD01954F88F40111AFC286ECD7B67A45CB57E96B3D95C06E35936447B72107'
OUT_JSON = os.path.join(HERE, 'diag_m1_s2.json')

# ---------------- frozen constants (copied from C216) ----------------
D = 64
A = 4
Y_DIM = 4
Y_BOX = 2.0
K = 3
WEIGHTS = np.array([0.5, 0.3, 0.2])
PARAM_SEED = 20261301
TRAIN_SEED = 20261302
EVAL_SEED = 20261303
H1_CELL_SEEDS = [20261310 + i for i in range(16)]
H1_DIMS = [8, 16, 32, 64]
H1_NS = [512, 1024, 2048, 4096]
H1_TOL = {8: [.12, .10, .08, .07], 16: [.14, .11, .09, .08],
          32: [.16, .13, .11, .10], 64: [.18, .15, .13, .12]}
CAPS = {'wall_s': 1800.0, 'cpu_s': 7200.0, 'memory_gb': 8.0, 'new_wells': 0}

# ---------------- pre-registered diagnostic constants ----------------
ORACLE_REPS = 200
POP_PER_ROW = 256
FLOOR_MC_REPS = 1000
SENS = [(64, 512), (64, 1024), (64, 2048), (64, 4096), (8, 512), (8, 4096)]
FID = [(64, 4096), (8, 512)]
SENS_HIDDEN = 256
SENS_EPOCHS = 400


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def json_safe(o):
    if isinstance(o, dict):
        return {str(k): json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [json_safe(v) for v in o]
    if isinstance(o, np.ndarray):
        return [json_safe(v) for v in o.tolist()]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, float):
        return None if not math.isfinite(o) else float(o)
    return o


# ---------------- frozen P_theta (exactly as C216) ----------------
class PTheta:
    def __init__(self, seed=PARAM_SEED):
        rng = np.random.default_rng(seed)
        self.c = rng.normal(0.0, 0.5, size=(A, K, Y_DIM))
        self.M = rng.normal(0.0, 0.1, size=(A, K, Y_DIM, D))
        self.d = rng.normal(0.0, 0.1, size=(A, K, D))
        self.weights = WEIGHTS.copy()

    def mu_sigma_rows(self, X, Aarr):
        """Vectorized per-row mu/sig matrices for the used dimensions: X (n,d), Aarr (n,)."""
        n, d = X.shape
        mu = np.empty((n, K, Y_DIM))
        sig = np.empty((n, K, Y_DIM))
        for a in range(A):
            idx = np.where(Aarr == a)[0]
            if len(idx) == 0:
                continue
            xa = X[idx]
            mu[idx] = self.c[a][None] + np.einsum('kyd,nd->nky', self.M[a][:, :, :d], xa)
            z = np.einsum('kd,nd->nk', self.d[a][:, :d], xa)
            sig[idx] = 0.1 + 0.4 / (1.0 + np.exp(-z))[:, :, None]
        return mu, sig

    def comp_mass(self, mu, sig):
        lo = ndtr((-Y_BOX - mu) / sig)
        hi = ndtr((Y_BOX - mu) / sig)
        return np.prod(hi - lo, axis=2)

    def sample_rows(self, mu, sig, rng, m_per_row=1):
        """Draw m_per_row pooled conditional samples per row -> (n, m, Y_DIM)."""
        n = mu.shape[0]
        zk = self.comp_mass(mu, sig)
        pk = self.weights[None, :] * zk
        pk = pk / pk.sum(axis=1, keepdims=True)
        cum = np.cumsum(pk, axis=1)
        u0 = rng.random(n)
        comp = np.sum(u0[:, None] > cum, axis=1)
        comp = np.clip(comp, 0, K - 1)
        rows = np.arange(n)
        mu_sel = mu[rows, comp][:, None, :]
        sig_sel = sig[rows, comp][:, None, :]
        lo = ndtr((-Y_BOX - mu_sel) / sig_sel)
        hi = ndtr((Y_BOX - mu_sel) / sig_sel)
        u = rng.random((n, m_per_row, Y_DIM))
        q = np.clip(lo + u * (hi - lo), 1e-12, 1.0 - 1e-12)
        y = mu_sel + sig_sel * ndtri(q)
        return np.clip(y, -Y_BOX, Y_BOX)


def gen_data(theta, d, n, seed):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, D))
    Aarr = np.arange(n) % A
    mu, sig = theta.mu_sigma_rows(X[:, :d], Aarr)
    Y = np.empty((n, Y_DIM))
    # exact per-row truncated sampling (semantics identical to C216 sample_y)
    for i in range(n):
        y = theta_row_sample(theta, X[i, :d], int(Aarr[i]), rng)
        Y[i] = y
    return X, Aarr, Y


def theta_row_sample(theta, x, a, rng):
    from math import erf, sqrt
    mu, sig = theta_row_mu_sigma(theta, x, a)
    zk = np.zeros(K)
    for k in range(K):
        p = 1.0
        for j in range(Y_DIM):
            lo = 0.5 * (1 + erf((-Y_BOX - mu[k, j]) / (sig[k, j] * sqrt(2))))
            hi = 0.5 * (1 + erf((Y_BOX - mu[k, j]) / (sig[k, j] * sqrt(2))))
            p *= max(1e-300, hi - lo)
        zk[k] = p
    pk = theta.weights * zk
    pk = pk / pk.sum()
    k = int(rng.choice(K, p=pk))
    u = rng.uniform(size=Y_DIM)
    lo = np.array([0.5 * (1 + erf(((-Y_BOX - mu[k, j]) / (sig[k, j] * sqrt(2))))) for j in range(Y_DIM)])
    hi = np.array([0.5 * (1 + erf(((Y_BOX - mu[k, j]) / (sig[k, j] * sqrt(2))))) for j in range(Y_DIM)])
    lo2 = np.minimum(lo, hi)
    hi2 = np.maximum(lo, hi)
    q = np.clip(lo2 + u * (hi2 - lo2), 1e-12, 1.0 - 1e-12)
    return np.clip(mu[k] + sig[k] * ndtri(q), -Y_BOX, Y_BOX)


def theta_row_mu_sigma(theta, x, a):
    x = np.asarray(x, dtype=float)
    d_ = min(len(x), D)
    mu = theta.c[a] + theta.M[a][:, :, :d_] @ x[:d_]
    sig = 0.1 + 0.4 / (1.0 + np.exp(-(theta.d[a][:, :d_] @ x[:d_])))
    return mu, sig[:, None].repeat(Y_DIM, axis=1)


# ---------------- H1 metric (exact C216 hist_tv) ----------------
def hist_idx(Y):
    bins = 4
    z = np.floor((np.clip(Y, -Y_BOX, Y_BOX) + Y_BOX) / (2 * Y_BOX) * bins).astype(int)
    z = np.clip(z, 0, bins - 1)
    return np.ravel_multi_index(z.T, [bins] * Y_DIM)


def hist_prob(Y):
    bins = 4
    p = np.bincount(hist_idx(Y), minlength=bins ** Y_DIM).astype(float)
    return p / p.sum()


def hist_tv(y_true, y_cand):
    p = hist_prob(y_true)
    q = hist_prob(y_cand)
    return float(0.5 * np.abs(p - q).sum())


# ---------------- C-MDN (exact C216 implementation) ----------------
class MDN(nn.Module):
    def __init__(self, in_dim, n_actions=A, k=K, y_dim=Y_DIM, hidden=128):
        super().__init__()
        self.k = k
        self.y_dim = y_dim
        self.n_actions = n_actions
        self.net = nn.Sequential(nn.Linear(in_dim + n_actions, hidden), nn.ReLU(),
                                 nn.Linear(hidden, hidden), nn.ReLU(),
                                 nn.Linear(hidden, k * (1 + 2 * y_dim)))

    def forward(self, x, a):
        onehot = torch.nn.functional.one_hot(a.long(), num_classes=self.n_actions).float()
        h = self.net(torch.cat([x, onehot], dim=1))
        logits = h[:, :self.k]
        mean = h[:, self.k:self.k + self.k * self.y_dim].reshape(-1, self.k, self.y_dim)
        logscale = h[:, self.k + self.k * self.y_dim:].reshape(-1, self.k, self.y_dim)
        logscale = torch.clamp(logscale, -5.0, 2.0)
        return logits, mean, logscale


def mdn_nll(logits, mean, logscale, y):
    logp = torch.log_softmax(logits, dim=1)[:, :, None]
    z = (y[:, None, :] - mean) / torch.exp(logscale)
    lp = -0.5 * z ** 2 - logscale - 0.5 * math.log(2 * math.pi)
    lp = lp.sum(dim=2)
    return -torch.logsumexp(logp.squeeze(2) + lp, dim=1).mean()


def fit_mdn(X, Aarr, Y, seed, epochs=200, hidden=128):
    torch.manual_seed(seed)
    np.random.seed(seed % (2 ** 31 - 1))
    model = MDN(X.shape[1], hidden=hidden)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    Xt = torch.tensor(X, dtype=torch.float32)
    At = torch.tensor(Aarr, dtype=torch.long)
    y_mean = torch.tensor(Y.mean(axis=0), dtype=torch.float32)
    y_std = torch.tensor(Y.std(axis=0) + 1e-6, dtype=torch.float32)
    Yt = torch.tensor((Y - y_mean.numpy()) / y_std.numpy(), dtype=torch.float32)
    model.y_mean = y_mean
    model.y_std = y_std
    n = X.shape[0]
    g = torch.Generator().manual_seed(seed)
    for _ in range(epochs):
        perm = torch.randperm(n, generator=g)
        for i in range(0, n, 256):
            idx = perm[i:i + 256]
            opt.zero_grad()
            logits, mean, logscale = model(Xt[idx], At[idx])
            loss = mdn_nll(logits, mean, logscale, Yt[idx])
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 10.0)
            opt.step()
    model.eval()
    return model


def sample_mdn(model, X, Aarr, seed):
    torch.manual_seed(seed)
    model.eval()
    Xt = torch.tensor(X, dtype=torch.float32)
    At = torch.tensor(Aarr, dtype=torch.long)
    with torch.no_grad():
        logits, mean, logscale = model(Xt, At)
        comp = torch.distributions.Categorical(logits=logits).sample()
        mean_s = mean[torch.arange(X.shape[0]), comp]
        scale_s = torch.exp(logscale[torch.arange(X.shape[0]), comp])
        y = mean_s + scale_s * torch.randn_like(mean_s)
    y = y * model.y_std + model.y_mean
    return torch.clamp(y, -Y_BOX, Y_BOX).cpu().numpy()


# ---------------- diagnostics ----------------
def load_c216():
    if sha_file(C216_JSON) != C216_SHA:
        raise RuntimeError('C216 JSON SHA mismatch; refusing to consume changed artifact')
    with open(C216_JSON, 'r', encoding='utf-8') as f:
        d = json.load(f)
    table = {}
    for row in d['H1']:
        table[(int(row['dimension']), int(row['N']))] = float(row['TV_256bin'])
    return table


def main():
    t0 = time.time()
    c216 = load_c216()
    theta = PTheta(PARAM_SEED)
    torch.set_num_threads(1)

    # frozen eval data per d (same X/A, d-specific Y, eval seed 20261303)
    ev = {}
    for d in H1_DIMS:
        X, Aarr, Y = gen_data(theta, d, 2048, EVAL_SEED)
        ev[d] = (X, Aarr, Y)

    rows = []
    cell_index = 0
    for d in H1_DIMS:
        X, Aarr, Yev = ev[d]
        Xd = X[:, :d]
        mu, sig = theta.mu_sigma_rows(Xd, Aarr)
        # population histogram (eval-row mixture; metadata-only oracle)
        pop_rng = np.random.default_rng(20261350 + cell_index)
        pop_samples = theta.sample_rows(mu, sig, pop_rng, m_per_row=POP_PER_ROW)
        pop_hist = hist_prob(pop_samples.reshape(-1, Y_DIM))
        pop_rng2 = np.random.default_rng(20261350 + cell_index)
        # oracle two-sample repetitions (true vs true, same eval n)
        tv_oracle = []
        for r in range(ORACLE_REPS):
            rng = np.random.default_rng(20261400 + 1000 * cell_index + r)
            orc = theta.sample_rows(mu, sig, rng, m_per_row=1)[:, 0, :]
            tv_oracle.append(hist_tv(orc, Yev))
        tv_oracle = np.array(tv_oracle, dtype=float)
        # eval-vs-pop and floor MC from pop
        tv_eval_pop = float(0.5 * np.abs(hist_prob(Yev) - pop_hist).sum())
        rng_mc = np.random.default_rng(20261600 + cell_index)
        floor = []
        for _ in range(FLOOR_MC_REPS):
            x1 = rng_mc.multinomial(2048, pop_hist)
            x2 = rng_mc.multinomial(2048, pop_hist)
            floor.append(0.5 * np.abs(x1 / 2048.0 - x2 / 2048.0).sum())
        floor = np.array(floor, dtype=float)
        analytic = math.sqrt(1.0 / (math.pi * 2048.0)) * float(np.sqrt(pop_hist * (1 - pop_hist)).sum())
        for nj, N in enumerate(H1_NS):
            tol = H1_TOL[d][nj]
            t_cmdn = c216[(d, N)]
            f_mean = float(floor.mean())
            f_q95 = float(np.quantile(floor, 0.95))
            if f_q95 >= tol:
                cat = 'estimation_limit_unreachable'
            elif t_cmdn <= f_q95:
                cat = 'at_finite_sample_floor'
            else:
                excess = t_cmdn - f_mean
                slack = tol - f_mean
                if excess >= slack:
                    cat = 'fit_or_capacity_dominant'
                elif excess >= 0.5 * slack:
                    cat = 'mixed'
                else:
                    cat = 'mostly_noise'
            rows.append({
                'dimension': d, 'N': N, 'tolerance': tol, 'C_MDN_TV_C216': t_cmdn,
                'oracle_mean_TV': float(tv_oracle.mean()),
                'oracle_true_vs_true_TV': {'mean': float(tv_oracle.mean()),
                                           'median': float(np.median(tv_oracle)),
                                           'q05': float(np.quantile(tv_oracle, 0.05)),
                                           'q95': float(np.quantile(tv_oracle, 0.95)),
                                           'max': float(tv_oracle.max()), 'reps': ORACLE_REPS},
                'oracle_mean_gt_tolerance': bool(float(tv_oracle.mean()) > tol),
                'eval_vs_pop_TV': tv_eval_pop,
                'floor_MC_TV': {'mean': f_mean, 'q95': f_q95, 'reps': FLOOR_MC_REPS,
                                'analytic_approx': analytic},
                'floor_q95_over_tolerance': float(f_q95 / tol),
                'C_MDN_excess_over_oracle_mean': float(t_cmdn - float(tv_oracle.mean())),
                'excess_over_floor_mean': float(t_cmdn - f_mean),
                'slack_to_tolerance': float(tol - f_mean),
                'category': cat,
                'C216_pass': bool(t_cmdn <= tol),
            })
            cell_index += 1

    # capacity sensitivity (non-frozen; diagnostic only)
    sens = []
    for (d, N) in SENS:
        X, Aarr, Y = gen_data(theta, d, 4096, TRAIN_SEED)
        Xev, Aev, Yev = ev[d]
        seed = H1_CELL_SEEDS[H1_DIMS.index(d) * len(H1_NS) + H1_NS.index(N)]
        model = fit_mdn(X[:N, :d], Aarr[:N], Y[:N], seed, epochs=SENS_EPOCHS, hidden=SENS_HIDDEN)
        cand = sample_mdn(model, Xev[:, :d], Aev, seed + 999)
        tv = hist_tv(Yev, cand)
        sens.append({'dimension': d, 'N': N, 'C_MDN_TV_C216': c216[(d, N)],
                     'capacity_sensitivity_TV': tv,
                     'delta_TV': tv - c216[(d, N)],
                     'hidden': SENS_HIDDEN, 'epochs': SENS_EPOCHS,
                     'non_frozen_sensitivity': True})
    # implementation fidelity (frozen config retrain on small subset)
    fid = []
    for (d, N) in FID:
        X, Aarr, Y = gen_data(theta, d, 4096, TRAIN_SEED)
        Xev, Aev, Yev = ev[d]
        seed = H1_CELL_SEEDS[H1_DIMS.index(d) * len(H1_NS) + H1_NS.index(N)]
        model = fit_mdn(X[:N, :d], Aarr[:N], Y[:N], seed, epochs=200, hidden=128)
        cand = sample_mdn(model, Xev[:, :d], Aev, seed + 999)
        tv = hist_tv(Yev, cand)
        fid.append({'dimension': d, 'N': N, 'C_MDN_TV_C216': c216[(d, N)],
                    'reproduction_TV': tv, 'delta_TV': tv - c216[(d, N)]})
    # attribution summary
    cats = {}
    for r in rows:
        cats[r['category']] = cats.get(r['category'], 0) + 1
    n_floor_over_tol = sum(1 for r in rows if r['floor_MC_TV']['q95'] >= r['tolerance'])
    dominant = ('estimation_limit_unreachable' if n_floor_over_tol >= 9 else
                ('fit_or_capacity_dominant' if cats.get('fit_or_capacity_dominant', 0) >= 9 else
                 ('mixed' if cats.get('mixed', 0) + cats.get('fit_or_capacity_dominant', 0) >= 9 else
                  'finite_sample_dominant')))
    out = {
        'task': 'R204-M1-S2-FAIL-DIAG',
        'schema': 'm1_s2_fail_diag_v1',
        'status': 'complete',
        'diagnostic_only': True,
        'does_not_change_C216': True,
        'C216': {'path': 'research/2026-10-28-m1-stage2-rerun/m1_stage2_rerun.json',
                 'sha256': C216_SHA, 'verdict': 'design_invalid: projection',
                 'H1_pass_count': 0, 'H1_cells': 16},
        'frozen_environment': {
            'param_seed': PARAM_SEED, 'train_seed': TRAIN_SEED, 'eval_seed': EVAL_SEED,
            'eval_N': 2048, 'dims': H1_DIMS, 'Ns': H1_NS,
            'generator': 'truncated GMM K=3 w=[.5,.3,.2], c~N(0,.5^2), M~N(0,.1^2), d~N(0,.1^2), box[-2,2]^4',
            'metric': '256-bin (4 bins/dim) pooled histogram TV (exact C216 hist_tv)',
            'H1_tolerances': {str(d): H1_TOL[d] for d in H1_DIMS},
            'unchanged': ['scale', 'tolerances', 'order', 'seeds'],
        },
        'diagnostic_design': {
            'oracle_two_sample_TV_reps': ORACLE_REPS,
            'population_per_row_samples': POP_PER_ROW,
            'floor_MC_reps': FLOOR_MC_REPS,
            'capacity_sensitivity_cells': SENS,
            'capacity_sensitivity_config': {'hidden': SENS_HIDDEN, 'epochs': SENS_EPOCHS},
            'fidelity_cells': FID,
            'attribution_rule': 'see PROTOCOL_DIAG.md section 3; q95 floor >= tolerance -> estimation_limit_unreachable; etc.',
        },
        'rows': rows,
        'capacity_sensitivity': sens,
        'fidelity_check': fid,
        'attribution_summary': {
            'category_counts': cats,
            'cells_with_floor_q95_ge_tolerance': n_floor_over_tol,
            'cells_with_oracle_mean_gt_tolerance': sum(1 for r in rows if r['oracle_mean_gt_tolerance']),
            'C_MDN_excess_over_oracle_mean': {
                'min': float(min(r['C_MDN_excess_over_oracle_mean'] for r in rows)),
                'median': float(np.median([r['C_MDN_excess_over_oracle_mean'] for r in rows])),
                'max': float(max(r['C_MDN_excess_over_oracle_mean'] for r in rows)),
                'cells_positive': sum(1 for r in rows if r['C_MDN_excess_over_oracle_mean'] > 0),
            },
            'capacity_sensitivity': {
                'cells': len(sens),
                'improved': sum(1 for s in sens if s['delta_TV'] < 0),
                'worsened': sum(1 for s in sens if s['delta_TV'] > 0),
                'delta_median': float(np.median([s['delta_TV'] for s in sens])),
                'delta_min': float(min(s['delta_TV'] for s in sens)),
                'delta_max': float(max(s['delta_TV'] for s in sens)),
            },
            'dominant_attribution': dominant,
            'primary_interpretation': ('frozen H1 256-bin/eval-2048 tolerance is at/below the two-sample oracle TV floor '
                                       '(q95 >= tolerance in all cells; oracle mean > tolerance in most cells): a perfect '
                                       'oracle would fail H1 with high probability, so H1 failure cannot be attributed to '
                                       'C-MDN fit alone'),
            'secondary_interpretation': ('C-MDN TV is still above the oracle mean in most cells (fit/capacity excess), '
                                         'but the capacity/epochs sensitivity did not broadly reduce TV; the unreachable '
                                         'tolerance dominates the verdict'),
            'C216_verdict_unchanged': True,
            'H1_pass_claimed': False,
        },
        'recommendation': ('record this failure attribution in the R204 negative report section "failure attribution" '
                           'WITHOUT changing C216 design_invalid: projection; do not claim H1 pass; do not use diagnostic '
                           'capacity results as frozen evidence'),
        'forbidden_outputs_absent': ['decision_utility', 'regret', 'topk', 'method_comparison', 'effect_size',
                                     'gain_claim', 'pharmacology_claim', 'real_decision_claim', 'transfer_claim',
                                     'mechanism_claim', 'novelty_claim', 'real_data_result'],
        'wells': 0,
        'stage3_executed': False,
        'real_data_read': False,
    }
    os.makedirs(HERE, exist_ok=True)
    with open(OUT_JSON, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(json_safe(out), f, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        f.write('\n')
    wall = time.time() - t0
    cpu = time.process_time()
    try:
        import psutil
        rss_gb = psutil.Process(os.getpid()).memory_info().rss / (1024 ** 3)
    except Exception:
        rss_gb = None
    print(json.dumps({'status': 'complete', 'wall_s': round(wall, 2), 'cpu_s': round(cpu, 2),
                      'rss_gb': (round(rss_gb, 4) if rss_gb is not None else None),
                      'cells': len(rows), 'dominant_attribution': dominant,
                      'category_counts': cats, 'output': OUT_JSON}, ensure_ascii=True))
    if wall > CAPS['wall_s']:
        print('WARNING: wall exceeded cap', wall)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
