"""Development-only check of acquisition rules and score normalisation (disclosed in the protocol).

File summary
- Path: research/selective_hit_triage_20261013/dev_explore2.py
- Purpose: settle the closed-loop design on development outcomes before the freeze. Each campaign
  buys PRISM secondary dose-response for 25% of its compounds; then it nominates.
- Acquisition rules:
  - `top`: the compounds with the best pre-acquisition score (conventional follow-up of the
    strongest hits).
  - `frontier`: the compounds whose best pair sits closest to the nomination cutoff, where a
    dose-response can change the decision.
- Post-acquisition scores:
  - conventional: two-way z plus secondary z;
  - MAESTRO: two-way z plus context plus secondary z.
  Each is tried as a plain sum and as a sum scaled by 1/sqrt(number of terms).
- Also listed: D3 + context + target-biomarker prediction (equal weights).
- Output: DEV_EXPLORE2.json.
"""
from __future__ import annotations

import json

import numpy as np

from arms import CAP, load_table, nominate
from census import HERE
from dev import campaigns, labels
from outcomes import qualified_outcomes

K_FRACTION = 0.25


def frontier_pick(score, core, line, budget, has_sec, k):
    """Compounds (with secondary available) whose best pair's rank is nearest the cutoff ``budget``."""
    s = np.where(np.isfinite(score), score, -np.inf)
    order = np.argsort(-s, kind="stable")
    best_rank: dict = {}
    pos = 0
    taken: dict = {}
    for idx in order:
        c = core[idx]
        if taken.get(c, 0) >= CAP:
            continue
        taken[c] = taken.get(c, 0) + 1
        pos += 1
        if has_sec[idx] and c not in best_rank:
            best_rank[c] = pos
    return set(sorted(best_rank, key=lambda c: (abs(best_rank[c] - budget), c))[:k])


def top_pick(score, core, has_sec, k):
    best: dict = {}
    for s, c, h in zip(score, core, has_sec):
        if h and np.isfinite(s):
            best[c] = max(best.get(c, -np.inf), s)
    return set(sorted(best, key=lambda c: (-best[c], c))[:k])


def main() -> None:
    t = load_table()
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    cores = split["development"]
    rows = np.flatnonzero(t["role"] == "development")
    y, ev, pan = labels(t, rows, qualified_outcomes("development"))
    core, line = t["core"][rows], t["line"][rows]
    camps = campaigns(cores)
    zr = t["z_r"][rows]
    ctx = np.where(np.isfinite(t["ctx_pred"][rows]), t["ctx_pred"][rows], 0.0)
    bio = np.where(np.isfinite(t["biomarker_pred"][rows]), t["biomarker_pred"][rows], 0.0)
    sec = t["sec_auc_z"][rows]
    has = np.isfinite(sec)
    out = {"label": "DEVELOPMENT exploration 2 (outcomes opened)", "results": {}}
    base = {"D3": -zr, "MAESTRO_ctx": -(zr + ctx), "MAESTRO_ctx_bio": -(zr + ctx + bio)}
    for b in (0.5, 1.0, 2.0):
        res = {}
        for name, s in base.items():
            nom = []
            for camp in camps:
                sel = np.flatnonzero(np.isin(core, camp))
                nom += list(sel[nominate(s[sel], core[sel], line[sel], int(round(b * len(camp))))])
            res[name] = [int(y[nom].sum()), len(nom)]
        for rule in ("top", "frontier"):
            for arm, pre, terms in (("conventional", -zr, 1), ("MAESTRO", -(zr + ctx), 2)):
                for norm in ("sum", "sqrt"):
                    nom, bought_total = [], 0
                    for camp in camps:
                        sel = np.flatnonzero(np.isin(core, camp))
                        B, k = int(round(b * len(camp))), int(round(K_FRACTION * len(camp)))
                        if rule == "top":
                            bought = top_pick(pre[sel], core[sel], has[sel], k)
                        else:
                            bought = frontier_pick(pre[sel], core[sel], line[sel], B, has[sel], k)
                        bought_total += len(bought)
                        use = np.isin(core[sel], list(bought)) & has[sel]
                        post = pre[sel].copy()
                        if norm == "sum":
                            post[use] = pre[sel][use] - sec[sel][use]
                        else:
                            post = post / np.sqrt(terms)
                            post[use] = (pre[sel][use] - sec[sel][use]) / np.sqrt(terms + 1)
                        nom += list(sel[nominate(post, core[sel], line[sel], B)])
                    res[f"{arm}_{rule}_{norm}"] = [int(y[nom].sum()), len(nom), bought_total]
        out["results"][str(b)] = res
    (HERE / "DEV_EXPLORE2.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for b, r in out["results"].items():
        print(b, json.dumps(r))


if __name__ == "__main__":
    main()
