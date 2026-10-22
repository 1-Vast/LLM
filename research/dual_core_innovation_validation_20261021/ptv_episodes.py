"""Build research-program episodes (one per held-out background) for a stage and a world-model version."""
from __future__ import annotations
import sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import ptv_data as D, ptv_tasks as T, ptv_direct as X, ptv_mol as MOL
from ptv_direct import logit

LAM_PRIMARY = 0.5
BUDGET = 5.0


class MolTool:
    """g_mol: P(sensitive | own measured state, drug features, priors), trained on TRAINING backgrounds only."""
    def __init__(self, prep, dr, train):
        self.prep, self.dr = prep, dr
        tr = train[train.y.notna()].reset_index(drop=True)
        self.space = MOL.MolSpace(prep, tr)
        X_, y_ = [], []
        for _, r in tr.iterrows():
            z = self.space.train_z.get((r.cell, r.perts))
            if z is None: continue
            X_.append(self.row(tr, r.cell, r.perts, z)); y_.append(r.y)
        X_ = np.array(X_); self.sc = StandardScaler().fit(X_)
        self.m = LogisticRegression(C=0.3, max_iter=2000).fit(self.sc.transform(X_), np.array(y_))

    def row(self, tr, cell, perts, z):
        dp, nb = self.dr.priors(tr, cell, perts); gm = float(tr.y.mean())
        dp = gm if dp != dp else dp; nb = dp if nb != nb else nb
        return np.concatenate([[logit(dp), logit(nb), self.dr.ntarg[perts]], self.dr.fp_pc[perts], z])

    def score(self, tr, cell, perts):
        z = self.space.z(cell, perts)
        if z is None: return None
        return float(self.m.predict_proba(self.sc.transform(self.row(tr, cell, perts, z)[None]))[0, 1]), z


def fp_similarity(dr, drugs):
    V = np.stack([dr.fp_pc[d] for d in drugs]); V = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
    S = V @ V.T
    return {a: {b: float(S[i, j]) for j, b in enumerate(drugs)} for i, a in enumerate(drugs)}


def build_episodes(prep, dr, stage, w_scores: pd.DataFrame, with_mol=True, lam=LAM_PRIMARY, budget=BUDGET, helds=None):
    """w_scores: DataFrame cell, perts, w (the world-model version's P(sensitive)) for the held-out singles."""
    ex = prep.R.experiments(1)
    parts = {"dev": ["dev"], "sel": ["dev", "sel"], "final": ["dev", "sel"]}[stage]
    hold = ex[ex.part == ("final" if stage == "final" else stage)]
    train_all = ex[ex.part.isin(parts)]
    eps = []
    for c in sorted(hold.cell.unique()):
        if helds and c not in helds: continue
        lin = D.lineage_of(c)
        tr = train_all[~train_all.lineage.isin([lin])]; tr = tr[tr.y.notna()]
        te = hold[hold.cell == c]
        avail = [d for d, y in zip(te.perts, te.y) if (y == y) or stage == "final"]
        pool = T.contested_pool(tr, list(te.perts))
        gm = float(tr.y.mean())
        pri, nnp = {}, {}
        for d in pool:
            a, b = dr.priors(tr, c, d); a = gm if a != a else a; pri[d] = a; nnp[d] = a if b != b else b
        ws = w_scores[w_scores.cell == c].set_index("perts").w
        W = {d: float(ws[d]) for d in pool if d in ws.index}
        pool = [d for d in pool if d in W]
        labels = {d: float(te.set_index("perts").y[d]) for d in pool if te.set_index("perts").y[d] == te.set_index("perts").y[d]}
        pool = [d for d in pool if d in labels]
        mol = {}
        if with_mol:
            tool = MolTool(prep, dr, tr)
            for d in pool:
                s = tool.score(tr, c, d)
                if s is not None: mol[d] = {"score": s[0], "z": [round(float(v), 3) for v in s[1]]}
        eps.append({"cell": c, "lineage": lin, "kwargs": dict(drugs=pool, W={d: W[d] for d in pool}, prior={d: pri[d] for d in pool},
                                                         nn={d: nnp[d] for d in pool}, sim=fp_similarity(dr, pool), labels={d: labels[d] for d in pool},
                                                         mol=mol, lam=lam, budget=budget)})
    return eps
