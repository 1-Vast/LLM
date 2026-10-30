"""E022: how much of a new cell's own data is needed before it beats cross-cell pooling?

Pre-registered in PROTOCOL_E022.md. Reads only PAIR_SCREEN.csv.

For each (layout, target cell): mu_o = mean viability of the other cells (351 pairs).
Sample m of the target's measurements, fit y ~ a + b*mu_o on those m, predict the rest,
and score precision@10 against the true ten lowest in the unmeasured set.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r22"
ANCHORS = {"high control", "low control"}
MS = (0, 5, 10, 25, 50, 100)
REPS = 20
TOP = 10
N_BOOT = 1000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def precision_at_k(pred: np.ndarray, truth: np.ndarray, k: int) -> float:
    n = len(pred)
    if n <= k:
        return float("nan")
    kk = min(k, n - 1)
    pred_top = set(np.argsort(pred)[:kk].tolist())
    true_top = set(np.argsort(truth)[:kk].tolist())
    return len(pred_top & true_top) / kk


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

    rows = []
    rng = np.random.default_rng(SEED)
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
                per_cell[c] = pd.concat(vs, axis=1).mean(axis=1)
        cs = sorted(per_cell)
        for c in cs:
            others = [x for x in cs if x != c]
            if len(others) < 1:
                continue
            idx = per_cell[c].index
            mu_o = pd.concat([per_cell[o] for o in others], axis=1).reindex(idx).mean(axis=1).to_numpy(float)
            yc = per_cell[c].to_numpy(float)
            if not np.isfinite(mu_o).all() or not np.isfinite(yc).all():
                continue
            n = len(yc)
            if n < 150:
                continue
            for m in MS:
                if m >= n - TOP - 5:
                    continue
                vals = []
                for _ in range(REPS):
                    meas = rng.choice(n, size=m, replace=False) if m else np.array([], dtype=int)
                    mask = np.ones(n, dtype=bool)
                    mask[meas] = False
                    pred = mu_o.copy()
                    if m >= 5:
                        x = mu_o[meas]
                        y = yc[meas]
                        if np.std(x) > 1e-9:
                            b = float(np.cov(x, y, bias=True)[0, 1] / np.var(x))
                            a = float(np.mean(y) - b * np.mean(x))
                        else:
                            b, a = 1.0, 0.0
                        b = float(np.clip(b, 0.0, 3.0))
                        pred = a + b * mu_o
                    p10 = precision_at_k(pred[mask], yc[mask], TOP)
                    vals.append(p10)
                rows.append({"layout": h[:12], "cell": c, "m": m, "n": n,
                             "precision10": float(np.mean(vals)),
                             "chance": TOP / (n - m - TOP)})

    d = pd.DataFrame(rows)
    res = {"kind": "minimal_evidence_for_a_new_cell_affine_calibration",
           "input_sha256": sha256(CSV),
           "settings": {"ms": list(MS), "reps": REPS, "top": TOP, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"layouts": int(d["layout"].nunique()) if len(d) else 0,
                     "cell_units": int(d.groupby(["layout", "cell"]).ngroups) if len(d) else 0,
                     "pairs_per_unit_median": float(d["n"].median()) if len(d) else None},
           "by_m": {}, "files": {}}

    def summ(sub):
        rng2 = np.random.default_rng(SEED + 3)
        units = sub.groupby(["layout", "cell"])["precision10"].mean().to_numpy(float)
        boots = [float(np.mean(rng2.choice(units, size=len(units), replace=True))) for _ in range(N_BOOT)]
        return {"n_units": int(len(units)), "mean_precision10": float(units.mean()),
                "ci95_unit_bootstrap": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
                "chance_mean": float(sub["chance"].mean()),
                "lift_over_chance": float(units.mean() / sub["chance"].mean()) if sub["chance"].mean() > 0 else None}

    if len(d):
        for m in MS:
            sub = d[d["m"] == m]
            if len(sub):
                res["by_m"][str(m)] = summ(sub)

        def paired(m1, m2):
            a = d[d["m"] == m1].groupby(["layout", "cell"])["precision10"].mean()
            b = d[d["m"] == m2].groupby(["layout", "cell"])["precision10"].mean()
            j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
            if len(j) < 3:
                return None
            dif = (j["a"] - j["b"]).to_numpy(float)
            rng3 = np.random.default_rng(SEED + 4)
            boots = [float(np.mean(rng3.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
            return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
                    "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}

        pairs = {f"{a}_vs_{b}": paired(a, b) for a, b in ((0, 5), (0, 10), (10, 25), (10, 50), (0, 100))}
        res["paired"] = pairs
        p0 = res["by_m"].get("0")
        p10 = res["by_m"].get("10")
        h049 = bool(p0 and p0["ci95_unit_bootstrap"][0] > 3 * p0["chance_mean"])
        h050 = bool(pairs.get("0_vs_10") and pairs["0_vs_10"]["ci95"][0] > 0)
        d10 = pairs.get("0_vs_10")
        d25 = pairs.get("10_vs_25")
        h051 = bool(d10 and d25 and d25["mean_diff"] <= 0.5 * d10["mean_diff"])
    else:
        h049 = h050 = h051 = False
    res["decisions"] = {"H049_zero_evidence_beats_chance": h049, "H050_ten_measurements_help": h050,
                        "H051_saturates_by_25": h051}
    res["decisions"]["verdict"] = ("minimal_evidence_is_about_ten" if h050 and h051 else
                                   "own_data_helps_but_needs_more" if h050 else
                                   "pooling_is_already_the_ceiling")
    res["limits"] = [
        "precision@10 is a ranking quantity, NOT a decision value or a clinical recommendation.",
        "Calibration uses only two parameters (a, b), so the 'own data' arm is deliberately weak; a stronger learner would need more measurements to fit.",
        "No dose dimension in this design; 'best' means the ten lowest-viability pairs in the unmeasured set.",
        "Exploratory: plates were used as scoring endpoints earlier and cells cross days.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r22/PROTOCOL_E022.md",
                "research/2026-10-27-agent-cell-identifiability-r22/e022_minimal_evidence.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E022_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(d):
        d.to_csv(OUT / "E022_units.csv", index=False)

    print("layouts=%d cell_units=%d" % (res["audit"]["layouts"], res["audit"]["cell_units"]))
    for m, v in res["by_m"].items():
        print("   m=%-3s precision@10=%.3f CI=[%.3f,%.3f] chance=%.3f lift=%.1fx" % (
            m, v["mean_precision10"], v["ci95_unit_bootstrap"][0], v["ci95_unit_bootstrap"][1],
            v["chance_mean"], v["lift_over_chance"] or 0))
    print("paired:", json.dumps({k: (None if v is None else {"d": round(v["mean_diff"], 4), "ci": [round(x, 4) for x in v["ci95"]]}) for k, v in res.get("paired", {}).items()}, ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
