"""Block P world model: evidence sources and a stacked hit model for lineage-selective killing.

Compounds live in one universe:
* block-N compounds: PRISM profile known (exposed), GSE92742 signatures (18 options) for all of
  them, GSE70138 signatures for 542;
* new compounds (confirmation): GSE70138 signatures only; PRISM profile sealed until the freeze.

Sources (each predicts a compound's PRISM profile from the *known* set: reference + screened):
* ``vc_native``: virtual cell, transcriptional transfer on GSE70138 signatures (cosine of all shared
  line x dose cells concatenated; F1's best hit AUROC), k nearest known compounds with signatures;
* ``vc_cross``: virtual cell across datasets, GSE70138 query vs GSE92742 reference on the five
  shared 24 h, 10 uM lines (weak; F1);
* ``klass``: mean profile of known compounds with the same annotated mechanism string;
* ``target``: k nearest by Hub target Jaccard;
* ``chem``: k nearest by Morgan (r=2, 2,048 bit) Tanimoto.

Selectivity for lineage T: s_T = mean LFC in T - mean LFC outside T; m_T = mean LFC in T.
Hit (registered definition candidate): s_T <= -0.5 and m_T <= -0.5.

The stacked hit model is an L2 logistic regression on per-source (s_T, m_T, top similarity)
features plus lineage intercepts, trained on leave-one-out predictions over the known set.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research/astra/mechanism_routing_20261011"))

SHARED5 = ["A375", "HA1E", "HT29", "MCF7", "PC3"]
SOURCES = ("vc_native", "vc_cross", "klass", "target", "chem")
VC_SOURCES = ("vc_native", "vc_cross")
K = 5
HIT_S = -0.5
HIT_M = -0.5
MIN_LINES = 20


def concat_cos(Q, R):
    """Cosine of concatenated options over the options both have. Q (nq, o, g), R (nr, o, g), NaN = absent."""
    hq = np.isfinite(Q[..., 0]).astype(np.float32)
    hr = np.isfinite(R[..., 0]).astype(np.float32)
    Qz, Rz = np.nan_to_num(Q).astype(np.float32), np.nan_to_num(R).astype(np.float32)
    dot = np.einsum("aog,bog->ab", Qz, Rz)
    den = np.sqrt(((Qz ** 2).sum(2) @ hr.T) * (hq @ (Rz ** 2).sum(2).T))
    return np.where(den > 0, dot / np.maximum(den, 1e-12), np.nan).astype(np.float32)


def mean_cos(Q, R):
    hq, hr = np.isfinite(Q[..., 0]), np.isfinite(R[..., 0])
    Qz, Rz = np.nan_to_num(Q).astype(np.float32), np.nan_to_num(R).astype(np.float32)
    Qn = Qz / np.maximum(np.linalg.norm(Qz, axis=2), 1e-12)[..., None]
    Rn = Rz / np.maximum(np.linalg.norm(Rz, axis=2), 1e-12)[..., None]
    s = np.zeros((len(Q), len(R)), np.float32)
    c = np.zeros((len(Q), len(R)), np.float32)
    for o in range(Q.shape[1]):
        m = np.outer(hq[:, o], hr[:, o])
        s += np.where(m, Qn[:, o] @ Rn[:, o].T, 0)
        c += m
    return np.where(c > 0, s / np.maximum(c, 1), np.nan).astype(np.float32)


@dataclass
class Universe:
    brd: np.ndarray
    name: np.ndarray
    group: np.ndarray        # "blockn" or "new"
    P: np.ndarray            # (n, lines) primary LFC; NaN rows for sealed compounds
    S2: np.ndarray           # secondary LFC at the dose closest to 2.5 uM (NaN where absent)
    lines: np.ndarray
    tissue: np.ndarray
    lineages: list
    moa: np.ndarray
    targets: list
    has_p2: np.ndarray
    has_p1: np.ndarray       # GSE92742 signatures usable as a reference (never for new compounds)
    sims: dict = field(default_factory=dict)

    def selectivity(self, M):
        """(n, n_lineage) s_T and m_T for profile matrix M (n, lines)."""
        s = np.stack([np.nanmean(M[:, self.tissue == T], 1) - np.nanmean(M[:, self.tissue != T], 1) for T in self.lineages], 1)
        m = np.stack([np.nanmean(M[:, self.tissue == T], 1) for T in self.lineages], 1)
        return s, m

    def hits(self, M=None):
        s, m = self.selectivity(self.P if M is None else M)
        return (s <= HIT_S) & (m <= HIT_M)


def build(include_new: bool, sealed: dict | None = None) -> Universe:
    """Assemble the universe. ``sealed`` is the opened new-compound tier (confirmation only)."""
    import extract as EX
    import predictors as PR
    from rdkit import Chem, DataStructs, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*")
    W = PR.load_world("sealed")
    L = EX.load_l1000()
    info = pd.read_csv(ROOT / "data/external/prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv")
    info["brd"] = info.broad_id.str[:13]
    meta = info.drop_duplicates("brd").set_index("brd")
    import json
    split = json.loads((ROOT / "research/astra/mechanism_routing_20261011/SPLIT.json").read_text(encoding="utf-8"))["units"]
    n2brd = {n: u["prism_columns"][0].split("::")[0][:13] for n, u in split.items()}
    bn_brd = np.array([n2brd[d] for d in W.drug])
    l_pos = {b: i for i, b in enumerate(L["brd"])}
    brd = list(bn_brd)
    name = list(W.drug)
    group = ["blockn"] * len(brd)
    P = [W.P.astype(np.float32)]
    S2 = [W.S2.astype(np.float32)]
    if include_new:
        new = [b for b, r in zip(L["brd"], L["role"]) if r == "new"]
        brd += new
        name += [str(L["name"][l_pos[b]]) for b in new]
        group += ["new"] * len(new)
        if sealed is not None:
            assert list(sealed["brd"]) == new
            P.append(sealed["primary"].astype(np.float32))
            S2.append(sealed["secondary"].astype(np.float32))
        else:
            P.append(np.full((len(new), W.P.shape[1]), np.nan, np.float32))
            S2.append(np.full((len(new), W.P.shape[1]), np.nan, np.float32))
    brd = np.array(brd)
    P = np.concatenate(P)
    S2 = np.concatenate(S2)
    cinfo = pd.read_csv(ROOT / "data/external/prism_19q4/raw/primary-screen-cell-line-info.csv").set_index("row_name")
    tissue = np.array([cinfo.at[l, "primary_tissue"] if l in cinfo.index else "na" for l in W.lines])
    lineages = [t for t, c in pd.Series(tissue).value_counts().items() if c >= MIN_LINES and t != "na"]
    moa = np.array([str(meta.at[b, "moa"]) if b in meta.index else "nan" for b in brd])
    targets = [set(x.strip() for x in str(meta.at[b, "target"]).split(",") if x.strip() and x.strip() != "nan")
               if b in meta.index else set() for b in brd]
    n = len(brd)
    # GSE70138 signatures
    X2 = np.full((n,) + L["x"].shape[1:], np.nan, np.float32)
    has_p2 = np.zeros(n, bool)
    for i, b in enumerate(brd):
        if b in l_pos:
            X2[i] = L["x"][l_pos[b]].astype(np.float32)
            has_p2[i] = True
    X2 = X2.reshape(n, -1, X2.shape[-1])
    # GSE92742 shared-5 signatures for block-N compounds
    p1_opts = [list(W.options).index(f"{l}|24 h") for l in SHARED5]
    X1 = np.full((n, len(SHARED5), W.Xf.shape[-1]), np.nan, np.float32)
    X1[: len(W.drug)] = np.where(W.l1000_have[:, p1_opts][..., None], W.Xf[:, p1_opts], np.nan)
    has_p1 = np.zeros(n, bool)
    has_p1[: len(W.drug)] = True
    lines2 = list(L["line"])
    q5 = X2.reshape(n, len(lines2), len(L["dose"]), -1)[:, [lines2.index(l) for l in SHARED5], list(L["dose"]).index("10.0 um")]
    sims = {}
    nat = np.full((n, n), np.nan, np.float32)
    idx2 = np.where(has_p2)[0]
    nat[np.ix_(idx2, idx2)] = concat_cos(X2[idx2], X2[idx2])
    sims["vc_native"] = nat
    sims["vc_cross"] = mean_cos(q5, X1)            # rows: query by its GSE70138; columns: reference by GSE92742
    sims["vc_cross"][~has_p2, :] = np.nan
    sims["vc_cross"][:, ~has_p1] = np.nan
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fps = []
    for b in brd:
        smi = str(meta.at[b, "smiles"]).split(",")[0] if b in meta.index else ""
        m = Chem.MolFromSmiles(smi) if smi and smi != "nan" else None
        fps.append(gen.GetFingerprint(m) if m is not None else None)
    chem = np.full((n, n), np.nan, np.float32)
    ok = [i for i in range(n) if fps[i] is not None]
    okf = [fps[i] for i in ok]
    for i in ok:
        chem[i, ok] = DataStructs.BulkTanimotoSimilarity(fps[i], okf)
    sims["chem"] = chem
    tgt = np.full((n, n), np.nan, np.float32)
    has_t = np.array([bool(t) for t in targets])
    allt = sorted(set().union(*targets))
    tpos = {t: j for j, t in enumerate(allt)}
    T = np.zeros((n, len(allt)), np.float32)
    for i, ts in enumerate(targets):
        for t in ts:
            T[i, tpos[t]] = 1
    inter = T @ T.T
    union = T.sum(1)[:, None] + T.sum(1)[None, :] - inter
    tgt = np.where(np.outer(has_t, has_t), inter / np.maximum(union, 1), np.nan).astype(np.float32)
    sims["target"] = tgt
    cls = (moa[:, None] == moa[None, :]) & (moa[:, None] != "nan")
    sims["klass"] = np.where(cls, 1.0, np.nan).astype(np.float32)
    for k in sims:
        np.fill_diagonal(sims[k], np.nan)
    return Universe(brd=brd, name=np.array(name), group=np.array(group), P=P, S2=S2, lines=W.lines, tissue=tissue,
                    lineages=lineages, moa=moa, targets=targets, has_p2=has_p2, has_p1=has_p1, sims=sims)


def knn_profiles(S: np.ndarray, Y: np.ndarray, k: int = K, mean_all: bool = False):
    """Predicted profiles (rows of S = candidates, columns = known) and top similarity. NaN if none."""
    ok = np.isfinite(S)
    any_ok = ok.any(1)
    Yz = np.nan_to_num(Y).astype(np.float32)
    Yok = np.isfinite(Y).astype(np.float32)
    if mean_all:
        Wm = ok.astype(np.float32)
        num, den = Wm @ Yz, Wm @ Yok
        top = np.where(any_ok, np.nanmax(np.where(ok, S, -np.inf), 1), np.nan).astype(np.float32)
    else:
        kk = min(k, S.shape[1])
        Sf = np.where(ok, S, -np.inf)
        idx = np.argpartition(-Sf, kk - 1, axis=1)[:, :kk]                  # (c, k)
        sv = np.take_along_axis(Sf, idx, 1)
        valid = np.isfinite(sv)
        w = np.where(valid, np.clip(sv, 0, None), 0.0)
        flat = (w.sum(1) <= 0) & valid.any(1)                               # all neighbours non-positive: equal weights
        w[flat] = valid[flat].astype(float)
        w = w.astype(np.float32)
        num = np.einsum("ck,ckl->cl", w, Yz[idx])
        den = np.einsum("ck,ckl->cl", w, Yok[idx])
        top = np.where(valid.any(1), np.max(np.where(valid, sv, -np.inf), 1), np.nan).astype(np.float32)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where((den > 0) & any_ok[:, None], num / np.maximum(den, 1e-12), np.nan).astype(np.float32)
    return out, top


class Stack:
    """Source predictions -> features -> L2 logistic hit model, refit on the known set.

    ``prior`` (optional, (n, n_lineage) with NaN where absent) is a per-compound external prior, such
    as the LLM's probabilities; it enters as a logit feature with a missing indicator, so its weight
    is learned from evidence like any other source.
    ``Y`` (optional) overrides the profiles of known compounds (feedback-permutation controls); hit
    labels for fitting are then computed from Y.
    """

    def __init__(self, U: Universe, sources=SOURCES, C: float = 0.3, prior: np.ndarray | None = None,
                 interact: bool = False):
        self.U = U
        self.sources = tuple(s for s in sources if s != "llm")
        self.C = C
        self.prior = prior if "llm" in sources else None
        self.interact = interact

    def source_preds(self, known: np.ndarray, cand: np.ndarray, loo: bool, Y: np.ndarray | None = None):
        """Per source: (s, m, top) for cand rows; ``loo`` means cand == known and self-pairs excluded."""
        U = self.U
        Y = U.P[known] if Y is None else Y
        out = {}
        for k in self.sources:
            S = U.sims[k][np.ix_(cand, known)]
            if loo:
                S = S.copy()
                np.fill_diagonal(S, np.nan)
            prof, top = knn_profiles(S, Y, mean_all=(k == "klass"))
            s, m = U.selectivity(prof)
            out[k] = (s, m, top)
        return out

    def features(self, preds, cand: np.ndarray):
        n, L = len(cand), len(self.U.lineages)
        cols = []
        for k in self.sources:
            s, m, top = preds[k]
            miss = ~np.isfinite(s)
            s_f = np.where(miss, 0.0, s)
            m_f = np.where(miss, 0.0, m)
            t_f = np.where(np.isfinite(top), top, 0.0)[:, None].repeat(L, 1)
            cols += [s_f, m_f, miss.astype(float), t_f * (~miss)]
        if self.prior is not None:
            p = self.prior[cand]
            miss = ~np.isfinite(p)
            pc = np.clip(np.where(miss, 0.01, p), 1e-3, 1 - 1e-3)
            cols += [np.where(miss, 0.0, np.log(pc / (1 - pc))), miss.astype(float)]
        F = np.stack(cols, -1)                    # (n, L, f)
        lin = np.broadcast_to(np.eye(L)[None], (n, L, L))
        parts = [F, lin]
        if self.interact:                         # lineage-specific copies of each source's selectivity feature
            sel = F[..., 0::4][..., : len(self.sources)]          # (n, L, n_sources): the s_T columns
            parts.append((sel[..., :, None] * np.eye(L)[None, :, None, :]).reshape(n, L, -1))
        return np.concatenate(parts, -1).reshape(n * L, -1)

    def oof(self, known: np.ndarray, rows: np.ndarray, folds: int = 5, seed: int = 0, Y: np.ndarray | None = None):
        """Out-of-fold P(hit) for ``rows`` (indices into ``known``): source features leave-one-out over
        the known set, logistic weights fitted without each fold. Shape (len(rows), n_lineage)."""
        from sklearn.linear_model import LogisticRegression
        preds = self.source_preds(known, known, loo=True, Y=Y)
        X = self.features(preds, known)
        L = len(self.U.lineages)
        if Y is None:
            y = self.U.hits()[known]
        else:
            s, m = self.U.selectivity(Y)
            y = (s <= HIT_S) & (m <= HIT_M)
        fold = np.random.default_rng(seed).integers(0, folds, len(known))
        out = np.full((len(known), L), np.nan)
        for f in range(folds):
            tr = np.repeat(fold != f, L)
            mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
            mdl = LogisticRegression(C=self.C, max_iter=2000).fit((X[tr] - mu) / sd, y.ravel()[tr])
            te = np.where(fold == f)[0]
            Xte = X.reshape(len(known), L, -1)[te].reshape(len(te) * L, -1)
            out[te] = mdl.predict_proba((Xte - mu) / sd)[:, 1].reshape(len(te), L)
        return out[rows]

    def fit(self, known: np.ndarray, Y: np.ndarray | None = None):
        from sklearn.linear_model import LogisticRegression
        preds = self.source_preds(known, known, loo=True, Y=Y)
        X = self.features(preds, known)
        y = (self.U.hits() if Y is None else None)
        if Y is None:
            y = y[known].ravel()
        else:
            s, m = self.U.selectivity(Y)
            y = ((s <= HIT_S) & (m <= HIT_M)).ravel()
        self.mu = X.mean(0)
        self.sd = X.std(0) + 1e-6
        self.model = LogisticRegression(C=self.C, max_iter=2000).fit((X - self.mu) / self.sd, y)
        return self

    def score(self, known: np.ndarray, cand: np.ndarray, Y: np.ndarray | None = None) -> np.ndarray:
        """P(hit) for (cand, lineage) pairs, shape (len(cand), n_lineage)."""
        preds = self.source_preds(known, cand, loo=False, Y=Y)
        X = self.features(preds, cand)
        p = self.model.predict_proba((X - self.mu) / self.sd)[:, 1]
        return p.reshape(len(cand), len(self.U.lineages))
