"""Scientific Decision Review for one triage campaign: competing explanations, follow-up selection, GO / NO-GO.

File summary
- Path: research/selective_hit_triage_20261013/review.py
- Purpose: the deterministic core of the SDR arms. MAESTRO_LOOP remains the ranking engine. The
  review adds three things, each of which can be ablated:
  - explanation-aware follow-up selection;
  - NO-GO vetoes that need qualified contradicting evidence;
  - a bounded re-ranking.
- Core points:
  - Three falsifiable explanations of a screen-selective pair (compound c, line l):
    - SELECTIVE: c acts on a coherent sensitive subpopulation that includes l. It predicts several
      lines with z_r <= -2.5 and a replicating dose-response for l.
    - NOISE: l is an isolated single-dose outlier. It predicts that l is the only such line (or one
      of two) and that the secondary dose-response does not replicate it.
    - GENERIC: c is broadly cytotoxic and l is merely fragile. It predicts a high fraction of
      lines with lfc <= -1.
  - Evidence and its admission:
    - breadth (lines with z_r <= -2.5) and the generic fraction (promiscuity) come from the
      primary screen; they are DERIVED_ANALYSIS of real measurements;
    - a bought secondary is REAL_MEASUREMENT, admitted when finite for the line;
    - unbought or unavailable secondaries are NOT_PLANNED or PLANNED_MISSING and never count as
      zero.
  - Follow-up selection:
    - `frontier` is MAESTRO_LOOP's rule;
    - a set is an externally chosen purchase (the LLM tournament arm), checked against K and
      availability;
    - `explanation` buys first for compounds inside the 2B window whose explanation is least
      settled (breadth 1-3), because that is where a replicate discriminates NOISE from
      SELECTIVE. Ties go to the pair nearest the cutoff.
  - A veto names its reason. ISOLATED_OUTLIER_UNREPLICATED applies when breadth <= 1 and no bought
    secondary replicates (sec_z <= -2) on the compound's best line. NON_REPLICATING applies when a
    bought secondary contradicts (sec_z > -1) on the best line.
  - Decisions per compound:
    - GO: at least one pair nominated;
    - NO_GO: named falsifying evidence, or NO_SELECTIVE_SIGNAL (no z_r <= -2);
    - NEED_MORE_EVIDENCE: not falsified but not funded, with the discriminating experiment named.
- Interfaces: `BREADTH_Z`, `explanation_features`, `review_campaign`, `window`.
"""
from __future__ import annotations

import numpy as np

from arms import CAP, nominate, tie
from dev_explore2 import frontier_pick

BREADTH_Z = -2.5
ISOLATED_MAX = 1
UNSETTLED_MAX = 3
REPLICATES, CONTRADICTS = -2.0, -1.0
SELECTIVE_SIGNAL = -2.0


def explanation_features(t: dict, rows: np.ndarray) -> dict:
    """Compound-level explanation evidence broadcast to pairs: selective breadth and generic fraction."""
    core, zr = t["core"][rows], t["z_r"][rows]
    breadth, lines = {}, {}
    for k in np.unique(core):
        m = core == k
        breadth[k] = int((zr[m] <= BREADTH_Z).sum())
        lines[k] = int(m.sum())
    return {"breadth": np.array([breadth[k] for k in core], dtype=float),
            "lines": np.array([lines[k] for k in core], dtype=float),
            "generic_fraction": t["promisc_c"][rows].astype(float),
            "vc_pred": t["vc_pred"][rows].astype(float)}


def _capped_order(score: np.ndarray, core: np.ndarray, line: np.ndarray) -> list[int]:
    s = np.where(np.isfinite(score), score, -np.inf)
    out, per = [], {}
    for k in np.lexsort((tie(core, line), -s)):
        if s[k] == -np.inf:
            break
        if per.get(core[k], 0) < CAP:
            per[core[k]] = per.get(core[k], 0) + 1
            out.append(int(k))
    return out


def _explanation_pick(pre: np.ndarray, core: np.ndarray, line: np.ndarray, breadth: np.ndarray, has: np.ndarray,
                      B: int, K: int) -> set:
    order = _capped_order(pre, core, line)
    best: dict = {}
    for pos, k in enumerate(order[:2 * B]):
        best.setdefault(core[k], (pos + 1, k))
    cand = [c for c, (pos, k) in best.items() if has[core == c].any()]
    unsettled = lambda c: 0 if breadth[best[c][1]] <= UNSETTLED_MAX else 1
    picked = sorted(cand, key=lambda c: (unsettled(c), abs(best[c][0] - B), c))[:K]
    if len(picked) < K:                                       # fill from the frontier if the window is short
        extra = frontier_pick(pre, core, line, B, has, K)
        picked += [c for c in sorted(extra) if c not in picked][:K - len(picked)]
    return set(picked)


