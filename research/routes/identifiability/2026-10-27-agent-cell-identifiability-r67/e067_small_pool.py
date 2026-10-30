"""E067: does the weak unseen-drug signal still help when the candidate pool shrinks?

Same construction as R66, but the unseen-drug pool is subsampled to 200 / 500 / 2000 / all.
Two budget definitions: fixed k=20 and a fixed 5% relative depth.
Pre-registered in PROTOCOL_E065.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r67"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
SIZES = (200, 500, 2000, None)   # None = full unseen pool
K_ABS = 20
REL_DEPTH = 0.05
REPEATS = 40
HOLDOUT_FRAC = 0.20
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]


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
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("a", "b", "tissue", "ap", "lp"):
        d[c] = d[c].astype(str).fillna("NA")

    ap_lv = sorted(d["ap"].unique())
    lp_lv = sorted(d["lp"].unique())
    ti_lv = sorted(d["tissue"].unique())
    X = np.hstack([onehot(d["ap"].to_numpy(), ap_lv), onehot(d["lp"].to_numpy(), lp_lv),
                   onehot(d["tissue"].to_numpy(), ti_lv)])
    y = d.synergy.to_numpy(float)
    syn = d.syn.to_numpy(bool)
    A = d["a"].to_numpy()
    B = d["b"].to_numpy()
    drugs = sorted(set(A) | set(B))

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        rng.shuffle(drugs)
        n_hold = max(3, int(round(HOLDOUT_FRAC * len(drugs))))
        held = set(drugs[:n_hold])
        seen_combo = np.array([(x not in held) and (z not in held) for x, z in zip(A, B)])
        any_unseen = np.array([(x in held) or (z in held) for x, z in zip(A, B)])
        tr = np.where(seen_combo)[0]
        if len(tr) < 20000:
            continue
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        Am = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        w = np.linalg.solve(Am, Xs.T @ (ytr - ytr.mean()))
        full = np.where(any_unseen)[0]
        if len(full) < 400:
            continue
        for S in SIZES:
            tag = "all" if S is None else str(S)
            pool = full.copy() if S is None or S >= len(full) else rng.choice(full, size=S, replace=False)
            perm = rng.permutation(len(pool))
            half = len(pool) // 2
            for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                p = pool[idxs]
                Xp = (X[p] - mu) / sd
                pred = ytr.mean() + Xp @ w
                rp = pd.Series(pred).rank(pct=True).to_numpy()
                for kdef, k in (("abs20", K_ABS), ("rel5", max(5, int(round(REL_DEPTH * len(p)))))):
                    if k >= len(p) // 4:
                        continue
                    e_hit = float(syn[p][np.argsort(-rp)[:k]].mean())
                    r_hit = float(syn[p][rng.choice(len(p), size=k, replace=False)].mean())
                    rows.append({"rep": rep, "S": tag, "kdef": kdef, "k": k, "part": part,
                                 "exploit": e_hit, "random": r_hit, "base": float(syn[p].mean()),
                                 "n_pool": int(len(p))})

    r = pd.DataFrame(rows)
    res = {"kind": "weak_signal_gain_versus_pool_size",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"sizes": [("all" if s is None else s) for s in SIZES], "k_abs": K_ABS,
                        "rel_depth": REL_DEPTH, "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "drugs": len(drugs), "reps_used": int(r["rep"].nunique()) if len(r) else 0},
           "by_size": {}, "files": {}}

    for S in SIZES:
        tag = "all" if S is None else str(S)
        ent = {}
        for kdef in ("abs20", "rel5"):
            sub = r[(r.S == tag) & (r.kdef == kdef)]
            if not len(sub):
                continue
            ev = sub[sub.part == "eval"].set_index("rep")
            ent[kdef] = {"k_median": float(ev["k"].median()), "n_eval": int(len(ev)),
                         "exploit": float(ev["exploit"].mean()), "random": float(ev["random"].mean()),
                         "base": float(ev["base"].mean()),
                         "gain_pp": float((ev["exploit"] - ev["random"]).mean()),
                         "paired": paired(ev["exploit"], ev["random"], 4001 + len(tag) + (1 if kdef == "rel5" else 0)),
                         "n_pool_median": float(ev["n_pool"].median())}
        if ent:
            res["by_size"][tag] = ent

    def gain(tag, kdef="abs20"):
        return res["by_size"].get(tag, {}).get(kdef, {}).get("gain_pp")

    def ci(tag, kdef="abs20"):
        return res["by_size"].get(tag, {}).get(kdef, {}).get("paired")

    small = []
    for tag in ("200", "500"):
        c = ci(tag)
        if c:
            small.append(c["ci95"][0] > 0)
    h168 = bool(small and all(small))
    seq = [gain(t) for t in ("200", "500", "2000", "all") if gain(t) is not None]
    viol = sum(1 for i in range(len(seq) - 1) if seq[i] < seq[i + 1] - 1e-9)
    h169 = bool(len(seq) >= 3 and viol <= 1)
    rel = [gain(t, "rel5") for t in ("200", "500", "2000", "all") if gain(t, "rel5") is not None]
    h170 = bool(rel and all(g > 0 for g in rel))
    res["decisions"] = {"H168_gain_survives_small_pools": h168,
                        "H169_gain_non_increasing_with_size": h169,
                        "H170_relative_depth_holds": h170,
                        "abs_gains": {t: gain(t) for t in ("200", "500", "2000", "all")},
                        "rel_gains": {t: gain(t, "rel5") for t in ("200", "500", "2000", "all")}}
    res["decisions"]["verdict"] = ("weak_signal_decision_value_is_pool_robust" if h168 and h170
                                   else "weak_signal_decision_value_needs_a_large_pool")
    res["limits"] = [
        "Subsampling the pool changes its composition; a 200-key pool may contain very few distinct drug pairs.",
        "At S=200 a fixed k=20 is a 10% cut, not comparable with the same k at S=20,000.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel_p in ("research/2026-10-27-agent-cell-identifiability-r67/PROTOCOL_E065.md",
                  "research/2026-10-27-agent-cell-identifiability-r67/e067_small_pool.py"):
        p = ROOT / rel_p
        if p.exists():
            res["files"][rel_p] = sha256(p)
    (OUT / "E067_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E067_rows.csv", index=False)

    print("keys=%d drugs=%d reps=%d" % (len(d), len(drugs), res["audit"]["reps_used"]))
    for tag in ("200", "500", "2000", "all"):
        if tag not in res["by_size"]:
            continue
        for kdef in ("abs20", "rel5"):
            e = res["by_size"][tag].get(kdef)
            if not e:
                continue
            c = e["paired"]
            print("  S=%-4s %-5s k~%-5.0f base=%.4f exploit=%.4f random=%.4f | gain %+.4f [%+.4f,%+.4f] n_eval=%d" % (
                tag, kdef, e["k_median"], e["base"], e["exploit"], e["random"],
                e["gain_pp"], c["ci95"][0], c["ci95"][1], e["n_eval"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
