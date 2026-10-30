"""E104: cross-dataset replication of "annotation adds beyond identity" on BATCHIE.

The raw-viability arena saturates (R86), so the dose-aware additivity residual arena is used
(R88/R89 showed it is learnable, CV R2 about 0.65). Three arms share the training rows:
identity, identity+gene annotation, and identity+random as a capacity control.

Pre-registered in PROTOCOL_E099.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r104"
ANCHORS = {"high control", "low control"}
K = 20
REPEATS = 8
BLOCKS = 5
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

    # gene universe: genes appearing for at least 5 drugs
    gc = {}
    for nm, gs in genes.items():
        for g0 in gs:
            gc[g0] = gc.get(g0, 0) + 1
    gene_lv = sorted([g0 for g0, c in gc.items() if c >= 5])

    rng = np.random.default_rng(SEED)
    rows, cvr2 = [], []
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 4:
            continue
        frames = {c: ok[ok["file"].isin(cells[c])] for c in good}
        drugs = sorted({d for f in frames.values() for d in list(f["Drug 1"]) + list(f["Drug 2"])})
        if len(gene_lv) < 5:
            continue
        gidx = {g0: i for i, g0 in enumerate(gene_lv)}
        didx = {d: i for i, d in enumerate(drugs)}
        nd, ng = len(drugs), len(gene_lv)
        per = {}
        for c in good:
            f = frames[c]
            d1 = f["Drug 1"].tolist()
            d2 = f["Drug 2"].tolist()
            lc1 = np.log10(np.clip(f["c1"].to_numpy(), 1e-9, None))
            lc2 = np.log10(np.clip(f["c2"].to_numpy(), 1e-9, None))
            Y = f["y"].to_numpy(float)
            Xadd = np.zeros((len(Y), 4 * nd))
            Xid = np.zeros((len(Y), 2 * nd))
            Xg = np.zeros((len(Y), ng))
            for t in range(len(Y)):
                i1, i2 = didx[d1[t]], didx[d2[t]]
                Xadd[t, i1] = 1.0
                Xadd[t, nd + i2] = 1.0
                Xadd[t, 2 * nd + i1] = lc1[t]
                Xadd[t, 3 * nd + i2] = lc2[t]
                Xid[t, i1] = 1.0
                Xid[t, nd + i2] = 1.0
                for d in (d1[t], d2[t]):
                    for g0 in genes.get(d, ()):
                        if g0 in gidx:
                            Xg[t, gidx[g0]] += 1.0
            per[c] = {"Xadd": Xadd, "Xid": Xid, "Xg": Xg, "Y": Y, "pairs": list(zip(d1, d2))}
        if not gene_lv:
            continue

        for _ in range(REPEATS):
            held = good[int(rng.integers(0, len(good)))]
            tr_cells = [c for c in good if c != held]
            Xa = np.vstack([per[c]["Xadd"] for c in tr_cells])
            ya = np.concatenate([per[c]["Y"] for c in tr_cells])
            cid = np.concatenate([[i] * len(per[c]["Y"]) for i, c in enumerate(tr_cells)])
            C = np.zeros((len(cid), len(tr_cells)))
            C[np.arange(len(cid)), cid] = 1.0
            XA = np.hstack([Xa, C])
            mu_a, sd_a = XA.mean(axis=0), XA.std(axis=0); sd_a[sd_a == 0] = 1.0
            ZA = (XA - mu_a) / sd_a
            wA = np.linalg.solve(ZA.T @ ZA + 100.0 * np.eye(ZA.shape[1]), ZA.T @ (ya - ya.mean()))
            pt = ya.mean() + ZA @ wA
            ss = float(np.sum((ya - pt) ** 2)); tot = float(np.sum((ya - ya.mean()) ** 2))
            cvr2.append(1.0 - ss / tot if tot > 0 else np.nan)
            m = None
            Xh = np.hstack([per[held]["Xadd"], np.zeros((len(per[held]["Y"]), len(tr_cells)))])
            ZH = (Xh - mu_a) / sd_a
            r_tr = ya - pt
            r_held = per[held]["Y"] - (ya.mean() + ZH @ wA)

            Xid_tr = np.vstack([per[c]["Xid"] for c in tr_cells])
            Xg_tr = np.vstack([per[c]["Xg"] for c in tr_cells])
            if len(np.unique(r_tr)) < 10:
                continue

            def ridge_fit_predict(XX_tr, XX_h):
                mu, sd = XX_tr.mean(axis=0), XX_tr.std(axis=0); sd[sd == 0] = 1.0
                Z = (XX_tr - mu) / sd
                w = np.linalg.solve(Z.T @ Z + 10.0 * np.eye(Z.shape[1]), Z.T @ (r_tr - r_tr.mean()))
                return r_tr.mean() + ((XX_h - mu) / sd) @ w

            s_id = ridge_fit_predict(Xid_tr, per[held]["Xid"])
            s_gene = ridge_fit_predict(np.hstack([Xid_tr, Xg_tr]), np.hstack([per[held]["Xid"], per[held]["Xg"]]))
            s_rand = np.zeros(len(per[held]["Y"]))
            for _ in range(BLOCKS):
                R_tr = rng.normal(size=(len(Xid_tr), len(gene_lv)))
                R_h = rng.normal(size=(len(per[held]["Y"]), len(gene_lv)))
                s_rand += ridge_fit_predict(np.hstack([Xid_tr, R_tr]), np.hstack([per[held]["Xid"], R_h]))
            s_rand /= BLOCKS

            pairh = per[held]["pairs"]
            agg = {"id": {}, "gene": {}, "rand": {}}
            for i, p in enumerate(pairh):
                agg["id"].setdefault(p, []).append(s_id[i])
                agg["gene"].setdefault(p, []).append(s_gene[i])
                agg["rand"].setdefault(p, []).append(s_rand[i])
            tru = {}
            for i, p in enumerate(pairh):
                tru.setdefault(p, []).append(r_held[i])
            ps = list(agg["id"])
            if len(ps) < 60:
                continue
            tv = np.array([float(np.mean(tru[p])) for p in ps])
            hit = (tv <= np.quantile(tv, 0.25)).astype(float)
            row = {"layout": h[:12], "cell": held, "n": len(ps)}
            for nm in ("id", "gene", "rand"):
                sv = np.array([float(np.mean(agg[nm][p])) for p in ps])
                row[nm] = float(hit[np.argsort(sv)[:K]].mean())
            rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "cross_dataset_replication_on_BATCHIE_residual_arena",
           "input_sha256": sha256(CSV),
           "settings": {"k": K, "repeats": REPEATS, "blocks": BLOCKS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(len(r)), "cells": int(r["cell"].nunique()) if len(r) else 0,
                     "genes_used": len(gene_lv), "drugs_annotated": len(genes),
                     "in_sample_r2_additive_null": float(np.nanmean(cvr2)) if cvr2 else None},
           "summary": {}, "files": {}}
    if len(r) >= 5:
        res["summary"] = {
            "n": int(len(r)),
            "identity": float(r["id"].mean()),
            "identity_gene": float(r["gene"].mean()),
            "identity_random": float(r["rand"].mean()),
            "gene_minus_identity": paired(r["gene"], r["id"], 31001),
            "gene_minus_random": paired(r["gene"], r["rand"], 31101),
            "random_minus_identity": paired(r["rand"], r["id"], 31201)}
    s = res["summary"]
    h269 = bool(s and s["gene_minus_identity"]["ci95"][0] > 0)
    h270 = bool(s and s["gene_minus_random"]["ci95"][0] > 0)
    res["decisions"] = {"H269_replicates_cross_dataset": h269,
                        "H270_annotation_beats_capacity_control": h270,
                        "H271_does_not_replicate": bool(not h269)}
    res["decisions"]["verdict"] = (
        "cross_dataset_replication_holds" if h269 and h270 else
        "replicates_but_not_beyond_capacity" if h269 else
        "does_NOT_replicate_cross_dataset")
    res["limits"] = [
        "BATCHIE has about 23 compounds per layout and gene annotation covers 131 of 209 compounds.",
        "The residual arena is not the same target as GDSC's synergy call, so only the relative contrast is comparable.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r104/PROTOCOL_E099.md",
                "research/2026-10-27-agent-cell-identifiability-r104/e104_cross_dataset.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E104_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E104_rows.csv", index=False)

    print("units=%d genes=%d cv_r2=%.3f" % (len(r), len(gene_lv),
          res["audit"]["in_sample_r2_additive_null"] or float("nan")))
    if s:
        for k in ("identity", "identity_gene", "identity_random"):
            print("  %-18s %.4f" % (k, s[k]))
        for k in ("gene_minus_identity", "gene_minus_random", "random_minus_identity"):
            c = s[k]
            print("  %-24s %+.4f [%+.4f,%+.4f]" % (k, c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
