"""E086: does the main conclusion (drug marginals beat pathway models) reproduce on BATCHIE,
the second resource?

Leave-one-cell-out within each high-diversity layout; four predictors sharing the same
training cells. Pre-registered in PROTOCOL_E081.md.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r86"
ANCHORS = {"high control", "low control"}
K = 20
REPEATS = 20
LAMBDA = 1.0
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
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    ok = df[(~df["anchor"]) & (~df["failed_qc"]) & df["y"].notna()].copy()

    # group files by layout (same well/drug/concentration grid) and cell
    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["Drug 2"])))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "qc": float(g["failed_qc"].mean()),
                       "npairs": int(g.groupby(["Drug 1", "Drug 2"]).ngroups)}
    groups = {}
    for f, s in meta.items():
        groups.setdefault(s["h"], {}).setdefault(s["cell"], []).append(f)

    # gene-level annotation from MAPKG (finer than pathway, a stronger test for the annotation arm)
    pathways = {}
    ap = ROOT / "data" / "external" / "mapkg_20261009" / "DRUG-GENE_filtered_by_existing_drugs_and_genes.csv"
    dm_path = ROOT / "data" / "external" / "mapkg_20261009" / "DRUG_merged_drugs_with_residuals.csv"
    if ap.exists() and dm_path.exists():
        dmap = pd.read_csv(dm_path, low_memory=False)
        gene = pd.read_csv(ap, low_memory=False)
        n2i = dict(zip(dmap["Drug Name"].astype(str).str.strip(), dmap["PubChem ID"]))
        i2g = gene.groupby("Drug ID")["Gene ID"].apply(lambda s: frozenset(s)).to_dict()
        for nm, pid in n2i.items():
            if pid in i2g:
                pathways[nm] = i2g[pid]
    n_drugs_annot = sum(1 for g in sorted(set(ok["Drug 1"]) | set(ok["Drug 2"])) if g in pathways)

    rng = np.random.default_rng(SEED)
    rows = []
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        # per-cell pair means
        per = {}
        for c in good:
            vs = []
            for f in cells[c]:
                s = ok[ok["file"] == f]
                v = s.groupby(["Drug 1", "Drug 2"])["y"].mean()
                if len(v) >= 100:
                    vs.append(v)
            if vs:
                per[c] = pd.concat(vs, axis=1).mean(axis=1).dropna()
        if len(per) < 3:
            continue
        for _ in range(REPEATS):
            held = rng.choice(sorted(per))
            tr_cells = [c for c in sorted(per) if c != held]
            pairs = [p for p in per[held].index if all(p in per[c].index for c in tr_cells)]
            if len(pairs) < 150:
                continue
            Ytr = np.column_stack([per[c].loc[pairs].to_numpy(float) for c in tr_cells])
            yheld = per[held].loc[pairs].to_numpy(float)
            hits = (yheld <= np.quantile(yheld, 0.25)).astype(float)

            # (a) marginal: per-drug mean over training cells
            dm_ = {}
            for gi, c in enumerate(tr_cells):
                for pi, (d1, d2) in enumerate(pairs):
                    dm_.setdefault(d1, []).append(Ytr[pi, gi])
                    dm_.setdefault(d2, []).append(Ytr[pi, gi])
            drug_mean = {g: float(np.mean(v)) for g, v in dm_.items()}
            sc_marg = np.array([0.5 * (drug_mean.get(d1, np.nan) + drug_mean.get(d2, np.nan)) for d1, d2 in pairs])
            ok_m = np.isfinite(sc_marg)

            # (b) ridge on compound identity
            comps = sorted({d for p in pairs for d in p})
            cidx = {d: i for i, d in enumerate(comps)}
            Xid = np.zeros((len(pairs), len(comps)))
            for pi, (d1, d2) in enumerate(pairs):
                Xid[pi, cidx[d1]] += 1.0
                Xid[pi, cidx[d2]] += 1.0

            # (c) ridge on gene annotation (a drug is represented by its target genes)
            genes = sorted({g for p in pairs for d in p if d in pathways for g in pathways[d]})
            sc_path = None
            if len(genes) > 5 and n_drugs_annot >= 10:
                gidx = {g: i for i, g in enumerate(genes)}
                Xp = np.zeros((len(pairs), len(genes)))
                for pi, (d1, d2) in enumerate(pairs):
                    for d in (d1, d2):
                        for g in pathways.get(d, ()):
                            if g in gidx:
                                Xp[pi, gidx[g]] += 1.0
                if (Xp.sum(axis=1) > 0).mean() > 0.7:
                    sc_path = Xp

            def ridge_score(X, ymean_target):
                ytr = Ytr.mean(axis=1)          # training target: mean over training cells
                mu, sd = X.mean(axis=0), X.std(axis=0)
                sd[sd == 0] = 1.0
                Xs = (X - mu) / sd
                A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
                w = np.linalg.solve(A, Xs.T @ (ytr - ytr.mean()))
                return ytr.mean() + Xs @ w

            sc_id = ridge_score(Xid, None)
            sc_pa = ridge_score(sc_path, None) if sc_path is not None else None

            def hitrate(score, mask=None):
                if score is None:
                    return np.nan
                s = score.copy()
                if mask is not None:
                    s = np.where(mask, s, np.inf)
                order = np.argsort(s)[:K]      # LOW viability = more synergistic
                return float(hits[order].mean())

            rows.append({"layout": h[:12], "cell": held, "n_pairs": len(pairs),
                         "marginal": hitrate(sc_marg, ok_m),
                         "ridge_identity": hitrate(sc_id),
                         "ridge_pathway": hitrate(sc_pa),
                         "random": float(hits[rng.choice(len(pairs), size=K, replace=False)].mean()),
                         "base": float(hits.mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "main_conclusion_replicated_on_BATCHIE",
           "input_sha256": sha256(CSV),
           "settings": {"k": K, "repeats": REPEATS, "lambda": LAMBDA, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(len(r)), "cells": int(r["cell"].nunique()) if len(r) else 0,
                     "drugs_annotated_with_pathway": int(n_drugs_annot)},
           "summary": {}, "files": {}}

    if len(r) >= 5:
        res["summary"] = {
            "n": int(len(r)),
            "marginal": float(r["marginal"].mean()),
            "ridge_identity": float(r["ridge_identity"].mean()),
            "ridge_pathway": float(r["ridge_pathway"].mean()),
            "random": float(r["random"].mean()),
            "base": float(r["base"].mean()),
            "marginal_minus_pathway": paired(r["marginal"], r["ridge_pathway"], 13001),
            "marginal_minus_identity": paired(r["marginal"], r["ridge_identity"], 13101),
            "identity_minus_pathway": paired(r["ridge_identity"], r["ridge_pathway"], 13201),
            "pathway_minus_random": paired(r["ridge_pathway"], r["random"], 13301),
            "marginal_minus_random": paired(r["marginal"], r["random"], 13401)}
    s = res["summary"]
    h218 = bool(s and s["marginal_minus_pathway"]["ci95"][0] > 0)
    h219 = bool(s and s["marginal_minus_identity"]["ci95"][0] <= 0 <= s["marginal_minus_identity"]["ci95"][1])
    pw = s.get("pathway_minus_random") if s else None
    h220 = bool(pw and pw["ci95"][0] <= 0)
    res["decisions"] = {"H218_marginal_beats_pathway_on_BATCHIE": h218,
                        "H219_marginal_close_to_identity": h219,
                        "H220_pathway_no_better_than_random": h220}
    res["decisions"]["verdict"] = (
        "main_conclusion_replicates_on_the_second_resource" if h218
        else "main_conclusion_is_GDSC_specific")
    res["limits"] = [
        "BATCHIE has 351 pairs per plate and 23 compounds, so pathway coverage is thin.",
        "Viability and the GDSC synergy score are different quantities; only ordering is compared.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r86/PROTOCOL_E081.md",
                "research/2026-10-27-agent-cell-identifiability-r86/e086_second_resource.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E086_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E086_rows.csv", index=False)

    print("units=%d cells=%d drugs_annotated=%d" % (len(r), res["audit"]["cells"], n_drugs_annot))
    if s:
        for name in ("base", "random", "ridge_pathway", "marginal", "ridge_identity"):
            print("  %-16s %.4f" % (name, s[name]))
        for name in ("marginal_minus_pathway", "marginal_minus_identity",
                     "identity_minus_pathway", "pathway_minus_random"):
            c = s[name]
            print("  %-24s %+.4f [%+.4f,%+.4f]" % (name, c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
