"""Calibrated falsification of mechanism hypotheses over an observation menu (block M engine).

Objects
-------
* Observations: a drug's signatures on a menu of options (here line x time), projected onto a
  K-dimensional basis fitted on reference drugs only (uncentred SVD, so zero stays "no response").
* Hypothesis model: one prototype vector per option, a support count ``n`` (reference drugs behind
  it) and a kind (``data``, ``knowledge``, ``hybrid``). A drug of class h is modelled as
  ``z_o = lambda * mu_{h,o} + e_o`` with one potency ``lambda >= 0`` shared across options (prior
  N(1, tau^2)) and per-option diagonal noise ``var_o``.
* Score: the profile negative log-likelihood of the observed set S under h with lambda fitted on S,
  divided by |S| ("absolute"), or that NLL minus the smallest NLL over the episode's hypothesis
  set ("relative"; see ``Calibration``). Larger is worse.
* Calibration (split conformal, Mondrian by support bucket, exact option set and optionally
  observed-energy bin): reference drugs
  scored against their own class model built without them. The p-value of h for a query is the
  rank of its score among calibration scores of the same bucket computed on the same S.
  Reject h when p <= alpha. Under exchangeability of the query with calibration drugs of its bucket
  and a design S that does not depend on the scored values, the true class is rejected with
  probability <= alpha.
* Planner: the next option minimises the expected number of surviving hypotheses, simulating the
  unseen signature under each survivor with resampled reference residuals.

Everything is numpy; no fitting reads a query drug's values.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

import numpy as np

BUCKETS = ("K", "1", "2-3", "4+")


def bucket_of(n: int, kind: str) -> str:
    if kind == "knowledge" or n <= 0:
        return "K"
    if n == 1:
        return "1"
    if n <= 3:
        return "2-3"
    return "4+"


# ----------------------------------------------------------------------------------------- basis
@dataclass
class Basis:
    components: np.ndarray  # (K, G)

    @classmethod
    def fit(cls, X: np.ndarray, k: int) -> "Basis":
        """Uncentred SVD of all available reference signatures (rows with NaN skipped)."""
        rows = X.reshape(-1, X.shape[-1])
        rows = rows[~np.isnan(rows).any(axis=1)]
        _, _, vt = np.linalg.svd(rows.astype(np.float64), full_matrices=False)
        return cls(components=vt[:k])

    def project(self, X: np.ndarray) -> np.ndarray:
        out = X @ self.components.T
        return out


# ----------------------------------------------------------------------------------------- models
@dataclass
class HypothesisModel:
    name: str
    proto: np.ndarray  # (n_opt, K); NaN rows where the option has no support
    n: int
    kind: str

    @property
    def bucket(self) -> str:
        return bucket_of(self.n, self.kind)


def class_prototypes(Z: np.ndarray, labels: np.ndarray, members: np.ndarray, shrink_to: np.ndarray | None,
                     kappa: float) -> dict[str, tuple[np.ndarray, int]]:
    """Per-class mean per option over member drugs, shrunk toward ``shrink_to`` with weight kappa.

    Z: (n_drug, n_opt, K) with NaN for absent options; members: boolean mask of drugs used.
    Returns {class: (proto (n_opt, K), n_members)}.
    """
    out: dict[str, tuple[np.ndarray, int]] = {}
    for c in np.unique(labels[members]):
        idx = np.where(members & (labels == c))[0]
        sub = Z[idx]
        have = ~np.isnan(sub[..., 0])
        cnt = have.sum(axis=0)  # (n_opt,)
        tot = np.nansum(sub, axis=0)
        if shrink_to is None:
            proto = np.where(cnt[:, None] > 0, tot / np.maximum(cnt, 1)[:, None], np.nan)
        else:
            proto = (tot + kappa * shrink_to) / (cnt[:, None] + kappa)
        out[str(c)] = (proto, len(idx))
    return out


# ----------------------------------------------------------------------------------------- scoring
@dataclass
class NoiseModel:
    var: np.ndarray  # (n_opt, K) per-option diagonal variance
    tau2: float      # potency prior variance


def score_batch(Zobs: np.ndarray, protos: np.ndarray, noise: NoiseModel, opts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Scores of many (drug, hypothesis) pairs on the option set ``opts``.

    Zobs:   (N, len(opts), K) observed projected signatures
    protos: (N, len(opts), K) prototypes of the hypothesis each row is scored against
    Returns (score (N,), lambda_hat (N,)). Rows whose prototype has NaN get score NaN.
    """
    v = noise.var[opts][None]  # (1, S, K)
    A = np.sum(protos * protos / v, axis=(1, 2))
    b = np.sum(protos * Zobs / v, axis=(1, 2))
    Q = np.sum(Zobs * Zobs / v, axis=(1, 2))
    inv = 1.0 / noise.tau2
    lam = np.maximum((b + inv) / (A + inv), 0.0)
    nll = Q - 2 * lam * b + lam * lam * A + (lam - 1.0) ** 2 * inv
    return nll / len(opts), lam


