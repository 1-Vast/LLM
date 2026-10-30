"""E068: the hardest transfer case - both the cell AND the drug are unseen.

Joint holdout of 20% cells and 20% drugs; training uses seen cells x both-seen drugs only.
Pre-registered in PROTOCOL_E066.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r68"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
K = 20
REPEATS = 40
HOLDOUT = 0.20
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
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("cell", "a", "b", "tissue", "ap", "lp"):
        d[c] = d[c].astype(str).fillna("NA")

    ap_lv = sorted(d["ap"].unique())
    lp_lv = sorted(d["lp"].unique())
    ti_lv = sorted(d["tissue"].unique())
    X = np.hstack([onehot(d["ap"].to_numpy(), ap_lv), onehot(d["lp"].to_numpy(), lp_lv),
                   onehot(d["tissue"].to_numpy(), ti_lv)])
    y = d.synergy.to_numpy(float)
    syn = d.syn.to_numpy(bool)
    cell = d["cell"].to_numpy()
    A = d["a"].to_numpy()
    B = d["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    cells = sorted(set(cell))

    rng = np.random.default_rng(SEED)
    rows = []
    train_sizes = []
    for rep in range(REPEATS):
        rng.shuffle(drugs)
        rng.shuffle(cells)
        held_d = set(drugs[: max(3, int(round(HOLDOUT * len(drugs))))])
        held_c = set(cells[: max(3, int(round(HOLDOUT * len(cells))))])
        drug_seen = np.array([(x not in held_d) and (z not in held_d) for x, z in zip(A, B)])
        any_drug_unseen = ~drug_seen
        cell_unseen = np.array([c in held_c for c in cell])

        tr = np.where((~cell_unseen) & drug_seen)[0]
        if len(tr) < 20000:
            continue
        train_sizes.append(len(tr))
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        Am = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        w = np.linalg.solve(Am, Xs.T @ (ytr - ytr.mean()))

        masks = {
            "cell_unseen": cell_unseen & drug_seen,
            "drug_unseen": (~cell_unseen) & any_drug_unseen,
            "both_unseen": cell_unseen & any_drug_unseen,
            "strict": cell_unseen & any_drug_unseen & np.array(
                [(x in held_d) and (z in held_d) for x, z in zip(A, B)]),
        }
        for label, mask in masks.items():
            pool = np.where(mask)[0]
            if len(pool) < 400:
                rows.append({"rep": rep, "pool": label, "skipped": True, "n": int(len(pool))})
                continue
            perm = rng.permutation(len(pool))
            half = len(pool) // 2
            for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                p = pool[idxs]
                if len(p) < 2 * K:
                    continue
                Xp = (X[p] - mu) / sd
                pred = ytr.mean() + Xp @ w
                rp = pd.Series(pred).rank(pct=True).to_numpy()
                e_hit = float(syn[p][np.argsort(-rp)[:K]].mean())
                r_hit = float(syn[p][rng.choice(len(p), size=K, replace=False)].mean())
                rows.append({"rep": rep, "pool": label, "part": part, "k": K,
                             "exploit": e_hit, "random": r_hit, "base": float(syn[p].mean()),
                             "n_pool": int(len(p))})

    r = pd.DataFrame([x for x in rows if not x.get("skipped")])
    res = {"kind": "joint_unseen_cell_and_drug_transfer",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "k": K, "repeats": REPEATS, "holdout": HOLDOUT,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "drugs": len(drugs), "cells": len(cells),
                     "reps_used": int(r["rep"].nunique()) if len(r) else 0,
                     "train_size_median": float(np.median(train_sizes)) if train_sizes else None},
           "by_pool": {}, "files": {}}

    for label in ("cell_unseen", "drug_unseen", "both_unseen", "strict"):
        sub = r[r["pool"] == label]
        if not len(sub):
            continue
        ev = sub[sub.part == "eval"].set_index("rep")
        res["by_pool"][label] = {
            "n_eval": int(len(ev)),
            "base": float(ev["base"].mean()), "exploit": float(ev["exploit"].mean()),
            "random": float(ev["random"].mean()),
            "gain_pp": float((ev["exploit"] - ev["random"]).mean()),
            "paired": paired(ev["exploit"], ev["random"], 5001 + len(label)),
            "n_pool_median": float(ev["n_pool"].median())}

    def g(label):
        return res["by_pool"].get(label, {}).get("gain_pp")

    def c(label):
        return res["by_pool"].get(label, {}).get("paired")

    strict_ci = c("strict")
    h171 = bool(strict_ci and strict_ci["ci95"][0] > 0)
    seq = [g("strict"), g("both_unseen"), g("drug_unseen")]
    viol = sum(1 for i in range(2) if seq[i] is not None and seq[i + 1] is not None and seq[i] > seq[i + 1] + 1e-9)
    h172 = bool(all(v is not None for v in seq) and viol <= 1)
    cu = c("cell_unseen")
    h173 = bool(cu and cu["ci95"][0] > 0)
    res["decisions"] = {"H171_strict_pool_still_works": h171,
                        "H172_gain_degrades_stepwise": h172,
                        "H173_cell_unseen_not_the_bottleneck": h173,
                        "gains": {k: g(k) for k in ("cell_unseen", "drug_unseen", "both_unseen", "strict")}}
    res["decisions"]["verdict"] = ("ranking_value_survives_joint_novelty" if h171
                                   else "ranking_value_needs_at_least_one_side_seen")
    res["limits"] = [
        "The joint holdout shrinks the training set to about 64% of keys, so part of any drop is weaker training, not novelty per se.",
        "Tissue is still seen for held-out cells, so 'completely unfamiliar' is not achieved.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r68/PROTOCOL_E066.md",
                "research/2026-10-27-agent-cell-identifiability-r68/e068_joint_unseen.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E068_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E068_rows.csv", index=False)

    print("keys=%d drugs=%d cells=%d reps=%d train~%s" % (
        len(d), len(drugs), len(cells), res["audit"]["reps_used"], res["audit"]["train_size_median"]))
    for label in ("cell_unseen", "drug_unseen", "both_unseen", "strict"):
        e = res["by_pool"].get(label)
        if not e:
            print("  %-13s (no data)" % label); continue
        ci = e["paired"]
        print("  %-13s base=%.4f exploit=%.4f random=%.4f | gain %+.4f [%+.4f,%+.4f] n_eval=%d pool~%.0f" % (
            label, e["base"], e["exploit"], e["random"], e["gain_pp"],
            ci["ci95"][0], ci["ci95"][1], e["n_eval"], e["n_pool_median"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
