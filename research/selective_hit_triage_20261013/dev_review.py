"""Development-only design of the Scientific Decision Review (SDR) arms (disclosed before the freeze).

File summary
- Path: research/selective_hit_triage_20261013/dev_review.py
- Purpose: decide, on development outcomes only, how competing explanations of a screen hit should
  enter the decision. Explanations act through follow-up selection, NO-GO vetoes and a bounded
  re-ranking. MAESTRO_LOOP stays the ranking engine.
- Explanations for "compound c selectively kills line l" (see review.py):
  - SELECTIVE: a coherent sensitive subpopulation;
  - NOISE: an isolated single-dose outlier;
  - GENERIC: broad cytotoxicity ordered by line fragility.
  The discriminating evidence is the compound's selective breadth: the number of lines with
  z_r <= -2.5 out of its screened lines.
- Variants compared at b in 0.5, 1, 2, against MAESTRO_LOOP:
  - rerank: score + beta * log1p(breadth) - gamma * generic fraction. The coefficients are fitted
    out of fold (family-grouped) by a two-feature logistic on decision-relevant pairs.
  - veto: NO-GO for an isolated compound (breadth <= 1) unless a bought secondary replicates
    (sec_z <= -2 on that line).
  - acquire: decision-aware acquisition, buying the K compounds whose best pair is inside the 2B
    window and whose explanation is least settled (breadth 1-3 first), instead of the frontier.
  - unverified: veto with virtual-cell predictions admitted as if they were measured replicates
    (the evidence-verification ablation).
- Decision quality per variant: GO, NO_GO and NEED_MORE_EVIDENCE counts, each with how many
  compounds are confirmable (any screen-selective pair, z_r <= -2, validates).
- Output: DEV_REVIEW.json.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

from arms import load_table, nominate
from census import HERE, SPLIT_SALT
from dev import FOLDS, campaigns, labels
from outcomes import qualified_outcomes
from review import BREADTH_Z, explanation_features, review_campaign
from test_choose import components


def main() -> None:
    from sklearn.linear_model import LogisticRegression
    t = load_table()
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    rows = np.flatnonzero(t["role"] == "development")
    y, ev, pan = labels(t, rows, qualified_outcomes("development"))
    c = components(t, rows)
    core = c["core"]
    fam = np.array([split["family"][k] for k in core])
    sizes, folds = np.zeros(FOLDS), {}
    for f in sorted(set(fam), key=lambda f: (-(fam == f).sum(), hashlib.sha256(f"{SPLIT_SALT}:fold:{f}".encode()).hexdigest())):
        k = int(np.argmin(sizes)); folds[f] = k; sizes[k] += (fam == f).sum()
    fold = np.array([folds[f] for f in fam])
    camps = campaigns(split["development"])
    ex = explanation_features(t, rows)
    out: dict = {"label": "DEVELOPMENT review design (outcomes opened)", "breadth_z": BREADTH_Z, "results": {}, "coefficients_by_fold": []}

    # out-of-fold rerank coefficients on decision-relevant pairs (MAESTRO score >= 2 before acquisition)
    pre = -(c["zr"] + c["ctx"]) / np.sqrt(2)
    relevant = ev & (pre >= 2.0)
    coef = np.zeros((len(rows), 2))
    for k in range(FOLDS):
        tr, te = relevant & (fold != k), fold == k
        X = np.column_stack([pre, np.log1p(ex["breadth"]), ex["generic_fraction"]])[tr]
        m = LogisticRegression(C=1.0, max_iter=2000).fit(X, y[tr])
        b0 = m.coef_[0]
        beta, gamma = b0[1] / b0[0], -b0[2] / b0[0]
        coef[te] = (beta, gamma)
        out["coefficients_by_fold"].append({"fold": k, "beta": float(beta), "gamma": float(gamma)})
    variants = {"MAESTRO_LOOP": dict(rerank=False, veto=False, acquire="frontier"),
                "SDR_rerank": dict(rerank=True, veto=False, acquire="frontier"),
                "SDR_veto": dict(rerank=False, veto=True, acquire="frontier"),
                "SDR_acquire": dict(rerank=False, veto=False, acquire="explanation"),
                "SDR_rerank_veto": dict(rerank=True, veto=True, acquire="frontier"),
                "SDR_rerank_acquire": dict(rerank=True, veto=False, acquire="explanation"),
                "SDR_veto_acquire": dict(rerank=False, veto=True, acquire="explanation"),
                "SDR_full": dict(rerank=True, veto=True, acquire="explanation"),
                "SDR_unverified": dict(rerank=False, veto=True, acquire="frontier", admit_predictions=True)}
    confirmable = {k: bool(y[(core == k) & (c["zr"] <= -2)].any()) for k in set(core)}
    for b in (0.5, 1.0, 2.0):
        res = {}
        for name, opt in variants.items():
            nom, decisions = [], {s_: {"compounds": 0, "confirmable": 0} for s_ in ("GO", "NO_GO", "NEED_MORE_EVIDENCE")}
            reasons: dict = {}
            for camp in camps:
                sel = np.flatnonzero(np.isin(core, camp))
                B, K = int(round(b * len(camp))), int(round(0.25 * len(camp)))
                beta, gamma = coef[sel][0] if opt["rerank"] else (0.0, 0.0)
                r = review_campaign(c, ex, sel, B, K, beta=float(beta), gamma=float(gamma), veto=opt["veto"], acquire=opt["acquire"],
                                    admit_predictions=opt.get("admit_predictions", False))
                nom += list(sel[r["nominated"]])
                for k, d in r["decisions"].items():
                    decisions[d["status"]]["compounds"] += 1
                    decisions[d["status"]]["confirmable"] += int(confirmable[k])
                    if d["status"] == "NO_GO":
                        rr = reasons.setdefault(d["reasons"][0], {"compounds": 0, "confirmable": 0})
                        rr["compounds"] += 1
                        rr["confirmable"] += int(confirmable[k])
            nom = np.array(nom, dtype=int)
            res[name] = {"hits": int(y[nom].sum()), "nominations": int(len(nom)), "pan_active_nominations": int(pan[nom].sum()),
                         "compounds_with_hit": len({core[k] for k in nom if y[k]}), "decisions": decisions, "no_go_reasons": reasons}
        out["results"][str(b)] = res
    (HERE / "DEV_REVIEW.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for b, r in out["results"].items():
        print(b, {k: (v["hits"], v["decisions"]["NO_GO"], v["decisions"]["NEED_MORE_EVIDENCE"]) for k, v in r.items()})
    print(out["coefficients_by_fold"])


if __name__ == "__main__":
    main()
