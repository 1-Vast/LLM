"""E102: equal-budget comparison of marginals, identity and identity+pathway, to state a
CONDITIONAL rule rather than another winner.

Pre-registered in PROTOCOL_E097.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r102"
LAMBDA = 1.0
K = 20
REPEATS = 70
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "Synergy"]


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
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), syn=("syn", "mean"))
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
    Xcombo = np.hstack([Xid, Xpa])
    y = g["syn"].to_numpy(bool)

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
        pools = {"one_unseen": np.where((a_u ^ b_u) & (~cell_u))[0],
                 "cell_unseen": np.where(cell_u & (a_u | b_u))[0],
                 "both_unseen": np.where(a_u & b_u)[0]}

        ytr = y[tr].astype(float)

        def ridge_scorer(XX):
            Xt = XX[tr]
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0)
            sd[sd == 0] = 1.0
            Xs = (Xt - mu) / sd
            Am = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
            w = np.linalg.solve(Am, Xs.T @ (ytr - ytr.mean()))
            return lambda XXe: ytr.mean() + ((XXe - mu) / sd) @ w

        f_id = ridge_scorer(Xid)
        f_combo = ridge_scorer(Xcombo)
        # marginals: two-way additive from training drug effects
        grand = float(y[tr].mean())
        dm = {}
        for i in tr:
            dm.setdefault(A[i], []).append(y[i])
            dm.setdefault(B[i], []).append(y[i])
        deff = {k: float(np.mean(v)) - grand for k, v in dm.items()}

        for pname, pool in pools.items():
            if len(pool) < 60:
                continue
            sc_m = np.array([deff.get(A[i], 0.0) + deff.get(B[i], 0.0) + grand for i in pool])
            sc_id = f_id(Xid[pool])
            sc_cb = f_combo(Xcombo[pool])
            perm = rng.permutation(len(pool))
            half = len(pool) // 2
            for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                if len(idxs) < 40:
                    continue
                hit = y[pool][idxs].astype(float)
                rows.append({"rep": rep, "pool": pname, "part": part,
                             "marginal": float(hit[np.argsort(-sc_m[idxs])[:K]].mean()),
                             "identity": float(hit[np.argsort(-sc_id[idxs])[:K]].mean()),
                             "identity_pathway": float(hit[np.argsort(-sc_cb[idxs])[:K]].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "equal_budget_three_way_for_a_conditional_rule",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "holdout": HOLDOUT, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r))},
           "by_pool": {}, "files": {}}

    for pname in ("one_unseen", "cell_unseen", "both_unseen"):
        ev = r[(r.pool == pname) & (r.part == "eval")].set_index("rep")
        if len(ev) < 5:
            continue
        res["by_pool"][pname] = {
            "n": int(len(ev)),
            "marginal": float(ev["marginal"].mean()),
            "identity": float(ev["identity"].mean()),
            "identity_pathway": float(ev["identity_pathway"].mean()),
            "combo_minus_marginal": paired(ev["identity_pathway"], ev["marginal"], 29001 + len(pname)),
            "marginal_minus_combo": paired(ev["marginal"], ev["identity_pathway"], 29101 + len(pname))}

    bu = res["by_pool"].get("both_unseen", {})
    ou = res["by_pool"].get("one_unseen", {})
    h263 = bool(bu and bu["combo_minus_marginal"]["ci95"][0] > 0)
    h264 = bool(ou and ou["marginal_minus_combo"]["ci95"][0] <= 0)
    res["decisions"] = {"H263_combo_beats_marginal_when_drugs_unseen": h263,
                        "H264_marginal_not_worse_when_combos_novel": h264,
                        "H265_conditional_rule_holds": bool(h263 and h264)}
    res["decisions"]["verdict"] = (
        "conditional_rule_holds_marginals_when_drugs_seen_combo_when_unseen" if h263 and h264 else
        "combo_does_not_beat_marginals_so_do_not_promote" if not h263 else
        "marginals_dominate")
    res["limits"] = [
        "The three pools share one training set.",
        "The both-unseen pool is small.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r102/PROTOCOL_E097.md",
                "research/2026-10-27-agent-cell-identifiability-r102/e102_three_way.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E102_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E102_rows.csv", index=False)

    print("rows=%d" % len(r))
    for pname, e in res["by_pool"].items():
        a = e["combo_minus_marginal"]; b = e["marginal_minus_combo"]
        print("  %-12s marginal %.4f identity %.4f combo %.4f" % (
            pname, e["marginal"], e["identity"], e["identity_pathway"]))
        print("      combo-marg %+.4f [%+.4f,%+.4f] | marg-combo %+.4f [%+.4f,%+.4f]" % (
            a["mean_diff"], a["ci95"][0], a["ci95"][1], b["mean_diff"], b["ci95"][0], b["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
