"""Read allocation in passes, the Gate 0 arms (A0, A1, OA-PF, ORACLE, A1c) and the Gate 1a pipeline."""
import hashlib

import numpy as np
from scipy import special

from common import ALPHA, CHECK_M, PF_MULTIPLES
from evalues import clip_bets, cumulative_table, ebh, log_lr, mixture_log_e, pf_table, stop_threshold


def allocate(order, remaining, budget):
    """Deal one read per listed unit per pass down `order` (unique unit indices) until `budget` reads are spent."""
    order = np.asarray(order, dtype=int)
    out = np.zeros(remaining.shape[0], dtype=int)
    budget = int(budget)
    if budget <= 0 or order.size == 0:
        return out
    rem = np.asarray(remaining)[order].astype(int)
    if budget >= rem.sum():
        out[order] = rem
        return out
    passes = 0
    while np.minimum(rem, passes + 1).sum() <= budget:
        passes += 1
    reads = np.minimum(rem, passes)
    left = budget - int(reads.sum())
    if left > 0:
        reads[np.nonzero(rem >= passes + 1)[0][:left]] += 1
    out[order] = reads
    return out


def desc_order(values, rng, subset=None):
    """Indices by descending value, NaN last, random tie-breaks; restricted to `subset` when given."""
    idx = np.arange(len(values)) if subset is None else np.asarray(subset, dtype=int)
    v = np.asarray(values, dtype=float)[idx]
    key = np.where(np.isnan(v), np.inf, -v)
    return idx[np.lexsort((rng.random(idx.size), key))]


def read_orders(unit_names, barcodes, n_replays):
    """Per replay, the reveal order of each unit's reads: ascending SHA256(f"{r}|{unit}|{BARCODE}")."""
    K, width = barcodes.shape
    orders = np.tile(np.arange(width, dtype=np.int16), (n_replays, K, 1))
    for u in range(K):
        codes = [b for b in barcodes[u] if b]
        n = len(codes)
        if n < 2:
            continue
        for r in range(n_replays):
            keys = [hashlib.sha256(f"{r}|{unit_names[u]}|{b}".encode()).digest() for b in codes]
            orders[r, u, :n] = sorted(range(n), key=keys.__getitem__)
    return orders


def reorder(X, order):
    return np.take_along_axis(X, order.astype(int), axis=1)


class Pool:
    """K units: evidence reads X (K, width) left-packed in reveal order, primary p, wells per read, optional truth mu."""

    def __init__(self, X, p, wells, mu=None):
        self.X = np.asarray(X, dtype=float)
        self.R = (~np.isnan(self.X)).sum(axis=1)
        self.p = np.asarray(p, dtype=float)
        self.wells = np.broadcast_to(np.asarray(wells, dtype=float), self.R.shape).copy()
        self.mu = None if mu is None else np.asarray(mu, dtype=float)
        self.K = self.X.shape[0]


class Bets:
    """Fitted noise model and the bets it allows."""

    def __init__(self, sigma, nu, valid):
        self.sigma, self.nu, self.valid = float(sigma), float(nu), np.asarray(valid, dtype=bool)

    def clip(self, m):
        return clip_bets(m, self.sigma, CHECK_M, self.valid)

    def pf(self, X):
        return pf_table(X, self.sigma, self.nu, multiples=self.clip(PF_MULTIPLES * self.sigma) / self.sigma)

    def fixed(self, X, m):
        return cumulative_table(X, np.atleast_1d(self.clip(m)), self.sigma, self.nu)

    def oracle(self, X, mu):
        bets = self.clip(np.where(mu > 0, mu, 0.0))
        return cumulative_table(X, bets[:, None], self.sigma, self.nu)


def _two_rounds(pool, C, budget, order1, second, rng):
    K = pool.K
    b1 = budget // 2
    n1 = allocate(order1, pool.R, b1)
    le1 = mixture_log_e(C, n1)
    _, k1 = ebh(le1)
    stopped = le1 >= stop_threshold(K, k1)
    order2 = second(n1, le1, stopped)
    n2 = allocate(order2, pool.R - n1, budget - b1)
    n = n1 + n2
    le = mixture_log_e(C, n)
    rej, k = ebh(le)
    return n, le, rej, k, k1


def a1_second_order(pool, n1, le1, stopped, rng):
    read = n1 > 0
    open_ = read & ~stopped
    promising = desc_order(le1, rng, np.nonzero(open_ & (le1 >= 0))[0])
    unread = desc_order(pool.p, rng, np.nonzero(~read)[0])
    losing = desc_order(le1, rng, np.nonzero(open_ & (le1 < 0))[0])
    return np.concatenate([promising, unread, losing])


def run_arm(arm, pool, bets, budget, rng, tables):
    """One arm on one replay; `tables` caches the PF and oracle cumulative tables of the pool."""
    K = pool.K
    if arm == "A0":
        C = tables["pf"]
        order1 = rng.permutation(K)
        n, le, rej, k, k1 = _two_rounds(pool, C, budget, order1, lambda n1, le1, s: rng.permutation(K), rng)
    elif arm == "A1":
        C = tables["pf"]
        order1 = desc_order(pool.p, rng)
        n, le, rej, k, k1 = _two_rounds(pool, C, budget, order1,
                                        lambda n1, le1, s: a1_second_order(pool, n1, le1, s, rng), rng)
    elif arm in ("OA-PF", "ORACLE"):
        C = tables["pf"] if arm == "OA-PF" else tables["oracle"]
        positive = np.nonzero(pool.mu > 0)[0]
        order1 = desc_order(pool.mu, rng, positive)
        n, le, rej, k, k1 = _two_rounds(pool, C, budget, order1,
                                        lambda n1, le1, s: desc_order(pool.mu, rng, positive[~s[positive]]), rng)
    else:
        raise ValueError(arm)
    wells = float((n * pool.wells).sum())
    out = {"D": k, "D1": k1, "reads": int(n.sum()), "wells": wells, "eff": 1000.0 * k / wells if wells else 0.0,
           "_n": n}
    if pool.mu is not None:
        false = int((rej & (pool.mu <= 0)).sum())
        out.update({"false": false, "fdp": false / max(k, 1)})
    return out


