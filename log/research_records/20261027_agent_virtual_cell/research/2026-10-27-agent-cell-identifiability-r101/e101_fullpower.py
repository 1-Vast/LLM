"""E100: does identity+pathway's increment replicate across pools and criteria?

R99 refuted "the annotation model is useless" on one pool with one criterion. A refutation
only counts if it survives other conditions, so the same bagged capacity control is run on
three pools and two criteria.

Pre-registered in PROTOCOL_E095.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r101"
LAMBDA = 1.0
K = 20
REPEATS = 80
BLOCKS = 10
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261027
METRICS = ["Synergy", "SYNERGY_DELTA_EMAX"]
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "Synergy", "SYNERGY_DELTA_EMAX"]


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


def onehot(vals, levels):
    M = np.zeros((len(vals), len(levels)))
    for j, v in enumerate(levels):
        M[:, j] = (vals == v).astype(float)
    return M


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), syn=("syn", "mean"),
        emax=("emax", "mean"))
    g["syn"] = g["syn"] > 0.5
    for c in ("cell", "a", "b", "ap", "lp", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy()
    B = g["b"].to_numpy()
    CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B))
    cells = sorted(set(CELL))
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpa = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                     onehot(g["lp"].to_numpy(), sorted(g["lp"].unique())),
                     onehot(g["tissue"].to_numpy(), sorted(g["tissue"].unique()))])

    targets = {"Synergy": (g["syn"].to_numpy(bool), "flag"),
               "SYNERGY_DELTA_EMAX": (g["emax"].to_numpy(float), "quartile")}

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        rng.shuffle(drugs)
        rng.shuffle(cells)
        heldd = set(drugs[: max(3, int(round(HOLDOUT * len(drugs))))])
        heldc = set(cells[: max(3, int(round(HOLDOUT * len(cells))))])
        a_u = np.array([x in heldd for x in A])
        b_u = np.array([z in heldd for z in B])
        cell_u = np.array([c in heldc for c in CELL])
        tr = np.where((~cell_u) & (~a_u) & (~b_u))[0]
        if len(tr) < 20000:
            continue
        pools = {
            "one_unseen": np.where((a_u ^ b_u) & (~cell_u))[0],
            "cell_unseen": np.where(cell_u & (a_u | b_u))[0],
            "both_unseen": np.where(a_u & b_u)[0],
        }
        for crit, (yt, kind) in targets.items():
            ytr = yt[tr].astype(float)
            ok_tr = np.isfinite(ytr)
            if ok_tr.sum() < 20000:
                continue

            def ridge_scores(XX):
                Xt = XX[tr][ok_tr]
                yy = ytr[ok_tr]
                mu, sd = Xt.mean(axis=0), Xt.std(axis=0)
                sd[sd == 0] = 1.0
                Xs = (Xt - mu) / sd
                Am = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
                w = np.linalg.solve(Am, Xs.T @ (yy - yy.mean()))
                return lambda XXe: yy.mean() + ((XXe - mu) / sd) @ w

            Xcombo = np.hstack([Xid, Xpa])
            f_id = (ridge_scores(Xid), Xid)
            f_combo = (ridge_scores(Xcombo), Xcombo)
            acc = []
            for _ in range(BLOCKS):
                Xb = np.hstack([Xid, rng.normal(size=(len(g), Xpa.shape[1]))])
                acc.append((ridge_scores(Xb), Xb))

            for pname, pool in pools.items():
                pool = pool[np.isfinite(yt[pool])]
                if len(pool) < 60:
                    continue
                sc_id = f_id[0](f_id[1][pool])
                sc_combo = f_combo[0](f_combo[1][pool])
                sc_rand = np.mean([f(Xb[pool]) for f, Xb in acc], axis=0)
                yv = yt[pool].astype(float)
                hit = (yv >= np.quantile(yv, 0.75)).astype(float) if kind == "quartile" else yv
                perm = rng.permutation(len(pool))
                half = len(pool) // 2
                for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                    p = idxs
                    if len(p) < 40:
                        continue
                    h = hit[p]
                    rows.append({"rep": rep, "criterion": crit, "pool": pname, "part": part,
                                 "identity": float(h[np.argsort(-sc_id[p])[:K]].mean()),
                                 "identity_pathway": float(h[np.argsort(-sc_combo[p])[:K]].mean()),
                                 "identity_random": float(h[np.argsort(-sc_rand[p])[:K]].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "full_power_replication_of_the_annotation_increment",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "blocks": BLOCKS, "holdout": HOLDOUT,
                        "lambda": LAMBDA, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "identity_dims": int(Xid.shape[1]),
                     "pathway_dims": int(Xpa.shape[1]), "rows": int(len(r))},
           "by_criterion": {}, "files": {}}

    for crit in METRICS:
        res["by_criterion"][crit] = {}
        for pname in ("one_unseen", "cell_unseen", "both_unseen"):
            ev = r[(r.criterion == crit) & (r.pool == pname) & (r.part == "eval")].set_index("rep")
            if len(ev) < 5:
                continue
            res["by_criterion"][crit][pname] = {
                "n": int(len(ev)),
                "identity": float(ev["identity"].mean()),
                "identity_pathway": float(ev["identity_pathway"].mean()),
                "identity_random": float(ev["identity_random"].mean()),
                "pathway_minus_random": paired(ev["identity_pathway"], ev["identity_random"],
                                               28001 + len(pname) + int(len(crit)))}

    def count_wins(crit):
        w = 0
        for pname, e in res["by_criterion"].get(crit, {}).items():
            if e["pathway_minus_random"]["ci95"][0] > 0:
                w += 1
        return w

    w_syn = count_wins("Synergy")
    w_emax = count_wins("SYNERGY_DELTA_EMAX")
    res["decisions"] = {"H257_replicates_across_pools": w_syn >= 2,
                        "H258_replicates_on_second_criterion": w_emax >= 2,
                        "H259_pool_specific": w_syn <= 1,
                        "wins_primary": w_syn, "wins_secondary": w_emax}
    res["decisions"]["verdict"] = (
        "refutation_holds_across_pools_and_criteria" if w_syn >= 2 and w_emax >= 2 else
        "refutation_holds_across_pools_only" if w_syn >= 2 else
        "refutation_is_pool_specific_and_must_be_downgraded")
    res["limits"] = [
        "The three pools share one training set, so they are not independent.",
        "The both-unseen pool is small (about 1,830 keys) and has the least power.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r100/PROTOCOL_E095.md",
                "research/2026-10-27-agent-cell-identifiability-r100/e100_replication.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E101_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E101_rows.csv", index=False)

    print("rows=%d dims=%d+%d" % (len(r), Xid.shape[1], Xpa.shape[1]))
    for crit in METRICS:
        print(" [%s]" % crit)
        for pname, e in res["by_criterion"].get(crit, {}).items():
            a = e["pathway_minus_random"]
            print("   %-12s id %.4f  combo %.4f  rand %.4f | pathway-rand %+.4f [%+.4f,%+.4f]" % (
                pname, e["identity"], e["identity_pathway"], e["identity_random"],
                a["mean_diff"], a["ci95"][0], a["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
