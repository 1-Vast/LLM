"""Development-only exploration of low-variance decision scores (disclosed in the protocol).

File summary
- Path: research/selective_hit_triage_20261013/dev_explore.py
- Purpose: after dev.py showed a flexible learner losing to the two-way selectivity z, test a small,
  pre-listed set of low-variance alternatives that build on that z. Development outcomes only.
- Candidates:
  - D3 plus context coherence with a fixed weight a (0.25, 0.5 or 1);
  - an L2 logistic model on six standardised features;
  - D3 averaged with the bought secondary z, a conventional two-stage rule;
  - the logistic model plus the secondary features.
  Learned candidates are fitted out of fold, grouped by family as in dev.py.
- Output: DEV_EXPLORE.json.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

from arms import load_table
from census import HERE, SPLIT_SALT
from dev import FOLDS, campaigns, labels, run_arm
from outcomes import qualified_outcomes

LOGIT = ("neg_z_r", "ctx_pred", "lineage_pred", "biomarker_pred", "tgt_mut", "vc_pred")


def design(t: dict, rows: np.ndarray, feats: tuple[str, ...]) -> np.ndarray:
    cols = []
    for f in feats:
        v = -t["z_r"][rows] if f == "neg_z_r" else t[f][rows].astype(float)
        cols.append(np.where(np.isfinite(v), v, 0.0))
        if f in ("vc_pred", "sec_auc_z", "sec_slope", "biomarker_pred"):
            cols.append(np.isfinite(v).astype(float))
    return np.column_stack(cols)


def auroc(score: np.ndarray, y: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score
    ok = np.isfinite(score)
    return float(roc_auc_score(y[ok], score[ok]))


def main() -> None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    t = load_table()
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    cores = split["development"]
    rows = np.flatnonzero(t["role"] == "development")
    y, ev, pan = labels(t, rows, qualified_outcomes("development"))
    core = t["core"][rows]
    fam = np.array([split["family"][c] for c in core])
    camps = campaigns(cores)
    sizes, folds = np.zeros(FOLDS), {}
    for f in sorted(set(fam), key=lambda f: (-(fam == f).sum(), hashlib.sha256(f"{SPLIT_SALT}:fold:{f}".encode()).hexdigest())):
        k = int(np.argmin(sizes)); folds[f] = k; sizes[k] += (fam == f).sum()
    fold = np.array([folds[f] for f in fam])
    zr, ctx = t["z_r"][rows], t["ctx_pred"][rows]
    sec = t["sec_auc_z"][rows]
    scores = {"D3": -zr}
    for a in (0.25, 0.5, 1.0):
        scores[f"D3+ctx{a}"] = -zr - a * np.where(np.isfinite(ctx), ctx, 0.0)
    scores["D3+sec"] = np.where(np.isfinite(sec), -(zr + sec) / np.sqrt(2), -zr)

    def oof_logit(feats, need_sec=False):
        p = np.full(len(rows), np.nan)
        X = design(t, rows, feats)
        for k in range(FOLDS):
            tr, te = (fold != k) & ev, fold == k
            if need_sec:
                tr = tr & np.isfinite(sec)
            sc = StandardScaler().fit(X[tr])
            m = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(X[tr]), y[tr])
            p[te] = m.predict_proba(sc.transform(X[te]))[:, 1]
        return p

    scores["LOGIT"] = oof_logit(LOGIT)
    with_sec = oof_logit(LOGIT + ("sec_auc_z", "sec_slope"), need_sec=True)
    scores["LOGIT+sec"] = np.where(np.isfinite(sec), with_sec, scores["LOGIT"])
    out = {"label": "DEVELOPMENT exploration (outcomes opened)", "arms": {}}
    for name, s in scores.items():
        out["arms"][name] = {"pair_auroc": auroc(s[ev], y[ev])}
        for b in (0.5, 1.0, 2.0):
            nom = run_arm(s, t, rows, camps, b)
            out["arms"][name][str(b)] = [int(y[nom].sum()), int(len(nom)), int(pan[nom].sum())]
    if True:
        X = design(t, rows, LOGIT)
        sc = StandardScaler().fit(X[ev])
        m = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(X[ev]), y[ev])
        names = [f for f in LOGIT for _ in ((0, 1) if f in ("vc_pred", "biomarker_pred") else (0,))]
        out["logit_coefficients_full_dev"] = {f"{n}{'_present' if k and names[k - 1] == n else ''}": float(c)
                                              for k, (n, c) in enumerate(zip(names, m.coef_[0]))}
    (HERE / "DEV_EXPLORE.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for name, v in out["arms"].items():
        print(f"{name:12s} auroc {v['pair_auroc']:.3f}  b0.5 {v['0.5']}  b1 {v['1.0']}  b2 {v['2.0']}")
    print(out["logit_coefficients_full_dev"])


if __name__ == "__main__":
    main()
