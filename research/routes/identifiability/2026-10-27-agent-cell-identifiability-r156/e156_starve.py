"""E156: starve the visible drug's support and see whether the pathway prior gains value.

R155 could not test the information-quality condition because no drug in this resource is poorly
characterised (minimum support 921). This creates that regime deliberately: for a visible drug S keep
only k of its training keys, so identity's estimate of S is degraded while the pathway prior, which
borrows from the rest of S's pathway, is untouched.

Pre-registered in PROTOCOL_E146.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r156"
LAMBDA = 1.0
REPS = 20
N_BOOT = 2000
SEED = 20261057
KS = (20, 50, 200, 800, None)
PAIRS = 6
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "SYNERGY_DELTA_EMAX"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


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
    pair_key = ["%s|||%s" % tuple(sorted((x, z))) for x, z in zip(A, B)]

    index = {}
    for i, pk in enumerate(pair_key):
        index.setdefault(pk, []).append(i)
    usable_pairs = [pk for pk, idxs in index.items() if len(idxs) >= 40]

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPS):
        order = usable_pairs[:]; rng.shuffle(order)
        chosen = order[:PAIRS]
        for pk in chosen:
            S, H = pk.split("|||")
            for k in KS:
                eval_idx = np.array(index[pk])
                if len(eval_idx) < 40:
                    continue
                contains_H = (A == H) | (B == H)
                tr = np.where(~contains_H)[0]
                if k is not None:
                    has_S = ((A == S) | (B == S))[tr]
                    keep_S = rng.random(has_S.sum()) < (k / max(1, has_S.sum()))
                    tr = np.concatenate([tr[~has_S], tr[has_S][keep_S]])
                if len(tr) < 15000:
                    continue
                ytr = y[tr]
                p_id = ridge_fp(Xid[tr], ytr, Xid[eval_idx])
                p_pa = ridge_fp(Xboth[tr], ytr, Xboth[eval_idx])
                yev = y[eval_idx]
                if np.std(yev) == 0:
                    continue
                ri = spearmanr(p_id, yev).statistic
                rp = spearmanr(p_pa, yev).statistic
                rows.append({"rep": rep, "S": S, "H": H, "k": -1 if k is None else k,
                             "n_eval": int(len(eval_idx)),
                             "rho_identity": 0.0 if not np.isfinite(ri) else float(ri),
                             "rho_pathway": 0.0 if not np.isfinite(rp) else float(rp)})

    r = pd.DataFrame(rows)
    res = {"kind": "does_starving_the_visible_drug_increase_the_value_of_the_pathway_prior",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "pairs_per_rep": PAIRS, "ks": [k if k else "all" for k in KS],
                        "seed": SEED, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_k": {}, "files": {}}
    for k in (-1, 20, 50, 200, 800):
        sub = r[r.k == k]
        if len(sub) < 10:
            continue
        gain = sub["rho_pathway"] - sub["rho_identity"]
        rng2 = np.random.default_rng(SEED + 100 + (k if k > 0 else 0))
        boots = [float(np.mean(rng2.choice(gain.to_numpy(), size=len(gain), replace=True)))
                 for _ in range(N_BOOT)]
        res["by_k"][str(k)] = {
            "n": int(len(sub)), "mean_eval": float(sub["n_eval"].mean()),
            "rho_identity": float(sub["rho_identity"].mean()),
            "rho_pathway": float(sub["rho_pathway"].mean()),
            "gain": float(gain.mean()),
            "gain_ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "sd": float(gain.std(ddof=1)),
            "mde_80pct": float(2.802 * gain.std(ddof=1) / np.sqrt(len(sub)))}
    if "20" in res["by_k"] and "-1" in res["by_k"]:
        g20 = (r[r.k == 20]["rho_pathway"] - r[r.k == 20]["rho_identity"]).mean()
        gall = (r[r.k == -1]["rho_pathway"] - r[r.k == -1]["rho_identity"]).mean()
        g20v = (r[r.k == 20]["rho_pathway"] - r[r.k == 20]["rho_identity"]).to_numpy()
        gallv = (r[r.k == -1]["rho_pathway"] - r[r.k == -1]["rho_identity"]).to_numpy()
        rng3 = np.random.default_rng(SEED + 201)          # seeded ONCE, outside the loop
        diffs = [float(np.mean(rng3.choice(g20v, size=len(g20v), replace=True))
                       - np.mean(rng3.choice(gallv, size=len(gallv), replace=True)))
                 for _ in range(N_BOOT)]
        if np.std(diffs) == 0.0:
            res.setdefault("audit_notes", []).append(
                "the k20-minus-all bootstrap is degenerate: zero dispersion across resamples")
        res["k20_minus_all"] = {"mean": float(g20 - gall),
                                "ci95": [float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975))]}
    km = res.get("k20_minus_all") or {}
    h378 = bool(km and km["ci95"][0] > 0)
    res["decisions"] = {"H378_starving_raises_the_gain": h378, "H379_no_effect": not h378}
    res["decisions"]["verdict"] = (
        "the_pathway_gain_rises_as_the_visible_drug_is_starved" if h378 else
        "starving_the_visible_drug_does_not_change_the_pathway_gain")
    res["limits"] = ["The evaluation set is a single drug pair, so it is small; the minimum detectable effect is reported.",
                     "Starvation acts on S's training rows only and leaves the pathway information intact, which is exactly the asymmetry being compared.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r156/PROTOCOL_E146.md",
                "research/2026-10-27-agent-cell-identifiability-r156/e156_starve.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E156_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E156_rows.csv", index=False)

    print("rows=%d" % len(r))
    for k in ("-1", "800", "200", "50", "20"):
        e = res["by_k"].get(k)
        if not e:
            continue
        print("  k=%-4s n=%3d eval %.0f | rho_id %+.4f rho_path %+.4f | gain %+.4f [%+.4f,%+.4f] MDE %.4f" % (
            ("all" if k == "-1" else k), e["n"], e["mean_eval"], e["rho_identity"], e["rho_pathway"],
            e["gain"], e["gain_ci95"][0], e["gain_ci95"][1], e["mde_80pct"]))
    if km:
        print("  k20 - all: %+.4f [%+.4f,%+.4f]" % (km["mean"], km["ci95"][0], km["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
