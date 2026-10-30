"""E118: the pair-level arena on BATCHIE - a third attempt at cross-dataset replication.

The two earlier attempts (R86, R105) were key-level: saturation in one, degenerate identity in the
other. Averaging residuals across cells gives a much less noisy target, and is the natural
pair-level analogue of GDSC's Synergy label.

Pre-registered in PROTOCOL_E111.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r118"
ANCHORS = {"high control", "low control"}
LAMBDA = 10.0
TEST_FRAC = 0.20
N_BOOT = 2000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def ridge_fit(X, y, lam):
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return mu, sd, w, float(y.mean())


def ridge_pred(X, mu, sd, w, b):
    return b + ((X - mu) / sd) @ w


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

    # ---- pair-level residual target, computed per layout over all cells ----
    layout_of = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["Drug 2"])))
        layout_of[fname] = hashlib.sha1(repr(layout).encode()).hexdigest()

    pair_res = []      # (layout, d1, d2, mean residual)
    for lay, sub in ok.assign(lay=ok["file"].map(layout_of)).groupby("lay"):
        drugs = sorted(set(sub["Drug 1"]) | set(sub["Drug 2"]))
        didx = {d: i for i, d in enumerate(drugs)}
        nd = len(drugs)
        cells = sorted(set(sub["Cell line"]))
        if len(cells) < 4 or nd < 5:
            continue
        cidx = {c: i for i, c in enumerate(cells)}
        X = np.zeros((len(sub), 4 * nd + len(cells)))
        for t, (_, r) in enumerate(sub.iterrows()):
            i1, i2 = didx[r["Drug 1"]], didx[r["Drug 2"]]
            X[t, i1] = 1.0
            X[t, nd + i2] = 1.0
            X[t, 2 * nd + i1] = np.log10(max(r["c1"], 1e-9))
            X[t, 3 * nd + i2] = np.log10(max(r["c2"], 1e-9))
            X[t, 4 * nd + cidx[r["Cell line"]]] = 1.0
        yv = sub["y"].to_numpy(float)
        mu, sd, w, b = ridge_fit(X, yv, 100.0)
        resid = yv - ridge_pred(X, mu, sd, w, b)
        tmp = pd.DataFrame({"d1": sub["Drug 1"].to_numpy(), "d2": sub["Drug 2"].to_numpy(),
                            "r": resid})
        agg = tmp.groupby(["d1", "d2"], as_index=False)["r"].mean()
        for _, r in agg.iterrows():
            pair_res.append((lay, r["d1"], r["d2"], float(r["r"])))
    pr = pd.DataFrame(pair_res, columns=["layout", "d1", "d2", "target"])
    if not len(pr):
        raise SystemExit("no pair-level residuals")

    gl = sorted({g for d in set(pr["d1"]) | set(pr["d2"]) for g in genes.get(d, ())})
    gidx = {g: i for i, g in enumerate(gl)}
    drugs = sorted(set(pr["d1"]) | set(pr["d2"]))
    didx = {d: i for i, d in enumerate(drugs)}
    n = len(pr)
    Xid = np.zeros((n, 2 * len(drugs)))
    Xg = np.zeros((n, len(gl)))
    for i, (a, b2) in enumerate(zip(pr["d1"], pr["d2"])):
        Xid[i, didx[a]] = 1.0
        Xid[i, didx[b2]] = 1.0
        for d in (a, b2):
            for g in genes.get(d, ()):
                if g in gidx:
                    Xg[i, gidx[g]] += 1.0
    y = pr["target"].to_numpy(float)

    # pair-hash split, so a pair never appears on both sides
    keys = (pr["d1"] + "|" + pr["d2"]).to_numpy()
    hh = np.array([int(hashlib.sha1(k.encode()).hexdigest()[:8], 16) % 1000 for k in keys])
    te = hh < int(TEST_FRAC * 1000)
    tr = ~te
    res = {"kind": "pair_level_arena_on_BATCHIE",
           "input_sha256": sha256(CSV),
           "settings": {"lambda": LAMBDA, "test_frac": TEST_FRAC, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"pairs": int(n), "train": int(tr.sum()), "test": int(te.sum()),
                     "layouts": int(pr["layout"].nunique()), "genes": len(gl),
                     "drugs": len(drugs)}, "files": {}}

    def evaluate(X):
        mu, sd, w, b = ridge_fit(X[tr], y[tr], LAMBDA)
        pred = ridge_pred(X[te], mu, sd, w, b)
        rho = float(spearmanr(pred, y[te]).statistic)
        ss = float(((y[te] - pred) ** 2).sum())
        tot = float(((y[te] - y[te].mean()) ** 2).sum())
        return rho, (1.0 - ss / tot if tot > 0 else float("nan"))

    rho_id, r2_id = evaluate(Xid)
    rho_g, r2_g = evaluate(np.hstack([Xid, Xg]))
    rho_pa = None

    rng = np.random.default_rng(SEED)
    boots = []
    idx_all = np.where(te)[0]
    for _ in range(N_BOOT):
        sel = rng.choice(idx_all, size=len(idx_all), replace=True)
        yb = y[sel]
        if np.std(yb) == 0:
            continue
        # refit on train, evaluate on the bootstrap selection
        def rho_on(X):
            mu, sd, w, b = ridge_fit(X[tr], y[tr], LAMBDA)
            p = ridge_pred(X[sel], mu, sd, w, b)
            return spearmanr(p, yb).statistic
        boots.append(rho_on(np.hstack([Xid, Xg])) - rho_on(Xid))
    boots = np.array(boots, float)
    diff = {"mean": float(np.nanmean(boots)),
            "ci95": [float(np.nanquantile(boots, 0.025)), float(np.nanquantile(boots, 0.975))]}

    res["results"] = {"identity_rho": rho_id, "identity_r2": r2_id,
                      "identity_gene_rho": rho_g, "identity_gene_r2": r2_g,
                      "rho_diff": diff}
    h293 = bool(rho_id > 0 and rho_id > 2.0 / np.sqrt(max(te.sum(), 2)))
    h294 = bool(diff["ci95"][0] > 0)
    h295 = bool(diff["ci95"][0] <= 0)
    res["decisions"] = {"H293_arena_has_signal": h293, "H294_annotation_adds": h294,
                        "H295_no_annotation_increment": h295}
    res["decisions"]["verdict"] = (
        "pair_level_replicates_annotation_increment" if h294 else
        "pair_level_arena_also_shows_no_increment" if h295 and h293 else
        "pair_level_arena_is_degenerate_too")
    res["limits"] = [
        "Only about 351 pairs per layout, and the pair-hash split puts few observations on the test side.",
        "The residual target still depends on the additive-null specification.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r118/PROTOCOL_E111.md",
                "research/2026-10-27-agent-cell-identifiability-r118/e118_pair_level.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E118_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    pr.to_csv(OUT / "E118_pairs.csv", index=False)

    print("pairs=%d train=%d test=%d layouts=%d genes=%d" % (
        n, tr.sum(), te.sum(), pr["layout"].nunique(), len(gl)))
    print("  identity      rho %.4f  R2 %.4f" % (rho_id, r2_id))
    print("  identity+gene rho %.4f  R2 %.4f" % (rho_g, r2_g))
    print("  rho diff %+.4f [%+.4f,%+.4f]" % (diff["mean"], diff["ci95"][0], diff["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
