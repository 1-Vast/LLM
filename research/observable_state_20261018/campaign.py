"""Series-to-context research campaign: Gaussian-belief core, runner and grader.

File summary
- Path: research/observable_state_20261018/campaign.py
- Purpose: one campaign = `n` compounds x `L` lines grouped into contexts (pools or lineage groups), a total budget of
  reads (a read = one compound in one context, hypothetical pool well), `rounds` adaptive rounds, and a final output of
  (nomination list, progression list). Compounds do NOT receive identical measurements: a policy allocates reads across
  compound-context pairs each round from the current belief only.
- The core is data-free (a Gaussian belief per compound: prior mean `m0[i]`, shared covariance `S`, probe noise variance
  `noise_var`). `real_adapter.py` builds it from a PRISM fold; tests use a synthetic world. Hidden outcomes enter only
  through the `observe` callable (the oracle) and through `grade`, which a policy never receives.
- Round plan: round 0 is a fixed seed read (every compound reads `seed_context`) so all arms share the first
  evidence; the remaining reads are spread over the other rounds. Equal total reads for every policy.
- Interfaces: `Campaign`, `run_campaign`, `grade`, `grader_for`.
- Scoring default: score = G - posterior mean (larger = stronger selective drop), the mean selective residual; the adapter
  may supply the repository's `call_score` instead. Nomination: `follow_up` pairs per campaign, at most `cap` per
  compound, unmeasured pairs on admissible lines only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Campaign:
    m0: np.ndarray            # (n, L) prior mean profiles
    S: np.ndarray             # (L, L) shared prior covariance
    noise_var: float
    contexts: list            # list of int arrays of line indices (admissible lines of each context)
    avail: np.ndarray         # (L,) admissible lines
    G: np.ndarray             # (L,) generic profile (reference for the selective residual)
    reads_per_compound: int = 3
    rounds: int = 3
    seed_context: int = 0
    follow_up: int = 32
    cap: int = 3
    progress_k: int = 8
    score_fn: object = None   # optional callable(campaign, i, mean) -> (L,) score
    # belief state ---------------------------------------------------------------------------
    done: np.ndarray = field(init=False)
    obs_lines: list = field(init=False)
    obs_y: list = field(init=False)
    _cov: dict = field(init=False, default_factory=dict)
    ledger: dict = field(init=False, default_factory=lambda: {"assay_wells": 0, "lines_read": 0, "rounds": 0, "logical_queries": 0})

    def __post_init__(self):
        n = self.m0.shape[0]
        self.done = np.zeros((n, len(self.contexts)), bool)
        self.obs_lines = [np.zeros(0, int) for _ in range(n)]
        self.obs_y = [np.zeros(0) for _ in range(n)]

    # ------------------------------------------------------------------ belief
    @property
    def n(self):
        return self.m0.shape[0]

    def cov(self, i):
        """Posterior covariance of compound i (depends on which lines were read, not on the outcomes)."""

        if i not in self._cov:
            P = self.obs_lines[i]
            if len(P) == 0:
                self._cov[i] = self.S
            else:
                A = self.S[np.ix_(P, P)] + self.noise_var * np.eye(len(P))
                self._cov[i] = self.S - self.S[:, P] @ np.linalg.solve(A, self.S[P, :])
        return self._cov[i]

    def cov_after(self, i, lines, cov=None):
        """Posterior covariance if `lines` were also read (no outcome needed)."""

        C = self.cov(i) if cov is None else cov
        lines = np.asarray(lines, int)
        if len(lines) == 0:
            return C
        A = C[np.ix_(lines, lines)] + self.noise_var * np.eye(len(lines))
        return C - C[:, lines] @ np.linalg.solve(A, C[lines, :])

    def mean(self, i):
        P, y = self.obs_lines[i], self.obs_y[i]
        ok = np.isfinite(y)
        P, y = P[ok], y[ok]
        if len(P) == 0:
            return self.m0[i].copy()
        A = self.S[np.ix_(P, P)] + self.noise_var * np.eye(len(P))
        out = self.m0[i] + self.S[:, P] @ np.linalg.solve(A, y - self.m0[i][P])
        out[P] = y  # probed values plugged in, as in the repository's conditional mean
        return out

    def score(self, i):
        m = self.mean(i)
        return self.score_fn(self, i, m) if self.score_fn else self.G - m

    def apply_read(self, i, c, y):
        lines = self.contexts[c]
        self.obs_lines[i] = np.concatenate([self.obs_lines[i], lines])
        self.obs_y[i] = np.concatenate([self.obs_y[i], np.asarray(y, float)])
        self.done[i, c] = True
        self._cov.pop(i, None)
        self.ledger["assay_wells"] += 1
        self.ledger["lines_read"] += len(lines)

    def queried_mask(self):
        q = np.zeros((self.n, self.m0.shape[1]), bool)
        for i in range(self.n):
            q[i, self.obs_lines[i]] = True
        return q

    # ------------------------------------------------------------------ decisions
    def nominate(self):
        """Top `follow_up` unmeasured admissible pairs, at most `cap` per compound. Returns [(i, line)]."""

        q = self.queried_mask()
        sc = np.stack([self.score(i) for i in range(self.n)])
        sc = np.where(self.avail[None, :] & ~q, sc, -np.inf)
        order = np.argsort(-sc, axis=None, kind="stable")
        out, per = [], {}
        for k in order:
            i, l = divmod(int(k), sc.shape[1])
            if not np.isfinite(sc[i, l]) or len(out) >= self.follow_up:
                break
            if per.get(i, 0) >= self.cap:
                continue
            per[i] = per.get(i, 0) + 1
            out.append((i, l))
        return out

    def progression(self, picks=None):
        """Compounds to progress: the `progress_k` with the largest summed nominated scores (a function of the belief only)."""

        picks = self.nominate() if picks is None else picks
        sc = np.zeros(self.n)
        for i, l in picks:
            sc[i] += self.score(i)[l]
        order = np.argsort(-sc, kind="stable")
        return [int(i) for i in order[: self.progress_k]]

    def decisions(self):
        picks = self.nominate()
        return {"nominations": [(int(i), int(l)) for i, l in picks], "progression": self.progression(picks),
                "reads": [(int(i), int(c)) for i, c in zip(*np.where(self.done))], "ledger": dict(self.ledger)}


# ---------------------------------------------------------------------- runner
def round_sizes(n, reads_per_compound, rounds):
    """Reads after the seed round, spread as evenly as possible over the remaining rounds."""

    rest = n * (reads_per_compound - 1)
    base, extra = divmod(rest, rounds - 1)
    return [base + (1 if r < extra else 0) for r in range(rounds - 1)]


def run_campaign(camp: Campaign, policy, observe) -> dict:
    """Seed round (fixed), then policy-chosen rounds. `observe(i, lines) -> y` is the oracle; the policy never sees it."""

    for i in range(camp.n):
        camp.apply_read(i, camp.seed_context, observe(i, camp.contexts[camp.seed_context]))
    camp.ledger["rounds"] += 1
    for size in round_sizes(camp.n, camp.reads_per_compound, camp.rounds):
        plan = policy.plan_round(camp, size)
        seen = set()
        for i, c in plan:
            if camp.done[i, c] or (i, c) in seen:
                raise ValueError(f"policy requested an already-read or duplicate pair {(i, c)}")
            seen.add((i, c))
        if len(plan) != size:
            raise ValueError(f"policy returned {len(plan)} reads, budget is {size}")
        for i, c in plan:
            camp.apply_read(i, c, observe(i, camp.contexts[c]))
        camp.ledger["rounds"] += 1
    camp.ledger["logical_queries"] = int(camp.done.sum())
    return camp.decisions()


# ---------------------------------------------------------------------- grading (reads the hidden side)
def grade(decisions: dict, truth: np.ndarray, avail: np.ndarray, false_reject_events: int = 2) -> dict:
    """Qualified nominations on unmeasured pairs, false progression and false rejection. `truth` is (n, L) bool."""

    hits = sum(bool(truth[i, l]) for i, l in decisions["nominations"])
    prog = set(decisions["progression"])
    ev = (truth & avail[None, :]).sum(1)
    false_prog = sum(1 for i in prog if ev[i] == 0)
    false_rej = sum(1 for i in range(truth.shape[0]) if i not in prog and ev[i] >= false_reject_events)
    return {"hits": int(hits), "listed": len(decisions["nominations"]), "unique_compounds": len({i for i, l in decisions["nominations"] if truth[i, l]}),
            "false_progression": int(false_prog), "false_rejection": int(false_rej), "assay_wells": decisions["ledger"]["assay_wells"]}


def grader_for(truth: np.ndarray, avail: np.ndarray):
    """Hidden-utility callable for `masked_interface.MaskedOutcomeInterface`: decisions -> scalar hits (search/select),
    full record for transfer. The policy and the agent hold no reference to `truth`."""

    def f(role, decisions):
        g = grade(decisions, truth, avail)
        return g if role == "transfer" else float(g["hits"])

    return f
