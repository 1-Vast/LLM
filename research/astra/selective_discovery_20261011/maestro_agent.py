"""The MAESTRO arm: an autonomous campaign system over the dual core.

Components, each separable and each logged:

* **Persistent state** (`campaign.State`): the reference set, every compound screened, the profiles
  believed for them, every pre-reveal prediction, and named refusals.
* **World model** (`world.Stack`): one pooled stacked hit model over five evidence sources plus the
  gated LLM prior, refit on the reference set and everything screened so far. Per-lineage model
  arbitration was tested and rejected (feasibility F5), so the blend stays at the feature level.
* **Planning**: each batch is split between two streams.
  * *confirm*: the best overall ranking;
  * *explore*: the best ranking **restricted to mechanism classes with no known selective member**
    for this lineage, scored by the virtual cell, which is the only source that reaches across
    classes (block N; feasibility F8).
  The split starts at `explore_seats` of each batch and moves with each stream's observed yield
  (Beta posterior means), so a stream that stops paying loses seats. `NO_NOVEL_CANDIDATE` returns
  the explore seats to confirm.
* **Verification**: a hit is only *verified* when the independent secondary screen agrees; absent
  compounds are refused `SECONDARY_ABSENT` rather than counted either way. Verification never feeds
  back into selection, so it cannot launder the primary screen's label into the model.
* **Stopping**: parameter-free. Before each batch the model's expected hits for the batch it would
  buy are compared with the expected hits of a uniformly random batch from the same candidates
  (both from the same calibrated model). When the planned batch is no better, the campaign stops
  with `BUDGET_EXHAUSTED_EARLY` and the unspent screens are reported as cost saved.
* **Replanning**: the stream split, the refit and the stopping test all run again every round, so a
  collapse in either stream's yield changes what is bought next.

No LLM call is made here: the prior is read from the cached records. The conventional
agent-plus-tool arm that *does* call an LLM per round is `conv_agent.py`.
"""
from __future__ import annotations

import numpy as np

import campaign as CA
import world as WM

EXPLORE_SEATS = 2          # of a batch of 5; set from feasibility F10 before the freeze
BETA_PRIOR = (1.0, 1.0)


def novel_classes(U, known, t):
    """Mechanism strings with a selective member for lineage ``t`` among ``known`` (observed, not true)."""
    H = U.hits()
    kn = set(U.moa[np.asarray(known)][H[np.asarray(known), t]])
    kn.discard("nan")
    return kn


