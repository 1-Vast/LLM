"""Per-line predictors updated by purchased readouts, adaptive acquisition, and complete campaigns.

File summary
- Path: research/program_revision_20261017/policy.py
- Purpose: the decision layer shared by Stage B (adaptive-acquisition comparator) and Stage C
  (complete policies under equal well budgets). Every readout is a purchased measurement of a
  real (drug, line) pair; nothing predicted is ever scored as observed.
- `LinePredictor`: the strong model of a `ContextFold` (trained on its training lines) for one
  of its target lines, optionally with a fitted program library. Readouts update the line state
  by Bayesian linear regression on y - a_d - correction_d; the probed drug's own readout is fused
  directly. Predictive variance = irreducible per-drug variance + state uncertainty.
- Readouts and costs (frozen in PROTOCOL.md):
  - probe: X1 of a source drug on the line, 1 well, noise 0.67 x replicate variance;
  - confirmation: X2 and X3 of the pair, 2 wells; the endpoint outcome (`Domain.hit`) and,
    as a readout, their mean with noise replicate variance / n_available. A failed pair (both
    missing) is charged and returns nothing.
- Acquisition (`afa_select`): greedy decision-weighted variance reduction over the current
  top-30 candidates (weight = squared density of the hit-probability argument), the
  conventional myopic value-of-information heuristic. One well per round.
- Campaigns (`run_campaign`): a policy spec (probe design, confirmation batch sizes, budget)
  executed on one line; returns confirmed hits, wells, rounds and the full action trace.
- Interfaces: `LinePredictor`, `afa_select`, `run_campaign`, `POLICIES`.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm

from vc import LineContext, blr, hit_probability

PROBE_NOISE = 0.67
CANDIDATES_FOR_AFA = 30


class LinePredictor:
    def __init__(self, fold, lib=None):
        dom, m = fold.dom, fold.model
        self.fold, self.dom, self.m = fold, dom, m
        W, mu_z, mu_s, C0, _ = m._lp
        Z = dom.line_Z(fold.target, fold.info, fold.lin_cols)
        self.m0 = (mu_s + (Z - mu_z) @ W) if W is not None else np.repeat(mu_s[None], len(fold.target), 0)
        self.C0 = C0
        self.H = np.column_stack([np.ones(len(m.a)), m.U])
        self.a = m.a
        self.drows = fold.drows
        self.pos = {d: i for i, d in enumerate(self.drows)}
        # irreducible variance: cross-fitted residual variance net of the average state uncertainty
        # that remained under the fold's own design (fold.C_target), floored at the in-sample variance
        sv = np.einsum("di,lij,dj->d", self.H, fold.C_target, self.H) / len(fold.target)
        self.s2 = np.maximum(fold.oos_var - sv, m.resid_var) + dom.rep_var[self.drows] / 6.0
        self.lib = None
        if lib is not None and lib.programs:
            self.lib = lib.copy()
            ctx_tr, _ = fold.contexts()
            self.lib.fit(fold.R_train, self.lib.states(ctx_tr), dom.df, self.drows)
            self.probe_ref = {k: float(np.nanmean(v)) for k, v in fold.probe_train.items()}
        self.thr = dom.thr[self.drows]

    def _correction(self, j, probes: dict, b: float) -> np.ndarray:
        if self.lib is None:
            return np.zeros(len(self.drows))
        c = self.fold.target[j]
        vals = {k: np.array([probes.get(k, self.probe_ref.get(k, 0.0))]) for k in self.probe_ref}
        ctx = LineContext(self.dom.lf, np.array([c]), vals, np.array([b]))
        return self.lib.correction(self.lib.states(ctx), self.dom.df, self.drows, novel=False)[:, 0]

    def predict(self, j, readouts):
        """readouts: list of (drug_row, value, noise, kind) on target line j. Returns mean, var, state."""

        probes = {}
        core = self.dom.drugs.core.to_numpy()
        for d, v, _, kind in readouts:
            if kind == "probe":
                probes[core[d]] = v
        s, C = self.m0[j], self.C0
        corr = self._correction(j, probes, float(s[0]))
        if readouts:
            idx = np.array([self.pos[d] for d, _, _, _ in readouts], int)
            y = np.array([v for _, v, _, _ in readouts]) - self.a[idx] - corr[idx]
            noise = np.array([n for _, _, n, _ in readouts]) + self.m.resid_var[idx]
            s, C = blr(self.m0[j], self.C0, self.H[idx], y, noise)
            corr = self._correction(j, probes, float(s[0]))
        mean = self.a + self.H @ s + corr
        var = self.s2 + np.einsum("di,ij,dj->d", self.H, C, self.H)
        # own readouts fused directly (a drug's own measurement on this line)
        for d, v, n, _ in readouts:
            i = self.pos[d]
            pv = 1.0 / (1.0 / var[i] + 1.0 / n)
            mean[i] = pv * (mean[i] / var[i] + v / n)
            var[i] = pv
        return mean, var, (s, C)

    def score(self, j, readouts):
        mean, var, st = self.predict(j, readouts)
        return hit_probability(mean, var, self.thr), mean, var, st


def probe_readout(dom, d, c):
    v = dom.X1[d, c]
    return (d, float(v), PROBE_NOISE * float(dom.rep_var[d]), "probe") if np.isfinite(v) else None


def confirmation_readout(dom, d, c):
    vals = [x for x in (dom.X2[d, c], dom.X3[d, c]) if np.isfinite(x)]
    if not vals:
        return None
    return (d, float(np.mean(vals)), float(dom.rep_var[d]) / len(vals), "confirm")


def afa_select(pred: LinePredictor, j, readouts, used: set):
    """Next probe: maximise decision-weighted variance reduction over the current top candidates."""

    sc, mean, var, (s, C) = pred.score(j, readouts)
    top = np.argsort(-sc)[:CANDIDATES_FOR_AFA]
    z = (pred.thr[top] - mean[top]) / np.sqrt(var[top])
    w = norm.pdf(z) ** 2 / var[top]
    HC = pred.H[top] @ C                                   # (top, r+1)
    q = np.einsum("ij,ij->i", pred.H @ C, pred.H)          # prior var of each candidate probe's state part
    noise = PROBE_NOISE * pred.dom.rep_var[pred.drows] + pred.m.resid_var
    cross = HC @ pred.H.T                                  # (top, drugs)
    gain = (w[:, None] * cross ** 2).sum(0) / (q + noise)
    gain[[pred.pos[d] for d in used if d in pred.pos]] = -np.inf
    return int(pred.drows[int(np.argmax(gain))])


def run_campaign(pred: LinePredictor, j, spec: dict, fixed_probes=()):
    """Execute one policy on target line j. spec keys: probes ('none'|'fixed'|'afa'), n_probes,
    batches (list of confirmation batch sizes), budget (wells)."""

    dom = pred.dom
    c = int(pred.fold.target[j])
    readouts, trace = [], []
    wells, rounds = 0, 0
    used = set()
    if spec["probes"] == "fixed":
        rounds += 1
        for core in fixed_probes:
            d = dom.drug_index[core]
            wells += 1
            used.add(d)
            r = probe_readout(dom, d, c)
            trace.append({"round": rounds, "action": "probe", "drug": core, "observed": r is not None})
            if r:
                readouts.append(r)
    elif spec["probes"] == "afa":
        for _ in range(spec["n_probes"]):
            rounds += 1
            d = afa_select(pred, j, readouts, used)
            wells += 1
            used.add(d)
            r = probe_readout(dom, d, c)
            trace.append({"round": rounds, "action": "probe", "drug": dom.drugs.core[d], "observed": r is not None})
            if r:
                readouts.append(r)
    confirmed = set()
    hits = 0
    first3 = None
    for size in spec["batches"]:
        if wells + 2 > spec["budget"]:
            break
        rounds += 1
        sc, mean, var, _ = pred.score(j, readouts)
        order = np.lexsort((dom.tie_drug[pred.drows], -sc))
        batch = []
        for i in order:
            d = int(pred.drows[i])
            if d in confirmed:
                continue
            if len(batch) >= size or wells + 2 > spec["budget"]:
                break
            batch.append((d, float(sc[i])))
            wells += 2
        for d, p in batch:
            confirmed.add(d)
            h = bool(dom.hit[d, c])
            known = bool(dom.known[d, c])
            hits += h
            if hits >= 3 and first3 is None:
                first3 = wells
            r = confirmation_readout(dom, d, c)
            trace.append({"round": rounds, "action": "confirm", "drug": dom.drugs.core[d], "p_hit": round(p, 4),
                          "known": known, "hit": h})
            if r:
                readouts.append(r)
    unknown = sum(1 for t in trace if t["action"] == "confirm" and not t["known"])
    return {"hits": int(hits), "wells": int(wells), "rounds": int(rounds), "confirmed": len(confirmed),
            "unknown": int(unknown), "wells_to_3_hits": first3, "trace": trace}


BUDGET = 28
POLICIES = {
    # equal budget of 28 wells per line (frozen); rounds differ and are reported
    "fixed_probes_then_confirm": {"probes": "fixed", "n_probes": 8, "batches": [10], "budget": BUDGET},
    "fixed_probes_feedback": {"probes": "fixed", "n_probes": 8, "batches": [5, 5], "budget": BUDGET},
    "exploit_first_feedback": {"probes": "none", "n_probes": 0, "batches": [5, 5, 4], "budget": BUDGET},
    "afa_probes_feedback": {"probes": "afa", "n_probes": 8, "batches": [5, 5], "budget": BUDGET},
}
