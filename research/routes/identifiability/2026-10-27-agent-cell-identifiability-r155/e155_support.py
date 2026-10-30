"""E155: is the pathway prior's value moderated by how reliable the available information is?

The conditional rule has only ever varied on one axis: how many drugs are unseen. But there is a second
axis in any real decision - how well the visible drug is characterised. A drug seen thirty times has a
noisy marginal; one seen twelve hundred times does not. This asks whether the pathway gain depends on
that.

Pre-registered in PROTOCOL_E145.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r155"
LAMBDA = 1.0
REPEATS = 200
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261056
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "SYNERGY_DELTA_EMAX"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def paired(a, b, off):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    m = len(j)
    if m < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(SEED + off)
    boots = [float(np.mean(rng.choice(dif, size=m, replace=True))) for _ in range(N_BOOT)]
    return {"n": int(m), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


def oh(vals, levels):
    ix = {v: i for i, v in enumerate(levels)}
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        M[t, ix[v]] = 1.0
    return M


def ridge_fp(Xtr, ytr, Xte, lam=LAMBDA):
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
    return ytr.mean() + ((Xte - mu) / sd) @ w


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xpath = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                       oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xboth = np.hstack([Xid, Xpath])
    y = g["emax"].to_numpy(float)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(HOLDOUT * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        tr = np.where((~au) & (~bu))[0]
        pool = np.where(au ^ bu)[0]          # exactly one drug unseen
        if len(tr) < 15000 or len(pool) < 300:
            continue
        # support of the SEEN drug inside the training set
        seen_count = {}
        for i in tr:
            seen_count[A[i]] = seen_count.get(A[i], 0) + 1
            seen_count[B[i]] = seen_count.get(B[i], 0) + 1
        ytr = y[tr]
        p_id = ridge_fp(Xid[tr], ytr, Xid[pool])
        p_pa = ridge_fp(Xboth[tr], ytr, Xboth[pool])
        sup = np.array([seen_count.get(B[i] if au[i] else A[i], 0) for i in pool], dtype=float)
        q1, q2 = np.quantile(sup, [1 / 3, 2 / 3])
        for name, mask in (("low", sup <= q1), ("mid", (sup > q1) & (sup <= q2)), ("high", sup > q2)):
            if mask.sum() < 80:
                continue
            yt = y[pool][mask]
            if np.std(yt) == 0:
                continue
            hi = (yt >= np.quantile(yt, 0.75)).astype(float)
            ri = spearmanr(p_id[mask], yt).statistic
            rp = spearmanr(p_pa[mask], yt).statistic
            rows.append({"rep": rep, "band": name, "n": int(mask.sum()),
                         "support_med": float(np.median(sup[mask])),
                         "rho_identity": 0.0 if not np.isfinite(ri) else float(ri),
                         "rho_pathway": 0.0 if not np.isfinite(rp) else float(rp)})

    r = pd.DataFrame(rows)
    res = {"kind": "does_the_seen_drugs_support_moderate_the_pathway_gain",
           "input_sha256": sha256(ORIG),
           "settings": {"repeats": REPEATS, "holdout": HOLDOUT, "seed": SEED, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_band": {}, "files": {}}
    for band in ("low", "mid", "high"):
        sub = r[r.band == band].set_index("rep")
        if len(sub) < 10:
            continue
        res["by_band"][band] = {
            "n": int(len(sub)), "support_med": float(sub["support_med"].mean()),
            "rho_identity": float(sub["rho_identity"].mean()),
            "rho_pathway": float(sub["rho_pathway"].mean()),
            "gain": paired(sub["rho_pathway"], sub["rho_identity"], 68001 + len(band))}
    if "low" in res["by_band"] and "high" in res["by_band"]:
        lo = r[r.band == "low"].set_index("rep")
        hi = r[r.band == "high"].set_index("rep")
        gl = lo["rho_pathway"] - lo["rho_identity"]
        gh = hi["rho_pathway"] - hi["rho_identity"]
        res["low_minus_high"] = paired(gl, gh, 68101)
    lh = res.get("low_minus_high") or {}
    h376 = bool(lh and lh["ci95"][0] > 0)
    res["decisions"] = {"gain_low": res["by_band"].get("low", {}).get("gain", {}).get("mean_diff"),
                        "gain_mid": res["by_band"].get("mid", {}).get("gain", {}).get("mean_diff"),
                        "gain_high": res["by_band"].get("high", {}).get("gain", {}).get("mean_diff"),
                        "low_minus_high": lh.get("mean_diff") if lh else None,
                        "H376_support_moderates": h376, "H377_no_moderation": not h376}
    res["decisions"]["verdict"] = (
        "the_pathway_gain_is_larger_when_the_seen_drug_is_poorly_characterised" if h376 else
        "the_pathway_gain_does_not_depend_on_the_seen_drugs_support")
    res["limits"] = ["Bands are within-split terciles, so only within-split comparisons are meaningful.",
                     "Only ridge and only this resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r155/PROTOCOL_E145.md",
                "research/2026-10-27-agent-cell-identifiability-r155/e155_support.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E155_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E155_rows.csv", index=False)

    print("rows=%d" % len(r))
    for band, e in res["by_band"].items():
        g2 = e["gain"]
        print("  [%-4s] n=%3d support_med %.0f | rho_id %+.4f rho_path %+.4f | gain %+.4f [%+.4f,%+.4f]" % (
            band, e["n"], e["support_med"], e["rho_identity"], e["rho_pathway"],
            g2["mean_diff"], g2["ci95"][0], g2["ci95"][1]))
    if lh:
        print("  low - high: %+.4f [%+.4f,%+.4f]" % (lh["mean_diff"], lh["ci95"][0], lh["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