class Maestro:
    def __init__(self, U, prior=None, explore_seats: int = EXPLORE_SEATS, sources=None, stop: bool = True):
        self.U = U
        self.prior = prior
        self.explore_seats = explore_seats
        self.sources = tuple(sources) if sources else WM.SOURCES + ("llm",)
        self.stop = stop
        # The explore stream ranks novel-class candidates with the virtual cell, which is the only
        # source that reaches across mechanism classes. An arm that is denied the virtual cell must
        # be denied it here too, or the H1 comparator would keep the very thing it is meant to lack.
        has_vc = any(s in self.sources for s in WM.VC_SOURCES)
        self.explore_sources = WM.VC_SOURCES if has_vc else self.sources

    def _known_hits(self, st: CA.State):
        """Hit flags implied by what the arm *believes*, so the permutation control propagates."""
        s, m = self.U.selectivity(st.Y)
        return (s <= WM.HIT_S) & (m <= WM.HIT_M)

    def _novel_mask(self, st: CA.State, cand):
        Hb = self._known_hits(st)
        kn = set(self.U.moa[np.asarray(st.known)][Hb[:, st.t]])
        kn.discard("nan")
        return ~np.isin(self.U.moa[cand], list(kn))

    def run(self, st: CA.State, rng, permute_rng=None):
        U, t = self.U, st.t
        yields = {"confirm": list(BETA_PRIOR), "explore": list(BETA_PRIOR)}
        trace = []
        while st.n_screened < st.budget:
            known = np.array(st.known)
            cand = np.array(st.left)
            if len(cand) == 0:
                st.refusals.append({"round": st.round, "code": "LIBRARY_EXHAUSTED"})
                break
            k = min(st.batch, st.budget - st.n_screened)
            full = WM.Stack(U, self.sources, prior=self.prior).fit(known, Y=st.Y)
            p_all = full.score(known, cand, Y=st.Y)[:, t] + 1e-12 * rng.standard_normal(len(cand))
            expl = WM.Stack(U, self.explore_sources, prior=self.prior if "llm" in self.explore_sources else None)
            expl = expl.fit(known, Y=st.Y)
            p_vc = expl.score(known, cand, Y=st.Y)[:, t] + 1e-12 * rng.standard_normal(len(cand))
            nov = self._novel_mask(st, cand)
            no_vc = ~np.isfinite(U.sims["vc_native"][np.ix_(cand, known)]).any(1)
            if no_vc.any():
                st.refusals.append({"round": st.round, "code": "VC_NO_NEIGHBOUR", "n": int(no_vc.sum())})
            # ---- planning: how many explore seats this batch deserves
            if self.explore_seats <= 0 or k < 2:
                n_exp = 0
            elif st.round == 0:
                n_exp = min(self.explore_seats, k - 1)        # declared opening split
            else:
                means = {s: yields[s][0] / (yields[s][0] + yields[s][1]) for s in yields}
                share = means["explore"] / max(means["explore"] + means["confirm"], 1e-9)
                n_exp = min(max(int(round(k * share)), 1), k - 1)   # each stream keeps at least one seat
            exp_cand = cand[nov]
            if n_exp and len(exp_cand) == 0:
                st.refusals.append({"round": st.round, "code": "NO_NOVEL_CANDIDATE", "seats_returned": int(n_exp)})
                n_exp = 0
            n_exp = min(n_exp, len(exp_cand))
            take_e = exp_cand[np.argsort(-p_vc[nov])[:n_exp]] if n_exp else np.array([], int)
            rest = ~np.isin(cand, take_e)
            take_c = cand[rest][np.argsort(-p_all[rest])[: k - len(take_e)]]
            planned = np.concatenate([take_e, take_c]).astype(int)
            # ---- stopping: does the planned batch beat a random batch, by the model's own numbers?
            if self.stop and st.n_screened:
                exp_plan = float(p_all[np.isin(cand, planned)].sum())
                exp_rand = float(p_all.mean() * len(planned))
                trace.append({"round": st.round, "expected_planned": round(exp_plan, 4),
                              "expected_random": round(exp_rand, 4), "n_explore": int(n_exp)})
                if exp_plan <= exp_rand:
                    st.refusals.append({"round": st.round, "code": "BUDGET_EXHAUSTED_EARLY",
                                        "unspent_screens": int(st.budget - st.n_screened),
                                        "expected_planned": round(exp_plan, 4), "expected_random": round(exp_rand, 4)})
                    break
            else:
                trace.append({"round": st.round, "n_explore": int(n_exp)})
            pos = {c: i for i, c in enumerate(cand)}
            st.predictions += [(int(c), float(p_all[pos[c]])) for c in planned]
            st.reveal(U, planned, permute_rng)
            # ---- replanning input: each stream's realised yield, as believed
            Hb = self._known_hits(st)
            n_ref = len(st.ref)
            for s, sel in (("explore", take_e), ("confirm", take_c)):
                if not len(sel):
                    continue
                rows = [n_ref + [c for _, c in st.screened].index(int(c)) for c in sel]
                h = int(Hb[rows, t].sum())
                yields[s][0] += h
                yields[s][1] += len(sel) - h
        return st, {"stream_trace": trace, "final_yields": yields}


def verify(U, st: CA.State):
    """Secondary-screen verification of the hits this campaign bought. Never feeds selection."""
    H = U.hits()
    s2, _ = U.selectivity(U.S2)
    sel = np.array([c for _, c in st.screened], int)
    if not len(sel):
        return {"hits": 0, "verified": 0, "refuted": 0, "unverifiable": 0}
    hit = H[sel, st.t]
    have = np.isfinite(s2[sel, st.t])
    ok = have & hit & (s2[sel, st.t] <= -0.25)
    bad = have & hit & ~(s2[sel, st.t] <= -0.25)
    return {"hits": int(hit.sum()), "verified": int(ok.sum()), "refuted": int(bad.sum()),
            "unverifiable": int((hit & ~have).sum()),
            "refusals": ([{"code": "SECONDARY_ABSENT", "n": int((hit & ~have).sum())}] if (hit & ~have).any() else [])}