def run_a1c(pool, rng, cert, alpha=ALPHA):
    """Conformal certificate of PERSPECTIVE 5.1: 10% uniform audit, labels read > 0, conformal p-values, BH(alpha)."""
    K = pool.K
    size = max(int(round(0.1 * K)), cert.minimum_audit(alpha))
    audit = np.sort(rng.choice(K, size=size, replace=False))
    in_audit = np.zeros(K, dtype=bool)
    in_audit[audit] = True
    rest = np.nonzero(~in_audit)[0]
    first = pool.X[:, 0]
    hits = first[audit] > 0
    scores = np.where(np.isnan(pool.p), -np.inf, pool.p)
    pv = cert.conformal_pvalues(scores[audit].tolist(), hits.tolist(), scores[rest].tolist())
    chosen = rest[np.asarray(cert.benjamini_hochberg(pv, alpha), dtype=bool)]
    wells = float(pool.wells[audit].sum())
    out = {"D": int(chosen.size), "wells": wells, "eff": 1000.0 * chosen.size / wells, "audit": int(size),
           "audit_hit_rate": float(hits.mean()),
           "false_label_fdp": float((first[chosen] <= 0).sum() / max(chosen.size, 1))}
    if pool.mu is not None:
        out["false_truth_fdp"] = float((pool.mu[chosen] <= 0).sum() / max(chosen.size, 1))
    return out


# ---------------------------------------------------------------- Gate 1a pipeline

def expert_steps(pool, bets):
    """Per-read log-multipliers of the portfolio experts: PF (posterior-weighted), m = 1 sigma, m = 3 sigma."""
    C = bets.pf(pool.X)
    lse = special.logsumexp(C, axis=2) - np.log(C.shape[2])
    pf_step = np.diff(lse, axis=1)
    m1, m3 = bets.clip(np.array([1.0, 3.0]) * bets.sigma)
    nan = np.isnan(pool.X)
    one = np.where(nan, 0.0, log_lr(pool.X, m1, bets.sigma, bets.nu))
    three = np.where(nan, 0.0, log_lr(pool.X, m3, bets.sigma, bets.nu))
    return C, np.stack([pf_step, one, three], axis=2)


def gate1_run(pool, bets, bettor, budget, rng, round1="random", round2="current_e", cache=None):
    """Two rounds on a pool; returns per-unit log e and reads at both stopping times, and e-BH counts."""
    K = pool.K
    b1 = budget // 2
    cache = cache if cache is not None else {}
    if bettor in ("pf", "portfolio") and "pf" not in cache:
        cache["pf"], cache["steps"] = expert_steps(pool, bets)
    if bettor == "fixed3" and "fixed3" not in cache:
        cache["fixed3"] = bets.fixed(pool.X, 3.0 * bets.sigma)
    cols = np.arange(pool.X.shape[1])[None, :]

    def log_e(n, n_from=None, weights=None, steps=None):
        if bettor == "pf":
            return mixture_log_e(cache["pf"], n)
        if bettor == "fixed3":
            return cache["fixed3"][np.arange(K), n, 0]
        mult = special.logsumexp(steps + np.log(np.maximum(weights, 1e-300))[None, None, :], axis=2)
        lo = np.zeros(K, dtype=int) if n_from is None else n_from
        return np.where((cols >= lo[:, None]) & (cols < n[:, None]), mult, 0.0).sum(axis=1)

    order1 = rng.permutation(K) if round1 == "random" else desc_order(pool.p, rng)
    n1 = allocate(order1, pool.R, b1)
    steps1 = cache.get("steps")
    if bettor == "portfolio":
        le1 = log_e(n1, weights=np.full(3, 1.0 / 3.0), steps=steps1)
    else:
        le1 = log_e(n1)
    _, k1 = ebh(le1)
    stopped = le1 >= stop_threshold(K, k1)
    if round2 == "a1":
        order2 = a1_second_order(pool, n1, le1, stopped, rng)
    else:
        order2 = desc_order(le1, rng, np.nonzero(~stopped)[0])
    n2 = allocate(order2, pool.R - n1, budget - b1)
    n = n1 + n2
    info = {}
    if bettor == "portfolio":
        seen = cols < n1[:, None]
        x1 = pool.X[seen]
        positive = x1[x1 > 0]
        learned = float(bets.clip(max(0.25 * bets.sigma, positive.mean() if positive.size else 0.0)))
        learned_step = np.where(np.isnan(pool.X), 0.0, log_lr(pool.X, learned, bets.sigma, bets.nu))
        steps2 = np.concatenate([steps1, learned_step[:, :, None]], axis=2)
        credit = np.where(seen[:, :, None], steps2[:, :, 1:], 0.0).sum(axis=(0, 1))
        soft = np.exp(credit - credit.max())
        soft /= soft.sum()
        weights = np.concatenate([[0.5], 0.5 * soft])
        le = le1 + log_e(n, n_from=n1, weights=weights, steps=steps2)
        info = {"learned_m_over_sigma": learned / bets.sigma, "round2_weights": weights.tolist()}
    else:
        le = log_e(n)
    _, k = ebh(le)
    return {"n1": n1, "le1": le1, "k1": k1, "n": n, "le": le, "k": k, **info}
