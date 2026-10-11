"""Block P campaign engine: one discovery campaign = (target lineage, library), run by one arm.

State (persisted per campaign as a JSON ledger by the runner):
* ``known``: reference compounds plus every compound screened so far;
* ``screened``: list of (round, compound) in screening order;
* ``Y``: the profiles the arm *believes* for known compounds. It equals the truth except in the
  feedback-permutation controls, where a batch's revealed profiles are permuted among the batch;
* ``predictions``: each arm's pre-reveal P(hit) for every compound it screened (prequential log);
* ``refusals``: named reasons when an arm's choice is invalid (``LLM_INVALID_SELECTION``,
  ``LLM_CALL_FAILED``) and what replaced it.

Scoring always uses the true hit labels of the compounds actually screened.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

import world as WM


@dataclass
class State:
    t: int
    ref: np.ndarray
    pool: np.ndarray
    budget: int
    batch: int
    known: list = field(default_factory=list)
    Y: np.ndarray | None = None
    left: list = field(default_factory=list)
    screened: list = field(default_factory=list)
    predictions: list = field(default_factory=list)
    refusals: list = field(default_factory=list)
    round: int = 0

    @classmethod
    def start(cls, U, t, ref, pool, budget, batch):
        s = cls(t=t, ref=np.asarray(ref), pool=np.asarray(pool), budget=budget, batch=batch)
        s.known = list(ref)
        s.Y = U.P[ref].copy()
        s.left = list(pool)
        return s

    def reveal(self, U, picks, permute_rng=None):
        """Screen ``picks``: append to known with their (true or, in the control, permuted) profiles."""
        prof = U.P[np.asarray(picks)].copy()
        if permute_rng is not None and len(picks) > 1:
            prof = prof[permute_rng.permutation(len(picks))]
        for c in picks:
            self.left.remove(int(c))
            self.screened.append((self.round, int(c)))
        self.known += [int(c) for c in picks]
        self.Y = np.concatenate([self.Y, prof])
        self.round += 1

    @property
    def n_screened(self):
        return len(self.screened)


def greedy(scores, cand, k, rng):
    return list(np.asarray(cand)[np.argsort(-(scores + 1e-12 * rng.standard_normal(len(cand))))[:k]])


def run_stack_arm(U, st: State, sources, mode, rng, prior=None, permute_rng=None, C=0.3):
    """Deterministic stack arms. mode: 'static' (fit on reference, one batch, no feedback),
    'featfb' (weights fixed, predictions from growing known set), 'refit' (weights refit each round)."""
    model = WM.Stack(U, sources, C=C, prior=prior).fit(np.array(st.known), Y=st.Y)
    if mode == "static":
        cand = np.array(st.left)
        p = model.score(np.array(st.known), cand, Y=st.Y)[:, st.t]
        picks = greedy(p, cand, st.budget, rng)
        st.predictions += [(int(c), float(p[list(cand).index(c)])) for c in picks]
        st.reveal(U, picks, permute_rng)
        return st
    while st.n_screened < st.budget:
        if mode == "refit" and st.n_screened:
            model = WM.Stack(U, sources, C=C, prior=prior).fit(np.array(st.known), Y=st.Y)
        cand = np.array(st.left)
        p = model.score(np.array(st.known), cand, Y=st.Y)[:, st.t]
        picks = greedy(p, cand, min(st.batch, st.budget - st.n_screened), rng)
        pos = {c: i for i, c in enumerate(cand)}
        st.predictions += [(int(c), float(p[pos[c]])) for c in picks]
        st.reveal(U, picks, permute_rng)
    return st


def hits_found(U, st: State, H=None):
    H = U.hits() if H is None else H
    sel = np.array([c for _, c in st.screened], int)
    return int(H[sel, st.t].sum()) if len(sel) else 0