def score_from_stats(Q: np.ndarray, b: np.ndarray, A: np.ndarray, tau2: float, n_opts: int) -> tuple[np.ndarray, np.ndarray]:
    inv = 1.0 / tau2
    lam = np.maximum((b + inv) / (A + inv), 0.0)
    return (Q - 2 * lam * b + lam * lam * A + (lam - 1.0) ** 2 * inv) / n_opts, lam


# ----------------------------------------------------------------------------------------- calibration
@dataclass
class Calibration:
    """Calibration drugs with their own-class (leave-self-out) prototypes and buckets.

    ``mode`` = "absolute": the score is the profile NLL under the hypothesis.
    ``mode`` = "relative": the score is that NLL minus the smallest NLL over the hypothesis set H
    of the episode (the drug's own class enters through its leave-self-out prototype, never through
    the full prototype that contains the drug). This removes how strongly a drug responds from the
    score and keeps how well the hypothesis explains the response compared with its competitors.
    ``n_bins`` > 1 adds a Mondrian split by observed energy (sum of whitened squares per option),
    with bin edges at quantiles of the calibration energies for the same option set; the energy is
    observed before any hypothesis is scored, so the split is a legitimate taxonomy.
    """

    Z: np.ndarray            # (M, n_opt, K) calibration drugs' projected signatures
    own_proto: np.ndarray    # (M, n_opt, K) prototype of their own class built without them
    bucket: np.ndarray       # (M,) bucket labels
    noise: NoiseModel
    P: np.ndarray | None = None          # (H, n_opt, K) hypothesis prototypes (relative mode)
    cal_class: np.ndarray | None = None  # (M,) index of the drug's own class in P (-1: none)
    mode: str = "absolute"
    n_bins: int = 1
    _cache: dict = field(default_factory=dict)

    def __post_init__(self):
        v = self.noise.var
        Zf, Of = np.nan_to_num(self.Z), np.nan_to_num(self.own_proto)
        self.z_ok = ~np.isnan(self.Z[..., 0])
        self.o_ok = ~np.isnan(self.own_proto[..., 0])
        self.Qo = np.sum(Zf * Zf / v, axis=2)          # (M, n_opt)
        self.bo_own = np.sum(Zf * Of / v, axis=2)      # (M, n_opt)
        self.Ao_own = np.sum(Of * Of / v, axis=2)      # (M, n_opt)
        if self.mode == "relative":
            if self.P is None or self.cal_class is None:
                raise ValueError("relative scores need P and cal_class")
            Pf = np.nan_to_num(self.P)
            self.p_ok = ~np.isnan(self.P[..., 0])      # (H, n_opt)
            self.bo = np.stack([(Zf[:, o] / v[o]) @ Pf[:, o].T for o in range(Zf.shape[1])], axis=2).astype(np.float32)  # (M, H, n_opt)
            self.Ao = np.sum(Pf * Pf / v, axis=2)      # (H, n_opt)
        elif self.mode != "absolute":
            raise ValueError(self.mode)

    def _key(self, opts, hyp):
        o = tuple(sorted(int(x) for x in opts))
        if self.mode == "absolute" or hyp is None:
            return o, None
        return o, hash(np.asarray(hyp, dtype=np.int64).tobytes())

    def scores(self, opts: tuple[int, ...], hyp: np.ndarray | None = None) -> tuple[dict, np.ndarray]:
        """({(bucket, bin): sorted calibration scores}, energy bin edges) for option set ``opts``."""
        key = self._key(opts, hyp)
        if key in self._cache:
            return self._cache[key]
        o = np.array(key[0])
        n = len(o)
        ok = self.z_ok[:, o].all(axis=1) & self.o_ok[:, o].all(axis=1)
        Q = self.Qo[:, o].sum(axis=1)
        s_own, _ = score_from_stats(Q, self.bo_own[:, o].sum(axis=1), self.Ao_own[:, o].sum(axis=1), self.noise.tau2, n)
        if self.mode == "relative":
            H = np.arange(self.P.shape[0]) if hyp is None else np.asarray(hyp)
            full = len(H) == self.P.shape[0] and bool(np.all(H == np.arange(len(H))))
            rows = np.where(ok)[0]
            b = self.bo[rows][:, :, o].sum(axis=2)
            if not full:
                b = b[:, H]
            A = self.Ao[H][:, o].sum(axis=1).astype(np.float32)
            nll, _ = score_from_stats(Q[rows, None].astype(np.float32), b, A[None], self.noise.tau2, n)
            nll[:, ~self.p_ok[H][:, o].all(axis=1)] = np.inf
            nll[self.cal_class[rows, None] == H[None, :]] = np.inf  # own class only via its LOO prototype
            s = np.full(len(s_own), np.nan)
            s[rows] = s_own[rows] - np.minimum(nll.min(axis=1), s_own[rows])
        else:
            s = s_own
        energy = Q / n
        edges = np.quantile(energy[ok], np.arange(1, self.n_bins) / self.n_bins) if self.n_bins > 1 and ok.any() else np.array([])
        bins = np.searchsorted(edges, energy, side="right")
        out = {(bk, k): np.sort(s[ok & (self.bucket == bk) & (bins == k)]) for bk in BUCKETS for k in range(self.n_bins)}
        self._cache[key] = (out, edges)
        return out, edges

    def pvalues(self, s: np.ndarray, energy: np.ndarray, buckets: np.ndarray, opts: tuple[int, ...],
                hyp: np.ndarray | None = None) -> np.ndarray:
        """Conformal p-values (1 + #{cal >= s}) / (n + 1).

        s: (D, Hn) scores of D drugs (or simulated draws) under the hypotheses whose buckets are
        given; energy: (D,). An empty calibration cell, or a NaN score, gives p = 1 (no rejection).
        """
        s = np.atleast_2d(s)
        energy = np.atleast_1d(energy)
        cal, edges = self.scores(opts, hyp)
        bins = np.searchsorted(edges, energy, side="right")
        p = np.ones(s.shape, dtype=float)
        for bk in BUCKETS:
            mh = buckets == bk
            if not mh.any():
                continue
            for k in range(self.n_bins):
                md = bins == k
                if not md.any():
                    continue
                c = cal[(bk, k)]
                if len(c) == 0:
                    continue
                sub = np.nan_to_num(s[np.ix_(md, mh)], nan=-np.inf)
                ge = len(c) - np.searchsorted(c, sub, side="left")
                p[np.ix_(md, mh)] = (1.0 + ge) / (len(c) + 1.0)
        p[np.isnan(s)] = 1.0
        return p


