"""E093: coverage as an operative condition.

R92 found the cross-tissue test only had 32% coverage for Breast, which suggests the real
constraint is how many drugs the algorithm has seen, not which tissue it came from. Here a
fraction of drugs is masked as unseen, so coverage is controlled directly and the algorithm's
value is traced as a function of coverage.

Pre-registered in PROTOCOL_E088.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r93"
K = 20
REPEATS = 40
N_BOOT = 2000
SEED = 20261027
TARGETS = {1.00: 0.0, 0.80: 0.106, 0.64: 0.20, 0.49: 0.30, 0.36: 0.40, 0.25: 0.50, 0.16: 0.60}
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "Synergy"]


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
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    g = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), syn=("syn", "mean"))
    g["syn"] = g["syn"] > 0.5
    g["a"] = g["a"].astype(str)
    g["b"] = g["b"].astype(str)
    A = g["a"].to_numpy()
    B = g["b"].to_numpy()
    y = g["syn"].to_numpy(bool)
    drugs = sorted(set(A) | set(B))

    rng = np.random.default_rng(SEED)
    rows = []
    for target, frac in TARGETS.items():
        for rep in range(REPEATS):
            masked = set(rng.choice(drugs, size=max(1, int(round(frac * len(drugs)))), replace=False))
            grand = float(y.mean())
            dm = {}
            seen_mask = []
            for i in range(len(g)):
                a_seen = A[i] not in masked
                b_seen = B[i] not in masked
                seen_mask.append(a_seen and b_seen)
                if a_seen:
                    dm.setdefault(A[i], []).append(y[i])
                if b_seen:
                    dm.setdefault(B[i], []).append(y[i])
            deff = {k: float(np.mean(v)) - grand for k, v in dm.items()}
            score = np.array([
                0.5 * (deff.get(A[i], 0.0) + deff.get(B[i], 0.0)) for i in range(len(g))
            ])
            # restrict to the covered subset: keys whose BOTH drugs are seen
            cov = np.array(seen_mask)
            if cov.sum() < 5 * K:
                continue
            idx = np.where(cov)[0]
            hit_m = float(y[idx][np.argsort(-score[idx])[:K]].mean())
            hit_r = float(y[idx][rng.choice(len(idx), size=K, replace=False)].mean())
            rows.append({"target_coverage": target, "actual_coverage": float(cov.mean()),
                         "rep": rep, "marginal": hit_m, "random": hit_r,
                         "base": float(y[idx].mean()), "n_covered": int(cov.sum())})

    r = pd.DataFrame(rows)
    res = {"kind": "coverage_as_an_operative_condition",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED,
                        "criterion": "dataset boolean Synergy", "targets": {str(k): v for k, v in TARGETS.items()}},
           "audit": {"keys": int(len(g)), "drugs": len(drugs), "units": int(len(r))},
           "by_coverage": {}, "files": {}}

    for target in TARGETS:
        sub = r[r.target_coverage == target]
        if len(sub) < 5:
            continue
        res["by_coverage"][f"{target:.2f}"] = {
            "target": target, "n": int(len(sub)),
            "actual_coverage": float(sub["actual_coverage"].mean()),
            "marginal": float(sub["marginal"].mean()), "random": float(sub["random"].mean()),
            "base": float(sub["base"].mean()),
            "marginal_minus_random": paired(sub["marginal"], sub["random"], 19001 + int(target * 1000))}

    covs = sorted(TARGETS, reverse=True)
    series = [(c, res["by_coverage"][f"{c:.2f}"]) for c in covs if f"{c:.2f}" in res["by_coverage"]]
    vals = [e["marginal"] for _, e in series]
    viol = sum(1 for i in range(len(vals) - 1) if vals[i] < vals[i + 1] - 1e-9)
    h237 = bool(len(vals) >= 3 and viol <= 1)
    fails = [c for c, e in series if e["marginal_minus_random"]["ci95"][0] <= 0]
    h238 = bool(fails)
    lo = res["by_coverage"].get("0.25")
    h239 = bool(lo and lo["marginal_minus_random"]["ci95"][0] > 0)
    res["decisions"] = {"H237_value_falls_with_coverage": h237,
                        "H238_failure_point_exists": h238,
                        "H239_still_useful_at_25pct_coverage": h239,
                        "first_failing_coverage": (min(fails) if fails else None)}
    res["decisions"]["verdict"] = (
        "coverage_threshold_exists" if h238 else
        "algorithm_is_insensitive_to_coverage")
    res["limits"] = [
        "Masking is artificial; real missingness also carries selection bias.",
        "Coverage is set by expectation, so actual coverage is reported alongside the target.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r93/PROTOCOL_E088.md",
                "research/2026-10-27-agent-cell-identifiability-r93/e093_coverage.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E093_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E093_rows.csv", index=False)

    print("keys=%d drugs=%d units=%d" % (len(g), len(drugs), len(r)))
    for c, e in series:
        a = e["marginal_minus_random"]
        print("  coverage %.2f (actual %.2f) | base %.4f marginal %.4f random %.4f | diff %+.4f [%+.4f,%+.4f]" % (
            c, e["actual_coverage"], e["base"], e["marginal"], e["random"],
            a["mean_diff"], a["ci95"][0], a["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
