"""E046: is the global-metric versus decision-tail inversion systematic across model variants,
or was it coincidental in the three places it appeared?

Pre-registered in PROTOCOL_E045.md. Same data, same 40 grouped splits; only the model varies.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r46"
METRIC = "SYNERGY_DELTA_AUC"
REPEATS = 40
LAMBDAS = (0.1, 1.0, 5.0, 20.0, 50.0, 200.0)
LAM_INTERS = (2.0, 5.0, 20.0, 50.0, 200.0)
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rank_corr(a, b):
    a = pd.Series(a).rank().to_numpy()
    b = pd.Series(b).rank().to_numpy()
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt((a ** 2).sum() * (b ** 2).sum())
    return float((a * b).sum() / den) if den > 0 else np.nan


def onehot(vals, levels):
    M = np.zeros((len(vals), len(levels)))
    for j, v in enumerate(levels):
        M[:, j] = (vals == v).astype(float)
    return M


def ridge_block(Xb, y, lam, Xtb):
    ym = float(y.mean())
    B = Xb - Xb.mean(axis=0)
    A = B.T @ B + lam * np.eye(B.shape[1])
    w = np.linalg.solve(A, B.T @ (y - ym))
    return ym + (Xtb - Xb.mean(axis=0)) @ w


def ridge_two(Xb, Xi, y, lam_b, lam_i, Xtb, Xti):
    ym = float(y.mean())
    B = Xb - Xb.mean(axis=0)
    I = Xi - Xi.mean(axis=0)
    X = np.hstack([B, I])
    pen = np.concatenate([np.full(B.shape[1], lam_b), np.full(I.shape[1], lam_i)])
    A = X.T @ X + np.diag(pen)
    w = np.linalg.solve(A, X.T @ (y - ym))
    Xte = np.hstack([Xtb - Xb.mean(axis=0), Xti - Xi.mean(axis=0)])
    return ym + Xte @ w


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        combo=("combo", "first"), tissue=("Tissue", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("tissue", "ap", "lp"):
        d[c] = d[c].astype(str).fillna("NA")

    ti = sorted(d["tissue"].unique())
    ap = sorted(d["ap"].unique())
    lp = sorted(d["lp"].unique())
    T = onehot(d["tissue"].to_numpy(), ti)
    A = onehot(d["ap"].to_numpy(), ap)
    L = onehot(d["lp"].to_numpy(), lp)
    feats = {
        "tissue": T,
        "pathway": np.hstack([T, A, L]),
        "full": np.hstack([T, A, L]),
    }
    inter = np.hstack([T[:, [j]] * np.hstack([A, L]) for j in range(len(ti))])
    y = d.synergy.to_numpy(float)
    combo = d["combo"].to_numpy()
    combos = pd.unique(combo)

    variants = []
    for fs in ("tissue", "pathway"):
        for lam in LAMBDAS:
            variants.append(("ridge", fs, lam, None))
    for lam_i in LAM_INTERS:
        variants.append(("hier", "pathway", 1.0, lam_i))

    rng = np.random.default_rng(SEED)
    splits = []
    for _ in range(REPEATS):
        order = rng.permutation(len(combos))
        n_tr = int(0.8 * len(combos))
        tr_combos = set(combos[order[:n_tr]])
        tr = np.array([i for i, c in enumerate(combo) if c in tr_combos])
        pool = np.array([i for i, c in enumerate(combo) if c not in tr_combos])
        if len(tr) >= 5000 and len(pool) >= 2000:
            splits.append((tr, pool))

    rows = []
    for kind, fs, lam, lam_i in variants:
        name = f"{kind}:{fs}:lam{lam:g}" + (f":li{lam_i:g}" if lam_i else "")
        for rep, (tr, pool) in enumerate(splits):
            yp = y[pool]
            k10 = max(1, int(0.10 * len(yp)))
            strong = yp >= np.quantile(yp, 0.90)
            if kind == "ridge":
                Xb = feats[fs]
                pred = ridge_block(Xb[tr], y[tr], lam, Xb[pool])
            else:
                Xb = feats[fs]
                pred = ridge_two(Xb[tr], inter[tr], y[tr], lam, lam_i, Xb[pool], inter[pool])
            rows.append({"variant": name, "kind": kind, "fs": fs, "lam": lam,
                         "lam_i": lam_i if lam_i else np.nan, "rep": rep,
                         "rho": rank_corr(pred, yp),
                         "p10": float(np.mean(strong[np.argsort(-pred)[:k10]]))})

    r = pd.DataFrame(rows)
    agg = r.groupby(["variant", "kind", "fs", "lam"], as_index=False).agg(
        rho=("rho", "mean"), p10=("p10", "mean"))
    base = agg[(agg.kind == "ridge") & (agg.fs == "pathway") & (np.isclose(agg.lam, 1.0))]
    if len(base):
        b_rho = float(base["rho"].iloc[0])
        b_p10 = float(base["p10"].iloc[0])
    else:
        b_rho, b_p10 = float(agg["rho"].mean()), float(agg["p10"].mean())
    agg["d_rho"] = agg["rho"] - b_rho
    agg["d_p10"] = agg["p10"] - b_p10

    def sp(a, b):
        return rank_corr(a, b)

    def boot_sp(a, b, off):
        rng2 = np.random.default_rng(SEED + off)
        n = len(a)
        vals = []
        for _ in range(N_BOOT):
            idx = rng2.integers(0, n, n)
            if np.std(a[idx]) > 0 and np.std(b[idx]) > 0:
                vals.append(rank_corr(a[idx], b[idx]))
        return [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))] if vals else None

    res = {"kind": "systematic_inversion_between_global_and_tail_metrics",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambdas": list(LAMBDAS), "lam_inters": list(LAM_INTERS),
                        "repeats": len(splits), "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "variants": int(len(agg)), "splits": len(splits),
                     "baseline": {"variant": "ridge:pathway:lam1", "rho": b_rho, "p10": b_p10}},
           "variants": agg.to_dict(orient="records"), "files": {}}

    a_all, b_all = agg["d_rho"].to_numpy(), agg["d_p10"].to_numpy()
    res["inversion"] = {
        "spearman_d_rho_vs_d_p10": sp(a_all, b_all),
        "ci_all": boot_sp(a_all, b_all, 101),
        "n_variants": int(len(agg))}
    for sub, name in ((agg[agg.kind == "ridge"], "ridge_only"), (agg[agg.kind == "hier"], "hier_only")):
        if len(sub) >= 4:
            res["inversion"][name] = {
                "spearman": sp(sub["d_rho"].to_numpy(), sub["d_p10"].to_numpy()),
                "n": int(len(sub))}
    res["inversion"]["levels"] = {
        "spearman_rho_vs_p10": sp(agg["rho"].to_numpy(), agg["p10"].to_numpy()),
        "ci": boot_sp(agg["rho"].to_numpy(), agg["p10"].to_numpy(), 102)}

    inv = res["inversion"]
    h118 = bool(inv["spearman_d_rho_vs_d_p10"] < 0 and inv["ci_all"] and inv["ci_all"][1] < 0)
    h119 = bool(inv.get("ridge_only", {}).get("spearman", 1) < 0 and inv.get("hier_only", {}).get("spearman", 1) < 0)
    lev = inv["levels"]
    h120 = bool(lev["spearman_rho_vs_p10"] < 0 and abs(lev["spearman_rho_vs_p10"]) > 0.3)
    res["decisions"] = {"H118_systematic_inversion": h118, "H119_in_both_families": h119,
                        "H120_levels_negatively_related": h120}
    res["decisions"]["verdict"] = ("inversion_is_systematic" if h118 and h119 else
                                   "inversion_not_systematic")
    res["limits"] = [
        "Single dataset, two model families, fixed metric definitions (rho and top-decile precision@10).",
        "Variants share data and splits, so only the model differs - which is the point, but it also means the range of rho explored is narrow.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r46/PROTOCOL_E045.md",
                "research/2026-10-27-agent-cell-identifiability-r46/e046_inversion.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E046_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    agg.to_csv(OUT / "E046_variants.csv", index=False)
    r.to_csv(OUT / "E046_rows.csv", index=False)

    print("keys=%d variants=%d splits=%d | baseline rho=%.4f p10=%.4f" % (
        res["audit"]["keys"], len(agg), len(splits), b_rho, b_p10))
    print("  variants (sorted by d_rho):")
    for _, row in agg.sort_values("d_rho").iterrows():
        print("    %-28s rho=%.4f p10=%.4f | d_rho %+.4f d_p10 %+.4f" % (
            row["variant"], row["rho"], row["p10"], row["d_rho"], row["d_p10"]))
    print("  inversion:", json.dumps(inv, ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
