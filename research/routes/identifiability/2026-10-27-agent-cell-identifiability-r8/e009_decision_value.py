"""E009: does regimen-instability information change a drug choice?

Pre-registered in PROTOCOL_E009.md. Reads only PAIR_SCREEN.csv.

For each held-out cell line the predictor, the per-well instability score and the VOI
score are built ONLY from the other cell lines of the same layout. The held-out cell's
own values are used for scoring and for the k purchased wells only.

Instability per well follows R7's object: for the sampled unit pairs, the reversal rate
across pairs of the other cells, averaged over the pairs incident to that well.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r8"
ANCHORS = {"high control", "low control"}
FLOOR = 0.10
K_GRID = (1, 2, 4, 8)
N_RANDOM = 20
N_BOOT = 1000
W_INSTAB = 0.5
PAIRS_SAMPLE = 400
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def zs(x):
    s = np.nanstd(x)
    return (x - np.nanmean(x)) / (s if s > 1e-9 else 1.0)


def build():
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")
    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], pd.to_numeric(g["Conc 1 (uM)"]).round(9),
                                  g["Drug 2"], pd.to_numeric(g["Conc 2 (uM)"]).round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "combo": {w: (str(d1).lower() != "dmso" and str(d2).lower() != "dmso")
                                 for w, (d1, c1, d2, c2) in
                                 {w: (d1, c1, d2, c2) for w, d1, c1, d2, c2 in layout}.items()},
                       "qc": float(g["failed_qc"].mean())}

    def vec(fname, units):
        sub = df[(df["file"] == fname) & (~df["failed_qc"]) & df["y"].notna() & (~df["anchor"])]
        return sub.drop_duplicates("Well").set_index("Well")["y"].reindex(units).to_numpy(dtype=float)

    groups = {}
    for f, s in meta.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)
    rng = np.random.default_rng(SEED)
    layouts = []
    for (it, h), cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 4:
            continue
        first = cells[good[0]][0]
        units = [u for u in sorted(meta[first]["combo"]) if meta[first]["combo"][u]]
        V = {c: [vec(f, units) for f in cells[c]] for c in good}
        Y = {c: np.nanmean(np.vstack(V[c]), axis=0) for c in good}
        units = np.asarray(units, dtype=object)
        nu = len(units)
        iu, ju = np.triu_indices(nu, 1)
        sel = rng.choice(iu.size, min(PAIRS_SAMPLE, iu.size), replace=False)
        layouts.append({"iteration": it, "hash": h[:12], "cells": good, "units": units,
                        "Y": Y, "iu": iu[sel], "ju": ju[sel]})
    return df, layouts


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df, layouts = build()
    rng = np.random.default_rng(SEED + 11)

    rows = []
    for L in layouts:
        cells, nu = L["cells"], L["units"].size
        lay = "%s/%s" % (L["iteration"], L["hash"])
        iu, ju = L["iu"], L["ju"]
        for c in cells:
            others = [x for x in cells if x != c]
            if len(others) < 3:
                continue
            Yc = L["Y"][c]
            M = np.vstack([L["Y"][x] for x in others])       # (n_other, nu)
            P = np.nanmean(M, axis=0)
            resid = M - P[None, :]
            sigma = float(np.nanmedian(np.nanstd(resid, axis=0)))
            if not np.isfinite(sigma) or sigma <= 0:
                continue

            # ---- per-well instability from the other cells (R7 object) ----
            Mo = M[:, iu] - M[:, ju]
            gapo = np.abs(Mo)
            sgn = np.sign(Mo)
            oko = np.isfinite(gapo) & (gapo >= FLOOR)
            pair_rev = np.zeros(iu.size)
            pair_obs = np.zeros(iu.size)
            for a in range(len(others)):
                for b in range(a + 1, len(others)):
                    m = oko[a] & oko[b]
                    if m.sum() == 0:
                        continue
                    pair_rev[m] += (sgn[a, m] != sgn[b, m])
                    pair_obs[m] += 1
            with np.errstate(invalid="ignore", divide="ignore"):
                prate = np.where(pair_obs > 0, pair_rev / np.maximum(pair_obs, 1), np.nan)
            inst = np.zeros(nu)
            for p in range(iu.size):
                if np.isfinite(prate[p]):
                    inst[iu[p]] += prate[p]
                    inst[ju[p]] += prate[p]
            wcount = np.bincount(np.concatenate([iu, ju]), minlength=nu).astype(float)
            with np.errstate(invalid="ignore", divide="ignore"):
                inst = np.where(wcount > 0, inst / np.maximum(wcount, 1), 0.0)

            valid = np.isfinite(P) & np.isfinite(Yc)
            if valid.sum() < 20:
                continue
            idx = np.where(valid)[0]
            p, truth, inst_v = P[idx], Yc[idx], inst[idx]
            n = idx.size
            best_true = float(np.min(truth))
            rank_true = np.argsort(np.argsort(truth))

            # ---- VOI: P(u is the best) ~ Phi((min_{v != u} p_v - p_u)/sigma) ----
            order = np.argsort(p)
            voi = np.empty(n)
            for j in range(n):
                rest = np.delete(p, j)
                m_other = float(np.min(rest)) if rest.size else np.inf
                voi[j] = 0.5 * math.erfc((p[j] - m_other) / (sigma * math.sqrt(2.0)))

            exploit = -p
            contender = -np.abs(p - np.min(p))
            combo = -zs(p) + W_INSTAB * zs(inst_v)

            def top_k(score, kk):
                """largest score first"""
                return list(np.argsort(-score)[:kk])

            for k in K_GRID:
                if k > n - 1:
                    continue
                picks = {
                    "none": [],
                    "exploit": top_k(exploit, k),
                    "contender": top_k(contender, k),
                    "voi": top_k(voi, k),
                    "instab": top_k(inst_v, k),
                    "exploit_instab": top_k(combo, k),
                }
                for name, sel in picks.items():
                    est = p.copy()
                    if name != "none":
                        est[sel] = truth[sel]
                    choice = int(np.argmin(est))
                    top3 = list(np.argsort(est)[:3])
                    rows.append({"layout": lay, "cell": c, "k": k, "strategy": name,
                                 "hit_top1": int(rank_true[choice] < 3),
                                 "regret": float(truth[choice] - best_true),
                                 "top3_utility": float(np.mean(truth[top3])), "n_units": int(n)})
                hits, regs, t3 = [], [], []
                for _ in range(N_RANDOM):
                    sel = list(rng.choice(n, k, replace=False))
                    est = p.copy()
                    est[sel] = truth[sel]
                    ch = int(np.argmin(est))
                    hits.append(int(rank_true[ch] < 3))
                    regs.append(float(truth[ch] - best_true))
                    t3.append(float(np.mean(truth[np.argsort(est)[:3]])))
                rows.append({"layout": lay, "cell": c, "k": k, "strategy": "random",
                             "hit_top1": float(np.mean(hits)), "regret": float(np.mean(regs)),
                             "top3_utility": float(np.mean(t3)), "n_units": int(n)})

    r = pd.DataFrame(rows)
    res = {"kind": "equal_budget_acquisition_decision_test_signs_fixed",
           "input_sha256": sha256(CSV),
           "settings": {"k_grid": list(K_GRID), "n_random": N_RANDOM, "n_boot": N_BOOT,
                        "w_instab": W_INSTAB, "pairs_sample": PAIRS_SAMPLE, "seed": SEED},
           "audit": {"layouts_used": int(r["layout"].nunique()),
                     "heldout_cells": int(r.groupby(["layout", "cell"]).ngroups),
                     "observations": int(len(r)), "note": "layouts need >=4 QC-passing cells"},
           "by_k": {}, "paired": {}, "files": {}}

    for k in K_GRID:
        sub = r[r["k"] == k]
        if sub.empty:
            continue
        res["by_k"][str(k)] = {
            s: {"n_cells": int(len(d)), "hit_top1": float(d["hit_top1"].mean()),
                "regret_mean": float(d["regret"].mean()), "regret_median": float(d["regret"].median()),
                "top3_utility_mean": float(d["top3_utility"].mean())}
            for s, d in sub.groupby("strategy")}

    def paired(k, a, b, metric):
        sa = r[(r["k"] == k) & (r["strategy"] == a)][["layout", "cell", metric]]
        sb = r[(r["k"] == k) & (r["strategy"] == b)][["layout", "cell", metric]]
        m = sa.merge(sb, on=["layout", "cell"], suffixes=("_a", "_b"))
        if m.empty:
            return None
        m["d"] = m[metric + "_a"] - m[metric + "_b"]
        lays = sorted(m["layout"].unique())
        rng2 = np.random.default_rng(SEED + 3)
        boots = []
        for _ in range(N_BOOT):
            pick = rng2.choice(lays, size=len(lays), replace=True)
            sel = pd.concat([m[m["layout"] == q] for q in pick])
            if len(sel):
                boots.append(float(sel["d"].mean()))
        return {"n": int(len(m)), "mean_diff": float(m["d"].mean()),
                "ci95_layout_clustered": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None,
                "frac_better_than_baseline": float((m["d"] < 0).mean()) if metric == "regret" else float((m["d"] > 0).mean())}

    for k in K_GRID:
        block = {}
        for a in ("instab", "exploit_instab", "voi", "contender", "random"):
            block[a + "_vs_exploit_regret"] = paired(k, a, "exploit", "regret")
            block[a + "_vs_exploit_hit"] = paired(k, a, "exploit", "hit_top1")
        res["paired"][str(k)] = block

    def meets(k, a):
        d = res["paired"].get(str(k), {}).get(a + "_vs_exploit_regret")
        return bool(d and d["mean_diff"] <= -0.02 and d["ci95_layout_clustered"] and d["ci95_layout_clustered"][1] < 0)

    h013a = any(meets(k, a) for k in K_GRID for a in ("instab", "exploit_instab"))
    h013b = any(meets(k, "voi") for k in K_GRID)
    exploit_best = all(
        res["by_k"][str(k)]["exploit"]["regret_mean"] <= min(v["regret_mean"] for v in res["by_k"][str(k)].values()) + 1e-12
        for k in K_GRID if str(k) in res["by_k"])
    res["decisions"] = {"H013a_instability_has_decision_value": h013a,
                        "H013b_voi_has_decision_value": h013b,
                        "exploit_is_best_at_every_k": exploit_best,
                        "verdict": ("instability_improves_choice" if h013a else
                                    "voi_improves_choice_without_instability" if h013b else
                                    "no_acquisition_beats_exploitation")}
    res["limits"] = [
        "Held-out cell's own values are used only for scoring and for the k purchased wells.",
        "Predictor is the mean of the other cells; no unit-space GP is identifiable here (no metric over units).",
        "Validation plates were already used as scoring endpoints by an earlier round and cross-cell comparisons also cross days: exploratory.",
        "Functional viability only; no mechanism, target engagement, selectivity or clinical claim.",
        "The menu is the author's validation layout, not a random sample of all possible regimens.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r8/PROTOCOL_E009.md",
                "research/2026-10-27-agent-cell-identifiability-r8/e009_decision_value.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E009_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E009_per_cell.csv", index=False)

    print("layouts=%d heldout cells=%d obs=%d" % (res["audit"]["layouts_used"], res["audit"]["heldout_cells"],
                                                  res["audit"]["observations"]))
    for k in K_GRID:
        if str(k) not in res["by_k"]:
            continue
        print("k=%d" % k)
        for s, v in sorted(res["by_k"][str(k)].items(), key=lambda kv: kv[1]["regret_mean"]):
            print("   %-15s hit=%.3f regret=%.4f top3=%.4f" % (s, v["hit_top1"], v["regret_mean"], v["top3_utility_mean"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
