"""Competing numerical response programs, belief updating, acquisition policies and the campaign loop.

A response program explains the residual e = A - (A_ref + z1) of a new background from probe observations. Four kinds:
  null         e ~ N(0, sigma^2)                                   (the prior; nothing to learn)
  unexplained  e ~ N(0, (c sigma)^2)                               (lets every real program be contradicted: unresolved mismatch)
  cont         e = V z + noise, z ~ N(0, I)                        (continuous latent-factor / functional-fingerprint program)
  gate         e = sum_g beta_g (s_g - pi_g) + conj + noise        (discrete hidden gates s_g in {0,1} learned from released backgrounds)
Every program declares: legal measurement requirements (`probe_classes`), the state transformation (posterior over its hidden state given probes),
downstream predictions (mean/sd per pair), observable applicability conditions (`applicable`) and evidence dependencies (history cells, parent gates).
A *gate* is the reusable executable procedure: scope classes + orientation + diagnostic probe order + its state transform; programs compose gates by id.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path

import numpy as np

SVC = Path(__file__).resolve().parents[1] / "self_improving_virtual_cell_20261020"
if str(SVC) not in sys.path:
    sys.path.insert(0, str(SVC))

from svc_programs import fit_prior  # noqa: E402
from svc_world import SHORTLIST_K  # noqa: E402
from iv_gates import Gate, discover_gates, refit_gates  # noqa: E402,F401

U_INFLATION = 2.0
EPS_STOP = 0.0003
KG_SAMPLES = 128
KG_CANDIDATES = 40
MAX_GATES_PER_PROGRAM = 4


def sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=lambda a: np.round(np.asarray(a), 8).tolist()).encode()).hexdigest()[:12]


# ----------------------------------------------------------------------------- released-history view
@dataclass
class Models:
    """Everything derived from a set of released cells (labels fully visible)."""
    cells: tuple
    prior: object
    E: np.ndarray           # [n, h] residual vs A_ref + z1
    pc: np.ndarray          # pair class
    n_cls: int
    sigma: np.ndarray       # [n] pair residual sd (class-shrunk)
    version: str


def build_models(world, cells, static) -> Models:
    hist = world.history(list(cells))
    prior = fit_prior(hist)
    z1 = np.stack([prior.z1(hist.Aref[:, k], hist.amin[:, k], hist.amax[:, k]) for k in range(len(cells))], 1)
    E = hist.R - z1
    pc = static.pair_class
    n_cls = len(static.classes)
    sp2 = E.var(1) + 1e-6
    cls_var = np.array([sp2[pc == c].mean() if (pc == c).any() else sp2.mean() for c in range(n_cls)])
    sigma = np.sqrt(0.5 * sp2 + 0.5 * cls_var[pc])
    return Models(tuple(cells), prior, E, pc, n_cls, np.maximum(sigma, 0.01), sha([list(cells)]))


def class_matrix(M: Models, E=None):
    E = M.E if E is None else E
    return np.stack([E[M.pc == c].mean(0) if (M.pc == c).any() else np.zeros(E.shape[1]) for c in range(M.n_cls)])


# ----------------------------------------------------------------------------- programs
@dataclass
class Program:
    pid: str
    kind: str                   # null | unexplained | cont | gate
    gates: tuple = ()           # gate ids (composition by reference)
    k: int = 0                  # cont rank
    conj: tuple = ()            # pairs (gate_a, gate_b) with a fitted extra effect
    status: str = "valid"       # valid | provisional | noninferior | demonstrated | retired
    parents: tuple = ()
    gen: int = 0
    evidence: dict = field(default_factory=dict)

    def key(self):
        return sha({"kind": self.kind, "gates": sorted(self.gates), "k": self.k, "conj": sorted(self.conj)})


@dataclass
class Fitted:
    """A program fitted on a released history; all arrays needed to reproduce its predictions."""
    program: Program
    sigma: np.ndarray                      # [n]
    states: np.ndarray = None              # [S, G] state combinations (gate programs)
    logprior: np.ndarray = None            # [S]
    mu: np.ndarray = None                  # [S, n] mean residual per state
    V: np.ndarray = None                   # [n, k] aligned cont basis
    probe_classes: tuple = ()
    cells: tuple = ()
    version: str = ""
    gate_ids: tuple = ()
    ref_basis: np.ndarray = None
    gates: dict = None

    def applicable(self, anchors_lo, anchors_hi, n_probed_in_scope, min_probes=1):
        """Observable applicability: the new background's monotherapy range is inside the range seen in the history, and at least one legal diagnostic
        probe has been taken for gate programs."""
        return bool(n_probed_in_scope >= min_probes or self.program.kind in ("null", "unexplained", "cont"))


def align_basis(V_new: np.ndarray, V_ref: np.ndarray) -> np.ndarray:
    """Orthogonal Procrustes alignment, so that 'latent coordinate j' keeps its meaning across fitted bases."""
    u, _, vt = np.linalg.svd(V_ref.T @ V_new, full_matrices=False)
    return V_new @ (u @ vt).T


def fit_program(prog: Program, M: Models, gates: dict, ref_basis=None, E=None, static=None) -> Fitted | None:
    E = M.E if E is None else E
    n, h = E.shape
    if prog.kind in ("null", "unexplained"):
        sig = M.sigma * (U_INFLATION if prog.kind == "unexplained" else 1.0)
        return Fitted(prog, sig, version=M.version, cells=M.cells)
    if prog.kind == "cont":
        U, s, _ = np.linalg.svd(E - E.mean(1, keepdims=True), full_matrices=False)
        V = U[:, : prog.k] * s[: prog.k] / np.sqrt(h)
        if ref_basis is not None and ref_basis.shape == V.shape:
            V = align_basis(V, ref_basis)
        res = E - V @ np.linalg.lstsq(V, E, rcond=None)[0]
        sig = np.sqrt(0.5 * res.var(1) + 0.5 * (M.sigma ** 2)) * 1.0
        return Fitted(prog, np.maximum(sig, 0.01), V=V, version=M.version, cells=M.cells, ref_basis=V)
    inherited = [gates[gid] for gid in prog.gates]
    gs, S_h = refit_gates(M, inherited, E)
    if gs is None:
        return None
    st_h = S_h
    G = len(gs)
    S = np.array(list(product([0, 1], repeat=G)))
    pis = np.array([g.pi for g in gs])
    beta = np.stack([g.beta for g in gs])
    mu = (S - pis) @ beta
    conj_terms = {}
    for (a, b) in prog.conj:
        ia, ib = prog.gates.index(a), prog.gates.index(b)
        both = (st_h[:, ia] == 1) & (st_h[:, ib] == 1)
        if both.sum() >= 2:
            additive = (st_h[both] - pis) @ beta
            resid = (E[:, both] - additive.T).mean(1)
            cm = np.array([resid[M.pc == c].mean() if (M.pc == c).any() else 0.0 for c in range(M.n_cls)])
            se = np.array([resid[M.pc == c].std() / np.sqrt(max(both.sum(), 1)) + 1e-6 if (M.pc == c).any() else 1.0 for c in range(M.n_cls)])
            keep = np.abs(cm) / se > 3.0
            gamma = np.where(keep[M.pc], cm[M.pc], 0.0)
            if np.abs(gamma).max() > 0:
                conj_terms[(ia, ib)] = gamma
    for (ia, ib), gamma in conj_terms.items():
        mu = mu + np.outer(S[:, ia] * S[:, ib] - pis[ia] * pis[ib], gamma)
    fit_mu = (st_h - pis) @ beta
    for (ia, ib), gamma in conj_terms.items():
        fit_mu = fit_mu + np.outer(st_h[:, ia] * st_h[:, ib] - pis[ia] * pis[ib], gamma)
    res = E - fit_mu.T
    sig = np.maximum(np.sqrt(0.5 * res.var(1) + 0.5 * (M.sigma ** 2)), 0.01)
    logprior = (S * np.log(pis) + (1 - S) * np.log(1 - pis)).sum(1)
    classes = tuple(sorted({k for g in gs for k in g.scope}))
    fitted_gates = {g.gid: g for g in gs}
    return Fitted(prog, sig, S, logprior, mu, version=M.version, cells=M.cells, probe_classes=classes, gate_ids=tuple(prog.gates), gates=fitted_gates)


# ----------------------------------------------------------------------------- belief over competing programs
@dataclass
class Belief:
    """Mixture of Gaussian components (one per program-state; one per cont program), updated after every measurement."""
    base: np.ndarray                 # A_ref + z1 for the new background
    comps: list                      # dicts: prog, mean[n], var[n], logw, Vz/Sz for cont
    probed: list = field(default_factory=list)
    obs: list = field(default_factory=list)

    @property
    def logw(self):
        return np.array([c["logw"] for c in self.comps])

    def weights(self):
        lw = self.logw
        w = np.exp(lw - lw.max())
        return w / w.sum()

    def program_weights(self):
        w = self.weights()
        out = {}
        for wj, c in zip(w, self.comps):
            out[c["prog"]] = out.get(c["prog"], 0.0) + float(wj)
        return out

    def matrices(self):
        M = np.stack([c["mean"] for c in self.comps])
        V = np.stack([c["var"] for c in self.comps])
        return M, V

    def mixture(self):
        w = self.weights()
        M, V = self.matrices()
        mean = w @ M
        var = w @ (V + (M - mean) ** 2)
        return mean, var

    def observe(self, p: int, y_resid: float):
        for c in self.comps:
            m, v = c["mean"][p], c["var"][p]
            c["logw"] += -0.5 * ((y_resid - m) ** 2 / v + np.log(2 * np.pi * v))
            if c.get("Vz") is not None:
                gain = (c["Vz"] @ c["Sz"] @ c["Vz"][p]) / v
                c["mean"] = c["mean"] + gain * (y_resid - m)
                Vp = c["Vz"][p]
                c["Sz"] = c["Sz"] - np.outer(c["Sz"] @ Vp, Vp @ c["Sz"]) / v
                c["var"] = c["sig2"] + np.einsum("ik,kl,il->i", c["Vz"], c["Sz"], c["Vz"])
                c["mean"][p] = y_resid
            else:
                pass
        self.probed.append(int(p))
        self.obs.append(float(y_resid))


def make_belief(fits: list, base: np.ndarray, prog_prior: dict | None = None) -> Belief:
    comps = []
    for f in fits:
        pr = f.program
        lp = np.log((prog_prior or {}).get(pr.kind, 1.0))
        s2 = f.sigma ** 2
        if pr.kind in ("null", "unexplained"):
            comps.append({"prog": pr.pid, "mean": np.zeros(len(base)), "var": s2.copy(), "logw": lp, "Vz": None})
        elif pr.kind == "cont":
            k = f.V.shape[1]
            Sz = np.eye(k)
            comps.append({"prog": pr.pid, "mean": np.zeros(len(base)), "var": s2 + np.einsum("ik,kl,il->i", f.V, Sz, f.V), "logw": lp, "Vz": f.V, "Sz": Sz, "sig2": s2})
        else:
            for si in range(len(f.states)):
                comps.append({"prog": pr.pid, "mean": f.mu[si].copy(), "var": s2.copy(), "logw": lp + f.logprior[si], "Vz": None, "state": tuple(int(x) for x in f.states[si])})
    return Belief(base, comps)


# ----------------------------------------------------------------------------- acquisition policies
def shortlist_scores(belief: Belief, pool: np.ndarray, recorded: dict):
    mean, _ = belief.mixture()
    score = belief.base + mean
    for p, v in recorded.items():
        score = score.copy()
        score[p] = v
    s = np.where(pool, score, -np.inf)
    return s


def top_k(score: np.ndarray, k: int = SHORTLIST_K):
    idx = np.lexsort((np.arange(len(score)), -score))
    return idx[:k]


def kg_values(belief: Belief, cand: np.ndarray, pool: np.ndarray, recorded: dict, rng, samples: int = KG_SAMPLES):
    """Preposterior decision value of each candidate probe (knowledge-gradient approximation).

    Worlds are sampled from the current belief (component ~ weights, diagonal Gaussian predictive); for a candidate probe p its simulated outcome updates the
    component weights (and the cont-program mean via the exact Kalman gain); the value is the expected change in the true shortlist utility of the re-ranked
    shortlist, where a queried candidate keeps its recorded value. Approximation: independent diagonal draws; cont posterior covariance is not propagated beyond
    the gain; states within gate programs are updated through component weights only."""
    w = belief.weights()
    Mx, Vx = belief.matrices()
    J, n = Mx.shape
    js = rng.choice(J, size=samples, p=w)
    truth = Mx[js] + np.sqrt(Vx[js]) * rng.standard_normal((samples, n))              # [S, n] residual worlds
    base = belief.base
    cur_score = shortlist_scores(belief, pool, recorded)
    cur_top = top_k(cur_score)
    util0 = (base + truth)[:, cur_top].mean(1)
    cont = [j for j, c in enumerate(belief.comps) if c.get("Vz") is not None]
    vals = np.zeros(len(cand))
    changed = []
    for ci, p in enumerate(cand):
        y = truth[:, p]
        ll = -0.5 * ((y[:, None] - Mx[:, p][None, :]) ** 2 / Vx[:, p][None, :] + np.log(Vx[:, p])[None, :])
        lw = np.log(w + 1e-300)[None, :] + ll
        lw -= lw.max(1, keepdims=True)
        W2 = np.exp(lw)
        W2 /= W2.sum(1, keepdims=True)
        mean2 = W2 @ Mx
        for j in cont:
            c = belief.comps[j]
            gain = (c["Vz"] @ c["Sz"] @ c["Vz"][p]) / Vx[j, p]
            mean2 += W2[:, [j]] * np.outer(y - Mx[j, p], gain)
        score2 = np.where(pool, base[None, :] + mean2, -np.inf)
        for q, v in recorded.items():
            score2[:, q] = v
        if pool[p]:
            score2[:, p] = base[p] + y                                            # queried candidate keeps its recorded value
        top2 = np.argsort(-score2, axis=1)[:, :SHORTLIST_K]
        u2 = np.take_along_axis(base[None, :] + truth, top2, 1).mean(1)
        vals[ci] = float((u2 - util0).mean())
        changed.append(sorted({int(q) for q in top2.ravel()} - {int(q) for q in cur_top}))
    return vals, changed, cur_top


def bald_values(belief: Belief, cand: np.ndarray):
    """Hypothesis discrimination without decision weighting: 0.5 log(1 + between-component variance / within-component variance)."""
    w = belief.weights()
    Mx, Vx = belief.matrices()
    mean = w @ Mx
    between = w @ (Mx - mean) ** 2
    within = w @ Vx
    return 0.5 * np.log1p(between[cand] / within[cand])


def aopt_values(belief: Belief, cand: np.ndarray):
    """Greedy A-optimal information on the continuous latent state of the cont programs (conventional matrix-completion acquisition)."""
    best = np.zeros(len(cand))
    for c in belief.comps:
        if c.get("Vz") is None:
            continue
        SV = c["Sz"] @ c["Vz"][cand].T
        best = np.maximum(best, (SV ** 2).sum(0) / (np.einsum("ik,kl,il->i", c["Vz"][cand], c["Sz"], c["Vz"][cand]) + c["sig2"][cand]))
    return best


POLICIES = ("kg", "bald", "variance", "coverage", "random", "exploit", "aopt")


def pick(policy: str, belief: Belief, legal: np.ndarray, pool: np.ndarray, recorded: dict, rng, classes: np.ndarray, plan=None):
    """Return (pair or None, record). None = stop (no probe has positive decision value)."""
    avail = legal.copy()
    for p in belief.probed:
        avail[p] = False
    idx = np.nonzero(avail)[0]
    if len(idx) == 0:
        return None, {"stop": "no legal action"}
    mean, var = belief.mixture()
    score = belief.base + mean
    if policy == "random":
        return int(rng.choice(idx)), {}
    if policy == "exploit":
        cand = idx[np.lexsort((idx, -score[idx]))]
        return int(cand[0]), {}
    if policy == "variance":
        return int(idx[np.lexsort((idx, -var[idx]))][0]), {}
    if policy == "coverage":
        counts = np.bincount([classes[p] for p in belief.probed], minlength=classes.max() + 1)
        order = np.lexsort((idx, -var[idx], counts[classes[idx]]))
        return int(idx[order][0]), {}
    # candidate screen: top by between-component variance and (end-to-end) by predicted score
    w = belief.weights()
    Mx, Vx = belief.matrices()
    between = w @ (Mx - w @ Mx) ** 2
    disc = between[idx] / np.maximum(w @ Vx, 1e-12)[idx]
    cand = list(idx[np.argsort(-disc)[: KG_CANDIDATES // 2 + 4]])
    inpool = idx[pool[idx]]
    if len(inpool):
        cand += list(inpool[np.argsort(-score[inpool])[: KG_CANDIDATES // 2]])
    cand = np.array(sorted(set(int(c) for c in cand)))
    if policy == "bald":
        v = bald_values(belief, cand)
        return int(cand[np.argmax(v)]), {}
    if policy == "aopt":
        v = aopt_values(belief, cand)
        if v.max() <= 0:
            return int(idx[np.lexsort((idx, -var[idx]))][0]), {"fallback": "variance"}
        return int(cand[np.argmax(v)]), {}
    vals, changed, cur_top = kg_values(belief, cand, pool, recorded, rng)
    j = int(np.argmax(vals))
    order = np.argsort(-vals)[:3]
    pw = belief.program_weights()
    p = int(cand[j])
    per_prog = {}
    for c, wj in zip(belief.comps, w):
        d = per_prog.setdefault(c["prog"], [0.0, 0.0, 0.0])
        d[0] += wj
        d[1] += wj * c["mean"][p]
        d[2] += wj * (c["var"][p] + c["mean"][p] ** 2)
    pred = {k: {"weight": v[0], "mean": v[1] / max(v[0], 1e-12), "sd": float(np.sqrt(max(v[2] / max(v[0], 1e-12) - (v[1] / max(v[0], 1e-12)) ** 2, 0)))} for k, v in per_prog.items()}
    rec = {"program_weights": pw, "competing_predictions_for_probe": pred, "probe": p, "kg_score": float(vals[j]),
           "alternatives": [{"pair": int(cand[o]), "kg": float(vals[o])} for o in order], "nominations_that_could_change": changed[j],
           "current_shortlist": [int(q) for q in cur_top]}
    if vals[j] < EPS_STOP:
        inpool = idx[pool[idx]]
        if len(inpool):                                    # alternative action: spend the remaining budget on direct measurement of the best candidate
            rec["alternative_action"] = "direct measurement (no probe has decision value above the stopping threshold)"
            return int(inpool[np.lexsort((inpool, -score[inpool]))][0]), rec
        rec["stop"] = "no probe has decision value above the stopping threshold"
        return None, rec
    return p, rec


# ----------------------------------------------------------------------------- campaign
def run_campaign(world, static, cell, fits: list, base_pred: tuple, policy: str, budget: int, contract: str, mask, rng, prog_prior=None, fixed_probes=None):
    """Execute programs on one new background. Every probe goes through the ledgered Campaign; recorded values replace predictions in the shortlist."""
    camp = world.campaign(cell, budget, probe_mask=mask)
    pool = np.ones(static.n, bool) if mask is None else ~mask
    legal = np.ones(static.n, bool) if mask is None else mask.copy()
    base = camp.Aref + base_pred[0]
    belief = make_belief(fits, base, prog_prior)
    classes = static.pair_class
    trace, recorded = [], {}
    steps = fixed_probes if fixed_probes is not None else range(budget)
    for t in steps:
        if fixed_probes is not None:
            p, rec = int(t), {"fixed": True}
        else:
            p, rec = pick(policy, belief, legal, pool, recorded, rng, classes)
        if p is None:
            rec["stopped_at_step"] = len(belief.probed)
            trace.append(rec)
            break
        val = camp.query([p], "probe" if contract != "E" else "act")[p]
        belief.observe(p, val - base[p])
        if pool[p]:
            recorded[p] = val
        pw = belief.program_weights()
        rec["after"] = {"program_weights": pw, "mismatch": any(c.get("prog", "").startswith("U") and pw.get(c["prog"], 0) > 0.5 for c in belief.comps)}
        trace.append(rec)
    score = shortlist_scores(belief, pool, recorded)
    nominated = [int(q) for q in top_k(score)]
    return camp, nominated, belief, trace
