"""World models for the viability-contrast dual-core run (protocol viability-contrast-3).

File summary
- Path: research/viability_contrast/world3.py
- Purpose: the virtual-cell channels. `reference` is the class-template predictive;
  `structural` adjusts the predictive mean toward the compound's Tanimoto-neighbour mean at
  each line (Morgan fingerprints), with the blend fitted on training-fold reading
  log-likelihood. The world's predictive proposes line choices; the score update inside an
  episode always uses the fixed validator templates (world output never becomes a reading).
- Interfaces / data: `FingerprintCache`, `neighbour_matrix`, `fit_lambda`.
- Depends on: research/viability_contrast/{prepare.py, qualify.py}
"""
from __future__ import annotations

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import DataStructs
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")

LAMBDA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)


class FingerprintCache:
    def __init__(self, smiles_by_compound: dict):
        self.fps = {}
        for c, smi in smiles_by_compound.items():
            mol = Chem.MolFromSmiles(str(smi).split(",")[0].strip()) if isinstance(smi, str) else None
            self.fps[c] = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048) if mol else None

    def similarity(self, query_compound: str, train_compounds: list) -> np.ndarray:
        q = self.fps.get(query_compound)
        if q is None:
            return np.zeros(len(train_compounds))
        refs = [self.fps[c] for c in train_compounds]
        out = np.zeros(len(train_compounds))
        have = [i for i, r in enumerate(refs) if r is not None]
        if have:
            sims = DataStructs.BulkTanimotoSimilarity(q, [refs[i] for i in have])
            for i, s in zip(have, sims):
                out[i] = s
        return out


def neighbour_matrix(auc, train_pos, sims, query_units, train_units):
    """NN[x, lj]: Tanimoto-weighted mean AUC at each line over training compounds,
    excluding the query compound's own connectivity unit.

    sims: (n_query, n_train) Tanimoto similarities; query_units: unit label per query
    row; train_units: unit label per row of train_pos (same order).
    """
    A = auc[train_pos]                       # (n_train, n_lines)
    fin = np.isfinite(A)
    Az = np.where(fin, A, 0.0)
    out = np.full((sims.shape[0], A.shape[1]), np.nan)
    for i in range(sims.shape[0]):
        w = sims[i].copy()
        w[train_units == query_units[i]] = 0.0
        W = w[:, None] * fin
        den = W.sum(axis=0)
        num = (W * Az).sum(axis=0)
        has = den > 0
        out[i, has] = num[has] / den[has]
    return out


def fit_lambda(auc, train_by_class, train_pos, NN, med, scale, valid, med_p, scale_p):
    """Blend weight by training reading log-likelihood under the own-class predictive.

    NN rows align with train_pos. The likelihood sums over every measured
    (training compound, line) reading, winsorized at |z| = 30 for robustness.
    """
    m = np.where(valid, med, med_p[None, :])
    s = np.where(valid, scale, scale_p[None, :])
    best_lam, best_ll = 0.0, -np.inf
    A = auc[train_pos]
    fin = np.isfinite(A)
    for lam in LAMBDA_GRID:
        ll_total = 0.0
        for ci, members in enumerate(train_by_class):
            rows = [int(np.where(train_pos == p)[0][0]) for p in members]
            mu = (1 - lam) * m[ci] + lam * NN[rows]
            z = (A[rows] - mu) / s[ci]
            term = -0.5 * np.minimum(z * z, 900.0) - np.log(s[ci])
            ll_total += float(term[np.isfinite(z)].sum())
        if ll_total > best_ll:
            best_lam, best_ll = lam, ll_total
    return best_lam