# ----------------------------------------------------------------------------------------- episode calibration
@dataclass
class StepCalibration:
    """Calibration of a whole adaptive procedure ("episode calibration").

    Calibration drugs run the same design policy as queries, step by step, with their own class
    represented by its leave-self-out (or knowledge) prototype. ``tables[k]`` holds, for step k + 1,
    the sorted own-class scores by (bucket, energy bin) and the energy bin edges. A query's
    hypothesis at step k + 1 is scored on the option set the query's own episode chose and compared
    with these scores. Because query and calibration drugs pass through the identical procedure,
    the true class's score is exchangeable with the calibration scores even though the design
    adapts to the observations; the price is pooling over option sets.
    """

    tables: list
    n_bins: int
    n_rows: list

    def pvalues(self, k: int, s: np.ndarray, energy: np.ndarray, buckets: np.ndarray) -> np.ndarray:
        s = np.atleast_2d(s)
        energy = np.atleast_1d(energy)
        cal, edges = self.tables[k]
        bins = np.searchsorted(edges, energy, side="right")
        p = np.ones(s.shape, dtype=float)
        for bk in BUCKETS:
            mh = buckets == bk
            if not mh.any():
                continue
            for b in range(self.n_bins):
                md = bins == b
                c = cal.get((bk, b), np.array([]))
                if not md.any() or len(c) == 0:
                    continue
                sub = np.nan_to_num(s[np.ix_(md, mh)], nan=-np.inf)
                ge = len(c) - np.searchsorted(c, sub, side="left")
                p[np.ix_(md, mh)] = (1.0 + ge) / (len(c) + 1.0)
        p[np.isnan(s)] = 1.0
        return p


