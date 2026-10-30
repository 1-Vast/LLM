#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R201-B T1 MVP synthetic simulator (design/frozen v0.4 implementation).

No real response data, no fitting to biological data, no effect result.
Implements: 40-plan universe, x1/x2/dose, fixed theta, gamma 5-point grid (125 worlds),
sigma=0.10 5-point noise grid, certificate ladder, R_max=5, anchored-key actions 363.6 CU,
10 arms (pi_dual + C0..C6 + C7 compute/experiment), integer keys + 1 CU blank/QC filler.
"""
from __future__ import annotations

import hashlib
import json
import math

import numpy as np

THETA = np.array([0.5, 0.3, 0.2, 0.1, -0.1], dtype=float)
TAU = 0.20
SIGMA = 0.10
DELTA_UTILITY = 0.10
K_TOPK = 5
R_MAX = 5
STEP_COST_S = 120.0
MIN_COMPUTE_UNIT_S = 120.0
CERT_WIDTHS = [0.40, 0.20, 0.10, 0.05, 0.025]
KEY_CU = 363.6
WELL_CU = 1.0  # synthetic blank/QC filler price assumption: 1 CU per well
N_KEYS_SENSITIVITY = None

Z = [-2.0, -1.0, 0.0, 1.0, 2.0]
_w = [math.exp(-0.5 * z * z) for z in Z]
W = [x / sum(_w) for x in _w]
# gamma grid values: tau * z; noise grid values: sigma * z
GAMMA_VALUES = [TAU * z for z in Z]
NOISE_VALUES = [SIGMA * z for z in Z]

ARMS = ['pi_dual', 'C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6',
        'C7_compute_only', 'C7_experiment_only']


def plan_table():
    rows = []
    for p in range(40):
        u = p // 10
        j = p % 10
        x1 = (j % 3) - 1
        x2 = ((j // 3) % 3) - 1
        dose = 0.5 if j < 5 else 1.0
        split = 'O' if p < 20 else ('M' if p < 30 else 'reserve')
        rows.append({'plan_id': p, 'cell_u': u, 'context_j': j, 'x1': x1, 'x2': x2,
                     'dose': dose, 'split': split})
    return rows


PLANS = plan_table()
PLAN_BY_ID = {r['plan_id']: r for r in PLANS}
O_IDS = [r['plan_id'] for r in PLANS if r['split'] == 'O']
M_IDS = [r['plan_id'] for r in PLANS if r['split'] == 'M']


def features(ids):
    X = []
    for p in ids:
        r = PLAN_BY_ID[p]
        X.append([1.0, r['x1'], r['x2'], r['x1'] * r['x2'], r['dose']])
    return np.asarray(X, dtype=float)


def fval(ids):
    return features(ids) @ THETA


def group_of(p):
    return PLAN_BY_ID[p]['x2']


def menu_hash():
    payload = [PLAN_BY_ID[p] for p in M_IDS]
    s = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(s.encode('utf-8')).hexdigest().upper()


class World:
    def __init__(self, seed, sigma=SIGMA, null=False):
        self.seed = int(seed)
        rng = np.random.default_rng(self.seed)
        self.gamma_true = {g: (0.0 if null else float(rng.normal(0.0, TAU))) for g in (-1, 0, 1)}
        base = fval([p for p in range(40)])
        self.u_latent = np.zeros(40)
        self.u_true = np.zeros(40)
        for p in range(40):
            lat = float(base[p] + self.gamma_true[group_of(p)])
            self.u_latent[p] = lat
            self.u_true[p] = float(np.clip(lat, 0.0, 1.0))
        self.obs_y = {}
        for p in O_IDS:
            self.obs_y[p] = float(np.clip(self.u_true[p] + rng.normal(0.0, sigma), 0.0, 1.0))
        self.oracle_M = int(M_IDS[int(np.argmax([self.u_true[p] for p in M_IDS]))])
        self.oracle_M_latent = int(M_IDS[int(np.argmax([self.u_latent[p] for p in M_IDS]))])


class Learner:
    """Fixed shared update: ridge theta + gamma-group residual means; certificate width ladder."""

    def __init__(self, obs_y, cert_width=0.40):
        self.obs = dict(obs_y)
        self.width = float(cert_width)
        self.steps = 0
        self.refit()

    def _state(self):
        return (tuple(sorted(self.obs.items())), self.width, self.steps)

    def state_hash(self):
        return hashlib.sha256(json.dumps(self._state(), sort_keys=True).encode()).hexdigest().upper()

    def _design(self, ids):
        X = features(ids)
        g = np.asarray([[1.0 if group_of(p) == 0 else 0.0,
                         1.0 if group_of(p) == 1 else 0.0] for p in ids], dtype=float)
        return np.hstack([X, g])

    def refit(self):
        ids = sorted(self.obs.keys())
        X = self._design(ids)
        y = np.asarray([self.obs[p] for p in ids], dtype=float)
        A = X.T @ X + 1e-8 * np.eye(X.shape[1])
        self.theta = np.linalg.solve(A, X.T @ y)
        # compatibility: group residual means not used for prediction (group fixed effects absorbed)
        self.gamma = {g: 0.0 for g in (-1, 0, 1)}

    def predict_raw(self, ids):
        return np.asarray(self._design(ids) @ self.theta, dtype=float)

    def predict(self, ids):
        return np.clip(self.predict_raw(ids), 0.0, 1.0)

    def select(self):
        pred = self.predict(M_IDS)
        return int(M_IDS[int(np.argmax(pred))])

    def observe(self, plan_id, y):
        self.obs[plan_id] = float(np.clip(y, 0.0, 1.0))
        self.refit()

    def compute_step(self):
        self.steps += 1
        self.width = CERT_WIDTHS[min(self.steps, len(CERT_WIDTHS) - 1)]
        return STEP_COST_S

    def cert_gap(self):
        return self.width / DELTA_UTILITY


def learner_from_world(world):
    return Learner(world.obs_y)


def copy_learner(l):
    n = Learner(l.obs)
    n.width = l.width
    n.steps = l.steps
    n.refit()
    return n


# ---------------- cost ledger ----------------
def config_budgets(B_C, B_E_keys, kappa):
    """Return T_seconds and T_CU_equivalent per frozen v0.4."""
    T_seconds = B_C + kappa * B_E_keys * KEY_CU
    T_cu = B_E_keys * KEY_CU + B_C / kappa
    return T_seconds, T_cu


def experiment_only_keys(B_C, B_E_keys, kappa):
    n0 = B_E_keys + int(math.floor((B_C / kappa) / KEY_CU))
    keys_cu = n0 * KEY_CU
    T_cu = B_E_keys * KEY_CU + B_C / kappa
    residual = T_cu - keys_cu
    return n0, keys_cu, residual, int(math.ceil(residual))


def spend_check_rows():
    rows = []
    pairs = [(300, 4), (1200, 16), (3600, 64)]
    kappas = [0.1, 1.0, 10.0]
    sigmas = [0.05, 0.10]
    for bc, be in pairs:
        for kappa in kappas:
            for sigma in sigmas:
                T_s, T_cu = config_budgets(bc, be, kappa)
                n0, keys_cu, residual, filler_wells = experiment_only_keys(bc, be, kappa)
                spend_cu = keys_cu + filler_wells * WELL_CU
                rows.append({'B_C_s': bc, 'B_E_keys': be, 'kappa': kappa, 'sigma': sigma,
                             'T_seconds': T_s, 'T_cu': T_cu,
                             'exp_n0': n0, 'keys_cu': keys_cu,
                             'residual_cu': residual, 'filler_wells': filler_wells,
                             'spend_cu': spend_cu, 'diff_cu': spend_cu - T_cu,
                             'no_negative': residual >= 0,
                             'within_1': abs(spend_cu - T_cu) <= 1.0})
    return rows


# ---------------- EV finite-discrete approximation ----------------
def _gamma_worlds():
    worlds = []
    vals = GAMMA_VALUES
    for i in range(5):
        for j in range(5):
            for k in range(5):
                worlds.append((vals[i], vals[j], vals[k], W[i] * W[j] * W[k]))
    return worlds


GAMMA_WORLDS = _gamma_worlds()


def true_utility_for_gamma(world, gamma_triple):
    base = fval([p for p in range(40)])
    g = {-1: gamma_triple[0], 0: gamma_triple[1], 1: gamma_triple[2]}
    u = np.zeros(40)
    for p in range(40):
        u[p] = float(np.clip(base[p] + g[group_of(p)], 0.0, 1.0))
    return u


def oracle_top_for_utility(u):
    return int(M_IDS[int(np.argmax([u[p] for p in M_IDS]))])


def ev_action(world, learner, action_plan, use_noise_grid):
    """Expected selection accuracy after measuring action_plan, averaged over gamma worlds.
    use_noise_grid=False: zero-noise expected observation (approx EV);
    use_noise_grid=True: average over 5-point noise grid (reference).
    """
    total_w = 0.0
    acc = 0.0
    for (g1, g2, g3, wgt) in GAMMA_WORLDS:
        u = true_utility_for_gamma(world, (g1, g2, g3))
        oracle = oracle_top_for_utility(u)
        if use_noise_grid:
            for eps in NOISE_VALUES:
                l2 = copy_learner(learner)
                l2.observe(action_plan, float(np.clip(u[action_plan] + eps, 0.0, 1.0)))
                acc += wgt * (1.0 / len(NOISE_VALUES)) * (1.0 if l2.select() == oracle else 0.0)
        else:
            l2 = copy_learner(learner)
            l2.observe(action_plan, float(np.clip(u[action_plan], 0.0, 1.0)))
            acc += wgt * (1.0 if l2.select() == oracle else 0.0)
        total_w += wgt
    return acc / max(total_w, 1e-12)


# ---------------- arms ----------------
def _fill_ledger(ledger, T_cu, kappa, rng, blank=True):
    """Fill residual with blank/QC wells (1 CU/well) and no-info compute; no learner change."""
    spent = ledger['compute_s'] / kappa + ledger['exp_keys'] * KEY_CU + ledger['filler_wells'] * WELL_CU
    residual = T_cu - spent
    if residual > 0:
        w = int(math.ceil(residual))
        ledger['filler_wells'] += w
    return ledger


def run_arm(arm, world, B_C, B_E_keys, kappa, seed):
    """Run one arm on one world; returns selection + cost ledger (not a main result)."""
    if arm not in ARMS:
        raise ValueError(arm)
    rng = np.random.default_rng(int(seed))
    T_s, T_cu = config_budgets(B_C, B_E_keys, kappa)
    learner = learner_from_world(world)
    ledger = {'compute_s': 0.0, 'exp_keys': 0, 'filler_wells': 0}
    rounds = 0

    def spend_compute(seconds):
        ledger['compute_s'] += seconds
        return seconds

    def do_exp(plan):
        if ledger['exp_keys'] >= B_E_keys and arm not in ('C1', 'C7_experiment_only'):
            return
        ledger['exp_keys'] += 1
        learner.observe(plan, float(np.clip(world.u_true[plan] + rng.normal(0.0, SIGMA), 0.0, 1.0)))

    def random_exp():
        do_exp(int(M_IDS[int(rng.integers(0, len(M_IDS)))]))

    if arm == 'C2':
        _fill_ledger(ledger, T_cu, kappa, rng)
    elif arm == 'C7_compute_only':
        n_steps = int(T_s // STEP_COST_S)
        for _ in range(n_steps):
            spend_compute(STEP_COST_S)
            learner.compute_step()
        _fill_ledger(ledger, T_cu, kappa, rng)
    elif arm == 'C7_experiment_only':
        n0, keys_cu, _, _ = experiment_only_keys(B_C, B_E_keys, kappa)
        for _ in range(n0):
            random_exp()
        _fill_ledger(ledger, T_cu, kappa, rng)
    elif arm == 'C0':
        for _ in range(int(B_C // STEP_COST_S)):
            spend_compute(STEP_COST_S)
            learner.compute_step()
        for _ in range(B_E_keys):
            random_exp()
        _fill_ledger(ledger, T_cu, kappa, rng)
    elif arm == 'C1':
        for _ in range(B_E_keys):
            random_exp()
        for _ in range(int(B_C // STEP_COST_S)):
            spend_compute(STEP_COST_S)
            learner.compute_step()
        _fill_ledger(ledger, T_cu, kappa, rng)
    elif arm in ('C3', 'C4', 'C5'):
        for _ in range(int(B_C // STEP_COST_S)):
            spend_compute(STEP_COST_S)
            learner.compute_step()
        for _ in range(B_E_keys):
            # uncertainty-style selection: least-observed gamma group plan
            counts = {g: 0 for g in (-1, 0, 1)}
            for p in learner.obs:
                counts[group_of(p)] += 1
            target_g = min(counts, key=lambda g: counts[g])
            cand = [p for p in M_IDS if group_of(p) == target_g and p not in learner.obs]
            plan = int(cand[int(rng.integers(0, len(cand)))]) if cand else int(M_IDS[int(rng.integers(0, len(M_IDS)))])
            do_exp(plan)
        _fill_ledger(ledger, T_cu, kappa, rng)
    elif arm == 'C6':
        frac = float(rng.uniform(0.2, 0.8))
        c_s = frac * B_C
        e_keys = int(round((1.0 - frac) * B_E_keys))
        for _ in range(int(c_s // STEP_COST_S)):
            spend_compute(STEP_COST_S)
            learner.compute_step()
        for _ in range(e_keys):
            random_exp()
        _fill_ledger(ledger, T_cu, kappa, rng)
    elif arm == 'pi_dual':
        # compute phase
        while learner.cert_gap() > 1.0 and ledger['compute_s'] + STEP_COST_S <= B_C:
            spend_compute(STEP_COST_S)
            learner.compute_step()
        # evidence phase until experiments/rounds exhausted
        while ledger['exp_keys'] < B_E_keys and rounds < R_MAX:
            rounds += 1
            # choose action maximizing EV approx (use sampled candidate actions to limit cost)
            cand = [int(pid) for pid in rng.choice(M_IDS, size=min(5, len(M_IDS)), replace=False)]
            best = max(cand, key=lambda p: ev_action(world, learner, p, use_noise_grid=False))
            do_exp(best)
        _fill_ledger(ledger, T_cu, kappa, rng)
    else:
        raise ValueError(arm)

    selected = learner.select()
    return {'arm': arm, 'selected': selected, 'oracle': world.oracle_M,
            'correct': int(selected == world.oracle_M), 'ledger': ledger,
            'T_cu': T_cu, 'spend_cu': ledger['compute_s'] / kappa + ledger['exp_keys'] * KEY_CU + ledger['filler_wells'] * WELL_CU}
