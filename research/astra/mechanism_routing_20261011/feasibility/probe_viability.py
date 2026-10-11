"""Feasibility probe V1-V3 (development drugs only; reference drugs as the pool; no provider calls).

Predict a development drug's PRISM primary viability profile (578 lines, 2.5 uM) with non-LLM
predictors fitted on reference drugs only:
  G  generic profile (mean of reference profiles)
  A  annotated class mean (reference members; G when none)
  L  L1000 kNN: 5 most transcriptionally similar reference drugs (block M signatures)
  C  chemical kNN: 5 nearest reference drugs by Morgan Tanimoto
  T  target kNN: 5 nearest reference drugs by Hub target Jaccard
Ceiling: the drug's own secondary-screen profile (independent run) against its primary profile.
Scores: Pearson r over lines (raw) and r of residuals after removing the generic profile
("selective"). Regimes: known class (all reference drugs) and novel class (same-class reference
drugs removed from every predictor).
Output: feasibility/probe_viability.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
sys.path.insert(0, str(STUDY))
sys.path.insert(0, str(HERE))
import probe_emh_claims as PE  # noqa: E402
import tiers as T  # noqa: E402

K = 5


def morgan(smiles):
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*")
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    m = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
    return gen.GetFingerprint(m) if m is not None else None


def resid(y, g):
    ok = np.isfinite(y) & np.isfinite(g)
    b = np.dot(y[ok] - y[ok].mean(), g[ok] - g[ok].mean()) / max(np.var(g[ok]) * ok.sum(), 1e-12)
    r = np.full_like(y, np.nan)
    r[ok] = (y[ok] - y[ok].mean()) - b * (g[ok] - g[ok].mean())
    return r


def pearson(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 50 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
        return np.nan
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def main() -> dict:
    from rdkit import DataStructs
    t = T.load("open")
    drug, moa, role, P, S2 = t["drug"].astype(str), t["moa"].astype(str), t["role"].astype(str), t["primary"], t["secondary"]
    ref, dev = np.where(role == "reference")[0], np.where(role == "development")[0]
    G = np.nanmean(P[ref], axis=0)
    # L1000 signatures (block M tiers) aligned by name
    X, ldrug, lmoa, options, genes = PE.load()
    li = {d: i for i, d in enumerate(ldrug)}
    Xa = X[[li[d] for d in drug]]
    have = np.isfinite(Xa[..., 0])
    Xf = np.nan_to_num(Xa)
    nrm = np.linalg.norm(Xf, axis=2)

    def l1000_sim(i, pool):
        num = np.einsum("og,pog->po", Xf[i], Xf[pool])
        den = nrm[i][None] * nrm[pool]
        ok = have[i][None] & have[pool] & (den > 0)
        c = np.where(ok, num / np.maximum(den, 1e-12), np.nan)
        return np.nanmean(c, axis=1)
    hub = pd.read_csv(PE.HUB, sep="\t", comment="!")
    tmap = {str(r.pert_iname): set(x for x in str(r.target).split("|") if x and x != "nan") for r in hub.itertuples()}
    smp = pd.read_csv(ROOT / "data/external/lincs_l1000_gse92742/repurposing_samples_20200324.txt", sep="\t", comment="!")
    smi = {}
    for r in smp.itertuples():
        if isinstance(r.smiles, str):
            smi.setdefault(str(r.pert_iname), r.smiles)
    fps = {d: morgan(smi.get(d)) for d in drug}

    def knn(sim, pool, k=K):
        ok = np.isfinite(sim)
        if ok.sum() == 0:
            return G
        order = np.argsort(-np.where(ok, sim, -np.inf))[:k]
        w = np.clip(sim[order], 0, None)
        if w.sum() <= 0:
            return np.nanmean(P[pool[order]], axis=0)
        return np.nansum(P[pool[order]] * w[:, None], axis=0) / w.sum()

    rows = []
    for i in dev:
        for regime in ("known_class", "novel_class"):
            pool = ref if regime == "known_class" else ref[moa[ref] != moa[i]]
            preds = {"G": G}
            mates = ref[moa[ref] == moa[i]]
            preds["A"] = np.nanmean(P[mates], axis=0) if (regime == "known_class" and len(mates)) else G
            preds["L"] = knn(l1000_sim(i, pool), pool)
            if fps[drug[i]] is not None:
                preds["C"] = knn(np.array([DataStructs.TanimotoSimilarity(fps[drug[i]], fps[drug[j]]) if fps[drug[j]] is not None else np.nan
                                           for j in pool]), pool)
            ti = tmap.get(drug[i], set())
            if ti:
                preds["T"] = knn(np.array([len(ti & tmap.get(drug[j], set())) / max(len(ti | tmap.get(drug[j], set())), 1)
                                           for j in pool]), pool)
            y = P[i]
            row = {"drug": drug[i], "moa": moa[i], "regime": regime, "n_mates": int(len(mates)),
                   "kill_sd": float(np.nanstd(y)), "frac_lfc_lt_-1": float(np.nanmean(y < -1))}
            for k, p in preds.items():
                row[f"r_{k}"] = pearson(p, y)
                row[f"rs_{k}"] = pearson(resid(p, G), resid(y, G)) if k != "G" else np.nan
            if regime == "known_class":
                row["ceiling_secondary"] = pearson(S2[i], y)
                row["ceiling_secondary_selective"] = pearson(resid(S2[i], G), resid(y, G))
            rows.append(row)
    df = pd.DataFrame(rows)
    res = {"n_dev": int(len(dev)), "n_ref": int(len(ref)), "k": K}
    for regime in ("known_class", "novel_class"):
        d = df[df["regime"] == regime]
        res[regime] = {}
        for sub, mask in (("all", np.ones(len(d), bool)), ("killers", d["frac_lfc_lt_-1"].to_numpy() >= 0.05)):
            dd = d[mask]
            entry = {"n": int(len(dd))}
            for col in [c for c in dd.columns if c.startswith("r_") or c.startswith("rs_") or c.startswith("ceiling")]:
                v = dd[col].to_numpy(float)
                ok = np.isfinite(v)
                if ok.sum() >= 5:
                    est, lo, hi = PE.IV.cluster_bootstrap(v[ok], dd["moa"].to_numpy()[ok], n_boot=500, seed=PE.SEED)
                    entry[col] = [round(est, 3), round(lo, 3), round(hi, 3), int(ok.sum())]
            res[regime][sub] = entry
    (HERE / "probe_viability.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    df.to_csv(HERE / "probe_viability_rows.csv", index=False)
    return res


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
