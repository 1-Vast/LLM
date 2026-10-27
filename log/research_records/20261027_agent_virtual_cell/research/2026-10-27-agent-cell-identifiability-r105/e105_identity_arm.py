"""E089: raise the power of the R88 residual test.

R88 found +2.81 pp [-5.42, +11.88] on only 48 units. The gene-feature matrix was being rebuilt
inside the repeat loop, so raising the repeat count was prohibitively slow; here it is
precomputed once per cell, which makes a 5x increase in units affordable.

Pre-registered in PROTOCOL_E084.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold, cross_val_predict

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r105"
ANCHORS = {"high control", "low control"}
K = 20
REPEATS = 60
N_BOOT = 2000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def paired(a, b, off):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(j) < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(SEED + off)
    boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
    return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["c1"] = pd.to_numeric(df["Conc 1 (uM)"], errors="coerce")
    df["c2"] = pd.to_numeric(df["Conc 2 (uM)"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    ok = df[(~df["anchor"]) & (~df["failed_qc"]) & df["y"].notna()
            & df["c1"].notna() & df["c2"].notna()].copy()

    genes = {}
    ap = ROOT / "data" / "external" / "mapkg_20261009" / "DRUG-GENE_filtered_by_existing_drugs_and_genes.csv"
    dmp = ROOT / "data" / "external" / "mapkg_20261009" / "DRUG_merged_drugs_with_residuals.csv"
    dmap = pd.read_csv(dmp, low_memory=False)
    gdf = pd.read_csv(ap, low_memory=False)
    n2i = dict(zip(dmap["Drug Name"].astype(str).str.strip(), dmap["PubChem ID"]))
    i2g = gdf.groupby("Drug ID")["Gene ID"].apply(lambda s: frozenset(s)).to_dict()
    for nm, pid in n2i.items():
        if pid in i2g:
            genes[nm] = i2g[pid]

    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["Drug 2"])))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "qc": float(g["failed_qc"].mean())}
    groups = {}
    for f, s in meta.items():
        groups.setdefault(s["h"], {}).setdefault(s["cell"], []).append(f)

    # ---- precompute everything that does not depend on the held-out choice ----
    layouts = []
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 4:
            continue
        frames = {c: ok[ok["file"].isin(cells[c])] for c in good}
        drugs = sorted({d for f in frames.values() for d in list(f["Drug 1"]) + list(f["Drug 2"])})
        drug_lv = {d: i for i, d in enumerate(drugs)}
        gl = sorted({g for d in drugs if d in genes for g in genes[d]})
        if len(gl) < 5:
            continue
        gidx = {g: i for i, g in enumerate(gl)}
        nd = len(drugs)
        per = {}
        for c in good:
            f = frames[c]
            d1 = f["Drug 1"].tolist()
            d2 = f["Drug 2"].tolist()
            c1 = f["c1"].to_numpy()
            c2 = f["c2"].to_numpy()
            Y = f["y"].to_numpy(float)
            lc1 = np.log10(np.clip(c1, 1e-9, None))
            lc2 = np.log10(np.clip(c2, 1e-9, None))
            X = np.zeros((len(Y), 4 * nd))
            Xid = np.zeros((len(Y), 2 * nd))
            G = np.zeros((len(Y), len(gl)))
            for t in range(len(Y)):
                i1 = drug_lv[d1[t]]
                i2 = drug_lv[d2[t]]
                X[t, i1] = 1.0
                X[t, nd + i2] = 1.0
                Xid[t, i1] = 1.0
                Xid[t, nd + i2] = 1.0
                X[t, 2 * nd + i1] = lc1[t]
                X[t, 3 * nd + i2] = lc2[t]
                for d in (d1[t], d2[t]):
                    for g in genes.get(d, ()):
                        if g in gidx:
                            G[t, gidx[g]] += 1.0
            per[c] = {"X": X, "Xid": Xid, "Y": Y, "G": G, "pairs": list(zip(d1, d2))}
        layouts.append({"h": h, "cells": good, "per": per})

    rng = np.random.default_rng(SEED)
    rows, cv_r2 = [], []
    for lay in layouts:
        good, per = lay["cells"], lay["per"]
        for _ in range(REPEATS):
            held = good[int(rng.integers(0, len(good)))]
            tr_cells = [c for c in good if c != held]
            Xtr = np.vstack([per[c]["X"] for c in tr_cells])
            ytr = np.concatenate([per[c]["Y"] for c in tr_cells])
            cid = np.concatenate([[i] * len(per[c]["Y"]) for i, c in enumerate(tr_cells)])
            C = np.zeros((len(cid), len(tr_cells)))
            C[np.arange(len(cid)), cid] = 1.0
            Xtr_full = np.hstack([Xtr, C])
            Xh_full = np.hstack([per[held]["X"], np.zeros((len(per[held]["Y"]), len(tr_cells)))])

            m = RidgeCV(alphas=(1.0, 10.0, 100.0, 1000.0))
            pt = cross_val_predict(m, Xtr_full, ytr, cv=KFold(5, shuffle=True, random_state=SEED))
            ss_res = float(np.sum((ytr - pt) ** 2))
            ss_tot = float(np.sum((ytr - ytr.mean()) ** 2))
            cv_r2.append(1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan)

            m.fit(Xtr_full, ytr)
            r_tr = ytr - m.predict(Xtr_full)
            r_held = per[held]["Y"] - m.predict(Xh_full)
            Gtr = np.vstack([per[c]["G"] for c in tr_cells])
            keep = Gtr.sum(axis=1) > 0
            Gh = per[held]["G"]
            if keep.sum() < 500 or (Gh.sum(axis=1) > 0).mean() < 0.7:
                continue
            gm = RidgeCV(alphas=(1.0, 10.0, 100.0, 1000.0))
            gm.fit(Gtr[keep], r_tr[keep])
            r_hat = gm.predict(Gh)

            Xid_tr = np.vstack([per[c]["Xid"] for c in tr_cells])
            im = RidgeCV(alphas=(1.0, 10.0, 100.0, 1000.0))
            im.fit(Xid_tr, r_tr)
            r_hat_id = im.predict(per[held]["Xid"])

            pairh = per[held]["pairs"]
            agg, tru, agg_id = {}, {}, {}
            for i, p in enumerate(pairh):
                agg.setdefault(p, []).append(r_hat[i])
                agg_id.setdefault(p, []).append(r_hat_id[i])
                tru.setdefault(p, []).append(r_held[i])
            ps = list(agg)
            if len(ps) < 60:
                continue
            tv = np.array([float(np.mean(tru[p])) for p in ps])
            sv = np.array([float(np.mean(agg[p])) for p in ps])
            sv_id = np.array([float(np.mean(agg_id[p])) for p in ps])
            hit = (tv <= np.quantile(tv, 0.25)).astype(float)
            top = np.argsort(sv)[:K]
            rnd = rng.choice(len(ps), size=K, replace=False)
            rows.append({"layout": lay["h"][:12], "cell": held,
                         "gene": float(hit[top].mean()), "random": float(hit[rnd].mean()),
                         "identity": float(hit[np.argsort(sv_id)[:K]].mean()),
                         "base": float(hit.mean()), "n_pairs": len(ps)})

    r = pd.DataFrame(rows)
    res = {"kind": "identity_arm_added_to_the_R89_residual_test",
           "input_sha256": sha256(CSV),
           "settings": {"k": K, "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(len(r)), "cells": int(r["cell"].nunique()) if len(r) else 0,
                     "mean_cv_r2_of_additive_null": float(np.nanmean(cv_r2)) if cv_r2 else None,
                     "R88_units": 48},
           "summary": {}, "files": {}}
    if len(r) >= 5:
        res["summary"] = {"n": int(len(r)),
                          "gene": float(r["gene"].mean()), "random": float(r["random"].mean()),
                          "identity": float(r["identity"].mean()),
                          "base": float(r["base"].mean()),
                          "gene_minus_random": paired(r["gene"], r["random"], 16001),
                          "gene_minus_identity": paired(r["gene"], r["identity"], 16002),
                          "identity_minus_random": paired(r["identity"], r["random"], 16003)}
    s = res["summary"]
    h224 = bool(res["audit"]["mean_cv_r2_of_additive_null"] and res["audit"]["mean_cv_r2_of_additive_null"] > 0)
    h227 = bool(s and s["gene_minus_random"]["ci95"][0] > 0)
    h228 = bool(s and s["gene_minus_random"]["ci95"][1] < 0.02)
    res["decisions"] = {"H224_residual_learnable": h224,
                        "H227_gain_becomes_significant_with_power": h227,
                        "H228_gain_ruled_out_above_2pp": h228}
    res["decisions"]["verdict"] = (
        "annotation_gain_is_real_but_small" if h227 else
        "gain_effectively_ruled_out" if h228 else
        "still_undetermined_after_power_increase")
    res["limits"] = [
        "Even 60 repeats per layout draws held-out cells with replacement, so units are not independent.",
        "Each drug still has only a few concentration points.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r89/PROTOCOL_E084.md",
                "research/2026-10-27-agent-cell-identifiability-r89/e089_high_power.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E105_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E105_rows.csv", index=False)

    print("units=%d (R88 had 48) cells=%d cv_r2=%.4f" % (
        len(r), res["audit"]["cells"], res["audit"]["mean_cv_r2_of_additive_null"] or float("nan")))
    if s:
        print("  base=%.4f random=%.4f gene=%.4f identity=%.4f" % (
            s["base"], s["random"], s["gene"], s["identity"]))
        c2 = s["gene_minus_identity"]
        print("  gene - identity = %+.4f [%+.4f,%+.4f]" % (c2["mean_diff"], c2["ci95"][0], c2["ci95"][1]))
        c = s["gene_minus_random"]
        print("  gene - random = %+.4f [%+.4f,%+.4f]" % (c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