# ----------------------------------------------------------------------------------------- episodes
@dataclass
class EpisodeResult:
    observed: list[int]
    surviving: list[list[str]]       # survivors after each observation
    pvalues_true: list[float]        # p-value of the true class after each observation (NaN if unknown)
    status: str


class Falsifier:
    """Hypothesis set H (models), calibration and the design policies."""

    def __init__(self, models: list[HypothesisModel], cal: Calibration, resid_pool: np.ndarray, alpha: float,
                 option_order: np.ndarray, rng_seed: int = 0):
        self.models = models
        self.names = np.array([m.name for m in models])
        self.P = np.stack([m.proto for m in models])  # (H, n_opt, K)
        self.buckets = np.array([m.bucket for m in models])
        self.cal = cal
        self.noise = cal.noise
        self.resid_pool = resid_pool  # (n_opt, R, K) residual vectors for simulation (NaN rows dropped per option)
        self.alpha = alpha
        self.option_order = option_order
        self.seed = rng_seed

    # -- state statistics
    def stats(self, z: np.ndarray, opts: list[int], hyp: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Sufficient statistics (Q, b, A) of the drug under hypotheses ``hyp`` on ``opts``."""
        if not opts:
            n = len(hyp)
            return np.zeros(n), np.zeros(n), np.zeros(n)
        o = np.array(opts)
        v = self.noise.var[o]  # (S, K)
        mu = np.nan_to_num(self.P[hyp][:, o])  # (h, S, K)
        Q = np.sum(z[o] ** 2 / v)
        b = np.sum(mu * z[o][None] / v[None], axis=(1, 2))
        A = np.sum(mu * mu / v[None], axis=(1, 2))
        return np.full(len(hyp), Q), b, A

    def _scores(self, nll: np.ndarray, bad: np.ndarray) -> np.ndarray:
        """nll (D, Hn) -> scores; hypotheses without a prototype on the set get NaN (p = 1)."""
        nll = np.where(bad[None], np.nan, nll)
        if self.cal.mode == "relative":
            with np.errstate(invalid="ignore"):
                best = np.nanmin(np.where(np.isnan(nll), np.inf, nll), axis=1, keepdims=True)
            nll = nll - best
        return nll

    def score_all(self, z: np.ndarray, opts: list[int], hyp: np.ndarray) -> tuple[np.ndarray, float]:
        """Scores of the hypotheses ``hyp`` on ``opts`` and the drug's observed energy."""
        Q, b, A = self.stats(z, opts, hyp)
        nll, _ = score_from_stats(Q, b, A, self.noise.tau2, len(opts))
        bad = np.isnan(self.P[hyp][:, opts, 0]).any(axis=1)
        return self._scores(nll[None], bad)[0], float(Q[0] / len(opts))

    def pvalues(self, z: np.ndarray, opts: list[int], hyp: np.ndarray, step_cal: "StepCalibration | None" = None) -> np.ndarray:
        """p-values of the hypotheses ``hyp`` (which also define the relative score's reference set).
        With ``step_cal`` the episode calibration of step len(opts) is used instead of the
        exact-option-set calibration."""
        s, e = self.score_all(z, opts, hyp)
        if step_cal is not None:
            return step_cal.pvalues(len(opts) - 1, s[None], np.array([e]), self.buckets[hyp])[0]
        return self.cal.pvalues(s[None], np.array([e]), self.buckets[hyp], tuple(opts), hyp)[0]

    def view(self, cls: int, proto: np.ndarray, bucket: str) -> "Falsifier":
        """The same falsifier with hypothesis ``cls`` represented by ``proto`` (a calibration drug's
        leave-self-out prototype) and assigned ``bucket``; everything else is shared."""
        v = copy.copy(self)
        v.P = self.P.copy()
        v.P[cls] = proto
        v.buckets = self.buckets.copy()
        v.buckets[cls] = bucket
        return v

    # -- design policies
    def choose(self, policy: str, z: np.ndarray, opts: list[int], avail: list[int], surv: np.ndarray,
               p_surv: np.ndarray, rng: np.random.Generator, hyp: np.ndarray | None = None,
               n_sim: int = 4, max_h: int = 40) -> int:
        cand = [o for o in avail if o not in opts]
        hyp = np.arange(len(self.models)) if hyp is None else hyp
        if policy == "fixed":
            for o in self.option_order:
                if o in cand:
                    return int(o)
        if policy == "random":
            return int(rng.choice(cand))
        # weights over survivors: proportional to p-values (a pseudo-posterior; documented as such)
        w = p_surv / p_surv.sum() if p_surv.sum() > 0 else np.full(len(surv), 1 / len(surv))
        Qs, bs, As = self.stats(z, opts, surv)
        _, lam = score_from_stats(Qs, bs, As, self.noise.tau2, max(len(opts), 1))
        if not opts:
            lam = np.ones(len(surv))
        if policy == "magnitude":
            best, best_val = cand[0], -1.0
            for o in cand:
                mu = self.P[surv][:, o]
                ok = ~np.isnan(mu[:, 0])
                val = float(np.sum(w[ok] * lam[ok] * np.linalg.norm(mu[ok], axis=1)))
                if val > best_val:
                    best, best_val = o, val
            return int(best)
        if policy == "falsify":
            # simulate from survivors drawn by weight (all of them when few; max_h draws with
            # replacement and equal weight otherwise, so ties at p = 1 are not broken by name order)
            if len(surv) <= max_h:
                sim_idx, ws = np.arange(len(surv)), w
            else:
                sim_idx = rng.choice(len(surv), size=max_h, replace=True, p=w)
                ws = np.full(max_h, 1.0 / max_h)
            Qh, bh, Ah = self.stats(z, opts, hyp)  # current statistics under every hypothesis of H
            best, best_val = cand[0], np.inf
            for o in cand:
                new_opts = sorted(opts + [o])
                mu_s = self.P[surv][:, o]
                keep = [j for j in range(len(sim_idx)) if not np.isnan(mu_s[sim_idx[j], 0])]
                if not keep:
                    continue
                pool = self.resid_pool[o]
                Zs = np.concatenate([lam[sim_idx[j]] * mu_s[sim_idx[j]][None] + pool[rng.integers(0, len(pool), size=n_sim)]
                                     for j in keep])  # (D, K)
                wd = np.repeat(ws[keep], n_sim)
                wd = wd / wd.sum()
                v = self.noise.var[o]
                mu_h = self.P[hyp][:, o]
                mu_safe = np.nan_to_num(mu_h)
                Qn = Qh[0] + np.sum(Zs * Zs / v, axis=1)                     # (D,)
                bn = bh[None, :] + (Zs / v) @ mu_safe.T                        # (D, Hn)
                An = Ah[None, :] + np.sum(mu_safe * mu_safe / v, axis=1)[None]  # (1, Hn)
                nll, _ = score_from_stats(Qn[:, None], bn, An, self.noise.tau2, len(new_opts))
                bad = np.isnan(self.P[hyp][:, new_opts, 0]).any(axis=1)
                s = self._scores(nll, bad)
                p = self.cal.pvalues(s, Qn / len(new_opts), self.buckets[hyp], tuple(new_opts), hyp)
                val = float(np.sum(wd * np.sum(p > self.alpha, axis=1)))
                if val < best_val:
                    best, best_val = o, val
            return int(best)
        raise ValueError(f"unknown policy {policy}")

    def run(self, z: np.ndarray, avail: list[int], policy: str, budget: int, true_name: str | None,
            seed: int, hyp: np.ndarray | None = None, stop_on_single: bool = True,
            step_cal: StepCalibration | None = None) -> EpisodeResult:
        rng = np.random.default_rng(seed)
        hyp = np.arange(len(self.models)) if hyp is None else hyp
        opts: list[int] = []
        surv = hyp.copy()
        p_surv = np.ones(len(surv))
        survivors, ptrue = [], []
        status = "BUDGET_EXHAUSTED"
        for _ in range(min(budget, len(avail))):
            status = "BUDGET_EXHAUSTED"
            o = self.choose(policy, z, opts, avail, surv, p_surv, rng, hyp=hyp)
            opts.append(o)
            p_all = self.pvalues(z, opts, hyp, step_cal)
            keep = p_all > self.alpha
            surv = hyp[keep]
            p_surv = p_all[keep]
            survivors.append(list(self.names[surv]))
            if true_name is not None:
                ti = np.where(self.names[hyp] == true_name)[0]
                ptrue.append(float(p_all[ti[0]]) if len(ti) else float("nan"))
            if len(surv) == 0:
                status = "HYPOTHESIS_SET_EXHAUSTED"
                break
            if len(surv) == 1:
                status = "SINGLE_SURVIVOR"
                if stop_on_single:
                    break
        return EpisodeResult(observed=opts, surviving=survivors, pvalues_true=ptrue, status=status)


def episode_calibration(fz: Falsifier, policy: str, budget: int, seed: int = 0, max_rows: int | None = None) -> StepCalibration:
    """Run every calibration drug through ``policy`` in lockstep and tabulate own-class scores per step.

    Hypothesis set: all of ``fz``'s hypotheses. A calibration row is used while it has options left
    on which both its signature and its own prototype exist. ``max_rows`` subsamples rows (seeded)
    for speed during development; None uses all.
    """
    cal = fz.cal
    H = np.arange(len(fz.models))
    rows = np.arange(len(cal.Z))
    if max_rows is not None and max_rows < len(rows):
        rows = np.sort(np.random.default_rng(seed).choice(rows, size=max_rows, replace=False))
    state = {}
    for j in rows:
        c = int(cal.cal_class[j]) if cal.cal_class is not None else -1
        if c < 0:
            continue
        avail = [o for o in range(cal.Z.shape[1]) if cal.z_ok[j, o] and cal.o_ok[j, o]]
        if not avail:
            continue
        state[j] = {"opts": [], "surv": H.copy(), "psurv": np.ones(len(H)), "rng": np.random.default_rng(seed + int(j)),
                    "avail": avail, "cls": c}

    def view(j):  # built on demand: one prototype copy at a time, not one per calibration drug
        return fz.view(state[j]["cls"], cal.own_proto[j], str(cal.bucket[j]))
    nb = cal.n_bins
    tables, n_rows = [], []
    for k in range(budget):
        live = [j for j in state if len(state[j]["avail"]) > k]
        recs = {}
        for j in live:
            st, v = state[j], view(j)
            o = v.choose(policy, cal.Z[j], st["opts"], st["avail"], st["surv"], st["psurv"], st["rng"], hyp=H)
            st["opts"].append(o)
            recs[j] = v.score_all(cal.Z[j], st["opts"], H)
            del v
        energy = np.array([recs[j][1] for j in live])
        own = np.array([recs[j][0][state[j]["cls"]] for j in live])
        bks = np.array([str(cal.bucket[j]) for j in live])
        edges = np.quantile(energy, np.arange(1, nb) / nb) if nb > 1 and len(live) else np.array([])
        bins = np.searchsorted(edges, energy, side="right")
        table = {(bk, b): np.sort(own[(bks == bk) & (bins == b) & np.isfinite(own)]) for bk in BUCKETS for b in range(nb)}
        tables.append((table, edges))
        n_rows.append(len(live))
        sc_k = StepCalibration(tables=tables, n_bins=nb, n_rows=n_rows)
        for j in live:
            sc, e = recs[j]
            bk_j = fz.buckets.copy()
            bk_j[state[j]["cls"]] = str(cal.bucket[j])
            pv = sc_k.pvalues(k, sc[None], np.array([e]), bk_j[H])[0]
            keep = pv > fz.alpha
            state[j]["surv"], state[j]["psurv"] = H[keep], pv[keep]
    return StepCalibration(tables=tables, n_bins=nb, n_rows=n_rows)
