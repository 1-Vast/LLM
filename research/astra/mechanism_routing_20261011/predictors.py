"""Shared predictors and scoring for block N (mechanism routing of viability profiles).

A query drug's PRISM primary profile (log fold change at 2.5 uM over 578 lines) is predicted from
reference drugs only. Non-LLM predictors:

* ``G``  generic profile: mean of reference profiles.
* ``A``  annotated class mean (known-class regime only).
* ``L``  virtual cell: transcriptional transfer. The 5 reference drugs whose GSE92742 signatures (9
  lines x 6/24 h, 10 uM) are most similar (mean cosine over shared options); similarity-weighted
  mean of their profiles.
* ``T``  target transfer: 5 nearest reference drugs by Repurposing Hub target Jaccard.
* ``C``  chemical transfer: 5 nearest reference drugs by Morgan (r=2, 2,048 bit) Tanimoto.
* ``E``  non-LLM ensemble: mean of the z-scored L, T and C predictions available.
* ``B0`` deterministic biomarker rule: lines expressing more of the drug's Hub targets are predicted
  more sensitive.

LLM outputs are compiled by ``compile_routes`` (mechanism classes -> mixture of reference class
means), ``compile_neighbours`` (kept transcriptional neighbours) and ``compile_biomarkers``
(gene features in CCLE 19Q4 -> line score). The primary score is ``selective_r``: Pearson r between
prediction and observation after removing each one's projection on the generic profile.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BLOCK_M = ROOT / "research/astra/mechanism_falsification_20261010"
HUB = ROOT / "data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt"
SAMPLES = ROOT / "data/external/lincs_l1000_gse92742/repurposing_samples_20200324.txt"
DEP = ROOT / "data/external/depmap_19q4"
K = 5


def pearson(a, b, min_n=50):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < min_n or np.std(a[ok]) < 1e-10 or np.std(b[ok]) < 1e-10:  # no variance (e.g. a pure G prediction)
        return np.nan
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def residual(y, g):
    """y minus its least-squares projection on g (both centred)."""
    ok = np.isfinite(y) & np.isfinite(g)
    out = np.full(len(y), np.nan)
    yc, gc = y[ok] - y[ok].mean(), g[ok] - g[ok].mean()
    b = float(np.dot(yc, gc) / max(np.dot(gc, gc), 1e-12))
    out[ok] = yc - b * gc
    return out


def selective_r(pred, obs, G):
    if pred is None:
        return np.nan
    return pearson(residual(pred, G), residual(obs, G))


def z(v):
    v = np.asarray(v, float)
    s = np.nanstd(v)
    return (v - np.nanmean(v)) / s if s > 0 else np.zeros_like(v)


@dataclass
class World:
    """Reference pool, query profiles and side information (all arrays aligned to ``drug``)."""

    drug: np.ndarray
    moa: np.ndarray
    role: np.ndarray
    P: np.ndarray            # (n_drug, n_line) primary profiles (query rows are only scored)
    S2: np.ndarray           # secondary-screen profiles (NaN where absent)
    lines: np.ndarray        # DepMap IDs
    ref: np.ndarray          # indices of reference drugs
    G: np.ndarray = field(init=False)

    def __post_init__(self):
        self.G = np.nanmean(self.P[self.ref], axis=0)
        self._l1000()
        self._targets_and_chemistry()
        self._ccle = None

    # ---------------------------------------------------------------- side information
    def _l1000(self):
        sys.path.insert(0, str(BLOCK_M))
        import study as S  # noqa: E402
        xs, names = [], []
        for tier in ("open", "sealed"):
            t = S.load_tier(tier)
            xs.append(t["x"])
            names += [str(d) for d in t["drug"]]
            self.options = list(t["option"])
        X = np.concatenate(xs)
        idx = {d: i for i, d in enumerate(names)}
        Xa = X[[idx[d] for d in self.drug]]
        self.l1000_have = np.isfinite(Xa[..., 0])
        self.Xf = np.nan_to_num(Xa)
        self.l1000_norm = np.linalg.norm(self.Xf, axis=2)

    def _targets_and_chemistry(self):
        from rdkit import Chem, RDLogger
        from rdkit.Chem import rdFingerprintGenerator
        RDLogger.DisableLog("rdApp.*")
        hub = pd.read_csv(HUB, sep="\t", comment="!")
        tmap = {str(r.pert_iname): sorted(set(x for x in str(r.target).split("|") if x and x != "nan")) for r in hub.itertuples()}
        self.targets = [tmap.get(d, []) for d in self.drug]
        smp = pd.read_csv(SAMPLES, sep="\t", comment="!")
        smi = {}
        for r in smp.itertuples():
            if isinstance(r.smiles, str):
                smi.setdefault(str(r.pert_iname), r.smiles)
        gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
        self.fps = []
        for d in self.drug:
            m = Chem.MolFromSmiles(smi[d]) if d in smi else None
            self.fps.append(gen.GetFingerprint(m) if m is not None else None)

    def ccle(self):
        """CCLE 19Q4 log2(TPM+1) expression and damaging/hotspot mutations for the PRISM lines."""
        if self._ccle is None:
            ids = set(self.lines)
            rows = []
            for chunk in pd.read_csv(DEP / "CCLE_expression.csv", index_col=0, chunksize=300):
                rows.append(chunk.loc[chunk.index.intersection(ids)])
            expr = pd.concat(rows).reindex(self.lines)
            expr.columns = [c.split(" (")[0] for c in expr.columns]
            mut = pd.read_csv(DEP / "CCLE_mutations.csv", usecols=["Hugo_Symbol", "DepMap_ID", "Variant_Classification",
                                                                 "isDeleterious", "isTCGAhotspot", "isCOSMIChotspot"])
            mut = mut[mut["DepMap_ID"].isin(ids) & (mut["Variant_Classification"] != "Silent")]
            mut = mut[mut["isDeleterious"].fillna(False) | mut["isTCGAhotspot"].fillna(False) | mut["isCOSMIChotspot"].fillna(False)]
            mutated: dict[str, set] = {}
            for r in mut.itertuples():
                mutated.setdefault(r.Hugo_Symbol, set()).add(r.DepMap_ID)
            self._ccle = (expr.loc[:, ~expr.columns.duplicated()], mutated)
        return self._ccle

    # ---------------------------------------------------------------- similarity and transfer
    def pool(self, i: int, regime: str) -> np.ndarray:
        if regime == "known_class":
            return self.ref[self.ref != i]
        return self.ref[(self.moa[self.ref] != self.moa[i]) & (self.ref != i)]

    def l1000_sim(self, i, pool):
        num = np.einsum("og,pog->po", self.Xf[i], self.Xf[pool])
        den = self.l1000_norm[i][None] * self.l1000_norm[pool]
        ok = self.l1000_have[i][None] & self.l1000_have[pool] & (den > 0)
        with np.errstate(invalid="ignore"):
            return np.nanmean(np.where(ok, num / np.maximum(den, 1e-12), np.nan), axis=1)

    def target_sim(self, i, pool):
        ti = set(self.targets[i])
        if not ti:
            return np.full(len(pool), np.nan)
        return np.array([len(ti & set(self.targets[j])) / max(len(ti | set(self.targets[j])), 1) for j in pool])

    def chem_sim(self, i, pool):
        from rdkit import DataStructs
        if self.fps[i] is None:
            return np.full(len(pool), np.nan)
        return np.array([DataStructs.TanimotoSimilarity(self.fps[i], self.fps[j]) if self.fps[j] is not None else np.nan for j in pool])

    def knn(self, sim, pool, k=K):
        ok = np.isfinite(sim)
        if ok.sum() == 0:
            return None
        order = np.argsort(-np.where(ok, sim, -np.inf))[:k]
        w = np.clip(sim[order], 0, None)
        if w.sum() <= 0:
            return np.nanmean(self.P[pool[order]], axis=0)
        return np.nansum(self.P[pool[order]] * w[:, None], axis=0) / w.sum()

    def neighbours(self, i, regime, n=10):
        pool = self.pool(i, regime)
        s = self.l1000_sim(i, pool)
        order = np.argsort(-np.where(np.isfinite(s), s, -np.inf))[:n]
        return [(str(self.drug[pool[j]]), str(self.moa[pool[j]]), float(s[j]), int(pool[j])) for j in order]

    def class_mean(self, c, pool):
        m = pool[self.moa[pool] == c]
        return np.nanmean(self.P[m], axis=0) if len(m) else None

    def vocabulary(self, i, regime):
        pool = self.pool(i, regime)
        cls, n = np.unique(self.moa[pool], return_counts=True)
        return dict(zip(cls.tolist(), n.tolist()))

    def baselines(self, i, regime) -> dict:
        pool = self.pool(i, regime)
        out = {"G": self.G}
        if regime == "known_class":
            out["A"] = self.class_mean(self.moa[i], pool)
        out["L"] = self.knn(self.l1000_sim(i, pool), pool)
        out["T"] = self.knn(self.target_sim(i, pool), pool)
        out["C"] = self.knn(self.chem_sim(i, pool), pool)
        parts = [z(out[k]) for k in ("L", "T", "C") if out.get(k) is not None]
        out["E"] = np.mean(parts, axis=0) if parts else None
        out["B0"] = self.target_rule(i)
        return out

    def target_rule(self, i):
        expr, _ = self.ccle()
        t = [g for g in self.targets[i] if g in expr.columns]
        if not t:
            return None
        return -np.nanmean(np.stack([z(expr[g].to_numpy(float)) for g in t]), axis=0)

    # ---------------------------------------------------------------- LLM compilation
    def compile_routes(self, routes, i, regime):
        pool = self.pool(i, regime)
        vocab = {c.lower(): c for c in self.vocabulary(i, regime)}
        prof, w = [], []
        for r in routes or []:
            c = vocab.get(str(r.get("class", "")).lower())
            if c is None:
                continue
            m = self.class_mean(c, pool)
            if m is not None:
                prof.append(m)
                w.append(max(float(r.get("weight", 1.0) or 0.0), 0.0))
        if not prof or sum(w) <= 0:
            return None
        return np.average(np.stack(prof), axis=0, weights=np.array(w))

    def compile_neighbours(self, keep, i, regime, offered):
        names = {n.lower(): (j, s) for n, _, s, j in offered}
        rows, w = [], []
        for k in keep or []:
            hit = names.get(str(k).lower())
            if hit is not None:
                rows.append(self.P[hit[0]])
                w.append(max(hit[1], 1e-3))
        if not rows:
            return None
        return np.average(np.stack(rows), axis=0, weights=np.array(w))

    def compile_biomarkers(self, biomarkers):
        expr, mutated = self.ccle()
        parts = []
        for b in biomarkers or []:
            gname = str(b.get("gene", "")).upper()
            feature = str(b.get("feature", "expression")).lower()
            sign = -1.0 if str(b.get("effect", "")).lower().startswith("sensit") else 1.0  # sensitising -> lower lfc
            if feature == "mutation":
                v = np.array([1.0 if line in mutated.get(gname, set()) else 0.0 for line in self.lines])
                if v.sum() == 0 or v.sum() == len(v):
                    continue
                parts.append(sign * z(v))
            elif gname in expr.columns:
                v = expr[gname].to_numpy(float)
                if np.nanstd(v) > 0:
                    parts.append(sign * z(v))
        return np.nanmean(np.stack(parts), axis=0) if parts else None


def combine(parts, weights=None):
    """Equal-weight (or given-weight) mean of z-scored predictions; None parts are skipped."""
    use = [(z(p), w) for p, w in zip(parts, weights or [1.0] * len(parts)) if p is not None]
    if not use:
        return None
    return np.sum([w * p for p, w in use], axis=0) / sum(w for _, w in use)


def load_world(tier: str = "open") -> World:
    sys.path.insert(0, str(HERE))
    import tiers as TI  # noqa: E402
    t = TI.load(tier) if tier == "open" else None
    if tier == "open":
        return World(drug=t["drug"].astype(str), moa=t["moa"].astype(str), role=t["role"].astype(str), P=t["primary"],
                     S2=t["secondary"], lines=t["line"].astype(str), ref=np.where(t["role"] == "reference")[0])
    o, s = TI.load("open"), TI.load("sealed")
    cat = {k: np.concatenate([o[k], s[k]]) for k in ("drug", "moa", "role", "primary", "secondary")}
    role = cat["role"].astype(str)
    # after development the reference pool is reference + development drugs
    ref = np.where(np.isin(role, ["reference", "development"]))[0]
    return World(drug=cat["drug"].astype(str), moa=cat["moa"].astype(str), role=role, P=cat["primary"], S2=cat["secondary"],
                 lines=o["line"].astype(str), ref=ref)
