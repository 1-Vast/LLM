"""POST HOC (not registered): is the own-mono / pathway information ceiling zero for a flexible learner too?

File summary
- Path: research/astra/mono_pretraining_20261005/posthoc_ceiling.py
- Purpose: after G2 failed with the registered 6-parameter head, test whether a gradient-boosted learner given the
  line's own observed GDSC2 mono shifts, the 14 pathway scores and drug potencies can predict the within-line
  residual of the two-orientation mean label beyond the leave-one-line-out pair prior. HD lines only,
  line-grouped 5-fold CV (the registered folds), full-HD leave-one-line-out pair prior (a strong, dense history).
- Core points: labelled POST HOC; it cannot reopen E and does not alter the registered verdict. A null here shows
  the registered null is not a head-capacity artefact; a positive would be the most informative next experiment.
- Interfaces: `main`.
- Depends on: `common`, `run_s2.setup`, scikit-learn.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor

from research.astra.confirmation_campaign_20261004.design import campaign as c

from . import common as cm
from .run_s2 import setup

SETS = {"z": ("z",), "own": ("own",), "own+z": ("own", "z"), "potency_only": ()}


def main():
    S = setup()
    fold = S["fold"]
    out = {}
    rows = []
    mono = cm.load_mono()
    beta = {}
    pool = mono[mono.eligible_primary_pretrain & ~mono.sibling_id_record & mono.jaaks_drug_id.notna()]
    beta = pool.groupby("jaaks_drug_id").y_rel.mean().to_dict()
    for tissue, T in S["tissues"].items():
        hd = sorted(S["split"][tissue]["HD"])
        for sidm in hd:
            others = [s for s in hd if s != sidm]
            Hh = c.restrict(T, others)
            li = T.lines.index(sidm)
            r = np.flatnonzero(T.c == li)
            prior = c.history_quantities(Hh, "SV", T.pid[r])["S_both"]
            y = (T.arrays["SV"]["y_s"][r] + T.arrays["SV"]["y_v"][r]) / 2
            for k, i in enumerate(r):
                a, b = T.pairs[i]
                rows.append(dict(tissue=tissue, line=sidm, fold=fold[sidm][1], prior=prior[k], y=y[k], a=a, b=b,
                                 ma=S["own"].get((sidm, S["drow"][a]), np.nan), mb=S["own"].get((sidm, S["drow"][b]), np.nan),
                                 ba=beta.get(a, np.nan), bb=beta.get(b, np.nan),
                                 tcode=cm.TISSUE_CODE[tissue], zrow=S["row"][sidm]))
    import pandas as pd
    d = pd.DataFrame(rows)
    d["res"] = d.y - d.prior
    d["res"] -= d.groupby("line").res.transform("mean")
    base_cols = ["prior", "ba", "bb", "tcode"]
    Z = S["z"][d.zrow.to_numpy()]
    feats = {"z": np.column_stack([d[base_cols].to_numpy(), Z]),
             "own": np.column_stack([d[base_cols].to_numpy(), d.ma - d.ba, d.mb - d.bb, d.ma, d.mb]),
             "potency_only": d[base_cols].to_numpy()}
    feats["own+z"] = np.column_stack([feats["own"], Z])
    res = {}
    for name, X in feats.items():
        pred = np.zeros(len(d))
        for k in range(cm.N_FOLDS):
            tr, te = d.fold != k, d.fold == k
            m = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, max_depth=3, min_samples_leaf=40,
                                              l2_regularization=10.0, random_state=0)
            m.fit(X[tr], d.res[tr])
            pred[te.to_numpy()] = m.predict(X[te])
        gain = []
        keys = []
        for (t, line), g in d.groupby(["tissue", "line"]):
            base_r = spearmanr(g.prior, g.y).correlation
            new_r = spearmanr(g.prior + pred[g.index], g.y).correlation
            if np.isfinite(base_r) and np.isfinite(new_r):
                gain.append(new_r - base_r); keys.append((t, line))
        gain = np.array(gain)
        ks = c.sort_keys(keys); order = [keys.index(k) for k in ks]
        idx = c.boot_indices(ks, 5000)
        m_ = np.array([gain[order][i].mean() for i in idx])
        res[name] = dict(mean_gain=float(gain.mean()), ci=[float(v) for v in np.percentile(m_, [2.5, 97.5])],
                         r2_residual=float(1 - ((d.res - pred) ** 2).sum() / (d.res ** 2).sum()), n_lines=len(gain))
        print(name, res[name], flush=True)
    out["post_hoc_gbm_concordance_gain_over_pair_prior"] = res
    out["note"] = "POST HOC, HD only, full-HD LOLO prior; not registered; cannot open E"
    cm.dump(cm.RESULTS / "posthoc_ceiling.json", out)


if __name__ == "__main__":
    main()
