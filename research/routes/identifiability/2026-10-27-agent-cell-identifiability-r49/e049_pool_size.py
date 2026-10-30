"""E049: is pool SIZE the determinant of the mix advantage, or the sampling scheme?

Pre-registered in PROTOCOL_E048.md. Training set is fixed (R37's 80%); only the evaluation
pool size changes, with R37's own random-key sampling. Two k definitions: absolute k=50 and
a fixed relative depth of 0.23%.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r49"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
SIZES = (2000, 8000, 21652)
K_ABS = 50
REL_DEPTH = 50 / 21652  # 0.23%
REPEATS = 40
SEARCH = list(range(0, 20))
EVAL = list(range(20, 40))
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

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        perm = rng.permutation(len(y))
        ntr = int(0.8 * len(y))
        tr, full_pool = perm[:ntr], perm[ntr:]
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        Ainv = np.linalg.inv(A)
        w = Ainv @ Xs.T @ (ytr - ytr.mean())
        for S in SIZES:
            if S >= len(full_pool):
                pool = full_pool.copy()
            else:
                pool = rng.choice(full_pool, size=S, replace=False)
            Xp = (X[pool] - mu) / sd
            pred = ytr.mean() + Xp @ w
            var = np.einsum("ij,jk,ik->i", Xp, Ainv, Xp)
            rp = pd.Series(pred).rank(pct=True).to_numpy()
            rv = pd.Series(var).rank(pct=True).to_numpy()
            mix = rp + rv
            for label, k in (("abs50", K_ABS), ("rel", max(5, int(round(REL_DEPTH * S))))):
                if k >= len(pool):
                    continue
                e_idx = np.argsort(-rp)[:k]
                m_idx = np.argsort(-mix)[:k]
                rows.append({"rep": rep, "S": S, "kdef": label, "k": k,
                             "exploit": float(syn[pool][e_idx].mean()),
                             "mix": float(syn[pool][m_idx].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "pool_size_versus_relative_depth",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"sizes": list(SIZES), "k_abs": K_ABS, "rel_depth": REL_DEPTH,
                        "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(y)), "pool_full": int(len(y) - int(0.8 * len(y)))},
           "by_size": {}, "files": {}}

    for S in SIZES:
        ent = {}
        for label in ("abs50", "rel"):
            sub = r[(r.S == S) & (r.kdef == label)]
            if not len(sub):
                continue
            m = sub.set_index("rep")["mix"]
            e = sub.set_index("rep")["exploit"]
            ent[label] = {"k": int(sub["k"].iloc[0]),
                          "search": paired(m[m.index.isin(SEARCH)], e[e.index.isin(SEARCH)], 401 + S % 97),
                          "eval": paired(m[m.index.isin(EVAL)], e[e.index.isin(EVAL)], 501 + S % 97),
                          "all": paired(m, e, 601 + S % 97),
                          "exploit_hit": float(e.mean()), "mix_hit": float(m.mean())}
        res["by_size"][str(S)] = ent

    abs_diffs = [res["by_size"][str(S)]["abs50"]["all"]["mean_diff"] for S in SIZES if "abs50" in res["by_size"][str(S)]]
    rel_diffs = [res["by_size"][str(S)]["rel"]["all"]["mean_diff"] for S in SIZES if "rel" in res["by_size"][str(S)]]
    h125 = bool(len(abs_diffs) == 3 and abs_diffs[0] <= abs_diffs[1] <= abs_diffs[2]
                and (abs_diffs[2] - abs_diffs[0]) > 0.01)
    h126 = bool(len(rel_diffs) == 3 and (max(rel_diffs) - min(rel_diffs)) < 0.015)
    res["decisions"] = {"H125_abs_advantage_grows_with_pool": h125,
                        "H126_relative_depth_is_the_driver": h126}
    res["decisions"]["verdict"] = (
        "relative_depth_drives_it" if h126 else
        "pool_size_drives_it" if h125 else
        "neither_explains_the_R37_R47_gap")
    res["limits"] = [
        "Single dataset; only two k definitions; the training set is fixed so only the pool varies.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r49/PROTOCOL_E048.md",
                "research/2026-10-27-agent-cell-identifiability-r49/e049_pool_size.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E049_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E049_rows.csv", index=False)

    print("keys=%d full pool=%d" % (len(y), res["audit"]["pool_full"]))
    for S in SIZES:
        ent = res["by_size"][str(S)]
        for label in ("abs50", "rel"):
            if label in ent:
                x = ent[label]
                print("  S=%-6d kdef=%-5s k=%-3d | all %+.4f [%+.4f,%+.4f] | search %+.4f eval %+.4f" % (
                    S, label, x["k"], x["all"]["mean_diff"], x["all"]["ci95"][0], x["all"]["ci95"][1],
                    x["search"]["mean_diff"], x["eval"]["mean_diff"]))
    print("abs diffs:", [round(v, 4) for v in abs_diffs], "| rel diffs:", [round(v, 4) for v in rel_diffs])
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
