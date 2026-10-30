"""E038: does the budget-conditioned rule (exploit at small k, mix at large k) transfer to
a different task - the BATCHIE high-diversity design?

Pre-registered in PROTOCOL_E038.md. Reads only PAIR_SCREEN.csv.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r38"
ANCHORS = {"high control", "low control"}
LAMBDA = 1.0
KS = (5, 10, 20, 40, 60)
REPEATS = 20
TRAIN_FRAC = 100 / 351
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
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "a": float(j["a"].mean()), "b": float(j["b"].mean())}


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
            if n < 200:
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
                ntr = int(TRAIN_FRAC * n)
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
                yp = y[pool]
                quart = float(np.quantile(yp, 0.25))
                hit = yp <= quart
                rp = pd.Series(-pred).rank(pct=True).to_numpy()   # lower predicted viability = better
                rv = pd.Series(var).rank(pct=True).to_numpy()
                for k in KS:
                    if k >= len(pool) // 3:
                        continue
                    for name, sc in (("exploit", rp), ("mix", rp + rv), ("explore", rv)):
                        idx = np.argsort(-sc)[:k]
                        rows.append({"layout": h[:12], "cell": c, "k": k, "strategy": name,
                                     "hit": float(hit[idx].mean())})
                    idx = rng.permutation(len(pool))[:k]
                    rows.append({"layout": h[:12], "cell": c, "k": k, "strategy": "random",
                                 "hit": float(hit[idx].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "budget_rule_transfer_to_batchie_high_diversity",
           "input_sha256": sha256(CSV),
           "settings": {"lambda": LAMBDA, "ks": list(KS), "repeats": REPEATS,
                        "train_frac": TRAIN_FRAC, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": units, "layouts": int(r["layout"].nunique()) if len(r) else 0,
                     "rows": int(len(r)), "hit_definition": "selected pair in the true bottom quartile of the pool"},
           "by_k": {}, "files": {}}

    for k in KS:
        sub = r[r["k"] == k]
        if not len(sub):
            continue
        ent = {"all": {s: float(g["hit"].mean()) for s, g in sub.groupby("strategy")}}
        a = sub[sub.strategy == "mix"].groupby(["layout", "cell"])["hit"].mean()
        b = sub[sub.strategy == "exploit"].groupby(["layout", "cell"])["hit"].mean()
        c = sub[sub.strategy == "explore"].groupby(["layout", "cell"])["hit"].mean()
        d = sub[sub.strategy == "random"].groupby(["layout", "cell"])["hit"].mean()
        ent["mix_minus_exploit"] = paired(a, b, 41)
        ent["exploit_minus_random"] = paired(b, d, 42)
        ent["explore_minus_exploit"] = paired(c, b, 43)
        res["by_k"][str(k)] = ent

    ks_used = sorted(int(x) for x in r["k"].unique())
    last = res["by_k"][str(ks_used[-1])]["mix_minus_exploit"]
    small = [res["by_k"][str(k)]["mix_minus_exploit"] for k in ks_used if k <= 10]
    h097 = bool(last and last["ci95"][0] > 0 and all(s and s["mean_diff"] <= 0 for s in small))
    any_positive = any(res["by_k"][str(k)]["mix_minus_exploit"]["mean_diff"] > 0 for k in ks_used)
    crossover = next((k for k in ks_used if res["by_k"][str(k)]["mix_minus_exploit"]["mean_diff"] > 0), None)
    h099 = bool(not any_positive)
    res["crossover_k"] = crossover
    res["decisions"] = {"H097_rule_shape_transfers": h097, "H099_rule_does_not_transfer": h099}
    res["decisions"]["verdict"] = ("rule_shape_transfers" if h097 else
                                   "direction_only_ci_includes_zero" if any_positive else
                                   "rule_is_gdsc_specific")
    res["limits"] = [
        "The hit definition differs between tasks (GDSC synergy flag/strong-decile vs BATCHIE bottom-quartile viability), so only the SHAPE is comparable.",
        "BATCHIE features are compound composition only; no pathway or tissue annotation.",
        "Retrospective candidate pool; one lambda; train fraction fixed at 100/351.",
        "No mechanistic, clinical or drug-choice claim.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r38/PROTOCOL_E038.md",
                "research/2026-10-27-agent-cell-identifiability-r38/e038_transfer.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E038_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E038_rows.csv", index=False)

    print("units=%d layouts=%d rows=%d | ks=%s" % (units, res["audit"]["layouts"], len(r), ks_used))
    for k in ks_used:
        e = res["by_k"][str(k)]
        m = e["mix_minus_exploit"]
        print("  k=%-3d exploit=%.4f mix=%.4f explore=%.4f random=%.4f | mix-exp %+.4f [%+.4f,%+.4f]" % (
            k, e["all"]["exploit"], e["all"]["mix"], e["all"]["explore"], e["all"]["random"],
            m["mean_diff"], m["ci95"][0], m["ci95"][1]))
    print("crossover_k:", crossover)
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
