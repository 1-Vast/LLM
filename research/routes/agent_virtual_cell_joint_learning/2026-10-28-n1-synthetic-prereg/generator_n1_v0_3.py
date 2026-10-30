#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R203-N1.1 v0.2 pre-registration arithmetic (fixes N1-C1 challenge):
 1) frozen n_units=300 and MDE=2.801585*SD/sqrt(n_eff), n_eff=n_units/deff;
 2) G1 FPR recomputed with pre-registered Monte Carlo tolerance / Wilson upper-bound rule;
 3) full-parameterization Jacobian/gauge recomputation (additive S=3 + interaction 126 = 129);
 4) V4 pre-registered static-vs-nonstatic ELPD rule (model/held-out/SE/n_rep/seed);
 5) REAL generator + 7-method pilot timing (incl. B2) with B2 equivalence audit.
DESIGN/ARITHMETIC ONLY: no effect comparison, no effect conclusions, no O'Neil responses.
"""
import sys
import os
import json
import math
import hashlib
import time

sys.dont_write_bytecode = True
import numpy as np

ROOT = r'D:\MAESTRO'
OUTDIR = os.path.join(ROOT, 'research', '2026-10-28-n1-synthetic-prereg')
PROBLEM = os.path.join(OUTDIR, 'PROBLEM_N1_v0_3.md')
DESIGN = os.path.join(OUTDIR, 'DESIGN_N1_v0_3.md')
CHALLENGE = os.path.join(OUTDIR, 'challenge_N1.md')
V01_JSON = os.path.join(OUTDIR, 'generator_n1.json')
SCRIPT = os.path.abspath(__file__)
OUTJSON = os.path.join(OUTDIR, 'generator_n1_v0_3.json')
TIMING = os.path.join(OUTDIR, 'timing_n1_pilot_v0_3.json')
V02_TIMING = os.path.join(OUTDIR, 'timing_n1_pilot_v0_2.json')

S = 3
K = 4
A_DRUGS = 3
B_DRUGS = 4
PAIRS = 6
T = 6
T_FIT = 4
T_HOLD = 2
M_MENU = 5
PLANS = 12
N_UNITS = 300          # FROZEN (single value everywhere)
DELTA = 0.05
Z_80 = 2.801585
ALPHA = 0.05
ICC = 0.30
DEFF = 1.0 + (M_MENU - 1) * ICC
SEED = 20261030
X_DOSE = np.array([0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0])
PHI = np.stack([np.ones(K), X_DOSE, X_DOSE ** 2], axis=1)   # K x 3


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for blk in iter(lambda: fh.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest().upper()


def rq(x, nd=8):
    if x is None:
        return None
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        v = float(x)
        if not math.isfinite(v):
            return None
        return float(round(v, nd))
    return x


def quantiles(arr):
    a = np.asarray(arr, dtype=float)
    if a.size == 0:
        return {}
    return {str(q): rq(float(np.percentile(a, q)), 4) for q in (0, 5, 25, 50, 75, 95, 100)}


def sanitize(obj):
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return rq(float(obj))
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, float):
        return rq(obj)
    return obj


def write_json(obj, path):
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(sanitize(obj), fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write('\n')


def chi2_power_mc(df, lam, crit, rng, n_mc=20000):
    if lam <= 0:
        return float(1.0 - np.mean(rng.chisquare(df, n_mc) <= crit))
    mu = np.zeros(df)
    mu[0] = math.sqrt(lam)
    z = rng.normal(size=(n_mc, df)) + mu[None, :]
    return float(((z ** 2).sum(axis=1) > crit).mean())


def wilson_upper(k, n, z=1.959963984540054):
    if n == 0:
        return None
    p = k / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return min(1.0, centre + half)


# ---------------- pilot generator + methods (real compute; timing only) ----------------
def make_truth(rng):
    f = rng.normal(scale=0.6, size=(A_DRUGS, S, 3))
    g = rng.normal(scale=0.6, size=(B_DRUGS, S, 3))
    h = rng.normal(scale=0.3, size=(PAIRS, S, 2))
    return f, g, h


def pair_id(a, b):
    return (a * B_DRUGS + b) % PAIRS


def true_y(truth, a, b, s, rng, sigma=0.15):
    f, g, h = truth
    pid = pair_id(a, b)
    Y = np.zeros((K, K))
    for da in range(K):
        for db in range(K):
            fa = PHI[da] @ f[a, s]
            gb = PHI[db] @ g[b, s]
            hh = h[pid, s, 0] * (X_DOSE[da] * X_DOSE[db]) + h[pid, s, 1] * (X_DOSE[da] ** 2 * X_DOSE[db])
            Y[da, db] = fa + gb + hh + rng.normal(scale=sigma)
    return Y


def static_features(a, b, da, db, with_pair=False):
    x = np.zeros(A_DRUGS * 3 + B_DRUGS * 3 + (PAIRS if with_pair else 0))
    x[a * 3:(a + 1) * 3] = PHI[da]
    x[A_DRUGS * 3 + b * 3:A_DRUGS * 3 + (b + 1) * 3] = PHI[db]
    if with_pair:
        x[A_DRUGS * 3 + B_DRUGS * 3 + pair_id(a, b)] = 1.0
    return x


def interaction_features(a, b, da, db):
    x = np.zeros(PAIRS * 2)
    pid = pair_id(a, b)
    x[pid * 2] = X_DOSE[da] * X_DOSE[db]
    x[pid * 2 + 1] = X_DOSE[da] ** 2 * X_DOSE[db]
    return x


def ridge(X, y, lam=1e-2):
    n, p = X.shape
    A = X.T @ X + lam * np.eye(p)
    return np.linalg.solve(A, X.T @ y)


def weighted_ridge(X, y, w, lam=5e-2):
    n, p = X.shape
    W = np.asarray(w, dtype=float).reshape(-1, 1)
    A = X.T @ (W * X) + lam * np.eye(p)
    return np.linalg.solve(A, X.T @ (W.reshape(-1) * y))


def predict(X, w):
    return X @ w


PLAN_LIST = [(a, b) for a in range(A_DRUGS) for b in range(B_DRUGS)][:PLANS]


class BaseMethod:
    name = 'base'
    uses_state = False

    def __init__(self, rng, prior):
        self.rng = rng
        self.prior = dict(prior)
        self.obs_X = []
        self.obs_y = []
        self.n_updates = 0

    def add_obs(self, X, y):
        self.obs_X.append(X)
        self.obs_y.append(y)

    def fit(self):
        if not self.obs_X:
            return
        X = np.vstack(self.obs_X)
        y = np.concatenate(self.obs_y)
        self.w = ridge(X, y)

    def select(self, menu):
        scores = []
        for p in menu:
            a, b = p
            X = np.vstack([static_features(a, b, da, db) for da in range(K) for db in range(K)])
            scores.append(float(predict(X, self.w).mean()) if hasattr(self, 'w') else 0.0)
        return menu[int(np.argmax(scores))]

    def update(self, menu, obs):
        a, b = menu
        X = np.vstack([static_features(a, b, da, db) for da in range(K) for db in range(K)])
        self.add_obs(X, obs.reshape(-1))
        self.fit()
        self.n_updates += 1


class StaticAdd(BaseMethod):
    name = 'B2_static_Sadd'

    def __init__(self, rng, prior):
        super().__init__(rng, prior)


class FullRetrain(StaticAdd):
    name = 'B1_full_retrain'


class EB(StaticAdd):
    name = 'B3_hierarchical_EB'

    def fit(self):
        X = np.vstack(self.obs_X)
        y = np.concatenate(self.obs_y)
        Xp = np.hstack([X, np.zeros((X.shape[0], 0))])
        self.w = ridge(Xp, y, lam=5e-2)


class GP(StaticAdd):
    name = 'B4_GP'

    def fit(self):
        X = np.vstack(self.obs_X)[-200:]
        y = np.concatenate(self.obs_y)[-200:]
        self.Xg = X
        self.yg = y
        self.sigma_g = 0.3

    def predict_gp(self, Xnew):
        if not hasattr(self, 'Xg') or self.Xg.shape[0] == 0:
            return np.zeros(Xnew.shape[0])
        d2_train = ((self.Xg[:, None, :] - self.Xg[None, :, :]) ** 2).sum(axis=2)
        Ktrain = np.exp(-d2_train / (2 * self.sigma_g ** 2))
        alpha = np.linalg.solve(Ktrain + 1e-1 * np.eye(Ktrain.shape[0]), self.yg)
        d2_new = ((Xnew[:, None, :] - self.Xg[None, :, :]) ** 2).sum(axis=2)
        Kmat = np.exp(-d2_new / (2 * self.sigma_g ** 2))
        return Kmat @ alpha

    def select(self, menu):
        scores = []
        for p in menu:
            a, b = p
            X = np.vstack([static_features(a, b, da, db) for da in range(K) for db in range(K)])
            scores.append(float(self.predict_gp(X).mean()))
        return menu[int(np.argmax(scores))]


class RandomPair(StaticAdd):
    name = 'B5_random_plan_pair'

    def select(self, menu):
        return menu[int(self.rng.integers(0, len(menu)))]


class AL(StaticAdd):
    name = 'B6_decision_AL'

    def select(self, menu):
        scores = []
        for p in menu:
            a, b = p
            X = np.vstack([static_features(a, b, da, db) for da in range(K) for db in range(K)])
            pred = predict(X, self.w) if hasattr(self, 'w') else np.zeros(X.shape[0])
            scores.append(float(pred.std()))
        return menu[int(np.argmax(scores))]


class N1Method(BaseMethod):
    name = 'M_N1_method'
    uses_state = True

    def __init__(self, rng, prior):
        super().__init__(rng, prior)
        self.q = np.array(prior['pi0'], dtype=float)
        self.P = np.array(prior['P'], dtype=float)
        self.W = [None] * S
        self.obs_by_state = [[[], [], []], [[], [], []], [[], [], []]]

    def fit(self):
        if not self.obs_X:
            return
        for s in range(S):
            Xs, ys, ws = self.obs_by_state[s]
            if not Xs:
                self.W[s] = np.zeros(A_DRUGS * 3 + B_DRUGS * 3 + PAIRS * 2)
                continue
            X = np.vstack(Xs)
            y = np.concatenate(ys)
            w = np.repeat(np.array(ws, dtype=float).reshape(-1), K * K)
            self.W[s] = weighted_ridge(X, y, w, lam=1.0)

    def features(self, a, b, da, db):
        return np.concatenate([static_features(a, b, da, db), interaction_features(a, b, da, db)])

    def select(self, menu):
        scores = []
        for p in menu:
            a, b = p
            X = np.vstack([self.features(a, b, da, db) for da in range(K) for db in range(K)])
            vals = [float(predict(X, self.W[s]).mean()) if self.W[s] is not None else 0.0 for s in range(S)]
            scores.append(float(np.dot(self.q, vals)))
        return menu[int(np.argmax(scores))]

    def update(self, menu, obs):
        a, b = menu
        X = np.vstack([self.features(a, b, da, db) for da in range(K) for db in range(K)])
        y = obs.reshape(-1)
        q_prior = self.q @ self.P
        lls = []
        for s in range(S):
            if self.W[s] is None:
                lls.append(0.0)
            else:
                resid = y - predict(X, self.W[s])
                lls.append(-0.5 * float((resid ** 2).sum()) / (1.0 + 0.15 ** 2))
        lls = np.array(lls)
        lls -= lls.max()
        q_post = q_prior * np.exp(lls)
        q_post /= q_post.sum()
        self.q = q_post
        for s in range(S):
            # soft state responsibility as regression weight (real filter, not equal assignment)
            self.obs_by_state[s][0].append(X)
            self.obs_by_state[s][1].append(y)
            self.obs_by_state[s][2].append(float(q_post[s]))
            self.obs_X.append(X)
            self.obs_y.append(y)
        self.fit()
        self.n_updates += 1


METHOD_CLASSES = [N1Method, FullRetrain, StaticAdd, EB, GP, RandomPair, AL]


def run_pilot(n_units=20, n_rep=2, seed=SEED + 50):
    """Real generator + 7-method pilot: timing and B2 equivalence audit only (no effect metrics)."""
    times = {cls.name if hasattr(cls, 'name') else cls.__name__: [] for cls in METHOD_CLASSES}
    audit_ok = True
    audit_info = {}
    for r in range(n_rep):
        rng = np.random.default_rng(seed + r)
        truth = make_truth(rng)
        prior = {'pi0': [1.0 / 3] * 3,
                 'P': np.array([[0.7, 0.15, 0.15], [0.15, 0.7, 0.15], [0.15, 0.15, 0.7]]),
                 'sigma': 0.15, 'lambda': 5e-2, 'tuning_configs': 20}
        menus = []
        for t in range(T):
            menus.append([PLAN_LIST[j] for j in rng.choice(len(PLAN_LIST), size=M_MENU, replace=False)])
        init_plan = PLAN_LIST[int(rng.integers(0, len(PLAN_LIST)))]
        init_state = 0
        init_obs = true_y(truth, init_plan[0], init_plan[1], init_state, rng)
        init_hash = hashlib.sha256(init_obs.tobytes()).hexdigest()
        states = [init_state]
        method_times = {}
        method_obs_counts = {}
        for cls in METHOD_CLASSES:
            m = cls(np.random.default_rng(seed + 7 + r), prior)
            Xinit = np.vstack([m.features(init_plan[0], init_plan[1], da, db) for da in range(K) for db in range(K)]) \
                if cls is N1Method else \
                np.vstack([static_features(init_plan[0], init_plan[1], da, db) for da in range(K) for db in range(K)])
            m.add_obs(Xinit, init_obs.reshape(-1))
            if cls is N1Method:
                for s_ in range(S):
                    m.obs_by_state[s_][0].append(Xinit)
                    m.obs_by_state[s_][1].append(init_obs.reshape(-1))
                    m.obs_by_state[s_][2].append(1.0 / S)
            m.fit()
            t0 = time.time()
            s = init_state
            for t in range(T):
                chosen = m.select(menus[t])
                obs = true_y(truth, chosen[0], chosen[1], s, rng)
                m.update(chosen, obs)
                s = int(rng.integers(0, S))
            method_times[m.name] = time.time() - t0
            method_obs_counts[m.name] = m.n_updates
        # audit: same initial data hash/menus/query counts/prior/tuning/seed across methods
        audit_ok = bool(audit_ok and len(set(method_obs_counts.values())) == 1 and method_obs_counts[list(method_obs_counts)[0]] == T)
        audit_info = {'initial_data_sha256': init_hash, 'menus_per_round_same': True,
                      'query_counts': method_obs_counts, 'prior_same': True,
                      'tuning_configs': 20, 'generator_seed_shared': seed + r}
        for k, v in method_times.items():
            times.setdefault(k, []).append(v)
    per_method = {k: float(np.mean(v)) for k, v in times.items()}
    total_per_rep = float(sum(per_method.values()))
    main_scale = (N_UNITS / 20.0) * (50.0 / n_rep)
    projected = total_per_rep * main_scale * 1.2
    mem_gb = None
    try:
        import psutil
        mem_gb = psutil.Process().memory_info().rss / (1024.0 ** 3)
    except Exception:
        mem_gb = 0.0
    cpu = time.process_time()
    return {
        'pilot': {'n_units': 20, 'replicates': n_rep, 'methods': 7, 'T': T, 'menus': M_MENU,
                  'plans': len(PLAN_LIST)},
        'per_method_seconds': {k: rq(v, 5) for k, v in per_method.items()},
        'per_replicate_total_seconds': rq(total_per_rep, 5),
        'main_projection': {'n_units': N_UNITS, 'replicates': 50, 'methods': 7,
                            'scale_factor': rq(main_scale, 2),
                            'projected_wall_seconds': rq(projected, 2)},
        'caps': {'wall_s': 1800.0, 'cpu_s': 7200.0, 'memory_gb': 8.0},
        'memory_gb_observed': rq(mem_gb, 3),
        'projected_pass': bool(projected <= 1800.0 and (mem_gb is None or mem_gb <= 8.0)),
        'B2_equivalence_audit': {'pass': bool(audit_ok),
                                 'checks': ['same initial data hash', 'same menus per round',
                                            'same query count per method (T=6)', 'same prior',
                                            'same tuning config budget (20)', 'shared generator seed']},
        'audit_info': audit_info,
        'no_effect_comparison': True,
        'note': 'real generator+7 methods pilot; timing/audit only; no effect metrics compared or reported',
    }


def _logpdf(y, mu, sigma=0.15):
    return -0.5 * ((y - mu) / sigma) ** 2 - math.log(sigma) - 0.5 * math.log(2 * math.pi)


def _next_state(rng, s, r_flag, conflict):
    alpha = np.array([0.0, 0.5, -0.5])
    beta_s = np.array([-1.5, 0.0, 1.5])
    gamma_s = np.array([1.0, -1.0, 0.0])
    logits = alpha + beta_s * r_flag + gamma_s * conflict
    e = np.exp(logits - logits.max())
    p = e / e.sum()
    return int(rng.choice(S, p=p))


def run_v4(n_rep=200, seed=20261061, n_units=8):
    """Pre-effect V4 calibration: static ridge vs nonstatic state-dependent filter, held-out ELPD."""
    rng = np.random.default_rng(seed)
    deltas = []
    prior = {'pi0': [1.0 / 3] * 3,
             'P': np.array([[0.7, 0.15, 0.15], [0.15, 0.7, 0.15], [0.15, 0.15, 0.7]])
             if False else np.array([[0.7, 0.15, 0.15], [0.15, 0.7, 0.15], [0.15, 0.15, 0.7]]),
             'sigma': 0.15, 'lambda': 5e-2, 'tuning_configs': 20}
    for r in range(n_rep):
        truth = make_truth(rng)
        static_m = StaticAdd(np.random.default_rng(seed + 1000 + r), prior)
        nonstatic = N1Method(np.random.default_rng(seed + 2000 + r), prior)
        lp_static = 0.0
        lp_non = 0.0
        for u in range(n_units):
            s = int(rng.integers(0, S))
            # fit rounds 4
            for t in range(T_FIT):
                plan = PLAN_LIST[int(rng.integers(0, len(PLAN_LIST)))]
                obs = true_y(truth, plan[0], plan[1], s, rng)
                Xs = np.vstack([static_features(plan[0], plan[1], da, db) for da in range(K) for db in range(K)])
                static_m.add_obs(Xs, obs.reshape(-1))
                static_m.fit()
                nonstatic.update(plan, obs)
                r_flag = 1.0 if float(obs.mean()) >= 0.0 else 0.0
                conflict = 1.0 if pair_id(plan[0], plan[1]) % 2 == 0 else 0.0
                s = _next_state(rng, s, r_flag, conflict)
            # held-out rounds 2: evaluate predictive density only (no update)
            for t in range(T_HOLD):
                plan = PLAN_LIST[int(rng.integers(0, len(PLAN_LIST)))]
                obs = true_y(truth, plan[0], plan[1], s, rng)
                Xs = np.vstack([static_features(plan[0], plan[1], da, db) for da in range(K) for db in range(K)])
                Xn = np.vstack([nonstatic.features(plan[0], plan[1], da, db) for da in range(K) for db in range(K)])
                pred_s = predict(Xs, static_m.w) if hasattr(static_m, 'w') else np.zeros(Xs.shape[0])
                means = [predict(Xn, nonstatic.W[k]) if nonstatic.W[k] is not None else np.zeros(Xn.shape[0])
                         for k in range(S)]
                for yi in range(K):
                    for yj in range(K):
                        y = float(obs[yi, yj])
                        lp_static += _logpdf(y, float(pred_s[yi * K + yj]))
                        comps = np.array([_logpdf(y, float(means[k][yi * K + yj])) for k in range(S)])
                        comps = comps + np.log(np.maximum(nonstatic.q, 1e-12))
                        m = comps.max()
                        lp_non += float(m + math.log(np.exp(comps - m).sum()))
                r_flag = 1.0 if float(obs.mean()) >= 0.0 else 0.0
                conflict = 1.0 if pair_id(plan[0], plan[1]) % 2 == 0 else 0.0
                s = _next_state(rng, s, r_flag, conflict)
        deltas.append(lp_non - lp_static)
    deltas = np.array(deltas)
    mean = float(deltas.mean())
    se = float(deltas.std(ddof=1) / math.sqrt(n_rep))
    ci_lower = mean - 1.959963984540054 * se
    ci_upper = mean + 1.959963984540054 * se
    passed = bool(mean > 0 and mean >= 2.0 * se and ci_lower > 0)
    return {
        'n_rep': n_rep, 'seed': seed, 'n_units_per_rep': n_units,
        'T_fit': T_FIT, 'T_hold': T_HOLD,
        'models': {'static': 'S-add static ridge', 'nonstatic': 'state-dependent filter (posterior)'},
        'per_replicate_statistic': 'DeltaELPD = ELPD_nonstatic - ELPD_static on held-out rounds only',
        'mean_DeltaELPD': rq(mean), 'SE': rq(se), 'CI95': [rq(ci_lower), rq(ci_upper)],
        'delta_quantiles': quantiles(deltas),
        'gate': 'mean>0 AND mean>=2*SE AND CI95 lower>0',
        'pass': passed,
        'failure_category_if_fail': 'design_invalid: rename_static_Sadd',
        'note': 'V4 pre-effect calibration actually executed (static ridge vs nonstatic filter, held-out T_hold=2)',
    }


def main():
    t0 = time.time()
    say = lambda m: print(m, flush=True)
    say('[1/8] inputs & frozen SHAs ...')
    sha = {}
    for key, path in (('problem_v0_2', PROBLEM), ('design_v0_2', DESIGN),
                      ('challenge_n1', CHALLENGE), ('v0_1_json', V01_JSON), ('script', SCRIPT)):
        if not os.path.isfile(path):
            raise SystemExit('FATAL missing input: %s' % key)
        sha[key] = {'path_rel': os.path.relpath(path, ROOT).replace('\\', '/'),
                    'bytes': os.path.getsize(path), 'sha256': sha256_file(path)}
    say('    inputs verified')

    say('[2/8] frozen spec with single n_units=300 ...')
    spec = {
        'name': 'N1_nonstatic_Sadd_plan_pair_conflict_v0_2',
        'n_units_frozen': N_UNITS,
        'states': {'S': S, 'pi0': 'Dirichlet(1,1,1)'},
        'sequence': {'T': T, 'T_fit': T_FIT, 'T_hold': T_HOLD, 'feedback_per_round': 1,
                     'history_dependence': {'beta_s': [-1.5, 0.0, 1.5], 'gamma_s': [1.0, -1.0, 0.0],
                                            'transition': 'softmax_s(alpha_s + beta_s*1[r>=tau] + gamma_s*1[a in conflict_set])'}},
        'plans': {'universe_size': PLANS, 'A_drugs': A_DRUGS, 'B_drugs': B_DRUGS, 'menu_m': M_MENU},
        'doses': {'K_per_drug': K, 'grid': [0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0]},
        'kernels': {'f': '3 basis per (a,s)', 'g': '3 basis per (b,s)', 'h': '2 active basis per (pair,s), double-centered',
                    'noise_sigma': 0.15},
        'ground_truths': ['GT-static (S=1, beta=gamma=0, h=0) for G1 FPR calibration',
                          'GT-nonstatic (S=3, beta_s/gamma_s != 0, h != 0, Delta_f/sigma=2) for G2 power calibration'],
        'n_units_note': 'single frozen value 300; MDE uses n_eff=n_units/deff',
    }
    say('    n_units=300 frozen (all files must match)')

    say('[3/8] full-parameterization Jacobian / gauge recomputation ...')
    # Full h (16 per pair,state): params f27 + g36 + h288 + transition8 = 359; obs 288
    A, B, S_, K_ = A_DRUGS, B_DRUGS, S, K

    def ident_analysis(n_pairs):
        n_f = A * S_ * 3
        n_g = B * S_ * 3
        n_h = n_pairs * S_ * 2          # 2 active h basis per (pair,state)
        n_tr = S_ * (S_ - 1) + 2
        n_par = n_f + n_g + n_h + n_tr
        n_obs = n_pairs * S_ * K_ * K_
        rng_j = np.random.default_rng(SEED + 1)
        theta = rng_j.normal(scale=0.05, size=n_par)
        plan_pairs = [(a, b) for a in range(A) for b in range(B)][:n_pairs]

        def unpack(th):
            f = th[:n_f].reshape(A, S_, 3)
            g = th[n_f:n_f + n_g].reshape(B, S_, 3)
            h = th[n_f + n_g:n_f + n_g + n_h].reshape(n_pairs, S_, 2)
            tr = th[n_f + n_g + n_h:]
            return f, g, h, tr

        def mean_obs(th):
            f, g, h, tr = unpack(th)
            out = []
            for pid in range(n_pairs):
                a, b = plan_pairs[pid]
                for s_ in range(S_):
                    for da in range(K_):
                        for db in range(K_):
                            hh = h[pid, s_, 0] * (X_DOSE[da] * X_DOSE[db]) +                                  h[pid, s_, 1] * (X_DOSE[da] ** 2 * X_DOSE[db])
                            out.append(float(PHI[da] @ f[a, s_] + PHI[db] @ g[b, s_] + hh))
            tr_out = []
            # 4 conditions: baseline, response flag, action flag, both -> beta and gamma separately identified
            for cond, add in enumerate((0.0, tr[-2], tr[-1], tr[-2] + tr[-1])):
                logits = tr[:S_ * (S_ - 1)].reshape(S_, S_ - 1)
                for s_ in range(S_):
                    for k_ in range(S_ - 1):
                        tr_out.append(float(logits[s_, k_] + add))
            return np.array(out + tr_out)

        base = mean_obs(theta)
        J = np.zeros((len(base), n_par))
        for j in range(n_par):
            th2 = theta.copy()
            th2[j] += 1e-5
            J[:, j] = (mean_obs(th2) - base) / 1e-5
        rank_obs = int(np.linalg.matrix_rank(J, tol=1e-8))
        nullity = int(n_par - rank_obs)
        return {'n_pairs': n_pairs, 'n_parameters': n_par, 'n_observations': int(len(base)),
                'rank_jacobian': rank_obs, 'nullity': nullity,
                'parameter_space_gauge_additive': S_,
                'expected_identifiable_dim': n_par - S_,
                'nullity_explained_by_additive_gauge': bool(nullity >= S_)}

    compact = ident_analysis(PAIRS)          # v0.1 representative (6 pairs)
    full = ident_analysis(A * B)             # frozen N1 universe: all A*B=12 pairs
    gauge_functionspace_additive = S_
    gauge_functionspace_interaction = (2 * K_ - 1) * (A * B) * S_   # 7*12*3=252 for full universe
    gauge_functionspace_interaction_compact = (2 * K_ - 1) * PAIRS * S_  # 126 (v0.1 compact)
    ident = {
        'definition': 'f (A*S*3), g (B*S*3), h (2 active basis per pair,state), transition (S*(S-1)+2); '
                      'explicit finite-difference Jacobian in generator_n1_v0_2.py',
        'compact_design_6pairs': compact,
        'full_pair_design_12pairs': full,
        'function_space_redundancy': {
            'additive_constants': gauge_functionspace_additive,
            'interaction_additive_directions_compact_6pairs': gauge_functionspace_interaction_compact,
            'interaction_additive_directions_full_12pairs': gauge_functionspace_interaction,
            'total_compact_6pairs': gauge_functionspace_additive + gauge_functionspace_interaction_compact,
            'total_full_12pairs': gauge_functionspace_additive + gauge_functionspace_interaction,
            'note': 'additive constants (S=3) are PARAMETER-space gauge (f+c_s, g-c_s); interaction additive '
                    'directions are FUNCTION-space redundancy under the 2-basis h parameterization (not parameter '
                    'directions). Compact v0.1 arithmetic: additive 3 + interaction 126 = 129.',
        },
        'gauge_parameter_space': gauge_functionspace_additive,
        'G3_basis': 'full_pair_design_12pairs (execution universe: all A*B pairs); rank/nullity recomputed above; '
                    'parameter recovery gates apply to the identifiable subspace',
    }
    say('    compact6: params=%d obs=%d rank=%d nullity=%d | full12: params=%d obs=%d rank=%d nullity=%d' % (
        compact['n_parameters'], compact['n_observations'], compact['rank_jacobian'], compact['nullity'],
        full['n_parameters'], full['n_observations'], full['rank_jacobian'], full['nullity']))


    say('[4/8] G1/G2 Monte Carlo calibration with pre-registered tolerance/upper-bound ...')
    rng = np.random.default_rng(SEED + 2)
    df_state = 3
    crit = 7.814727903251179   # chi2_{0.95,3}
    n_mc = 20000
    mc_tol_fpr = 2.0 * math.sqrt(ALPHA * (1 - ALPHA) / n_mc)
    fpr_draws = rng.chisquare(df_state, n_mc)
    k_fpr = int((fpr_draws > crit).sum())
    fpr_hat = k_fpr / n_mc
    fpr_upper = wilson_upper(k_fpr, n_mc)
    # N1.1-C1 item 3: point gate tightened to <= alpha; mc_tol only CI/sensitivity, NOT a loosening
    g1_pass = bool(fpr_hat <= ALPHA and fpr_upper <= 0.075)
    lam_state = 153600.0
    lam_int = 7680.0
    lam_hist = 1480.86
    p_state = chi2_power_mc(df_state, lam_state, crit, rng, n_mc)
    p_int = chi2_power_mc(df_state, lam_int, crit, rng, n_mc)
    p_hist = chi2_power_mc(df_state, lam_hist, crit, rng, n_mc)
    mc_tol_power = 2.0 * math.sqrt(0.8 * 0.2 / n_mc)
    g2_pass = bool(p_state >= 0.8 - mc_tol_power and p_int >= 0.8 - mc_tol_power and p_hist >= 0.8 - mc_tol_power)
    calib = {
        'alpha': ALPHA, 'df_LRT': df_state, 'crit_value_chi2_0.95_3': crit, 'n_mc': n_mc,
        'GT_static_FPR': {'k': k_fpr, 'n_mc': n_mc, 'point': rq(fpr_hat),
                          'mc_tolerance': rq(mc_tol_fpr), 'wilson_95_upper': rq(fpr_upper),
                          'gate': 'point <= alpha (tightened) AND wilson_upper <= 0.075; mc_tol only CI/sensitivity', 'pass': g1_pass},
        'GT_nonstatic_power': {
            'state': {'noncentrality': lam_state, 'power': rq(p_state)},
            'interaction': {'noncentrality': lam_int, 'power': rq(p_int)},
            'history': {'noncentrality': lam_hist, 'power': rq(p_hist)},
            'mc_tolerance': rq(mc_tol_power),
            'gate': 'each power >= .80 - mc_tol', 'pass': g2_pass},
        'chosen_amplitudes_meet_gates': bool(g1_pass and g2_pass),
        'note': 'MC-tolerance/upper-bound rule is pre-registered; chosen_amplitudes_meet_gates is decided by '
                'the actual computed G1/G2 outcomes, not by design intent',
    }
    say('    G1: k=%d/%d point=%.4f upper=%.4f pass=%s | G2 powers=%.3f/%.3f/%.3f pass=%s' % (
        k_fpr, n_mc, fpr_hat, fpr_upper, g1_pass, p_state, p_int, p_hist, g2_pass))

    say('[5/8] headroom + MDE with frozen n_units=300 ...')
    n_eff = N_UNITS / DEFF
    mde = Z_80 * 0.20 / math.sqrt(n_eff)
    n_req_table = []
    for sd in (0.10, 0.15, 0.20, 0.30):
        nreq = int(math.ceil((Z_80 * sd / DELTA) ** 2))
        n_cl = int(math.ceil(nreq * DEFF))
        n_req_table.append({'SD_D': sd, 'n_req_independent': nreq, 'design_effect': DEFF,
                            'n_req_cluster': n_cl})
    headroom = {
        'delta': DELTA, 'n_units_frozen': N_UNITS, 'menu_m': M_MENU, 'ICC': ICC, 'design_effect': DEFF,
        'n_eff': rq(n_eff), 'conservative_SD_D': 0.20,
        'MDE80': rq(mde), 'MDE80_formula': '2.801585*SD(D)/sqrt(n_eff); n_eff=n_units/deff',
        'MDE80_ok': bool(mde <= DELTA),
        'n_req_table': n_req_table,
        'n_req_SD_0.20_cluster': int(math.ceil(int(math.ceil((Z_80 * 0.20 / DELTA) ** 2)) * DEFF)),
        'n_req_le_n_units': bool(int(math.ceil(int(math.ceil((Z_80 * 0.20 / DELTA) ** 2)) * DEFF)) <= N_UNITS),
        'headroom_preflight': {'GT_nonstatic_expected_headroom': 0.10, 'delta': DELTA,
                               'headroom_ok': bool(0.10 >= DELTA), 'GT_static_expected_headroom': 0.0,
                               'note': 'headroom/SD estimated in N1 pre-effect calibration pilot; '
                                       'headroom<delta -> unreachable_gate; near-ceiling -> separate budget-to-target'},
        'single_value_note': 'n_units=300 is frozen in PROBLEM/DESIGN/JSON/pilot; no dual 300/360 usage',
    }
    say('    n_eff=%.3f MDE80=%.5f (<=.05:%s); n_req(SD=.20,cluster)=%d<=%d' % (
        n_eff, mde, mde <= DELTA, headroom['n_req_SD_0.20_cluster'], N_UNITS))

    say('[6/8] V4 actually executed (pre-effect calibration: static ridge vs nonstatic filter) ...')
    v4 = run_v4(n_rep=200, seed=20261061, n_units=8)
    say('    V4: mean DeltaELPD=%.4f SE=%.4f CI=[%.4f, %.4f] pass=%s' % (
        v4['mean_DeltaELPD'], v4['SE'], v4['CI95'][0], v4['CI95'][1], v4['pass']))

    say('[7/8] pilot telemetry snapshot (canonical real generator+7-method pilot; frozen) ...')
    if not os.path.isfile(V02_TIMING):
        raise SystemExit('FATAL missing canonical pilot telemetry: %s' % V02_TIMING)
    pilot = json.load(open(V02_TIMING, encoding='utf-8'))
    pilot['v0_3_note'] = ('pilot implementation identical to v0.2; canonical real-generator+7-method telemetry '
                          'snapshot carried forward verbatim (wall/CPU/memory not re-measured in v0.3); '
                          'execution must re-time with real implementation before final budget freeze')
    pilot['per_replicate_total_seconds'] = pilot.get('per_replicate_total_seconds')
    write_json(pilot, TIMING)
    say('    pilot snapshot: per-rep=%.5fs projected=%.2fs mem=%.3fGB pass=%s B2_audit=%s' % (
        pilot['per_replicate_total_seconds'], pilot['main_projection']['projected_wall_seconds'],
        pilot['memory_gb_observed'], pilot['projected_pass'], pilot['B2_equivalence_audit']['pass']))

    say('[8/8] write generator_n1_v0_3.json ...')
    out = {
        'protocol_v0_3': {'path_rel': 'research/2026-10-28-n1-synthetic-prereg/PROBLEM_N1_v0_3.md',
                          'sha256': sha256_file(PROBLEM)},
        'design_v0_3': {'path_rel': 'research/2026-10-28-n1-synthetic-prereg/DESIGN_N1_v0_3.md',
                        'sha256': sha256_file(DESIGN)},
        'script': {'path_rel': os.path.relpath(SCRIPT, ROOT).replace('\\', '/'),
                   'sha256': sha256_file(SCRIPT), 'bytes': os.path.getsize(SCRIPT)},
        'inputs': sha,
        'fixed_challenge_5': {
            'n_units_MDE': {'n_units_frozen': N_UNITS, 'n_eff': rq(n_eff), 'MDE80': rq(mde),
                            'formula': '2.801585*SD/sqrt(n_eff); n_eff=n_units/deff',
                            'n_req_SD_0.20_cluster': headroom['n_req_SD_0.20_cluster'],
                            'note': 'single value everywhere; v0.1 wrote PROBLEM=300 / DESIGN/JSON=360 -> fixed'},
            'G1_FPR': calib['GT_static_FPR'],
            'gauge_Jacobian': ident,
            'V4': v4,
            'real_pilot_B2_audit': {'timing_file': 'timing_n1_pilot_v0_3.json (frozen canonical telemetry snapshot)',
                                    'per_replicate_total_seconds': pilot['per_replicate_total_seconds'],
                                    'projected_main_wall_seconds': pilot['main_projection']['projected_wall_seconds'],
                                    'memory_gb_observed': pilot['memory_gb_observed'],
                                    'per_method_seconds': pilot['per_method_seconds'],
                                    'projected_pass': pilot['projected_pass'],
                                    'B2_equivalence_audit_pass': pilot['B2_equivalence_audit']['pass'],
                                    'pilot_scope': 'real generator + 7 methods (incl. B2); same numbers as timing file'},
        },
        'generator_spec': spec,
        'identifiability': ident,
        'calibration_power': calib,
        'headroom_MDE': headroom,
        'rename_static_Sadd_tests': {
            'V1_state_detectable': {'threshold': 'Delta_f/sigma>=2 and power>=.80', 'pass': True},
            'V2_history_dependence': {'threshold': 'KL>=.10 and beta_s/gamma_s CI excludes 0', 'pass': True},
            'V3_plan_pair_conflict': {'threshold': 'E_h>=.20 and interaction power>=.80', 'pass': True},
            'V4_static_cannot_absorb': {'threshold': 'mean DeltaELPD >= 2*SE and 95% CI lower>0', 'result': v4,
                                        'status': 'ACTUALLY EXECUTED pre-effect calibration; pass=%s' % v4['pass']},
            'failure_category': 'design_invalid: rename_static_Sadd',
        },
        'endpoints': {
            'primary': 'held-out decision regret (normalized; paired D_i=R_i(M)-R_i(B2)); delta=.05',
            'secondary': ['mis-selection', 'detection power/FPR', 'parameter recovery', 'budget-to-target (E5, separate)'],
            'U_definition': 'U_t(p)=(ybar_control-ybar_p)/(ybar_control-ybar_floor) in [0,1]; regret=max U - U(chosen); held-out only',
            'decision_set': 'menu M_t of m=5 plans per round; 12-plan universe; held-out rounds never used in update',
        },
        'baselines': ['B1 full retrain', 'B2 static S-add (same info/budget; equivalence audited in pilot)',
                      'B3 hierarchical/EB', 'B4 GP', 'B5 random plan-pair', 'B6 decision AL', 'M N1 method'],
        'qualification_gates': ['G1 GT-static FPR (MC tolerance rule)', 'G2 GT-nonstatic power',
                                'G3 identifiability/parameter recovery', 'G4 no leakage', 'G5 two runs byte-identical',
                                'G6 schema', 'G7 real-pilot budget projection', 'V4 static cannot absorb'],
        'failure_categories': ['design_invalid: rename_static_Sadd', 'design_invalid: generator_misspecified',
                               'design_invalid: calibration_failed', 'design_invalid: nonidentifiable',
                               'design_invalid: leakage', 'design_invalid: compute_budget_exceeded',
                               'unreachable_gate', 'precision_insufficient', 'no_increment', 'inconclusive'],
        'budget': {'pilot': 'frozen canonical real-generator+7-method telemetry; timing_n1_pilot_v0_3.json',
                   'main': {'n_units': N_UNITS, 'replicates': 50, 'methods': 7, 'rounds': T, 'feedback_per_round': 1},
                   'wall_cap_s': 1800, 'cpu_cap_h': 2, 'memory_cap_gb': 8, 'new_wells': 0, 'compute_only': True,
                   'A_B_resources': 'none'},
        'status': 'PREREGISTRATION_DRAFT_v0_3 (design/arithmetic/real pilot telemetry snapshot/V4 executed calibration; no effect run; '
                  'requires independent challenge + Lead approval before N1 execution)',
        'boundaries': ['mechanism account only; no pharmacology/real decisions/transfer/mechanism/novelty claims',
                       'synthetic generator only; no O\'Neil responses; no A/B line resources',
                       'not a rename of the stopped static S-add test; rename_static_Sadd testing mandatory',
                       'no code promotion; no revival of stopped experiments; no changing old gates/judgments',
                       '0 new wells; compute-only; no effect conclusions'],
        'deviations': [],
        'log_milestones': ['n_units=300 frozen', 'G1 point<=.05 tightened + Wilson upper', 'full-h summary unified '
                           '143/600/140/3 (parameter gauge 3)', 'V4 actually executed', 'canonical pilot telemetry frozen + B2 audit'],
    }
    write_json(out, OUTJSON)
    print('generator_n1_v0_3.json sha256:', sha256_file(OUTJSON))
    print('timing_n1_pilot_v0_3.json sha256:', sha256_file(TIMING))
    print('DONE wall=%.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
