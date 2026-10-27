"""E024: is the missing tail the transferable interaction residual?

Pre-registered in PROTOCOL_E024.md. Reads only PAIR_SCREEN.csv.

Baseline A: within-cell additive model (y ~ mu + a_A + a_B, ridge lambda fixed), exact LOO.
Treatment B: A plus the mean additive residual of the other cells for the same compound pair
(other cells only; no data from the target cell for that pair).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r24"
ANCHORS = {"high control", "low control"}
LAMBDA = 1.0
TOP = 10
N_BOOT = 1000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a, b) -> float:
    if len(a) < 8:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def fit_loo(X: np.ndarray, y: np.ndarray, lam: float = LAMBDA):
    n, p = X.shape
    xm = X.mean(axis=0)
    Xc = X - xm
    ym = float(y.mean())
    yc = y - ym
    A = Xc.T @ Xc + lam * np.eye(p)
    H = Xc @ np.linalg.inv(A) @ Xc.T
    h = np.clip(np.diag(H), 0.0, 1.0 - 1e-9)
    fit = ym + H @ yc
    loo = y - (y - fit) / (1.0 - h)
    resid = y - fit
    return loo, resid, h


def design(pairs, comps_idx):
    X = np.zeros((len(pairs), len(comps_idx)))
    for i, (a, b) in enumerate(pairs):
        X[i, comps_idx[a]] += 1.0
        X[i, comps_idx[b]] += 1.0
    return X


def p_at_k(pred, truth, k=TOP):
    n = len(pred)
    kk = min(k, n - 1)
    return len(set(np.argsort(pred)[:kk]) & set(np.argsort(truth)[:kk])) / kk


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["c1"] = pd.to_numeric(df["Conc 1 (uM)"], errors="coerce")
    df["c2"] = pd.to_numeric(df["Conc 2 (uM)"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    ok = df[(~df["anchor"]) & (~df["failed_qc"]) & df["y"].notna()]

    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["c1"].round(9), g["Drug 2"], g["c2"].round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "qc": float(g["failed_qc"].mean()),
                       "npairs": int(g.groupby(["Drug 1", "Drug 2"]).ngroups)}
    groups = {}
    for f, s in meta.items():
        groups.setdefault(s["h"], {}).setdefault(s["cell"], []).append(f)

    rows, resid_pairs = [], []
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 2:
            continue
        if max(meta[f]["npairs"] for c in good for f in cells[c]) < 100:
            continue
        per_cell = {}
        for c in good:
            vs = []
            for f in cells[c]:
                s = ok[ok["file"] == f]
                v = s.groupby(["Drug 1", "Drug 2"])["y"].mean()
                if len(v) >= 100:
                    vs.append(v)
            if vs:
                per_cell[c] = pd.concat(vs, axis=1).mean(axis=1).dropna()
        cs = sorted(per_cell)
        if len(cs) < 2:
            continue
        comps = sorted({d for c in cs for p in per_cell[c].index for d in p})
        cidx = {d: i for i, d in enumerate(comps)}
        fits = {}
        for c in cs:
            ser = per_cell[c]
            X = design(list(ser.index), cidx)
            loo, resid, _ = fit_loo(X, ser.to_numpy(float))
            fits[c] = {"pairs": list(ser.index), "y": ser.to_numpy(float), "loo": loo,
                       "resid": resid, "idx": {p: i for i, p in enumerate(ser.index)}}
        # residual conservation between cell pairs (H055)
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                a, b = fits[cs[i]], fits[cs[j]]
                common = [p for p in a["pairs"] if p in b["idx"]]
                if len(common) < 100:
                    continue
                ra = np.array([a["resid"][a["idx"][p]] for p in common])
                rb = np.array([b["resid"][b["idx"][p]] for p in common])
                r = spearman(ra, rb)
                if np.isfinite(r):
                    resid_pairs.append({"layout": h[:12], "cell_a": cs[i], "cell_b": cs[j],
                                        "rho_resid": r, "n": len(common)})
        # treatment vs baseline (H056)
        for c in cs:
            others = [x for x in cs if x != c]
            if not others:
                continue
            ser = fits[c]
            trans = np.zeros(len(ser["pairs"]))
            counts = np.zeros(len(ser["pairs"]))
            for o in others:
                fo = fits[o]
                for k, p in enumerate(ser["pairs"]):
                    if p in fo["idx"]:
                        trans[k] += fo["resid"][fo["idx"][p]]
                        counts[k] += 1
            mask_has = counts > 0
            if mask_has.sum() < 100:
                continue
            trans = np.where(counts > 0, trans / np.maximum(counts, 1), 0.0)
            y = ser["y"]
            loo = ser["loo"]
            pred_b = loo + trans
            sel = mask_has
            rows.append({"layout": h[:12], "cell": c, "n": int(sel.sum()),
                         "rho_A": spearman(loo[sel], y[sel]), "rho_B": spearman(pred_b[sel], y[sel]),
                         "p10_A": p_at_k(loo[sel], y[sel]), "p10_B": p_at_k(pred_b[sel], y[sel]),
                         "trans_sd": float(np.std(trans[sel]))})

    d = pd.DataFrame(rows)
    rp = pd.DataFrame(resid_pairs)
    res = {"kind": "transferable_interaction_residual_for_the_tail",
           "input_sha256": sha256(CSV),
           "settings": {"lambda": LAMBDA, "top": TOP, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(len(d)), "layouts": int(d["layout"].nunique()) if len(d) else 0,
                     "residual_pairs": int(len(rp))},
           "files": {}}

    def bsum(v, seed_off):
        v = np.asarray(v, float)
        v = v[np.isfinite(v)]
        if not len(v):
            return None
        rng = np.random.default_rng(SEED + seed_off)
        boots = [float(np.mean(rng.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
        return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)),
                "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}

    if len(rp):
        res["residual_conservation"] = bsum(rp["rho_resid"].to_numpy(float), 31)
        res["residual_conservation"]["frac_positive"] = float((rp["rho_resid"] > 0).mean())
    if len(d):
        res["baseline_A"] = {"precision10": bsum(d["p10_A"].to_numpy(float), 32),
                             "spearman": bsum(d["rho_A"].to_numpy(float), 33)}
        res["treatment_B"] = {"precision10": bsum(d["p10_B"].to_numpy(float), 34),
                              "spearman": bsum(d["rho_B"].to_numpy(float), 35)}
        res["paired"] = {
            "precision10_B_minus_A": bsum((d["p10_B"] - d["p10_A"]).to_numpy(float), 36),
            "spearman_B_minus_A": bsum((d["rho_B"] - d["rho_A"]).to_numpy(float), 37)}
        dl = bsum((d["p10_B"] - d["p10_A"]).to_numpy(float), 38)
        ds = bsum((d["rho_B"] - d["rho_A"]).to_numpy(float), 39)
        h055 = bool(res.get("residual_conservation") and res["residual_conservation"]["ci95"][0] > 0)
        h056 = bool(dl and dl["mean"] > 0 and dl["ci95"][0] > 0)
        h057 = bool(dl and dl["mean"] > 0 and ds and abs(ds["mean"]) <= 0.01)
    else:
        h055 = h056 = h057 = False
    res["decisions"] = {"H055_residual_conserved": h055, "H056_transfer_fixes_tail": h056,
                        "H057_gain_concentrated_in_tail": h057}
    res["decisions"]["verdict"] = ("tail_is_transferable_interaction" if h056 else
                                   "tail_is_not_transferable_interaction")
    res["limits"] = [
        "The residual is a deviation from additivity, not a mechanism or a target effect.",
        "This is an unseen COMBINATION, not an unseen drug.",
        "No dose dimension; viability is clipped at 1.0 (17.9% exactly 1.0), which coarsens the top-10.",
        "The additive model is fitted per cell with a fixed ridge penalty and no tuning.",
        "Exploratory: plates were used as scoring endpoints earlier and cells cross days.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r24/PROTOCOL_E024.md",
                "research/2026-10-27-agent-cell-identifiability-r24/e024_residual_transfer.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E024_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(d):
        d.to_csv(OUT / "E024_units.csv", index=False)
    if len(rp):
        rp.to_csv(OUT / "E024_residual_pairs.csv", index=False)

    print("units=%d layouts=%d residual_pairs=%d" % (len(d), res["audit"]["layouts"], len(rp)))
    for k in ("residual_conservation", "baseline_A", "treatment_B", "paired"):
        if k in res:
            print(k, json.dumps(res[k], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
