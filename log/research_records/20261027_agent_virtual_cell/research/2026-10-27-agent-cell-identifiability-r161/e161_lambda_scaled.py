"""E161: is the starvation pattern a regularization artefact?

E160 found the annotation gain at the top-20 percent hit rate was NOT resolvable with full data
(+0.0018) yet resolvable at intermediate budgets (+0.0086), an inverted U. One explanation is that the
starved runs were not measuring information at all: lambda was held at 1.0 while n fell from 71,772 to
831, so each parameter was regularized about eighty times more heavily. Under stronger relative
shrinkage the drug-level coefficients collapse toward the mean and group structure takes over the
ranking.

The test is direct: scale lambda linearly with n so that lambda over n is constant, and see whether the
inverted U flattens.

Pre-registered by extension of PROTOCOL_E149.md; the change is stated in the record.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r161"
LAMBDA_FULL = 1.0
REPS = 40
N_BOOT = 2000
SEED = 20261063
KS = (None, 400, 120, 40)
FRAC = 0.20
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "Synergy", "SYNERGY_DELTA_EMAX"]


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


def ridge_fp(Xtr, ytr, Xte, lam):
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
    return ytr.mean() + ((Xte - mu) / sd) @ w


def hit_gain(pa, pb, positive, frac=FRAC):
    k = max(3, int(round(frac * len(positive))))
    if k >= len(positive):
        return None
    return float(positive[np.argsort(-pa)[:k]].mean() - positive[np.argsort(-pb)[:k]].mean())


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
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[:12])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        te = np.where(au ^ bu)[0]
        if len(te) < 200:
            continue
        full_tr = np.where((~au) & (~bu))[0]
        n_full = len(full_tr)
        for k in KS:
            tr = full_tr
            if k is not None:
                budget = {dn: k for dn in drugs}
                keep = []
                for i in tr[rng.permutation(len(tr))]:
                    if budget.get(A[i], 0) > 0 and budget.get(B[i], 0) > 0:
                        keep.append(i); budget[A[i]] -= 1; budget[B[i]] -= 1
                tr = np.array(sorted(keep))
            if len(tr) < 500:
                continue
            # the corrected schedule: lambda proportional to n, so lambda over n is constant
            lam = LAMBDA_FULL * (len(tr) / n_full)
            ytr = y[tr]
            p_id = ridge_fp(Xid[tr], ytr, Xid[te], lam)
            p_pa = ridge_fp(Xboth[tr], ytr, Xboth[te], lam)
            pos = (y[te] >= np.quantile(y[te], 0.75)).astype(float)
            gv = hit_gain(p_pa, p_id, pos)
            if gv is None:
                continue
            rows.append({"rep": rep, "k": -1 if k is None else k, "n_train": int(len(tr)),
                         "lambda": float(lam), "gain": gv})

    r = pd.DataFrame(rows)
    res = {"kind": "does_scaling_lambda_with_n_remove_the_inverted_U",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "ks": [k if k else "all" for k in KS], "seed": SEED,
                        "lambda_schedule": "lambda proportional to n, so lambda/n constant",
                        "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_k": {}, "files": {}}
    for k in (-1, 400, 120, 40):
        sub = r[r.k == k]
        if len(sub) < 8:
            continue
        v = sub["gain"].to_numpy()
        rng2 = np.random.default_rng(SEED + 400 + (k if k > 0 else 0))
        boots = [float(np.mean(rng2.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
        res["by_k"][str(k)] = {"n": int(len(sub)), "mean_train": float(sub["n_train"].mean()),
                               "lambda": float(sub["lambda"].mean()),
                               "gain": float(v.mean()),
                               "ci95": [float(np.quantile(boots, 0.025)),
                                        float(np.quantile(boots, 0.975))],
                               "mde_80pct": float(2.802 * v.std(ddof=1) / np.sqrt(len(sub)))}
    gs = [v["gain"] for v in res["by_k"].values()]
    ci_lo = [v["ci95"][0] for v in res["by_k"].values()]
    res["decisions"] = {"gains": gs, "ci_lower_bounds": ci_lo,
                        "spread": (max(gs) - min(gs)) if gs else None,
                        "all_resolvable": all(x > 0 for x in ci_lo),
                        "shape_flat_within_mde": bool(gs and (max(gs) - min(gs))
                                                       < max(v["mde_80pct"] for v in res["by_k"].values()))}
    res["decisions"]["verdict"] = (
        "with_lambda_scaled_to_n_the_gain_is_flat_and_resolvable_at_every_budget_so_the_inverted_U_was_a_regularisation_artefact"
        if res["decisions"]["shape_flat_within_mde"] and res["decisions"]["all_resolvable"] else
        "the_pattern_survives_the_lambda_correction_so_it_is_not_only_a_regularisation_artefact")
    res["limits"] = ["Only the dense criterion and the top-20 percent hit-rate metric.",
                     "Lambda proportional to n is one corrected schedule, not the only defensible one; inner cross-validation would be better.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r160/PROTOCOL_E149.md",
                "research/2026-10-27-agent-cell-identifiability-r161/e161_lambda_scaled.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E161_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E161_rows.csv", index=False)

    print("rows=%d   (lambda proportional to n)" % len(r))
    for k in ("-1", "400", "120", "40"):
        e = res["by_k"].get(k)
        if not e:
            continue
        print("  k=%-5s train %7.0f  lambda %.4f | gain %+.4f [%+.4f,%+.4f] MDE %.4f" % (
            ("all" if k == "-1" else k), e["mean_train"], e["lambda"],
            e["gain"], e["ci95"][0], e["ci95"][1], e["mde_80pct"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