def review_campaign(c: dict, ex: dict, sel: np.ndarray, B: int, K: int, *, beta: float = 0.0, gamma: float = 0.0,
                    veto: bool = True, acquire: str | set = "explanation", admit_predictions: bool = False) -> dict:
    """Nominated positions (into ``sel``), bought compounds and one decision record per compound.

    ``admit_predictions`` is the evidence-verification ablation. The transcriptional virtual cell's
    prediction for a line (MODEL_PREDICTION) is then treated as if it were a measured replicate
    wherever no secondary was bought. The verified review never lets a prediction falsify or
    rescue a candidate.
    """
    zr, ctx, sec, has = c["zr"][sel], c["ctx"][sel], c["sec"][sel], c["has"][sel]
    core, line = c["core"][sel], c["line"][sel]
    breadth, generic = ex["breadth"][sel], ex["generic_fraction"][sel]
    adj = beta * np.log1p(breadth) - gamma * generic
    pre = -(zr + ctx) / np.sqrt(2) + adj
    if isinstance(acquire, set):                                      # chosen elsewhere (the LLM tournament arm)
        if len(acquire) > K or not acquire <= set(core[has]):
            raise ValueError("ACQUISITION_OUTSIDE_BUDGET_OR_AVAILABILITY")
        bought = set(acquire)
    elif acquire == "frontier":
        bought = frontier_pick(pre, core, line, B, has, K)
    elif acquire == "explanation":
        bought = _explanation_pick(pre, core, line, breadth, has, B, K)
    else:
        raise ValueError(acquire)
    use = np.isin(core, list(bought)) & has
    post = pre.copy()
    post[use] = -(zr[use] + ctx[use] + sec[use]) / np.sqrt(3) + adj[use]
    rep = np.where(use, sec, np.nan)                                  # admitted replicate evidence per pair
    if admit_predictions:
        vc = ex["vc_pred"][sel]
        rep = np.where(~use & np.isfinite(vc), vc, rep)
    decisions: dict = {}
    for k in sorted(set(core)):
        m = np.flatnonzero(core == k)
        best = m[np.argmax(np.where(np.isfinite(post[m]), post[m], -np.inf))]
        rec = {"status": None, "reasons": [], "experiment": None, "bought": k in bought,
               "evidence": {"breadth": int(breadth[best]), "generic_fraction": round(float(generic[best]), 4),
                            "best_line": str(line[best]), "best_z_r": round(float(zr[best]), 3), "best_ctx": round(float(ctx[best]), 3),
                            "best_sec_z": round(float(sec[best]), 3) if use[best] else None}}
        if not (zr[m] <= SELECTIVE_SIGNAL).any():
            rec["status"], rec["reasons"] = "NO_GO", ["NO_SELECTIVE_SIGNAL"]
        elif veto and np.isfinite(rep[best]) and rep[best] > CONTRADICTS:
            rec["status"], rec["reasons"] = "NO_GO", ["NON_REPLICATING" if use[best] else "PREDICTED_NON_REPLICATING"]
        elif veto and breadth[best] <= ISOLATED_MAX and not (np.isfinite(rep[best]) and rep[best] <= REPLICATES):
            rec["status"], rec["reasons"] = "NO_GO", ["ISOLATED_OUTLIER_UNREPLICATED"]
        decisions[k] = rec
    vetoed = np.array([decisions[k]["status"] == "NO_GO" and decisions[k]["reasons"] != ["NO_SELECTIVE_SIGNAL"] for k in core])
    final = np.where(vetoed, -np.inf, post)
    nominated = nominate(final, core, line, B)
    chosen = set(core[nominated])
    for k, rec in decisions.items():
        if k in chosen:
            rec["status"] = "GO"
            rec["reasons"] = ["SELECTIVE_FAVOURED"] + (["REPLICATED"] if rec["evidence"]["best_sec_z"] is not None
                                                       and rec["evidence"]["best_sec_z"] <= REPLICATES else [])
            rec["lines"] = sorted(str(line[j]) for j in nominated if core[j] == k)
        elif rec["status"] is None:
            rec["status"] = "NEED_MORE_EVIDENCE"
            rec["reasons"] = ["NOT_FALSIFIED_NOT_FUNDED"]
            rec["experiment"] = ("PRISM_SECONDARY_DOSE_RESPONSE" if has[core == k].any() and k not in bought
                                 else "ORTHOGONAL_CONFIRMATION_BEST_LINE")
    return {"nominated": nominated, "bought": bought, "decisions": decisions, "post": final}


def window(c: dict, ex: dict, sel: np.ndarray, B: int) -> list[int]:
    """Positions (into ``sel``) of the capped top 2B pairs under the unadjusted pre-acquisition score."""
    pre = -(c["zr"][sel] + c["ctx"][sel]) / np.sqrt(2)
    return _capped_order(pre, c["core"][sel], c["line"][sel])[:2 * B]
