"""E050: does the pool-size mechanism from GDSC (R49) show the same DIRECTION on BATCHIE?

Pre-registered in PROTOCOL_E049.md. Small pools only (80/160/320 out of 351), fixed k=20.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r54"
ANCHORS = {"high control", "low control"}
LAMBDA = 1.0
SIZES = (80, 160, 320)
K = 20
REPEATS = 20
N_BOOT = 2000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


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
    assert sha256(CSV) == SHA
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["c1"] = pd.to_numeric(df["Conc 1 (uM)"], errors="coerce")
    df["c2"] = pd.to_numeric(df["Conc 2 (uM)"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    ok = df[(~df["anchor"]) & (~df["failed_qc"]) & df["y"].notna()]
    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["c1"].round(9), g["Drug 2"], g["c2"].round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "qc": float(g["failed_qc"].mean()),
                       "npairs": int(g.groupby(["Drug 1", "Drug 2"]).ngroups)}
    groups = {}
    for f, s in meta.items():
        groups.setdefault(s["h"], {}).setdefault(s["cell"], []).append(f)

    rng = np.random.default_rng(SEED)
    rows = []
    units = 0
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 2:
            continue
        if max(meta[f]["npairs"] for c in good for f in cells[c]) < 100:
            continue
        per_cell = {}
        for c in good:
            vs = []
            for f in cells[c]:
                s = ok[ok["file"] == f]
                v = s.groupby(["Drug 1", "Drug 2"])["y"].mean()
                if len(v) >= 100:
                    vs.append(v)
            if vs:
                per_cell[c] = pd.concat(vs, axis=1).mean(axis=1).dropna()
        for c, ser in per_cell.items():
            pairs = list(ser.index)
            y = ser.to_numpy(float)
            n = len(y)
            if n < 340:
                continue
            comps = sorted({d for p in pairs for d in p})
            cidx = {d: i for i, d in enumerate(comps)}
            X = np.zeros((n, len(comps)))
            for i, (a, b) in enumerate(pairs):
                X[i, cidx[a]] += 1.0
                X[i, cidx[b]] += 1.0
            units += 1
            for _ in range(REPEATS):
                perm = rng.permutation(n)
                for S in SIZES:
                    pool = perm[:S]
                    tr = perm[S:]
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
                    yp = y[pool]
                    hit = yp <= np.quantile(yp, 0.25)
                    rp = pd.Series(-pred).rank(pct=True).to_numpy()
                    rv = pd.Series(var).rank(pct=True).to_numpy()
                    mix = rp + rv
                    e_idx = np.argsort(-rp)[:K]
                    m_idx = np.argsort(-mix)[:K]
                    rows.append({"layout": h[:12], "cell": c, "S": S,
                                 "exploit": float(hit[e_idx].mean()),
                                 "mix": float(hit[m_idx].mean()),
                                 "chance": 0.25})

    r = pd.DataFrame(rows)
    r["diff"] = r["mix"] - r["exploit"]
    agg = r.groupby(["layout", "cell", "S"], as_index=False)[["exploit", "mix", "diff"]].mean()
    res = {"kind": "bidirectional_transfer_of_pool_size_predicate",
           "input_sha256": sha256(CSV),
           "settings": {"sizes": list(SIZES), "k": K, "repeats": REPEATS,
                        "lambda": LAMBDA, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": units, "rows": int(len(r)), "cells_scored": int(agg.groupby(["layout", "cell"]).ngroups)},
           "by_size": {}, "files": {}}

    for S in SIZES:
        sub = agg[agg.S == S].set_index(["layout", "cell"])
        res["by_size"][str(S)] = {
            "exploit": float(sub["exploit"].mean()), "mix": float(sub["mix"].mean()),
            "diff": float(sub["diff"].mean()),
            "paired": paired(sub["mix"], sub["exploit"], 701 + S % 89)}

    d80 = res["by_size"]["80"]["diff"]
    d320 = res["by_size"]["320"]["diff"]
    h127 = bool(d320 > d80 and (d320 - d80) > 0.01)
    h128 = bool(all(res["by_size"][str(S)]["diff"] < 0 for S in SIZES))

    # ---- cross-task transfer of the GDSC predicate ----
    S_STAR_GDSC = 3000
    decisions = {}
    for S in SIZES:
        decisions[str(S)] = "exploit" if S < S_STAR_GDSC else "mix"
    res["transfer_A_gdsc_to_batchie"] = {
        "gdsc_threshold": S_STAR_GDSC,
        "predicted_action_by_size": decisions,
        "all_pools_below_threshold": all(S < S_STAR_GDSC for S in SIZES),
        "actual_exploit_wins_by_size": {str(S): bool(res["by_size"][str(S)]["diff"] < 0) for S in SIZES},
        "prediction_holds": all(res["by_size"][str(S)]["diff"] < 0 for S in SIZES)}
    res["transfer_B_batchie_to_gdsc"] = {
        "sizes_available": list(SIZES),
        "any_positive_diff": any(res["by_size"][str(S)]["diff"] > 0 for S in SIZES),
        "threshold_learnable": any(res["by_size"][str(S)]["diff"] > 0 for S in SIZES),
        "note": "with only pools of 80-320 the smallest positive size does not exist, so the GDSC threshold cannot be learned from BATCHIE"}

    h138 = res["transfer_A_gdsc_to_batchie"]["prediction_holds"]
    h139 = not res["transfer_B_batchie_to_gdsc"]["threshold_learnable"]
    h140 = bool(h138 and h139)
    res["decisions"] = {"H127_direction_matches_GDSC": h127, "H128_all_negative_small_pools": h128,
                        "H138_transfer_A_holds": h138, "H139_transfer_B_unlearnable": h139,
                        "H140_directional_transfer": h140}
    res["decisions"]["verdict"] = (
        "predicate_transfers_one_way" if h140 else
        "mechanism_replicates_in_direction" if h127 and h128 else
        "pool_size_does_not_explain_batchie")
    res["limits"] = [
        "BATCHIE pools max out at 351 pairs, far below GDSC's 21,652, so only the small-pool regime is probed.",
        "The hit definitions differ between tasks (synergy flag vs bottom-quartile viability); only the direction is comparable.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r50/PROTOCOL_E049.md",
                "research/2026-10-27-agent-cell-identifiability-r50/e050_batchie_pools.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E054_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E054_rows.csv", index=False)

    print("units=%d cells scored=%d" % (units, res["audit"]["cells_scored"]))
    for S in SIZES:
        e = res["by_size"][str(S)]
        print("  S=%-4d exploit=%.4f mix=%.4f | diff %+.4f [%+.4f,%+.4f]" % (
            S, e["exploit"], e["mix"], e["diff"], e["paired"]["ci95"][0], e["paired"]["ci95"][1]))
    print("S320 - S80 = %+.4f" % (d320 - d80))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
