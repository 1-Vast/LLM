"""Read-allocation policies for the campaign: fixed design, batch Bayesian design, target-set posterior sampling.

File summary
- Path: research/observable_state_20261018/policies.py
- A policy exposes `plan_round(camp, size) -> [(compound, context)]` and may read only the campaign's belief state
  (prior, covariance, what was read and the values already observed). It never receives hidden outcomes.
- `FixedPolicy`  : the fixed design (A1-neutral reference A0): every compound walks the same context order.
- `BatchEIGPolicy`: batch Bayesian design baseline in the spirit of BATCHIE: each batch is built greedily by Gaussian
  information gain 0.5*logdet(I + C_cc / noise_var) of the read about the compound's profile. SIMPLIFICATION: BATCHIE's
  Probabilistic-Diameter-based Active Learning (PDBAL) is NOT implemented; this is a batch-EIG stand-in until the primary
  paper's algorithm is read and ported. Do not describe results as "BATCHIE".
- `PSBAXPolicy` : posterior-sampling design for a target SET (Cheng et al. 2024 idea): draw one posterior profile per
  compound, run the base algorithm (the campaign's nomination rule) on the draw to get a sampled target set, then spend the
  batch greedily on the reads that cover the largest posterior variance on sampled-target lines. SIMPLIFICATION: one draw
  per round and a variance criterion, not the paper's exact selection rule; label as "PS-BAX-style".
- Greedy batches condition on chosen reads through the covariance only (Gaussian variance does not depend on outcomes), so
  batch construction is exact for these criteria. Ties go to the fixed order.
"""
from __future__ import annotations

import numpy as np


class FixedPolicy:
    name = "fixed"

    def __init__(self, order):
        self.order = list(order)
        self.cursor = 0  # rotates the starting compound so uneven batches spread evenly

    def plan_round(self, camp, size):
        plan, n = [], camp.n
        taken = set()
        while len(plan) < size:
            added = False
            start = self.cursor
            for step in range(n):
                i = (start + step) % n
                c = next((c for c in self.order if not camp.done[i, c] and (i, c) not in taken), None)
                if c is None:
                    continue
                plan.append((i, c))
                taken.add((i, c))
                added = True
                self.cursor = (i + 1) % n
                if len(plan) == size:
                    break
            if not added:
                break
        return plan


def _gain_eig(C, lines, s2):
    sub = C[np.ix_(lines, lines)] / s2
    return 0.5 * np.linalg.slogdet(np.eye(len(lines)) + sub)[1]


class _Greedy:
    """Greedy batch construction over (compound, context) with per-compound conditioning."""

    def __init__(self, order):
        self.order = list(order)

    def criterion(self, camp, i, c, C, ctx):  # pragma: no cover - overridden
        raise NotImplementedError

    def prepare(self, camp):
        return None

    def plan_round(self, camp, size):
        ctx = self.prepare(camp)
        cov = {i: camp.cov(i) for i in range(camp.n)}
        taken = camp.done.copy()
        plan = []
        gains = {}
        for _ in range(size):
            best = None
            for i in range(camp.n):
                for c in self.order:
                    if taken[i, c] or len(camp.contexts[c]) == 0:
                        continue
                    key = (i, c)
                    if key not in gains:
                        gains[key] = self.criterion(camp, i, c, cov[i], ctx)
                    g = gains[key]
                    if best is None or g > best[0] + 1e-12:
                        best = (g, i, c)
            if best is None:
                break
            _, i, c = best
            plan.append((i, c))
            taken[i, c] = True
            cov[i] = camp.cov_after(i, camp.contexts[c], cov[i])
            for cc in self.order:  # conditioning changes this compound's gains only
                gains.pop((i, cc), None)
        return plan


class BatchEIGPolicy(_Greedy):
    name = "batch_eig"

    def criterion(self, camp, i, c, C, ctx):
        return _gain_eig(C, camp.contexts[c], camp.noise_var)


class PSBAXPolicy(_Greedy):
    name = "ps_bax_style"

    def __init__(self, order, seed=20261018):
        super().__init__(order)
        self.seed = seed
        self.round = 0

    def prepare(self, camp):
        rng = np.random.default_rng([self.seed, self.round])
        self.round += 1
        q = camp.queried_mask()
        draw = np.zeros_like(camp.m0)
        for i in range(camp.n):
            C = camp.cov(i)
            w, V = np.linalg.eigh((C + C.T) / 2)
            draw[i] = camp.mean(i) + V @ (np.sqrt(np.clip(w, 0, None)) * rng.standard_normal(len(w)))
        # base algorithm = the campaign's nomination rule applied to the sampled profiles
        sc = camp.G[None, :] - draw
        sc = np.where(camp.avail[None, :] & ~q, sc, -np.inf)
        order = np.argsort(-sc, axis=None, kind="stable")
        targets = {i: [] for i in range(camp.n)}
        cnt = 0
        per = {}
        for k in order:
            i, l = divmod(int(k), sc.shape[1])
            if not np.isfinite(sc[i, l]) or cnt >= camp.follow_up:
                break
            if per.get(i, 0) >= camp.cap:
                continue
            per[i] = per.get(i, 0) + 1
            cnt += 1
            targets[i].append(l)
        return {i: np.array(v, int) for i, v in targets.items()}

    def criterion(self, camp, i, c, C, ctx):
        T = ctx[i]
        if len(T) == 0:
            return 0.0
        lines = camp.contexts[c]
        inter = np.intersect1d(lines, T)
        # posterior variance on sampled-target lines that this read would resolve, plus a small spill-over term
        A = C[np.ix_(lines, lines)] + camp.noise_var * np.eye(len(lines))
        red = np.diag(C[np.ix_(T, lines)] @ np.linalg.solve(A, C[np.ix_(lines, T)])).sum()
        return float(red) + 1e-6 * len(inter)
