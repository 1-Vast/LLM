"""E160: the criterion-by-budget table.

Two things were known separately: which criterion resolves the annotation effect in which pool, and how
the effect survives a data reduction on the dense criterion. The grid of criterion against training
budget was never computed, and that is exactly what a user needs: "I have this much data and want to use
this criterion, is it enough?"

Both criteria are scored with the SAME metric - the gain in hit rate among the top 20 percent of
predictions - so their minimum detectable effects are comparable.

Pre-registered in PROTOCOL_E149.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r160"
LAMBDA = 1.0
REPS = 40
N_BOOT = 2000
SEED = 20261062
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


def ridge_fp(Xtr, ytr, Xte, lam=LAMBDA):
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
    return ytr.mean() + ((Xte - mu) / sd) @ w


def hit_gain(pred_a, pred_b, positive, frac=FRAC):
    k = max(3, int(round(frac * len(positive))))
    if k >= len(positive):
        return None
    top_a = np.argsort(-pred_a)[:k]
    top_b = np.argsort(-pred_b)[:k]
    return float(positive[top_a].mean() - positive[top_b].mean())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["syn"] = pd.to_numeric(d["Synergy"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"), syn=("syn", "max"))
    for c in ("a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)
    g["syn"] = (g["syn"] > 0).astype(float)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xpath = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                       oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xboth = np.hstack([Xid, Xpath])
    y = g["emax"].to_numpy(float)
    syn = g["syn"].to_numpy(float)
    rng = np.random.default_rng(SEED)

    rows = []
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[:12])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        te = np.where(au ^ bu)[0]                      # exactly one drug unseen
        if len(te) < 200:
            continue
        for k in KS:
            tr = np.where((~au) & (~bu))[0]
            if k is not None:
                budget = {dn: k for dn in drugs}
                keep = []
                for i in tr[rng.permutation(len(tr))]:
                    if budget.get(A[i], 0) > 0 and budget.get(B[i], 0) > 0:
                        keep.append(i); budget[A[i]] -= 1; budget[B[i]] -= 1
                tr = np.array(sorted(keep))
            if len(tr) < 500:
                continue
            ytr = y[tr]
            p_id = ridge_fp(Xid[tr], ytr, Xid[te])
            p_pa = ridge_fp(Xboth[tr], ytr, Xboth[te])
            dense_pos = (y[te] >= np.quantile(y[te], 0.75)).astype(float)
            bool_pos = syn[te]
            gd = hit_gain(p_pa, p_id, dense_pos)
            gb = hit_gain(p_pa, p_id, bool_pos)
            if gd is None or gb is None:
                continue
            rows.append({"rep": rep, "k": -1 if k is None else k, "n_eval": int(len(te)),
                         "n_train": int(len(tr)),
                         "n_pos_dense": int(dense_pos.sum()), "n_pos_bool": int(bool_pos.sum()),
                         "gain_dense": gd, "gain_bool": gb})

    r = pd.DataFrame(rows)
    res = {"kind": "criterion_by_budget_decision_table",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "ks": [k if k else "all" for k in KS], "top_frac": FRAC,
                        "seed": SEED, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "table": {}, "files": {}}
    for k in (-1, 400, 120, 40):
        sub = r[r.k == k]
        if len(sub) < 8:
            continue
        cell = {"n": int(len(sub)), "mean_train": float(sub["n_train"].mean()),
                "mean_eval": float(sub["n_eval"].mean()),
                "mean_pos_dense": float(sub["n_pos_dense"].mean()),
                "mean_pos_bool": float(sub["n_pos_bool"].mean())}
        for crit in ("dense", "bool"):
            v = sub["gain_" + crit].to_numpy()
            rng2 = np.random.default_rng(SEED + 300 + (k if k > 0 else 0) + (0 if crit == "dense" else 7))
            boots = [float(np.mean(rng2.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
            cell[crit] = {"gain": float(v.mean()),
                          "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
                          "sd": float(v.std(ddof=1)),
                          "mde_80pct": float(2.802 * v.std(ddof=1) / np.sqrt(len(v)))}
        res["table"][str(k)] = cell

    def resolvable(c):
        return c["dense"]["ci95"][0] > 0
    def bool_ok(c):
        return c["bool"]["ci95"][0] > 0
    d_all = res["table"].get("-1", {})
    d_small = res["table"].get("40", {})
    h386 = bool(d_all and d_small and all(resolvable(v) for v in res["table"].values())
                and bool_ok(d_all) and not bool_ok(d_small))
    res["decisions"] = {"dense_resolvable_everywhere": all(resolvable(v) for v in res["table"].values()),
                        "bool_resolvable_at_full": bool_ok(d_all) if d_all else None,
                        "bool_resolvable_at_smallest": bool_ok(d_small) if d_small else None,
                        "H386_crossing_exists": h386, "H387_no_crossing": not h386}
    res["decisions"]["verdict"] = (
        "the_dense_criterion_works_at_every_budget_while_the_boolean_fails_at_small_ones" if h386 else
        "the_two_criteria_do_not_cross_over_this_range")
    res["limits"] = ["The boolean criterion has a 1.43 percent base rate, so positive counts per cell are small and are reported.",
                     "Only ridge and one resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r160/PROTOCOL_E149.md",
                "research/2026-10-27-agent-cell-identifiability-r160/e160_criterion_budget.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E160_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E160_rows.csv", index=False)

    print("rows=%d" % len(r))
    print("  %-6s %10s %8s %10s %26s %26s" % ("k", "train", "pos_d", "pos_b", "dense gain [CI]", "bool gain [CI]"))
    for k in ("-1", "400", "120", "40"):
        c = res["table"].get(k)
        if not c:
            continue
        print("  %-6s %10.0f %8.1f %10.1f  %+.4f [%+.4f,%+.4f] MDE %.4f   %+.4f [%+.4f,%+.4f] MDE %.4f" % (
            ("all" if k == "-1" else k), c["mean_train"], c["mean_pos_dense"], c["mean_pos_bool"],
            c["dense"]["gain"], c["dense"]["ci95"][0], c["dense"]["ci95"][1], c["dense"]["mde_80pct"],
            c["bool"]["gain"], c["bool"]["ci95"][0], c["bool"]["ci95"][1], c["bool"]["mde_80pct"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
