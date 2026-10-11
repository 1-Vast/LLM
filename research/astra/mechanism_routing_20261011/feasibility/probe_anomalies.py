"""Feasibility probe P1-P3 (exploratory, exposed data, no provider calls).

P1  How many active GSE92742 drugs respond like another mechanism class more than like their own
    annotated class (L1000 anomalies)?
P2  Does PRISM (primary screen, 2.5 uM, an independent viability assay on ~578 lines) recover
    annotated classes, and for which classes is it informative?
P3  For anomalies, does PRISM side with the annotation (X) or with the L1000 alternative (Y), and do
    simple non-LLM signals (L1000 margin, Hub target overlap, chemical similarity) predict that?

Output: feasibility/probe_anomalies.json and probe_anomalies_rows.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BLOCK_M = ROOT / "research/astra/mechanism_falsification_20261010"
sys.path.insert(0, str(BLOCK_M))
sys.path.insert(0, str(HERE))
import probe_emh_claims as PE  # noqa: E402

PRISM = ROOT / "data/external/prism_19q4/raw"
SAMPLES = ROOT / "data/external/lincs_l1000_gse92742/repurposing_samples_20200324.txt"


def l1000_similarity(X, moa, active):
    """sim[d, c]: mean over options of cosine(x[d, o], class mean of active members at o); own class
    leave-self-out. Classes need >= 1 other active member (own) or >= 2 (alternatives)."""
    classes = sorted(set(moa))
    ci = {c: i for i, c in enumerate(classes)}
    n_opt = X.shape[1]
    Xf = np.nan_to_num(X)
    have = np.isfinite(X[..., 0])
    S = np.zeros((len(classes), n_opt, X.shape[2]))
    N = np.zeros((len(classes), n_opt))
    for d in np.where(active)[0]:
        S[ci[moa[d]]] += Xf[d]
        N[ci[moa[d]]] += have[d]
    n_members = np.array([int((active & (moa == c)).sum()) for c in classes])
    sim = np.full((len(moa), len(classes)), np.nan)
    for d in np.where(active)[0]:
        Sd, Nd = S.copy(), N.copy()
        k = ci[moa[d]]
        Sd[k] -= Xf[d]
        Nd[k] -= have[d]
        M = Sd / np.maximum(Nd, 1)[..., None]
        ok_c = (Nd > 0)
        num = np.einsum("og,cog->co", Xf[d], M)
        den = np.linalg.norm(Xf[d], axis=1)[None] * np.linalg.norm(M, axis=2)
        cos = np.where(ok_c & have[d][None] & (den > 0), num / np.maximum(den, 1e-12), np.nan)
        sim[d] = np.nanmean(cos, axis=1)
        eligible = n_members - (np.arange(len(classes)) == k) >= np.where(np.arange(len(classes)) == k, 1, 2)
        sim[d, ~eligible] = np.nan
    return sim, classes


def prism_profiles():
    info = pd.read_csv(PRISM / "primary-screen-replicate-collapsed-treatment-info.csv")
    lfc = pd.read_csv(PRISM / "primary-screen-replicate-collapsed-logfold-change.csv", index_col=0)
    info = info[info["column_name"].isin(lfc.columns)]
    prof = {}
    for name, grp in info.groupby(info["name"].astype(str).str.lower()):
        prof[name] = lfc[grp["column_name"].tolist()].mean(axis=1).to_numpy(float)
    return prof, lfc.index.tolist()


def corr(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 50:
        return np.nan
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def morgan_max_sim(smiles_by_drug, d, members):
    from rdkit import Chem, DataStructs
    from rdkit.Chem import rdFingerprintGenerator
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

    def fp(s):
        m = Chem.MolFromSmiles(s) if isinstance(s, str) else None
        return gen.GetFingerprint(m) if m is not None else None
    f0 = fp(smiles_by_drug.get(d))
    if f0 is None:
        return np.nan
    sims = [DataStructs.TanimotoSimilarity(f0, f) for f in (fp(smiles_by_drug.get(m)) for m in members) if f is not None]
    return max(sims) if sims else np.nan


def main() -> dict:
    X, drug, moa, options, genes = PE.load()
    a = PE.activity(X)
    active = np.nanmax(a, axis=1) >= 0.9
    sim, classes = l1000_similarity(X, moa, active)
    ci = {c: i for i, c in enumerate(classes)}
    res = {"n_active": int(active.sum())}

    # ---------------- P1 anomalies
    rows = []
    for d in np.where(active)[0]:
        s_own = sim[d, ci[moa[d]]]
        if not np.isfinite(s_own):
            continue
        alt = sim[d].copy()
        alt[ci[moa[d]]] = np.nan
        if not np.isfinite(alt).any():
            continue
        y = int(np.nanargmax(alt))
        rank_own = int(np.sum(sim[d][np.isfinite(sim[d])] > s_own)) + 1
        rows.append({"drug": drug[d], "X": moa[d], "Y": classes[y], "s_X": float(s_own), "s_Y": float(alt[y]),
                     "margin": float(alt[y] - s_own), "rank_own": rank_own, "activity": float(np.nanmax(a[d]))})
    df = pd.DataFrame(rows)
    res["P1"] = {"n_scored": len(df), "own_top1": float(np.mean(df["rank_own"] == 1)),
                 "s_X_quantiles": df["s_X"].quantile([0.1, 0.5, 0.9]).round(3).tolist(),
                 "s_Y_quantiles": df["s_Y"].quantile([0.1, 0.5, 0.9]).round(3).tolist(),
                 "margin_quantiles": df["margin"].quantile([0.5, 0.75, 0.9, 0.95]).round(3).tolist()}
    anom = df[(df["s_Y"] >= 0.25) & (df["margin"] >= 0.10)].copy()
    res["P1"]["anomalies_sY>=0.25_margin>=0.10"] = len(anom)
    res["P1"]["top_Y_classes"] = anom["Y"].value_counts().head(15).to_dict()

    # ---------------- P2 PRISM recovery of annotated classes
    prof, lines = prism_profiles()
    inP = np.array([d.lower() in prof for d in drug])
    res["P2"] = {"n_drugs_in_prism": int(inP.sum()), "n_active_in_prism": int((inP & active).sum())}
    P = {d: prof[d.lower()] for d in drug if d.lower() in prof}
    members = {c: [d for d, m in zip(drug, moa) if m == c and d in P] for c in classes}

    def class_mean(c, exclude):
        ms = [P[m] for m in members[c] if m != exclude]
        return np.nanmean(np.stack(ms), axis=0) if ms else None
    own_vs_other = []
    rng = np.random.default_rng(PE.SEED)
    for d, m in zip(drug, moa):
        if d not in P:
            continue
        mx = class_mean(m, d)
        if mx is None:
            continue
        others = [c for c in classes if c != m and len(members[c]) >= 2]
        c2 = others[rng.integers(len(others))]
        own_vs_other.append((m, corr(P[d], mx), corr(P[d], class_mean(c2, d))))
    ov = pd.DataFrame(own_vs_other, columns=["moa", "r_own", "r_rand"])
    cls_inf = ov.groupby("moa").agg(n=("r_own", "size"), r_own=("r_own", "mean"), r_rand=("r_rand", "mean"))
    informative = set(cls_inf[(cls_inf["n"] >= 2) & (cls_inf["r_own"] >= 0.2)].index)
    res["P2"].update({"own_minus_random_mean": float((ov["r_own"] - ov["r_rand"]).mean()),
                      "share_own_gt_random": float(np.mean(ov["r_own"] > ov["r_rand"])),
                      "n_prism_informative_classes": len(informative),
                      "informative_examples": sorted(informative)[:40]})

    # ---------------- P3 anomalies adjudicated by PRISM
    hub = pd.read_csv(PE.HUB, sep="\t", comment="!")
    tmap = {str(r.pert_iname): set(t for t in str(r.target).split("|") if t and t != "nan") for r in hub.itertuples()}
    smp = pd.read_csv(SAMPLES, sep="\t", comment="!")
    hub_names = dict(zip(hub["pert_iname"].astype(str), hub["pert_iname"].astype(str)))
    smiles = {}
    for r in smp.itertuples():
        if isinstance(r.smiles, str) and str(r.pert_iname) in hub_names:
            smiles.setdefault(str(r.pert_iname), r.smiles)
    out_rows = []
    for r in anom.itertuples():
        if r.drug not in P:
            continue
        mx, my = class_mean(r.X, r.drug), class_mean(r.Y, r.drug)
        if mx is None or my is None:
            continue
        ty = set().union(*[tmap.get(m, set()) for m in members[r.Y]]) if members[r.Y] else set()
        y_l1000 = [d for d, m in zip(drug, moa) if m == r.Y]
        out_rows.append({**r._asdict(), "r_prism_X": corr(P[r.drug], mx), "r_prism_Y": corr(P[r.drug], my),
                         "X_informative": r.X in informative, "Y_informative": r.Y in informative,
                         "target_overlap_Y": len(tmap.get(r.drug, set()) & ty) / max(len(tmap.get(r.drug, set())), 1),
                         "morgan_max_Y": morgan_max_sim(smiles, r.drug, y_l1000),
                         "morgan_max_X": morgan_max_sim(smiles, r.drug, [d for d, m in zip(drug, moa) if m == r.X and d != r.drug])})
    od = pd.DataFrame(out_rows)
    od["prism_prefers_Y"] = od["r_prism_Y"] - od["r_prism_X"]
    sub = od[od["Y_informative"] | od["X_informative"]]
    res["P3"] = {"n_anomalies_with_prism": len(od), "n_with_informative_class": len(sub),
                 "share_prism_prefers_Y_all": float(np.mean(od["prism_prefers_Y"] > 0)) if len(od) else None,
                 "share_prism_prefers_Y_informative": float(np.mean(sub["prism_prefers_Y"] > 0)) if len(sub) else None,
                 "share_prism_prefers_Y_by_0.1_informative": float(np.mean(sub["prism_prefers_Y"] > 0.1)) if len(sub) else None,
                 "baselines_spearman_with_prism_preference_informative": {
                     k: (float(spearmanr(sub[k], sub["prism_prefers_Y"], nan_policy="omit").statistic) if len(sub) > 5 else None)
                     for k in ("margin", "s_Y", "target_overlap_Y", "morgan_max_Y")}}
    (HERE / "probe_anomalies.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    (HERE / "probe_anomalies_rows.json").write_text(od.to_json(orient="records", indent=0), encoding="utf-8")
    return res


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
