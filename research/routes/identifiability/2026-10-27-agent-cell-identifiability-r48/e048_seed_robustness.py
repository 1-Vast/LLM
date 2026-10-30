"""E048: is R37's k=50 mix advantage robust across random seed sets, or was it seed luck?

Pre-registered in PROTOCOL_E047.md. Identical construction to E037; only the seeds change.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r48"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
K = 50
N_SEEDS = 10
SPLITS_PER_SEED = 40
HALF = 20
N_BOOT = 2000
BASE_SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"), tissue=("Tissue", "first"),
        synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("tissue", "ap", "lp"):
        d[c] = d[c].astype(str).fillna("NA")

    blocks = []
    for c in ("tissue", "ap", "lp"):
        lv = sorted(d[c].unique())
        M = np.zeros((len(d), len(lv)))
        vals = d[c].to_numpy()
        for j, v in enumerate(lv):
            M[:, j] = (vals == v).astype(float)
        blocks.append(M)
    X = np.hstack(blocks)
    y = d.synergy.to_numpy(float)
    syn = d.syn.to_numpy(bool)

    rows = []
    for s in range(N_SEEDS):
        seed = BASE_SEED + 1000 * (s + 1)
        rng = np.random.default_rng(seed)
        for rep in range(SPLITS_PER_SEED):
            perm = rng.permutation(len(y))
            ntr = int(0.8 * len(y))
            tr, pool = perm[:ntr], perm[ntr:]
            Xtr, ytr = X[tr], y[tr]
            mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
            sd[sd == 0] = 1.0
            Xs = (Xtr - mu) / sd
            Xp = (X[pool] - mu) / sd
            A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
            Ainv = np.linalg.inv(A)
            w = Ainv @ Xs.T @ (ytr - ytr.mean())
            pred = ytr.mean() + Xp @ w
            var = np.einsum("ij,jk,ik->i", Xp, Ainv, Xp)
            rp = pd.Series(pred).rank(pct=True).to_numpy()
            rv = pd.Series(var).rank(pct=True).to_numpy()
            mix = rp + rv
            e_idx = np.argsort(-rp)[:K]
            m_idx = np.argsort(-mix)[:K]
            rows.append({"seed_set": s, "rep": rep, "half": "search" if rep < HALF else "eval",
                         "exploit": float(syn[pool][e_idx].mean()),
                         "mix": float(syn[pool][m_idx].mean())})

    r = pd.DataFrame(rows)
    ev = r[r.half == "eval"].copy()
    ev["diff"] = ev["mix"] - ev["exploit"]
    per_seed = ev.groupby("seed_set")["diff"].mean()
    res = {"kind": "seed_robustness_of_R37_advantage",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"k": K, "n_seeds": N_SEEDS, "splits_per_seed": SPLITS_PER_SEED,
                        "half": HALF, "n_boot": N_BOOT, "base_seed": BASE_SEED},
           "audit": {"keys": int(len(y)), "eval_splits_total": int(len(ev))},
           "per_seed_diff": {str(int(k)): float(v) for k, v in per_seed.items()},
           "files": {}}

    vals = per_seed.to_numpy(float)
    rng2 = np.random.default_rng(BASE_SEED + 7)
    boots = [float(np.mean(rng2.choice(vals, size=len(vals), replace=True))) for _ in range(N_BOOT)]
    res["summary"] = {
        "mean_diff": float(vals.mean()),
        "ci95_over_seeds": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
        "frac_seeds_positive": float((vals > 0).mean()),
        "min": float(vals.min()), "max": float(vals.max())}
    per_seed_detail = ev.groupby("seed_set")[["exploit", "mix"]].mean()
    res["per_seed_levels"] = {str(int(k)): {"exploit": float(row["exploit"]), "mix": float(row["mix"])}
                              for k, row in per_seed_detail.iterrows()}

    h123 = bool(res["summary"]["frac_seeds_positive"] >= 0.8 and res["summary"]["ci95_over_seeds"][0] > 0)
    res["decisions"] = {"H123_robust_across_seeds": h123, "H124_seed_dependent": (not h123)}
    res["decisions"]["verdict"] = ("R37_advantage_robust_across_seeds" if h123
                                   else "R37_advantage_is_seed_dependent")
    res["limits"] = [
        "Only k=50 is tested; the full k sweep is not repeated.",
        "Single dataset and feature set; the seed changes only the split, not the data.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r48/PROTOCOL_E047.md",
                "research/2026-10-27-agent-cell-identifiability-r48/e048_seed_robustness.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E048_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E048_rows.csv", index=False)

    print("keys=%d eval splits=%d" % (len(y), len(ev)))
    print("per-seed eval mix-exploit at k=50:")
    for k, v in res["per_seed_diff"].items():
        lv = res["per_seed_levels"][k]
        print("   seed %-2s exploit=%.4f mix=%.4f | diff %+.4f" % (k, lv["exploit"], lv["mix"], v))
    print("summary:", json.dumps(res["summary"], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
