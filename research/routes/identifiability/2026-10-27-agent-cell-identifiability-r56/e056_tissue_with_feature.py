"""E055: does the pool-size crossover exist in a HELD-OUT tissue population, and does the
threshold learned on the other two tissues transfer to it?

Pre-registered in PROTOCOL_E054.md. Pathway features only (38 dims) so that training and the
held-out population share the same feature space.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r56"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
SIZES = (500, 1000, 2000, 3500)
K = 20
REPEATS = 20
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


def evaluate(Xtr, ytr, Xpool, ypool, k):
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd[sd == 0] = 1.0
    Xs = (Xtr - mu) / sd
    Xp = (Xpool - mu) / sd
    A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
    Ainv = np.linalg.inv(A)
    w = Ainv @ Xs.T @ (ytr - ytr.mean())
    pred = ytr.mean() + Xp @ w
    var = np.einsum("ij,jk,ik->i", Xp, Ainv, Xp)
    strong = ypool >= np.quantile(ypool, 0.90)
    rp = pd.Series(pred).rank(pct=True).to_numpy()
    rv = pd.Series(var).rank(pct=True).to_numpy()
    mix = rp + rv
    e = float(strong[np.argsort(-rp)[:k]].mean())
    m = float(strong[np.argsort(-mix)[:k]].mean())
    return e, m


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        tissue=("Tissue", "first"), ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        synergy=(METRIC, "mean"))
    for c in ("tissue", "ap", "lp"):
        d[c] = d[c].astype(str).fillna("NA")

    ap_lv = sorted(d["ap"].unique())
    lp_lv = sorted(d["lp"].unique())
    ti_lv = sorted(d["tissue"].unique())
    X = np.hstack([onehot(d["ap"].to_numpy(), ap_lv),
                   onehot(d["lp"].to_numpy(), lp_lv),
                   onehot(d["tissue"].to_numpy(), ti_lv)])
    y = d.synergy.to_numpy(float)
    tissue = d["tissue"].to_numpy()
    tissues = sorted(pd.unique(tissue))

    res = {"kind": "held_out_tissue_threshold_transfer_with_tissue_feature",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"sizes": list(SIZES), "k": K, "repeats": REPEATS, "lambda": LAMBDA,
                        "features": "pathway + tissue (held-out tissue column constant in training)", "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(y)), "features": int(X.shape[1]),
                     "per_tissue": {t: int((tissue == t).sum()) for t in tissues}},
           "folds": {}, "files": {}}

    rng = np.random.default_rng(SEED)
    crossovers = {}
    for held in tissues:
        tr_idx = np.where(tissue != held)[0]
        ho_idx = np.where(tissue == held)[0]
        Xtr_all, ytr_all = X[tr_idx], y[tr_idx]
        rows = []
        for rep in range(REPEATS):
            for S in SIZES:
                if S >= len(ho_idx):
                    continue
                pool = rng.choice(ho_idx, size=S, replace=False)
                e, m = evaluate(Xtr_all, ytr_all, X[pool], y[pool], K)
                rows.append({"rep": rep, "S": S, "exploit": e, "mix": m})
        rr = pd.DataFrame(rows)
        by = {}
        for S in SIZES:
            sub = rr[rr.S == S]
            if not len(sub):
                continue
            by[str(S)] = {"exploit": float(sub["exploit"].mean()), "mix": float(sub["mix"].mean()),
                          "diff": float((sub["mix"] - sub["exploit"]).mean()),
                          "paired": paired(sub["mix"], sub["exploit"], 1501 + S % 97 + len(held))}
        # crossover in the held-out population
        pos_sizes = [S for S in SIZES if str(S) in by and by[str(S)]["diff"] > 0]
        crossovers[held] = min(pos_sizes) if pos_sizes else None
        res["folds"][held] = {"by_size": by, "n_holdout_keys": int(len(ho_idx)),
                              "crossover": crossovers[held]}

    # learn the threshold on the training tissues for each fold (80/20 inside the training set)
    res["training_thresholds"] = {}
    for held in tissues:
        tr_idx = np.where(tissue != held)[0]
        Xt, yt = X[tr_idx], y[tr_idx]
        rows = []
        for rep in range(REPEATS):
            perm = rng.permutation(len(yt))
            ntr = int(0.8 * len(yt))
            a, b = perm[:ntr], perm[ntr:]
            for S in SIZES:
                if S >= len(b):
                    continue
                pool = rng.choice(b, size=S, replace=False)
                e, m = evaluate(Xt[a], yt[a], Xt[pool], yt[pool], K)
                rows.append({"rep": rep, "S": S, "exploit": e, "mix": m})
        rr = pd.DataFrame(rows)
        by = {str(S): float((rr[rr.S == S]["mix"] - rr[rr.S == S]["exploit"]).mean())
              for S in SIZES if len(rr[rr.S == S])}
        pos = [S for S in SIZES if str(S) in by and by[str(S)] > 0]
        res["training_thresholds"][held] = {"by_size": by, "threshold": min(pos) if pos else None}

    # H141: crossover exists in at least 2/3 held-out populations
    n_cross = sum(1 for v in crossovers.values() if v is not None)
    h141 = n_cross >= 2
    # H142: threshold transfers, measured as agreement of the per-size decision
    agree, total = 0, 0
    detail = {}
    for held in tissues:
        thr = res["training_thresholds"][held]["threshold"]
        fold = res["folds"][held]["by_size"]
        if thr is None:
            continue
        d_ = {}
        for S in SIZES:
            if str(S) not in fold:
                continue
            pred = "mix" if S >= thr else "exploit"
            actual = "mix" if fold[str(S)]["diff"] > 0 else "exploit"
            d_[str(S)] = {"predicted": pred, "actual": actual, "agree": pred == actual}
            agree += int(pred == actual)
            total += 1
        detail[held] = {"threshold_from_training": thr, "decisions": d_}
    res["transfer_decisions"] = detail
    h142 = bool(total and agree / total >= 0.75)
    # H143: crossover within one size step of the learned threshold
    close = 0
    n = 0
    for held in tissues:
        thr = res["training_thresholds"][held]["threshold"]
        cr = crossovers[held]
        if thr is None or cr is None:
            continue
        n += 1
        if abs(SIZES.index(cr) - SIZES.index(thr)) <= 1:
            close += 1
    h143 = bool(n and close == n)
    res["decisions"] = {"H141_crossover_in_heldout": h141, "H142_threshold_transfers": h142,
                        "H143_positions_close": h143,
                        "agreement_rate": (agree / total) if total else None}
    res["decisions"]["verdict"] = ("threshold_transfers_to_unseen_population" if h141 and h142 else
                                   "crossover_not_universal" if not h141 else
                                   "crossover_exists_but_threshold_does_not_transfer")
    res["limits"] = [
        "Tissue strata are populations within one dataset, not separate tasks.",
        "Pathway features only, so training and the held-out population share a feature space.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r55/PROTOCOL_E054.md",
                "research/2026-10-27-agent-cell-identifiability-r55/e055_tissue_transfer.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E056_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("keys=%d features=%d" % (len(y), res["audit"]["features"]))
    for held in tissues:
        f = res["folds"][held]
        print("held-out %s (pool max %d) crossover=%s" % (held, f["n_holdout_keys"], f["crossover"]))
        for S in SIZES:
            if str(S) in f["by_size"]:
                x = f["by_size"][str(S)]
                print("    S=%-5d exploit=%.4f mix=%.4f | diff %+.4f [%+.4f,%+.4f]" % (
                    S, x["exploit"], x["mix"], x["diff"], x["paired"]["ci95"][0], x["paired"]["ci95"][1]))
        t = res["training_thresholds"][held]
        print("    training threshold=%s by_size=%s" % (t["threshold"], {k: round(v, 4) for k, v in t["by_size"].items()}))
    print("agreement:", res["decisions"]["agreement_rate"])
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
