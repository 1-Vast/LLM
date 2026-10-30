"""E094: coverage re-done properly, per R93's own remedy.

Combination-level evaluation with m fixed at 5, 100 independent masking draws per coverage
level, and the identity stability of the chosen pairs reported so that "which pair won" can
no longer masquerade as a coverage effect.

Pre-registered in PROTOCOL_E089.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r94"
M = 5
DRAWS = 100
N_BOOT = 2000
SEED = 20261027
LEVELS = {1.00: 0.0, 0.64: 0.20, 0.36: 0.40, 0.16: 0.60}
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
        combo=("combo", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        syn=("syn", "mean"))
    g["syn"] = g["syn"] > 0.5
    g["a"] = g["a"].astype(str)
    g["b"] = g["b"].astype(str)
    A = g["a"].to_numpy()
    B = g["b"].to_numpy()
    COMBO = g["combo"].to_numpy()
    y = g["syn"].to_numpy(bool)
    drugs = sorted(set(A) | set(B))
    combos_all = pd.unique(COMBO)

    rng = np.random.default_rng(SEED)
    rows = []
    prev_top = None
    for target, frac in LEVELS.items():
        draws = []
        for k in range(DRAWS):
            masked = set(rng.choice(drugs, size=max(1, int(round(frac * len(drugs)))), replace=False))
            grand = float(y.mean())
            dm = {}
            for i in range(len(g)):
                if A[i] not in masked:
                    dm.setdefault(A[i], []).append(y[i])
                if B[i] not in masked:
                    dm.setdefault(B[i], []).append(y[i])
            deff = {key: float(np.mean(v)) - grand for key, v in dm.items()}
            score = np.array([0.5 * (deff.get(A[i], 0.0) + deff.get(B[i], 0.0)) for i in range(len(g))])
            df = pd.DataFrame({"combo": COMBO, "score": score, "syn": y.astype(float)})
            agg = df.groupby("combo", as_index=False).agg(score=("score", "mean"),
                                                          rate=("syn", "mean"), n=("syn", "size"))
            # only combinations whose BOTH drugs are seen can be recommended
            seen_combo = np.array([
                (c.split(" + ")[0] not in masked) and (c.split(" + ")[1] not in masked) for c in agg["combo"]
            ])
            avail = int(seen_combo.sum())
            if avail < M:
                continue
            sub = agg[seen_combo].nlargest(M, "score")
            hit = float((sub["rate"] * sub["n"]).sum() / sub["n"].sum())
            rnd = agg[seen_combo].sample(n=M, random_state=int(rng.integers(0, 10 ** 6)))
            hit_r = float((rnd["rate"] * rnd["n"]).sum() / rnd["n"].sum())
            top = tuple(sub["combo"].tolist())
            rows.append({"coverage": target, "actual_coverage": float(seen_combo.mean()),
                         "marginal": hit, "random": hit_r, "avail_combos": avail,
                         "n_keys_total": int(sub["n"].sum()), "top": top})
            draws.append(top)
        # identity stability: how often the same top-m set repeats between consecutive draws
        if len(draws) > 1:
            same_all = float(np.mean([draws[i] == draws[i - 1] for i in range(1, len(draws))]))
            overlap = float(np.mean([
                len(set(draws[i]) & set(draws[i - 1])) / M for i in range(1, len(draws))]))
        else:
            same_all, overlap = float("nan"), float("nan")
        prev_top = draws[-1] if draws else prev_top
        if draws:
            rows[-1]["same_as_prev_draw"] = same_all
            rows[-1]["overlap_with_prev_draw"] = overlap

    r = pd.DataFrame(rows)
    res = {"kind": "coverage_redo_combination_level_m5",
           "input_sha256": sha256(ORIG),
           "settings": {"m": M, "draws_per_level": DRAWS, "n_boot": N_BOOT, "seed": SEED,
                        "criterion": "dataset boolean Synergy", "levels": {str(k): v for k, v in LEVELS.items()}},
           "audit": {"keys": int(len(g)), "combos": int(len(combos_all)), "drugs": len(drugs),
                     "units": int(len(r))},
           "by_coverage": {}, "files": {}}

    for target in LEVELS:
        sub = r[r.coverage == target]
        if len(sub) < 10:
            continue
        res["by_coverage"][f"{target:.2f}"] = {
            "n": int(len(sub)), "actual_coverage": float(sub["actual_coverage"].mean()),
            "avail_combos": float(sub["avail_combos"].mean()),
            "marginal": float(sub["marginal"].mean()), "random": float(sub["random"].mean()),
            "hit_minus_random": paired(sub["marginal"], sub["random"], 20001 + int(target * 100)),
            "identity_same_as_previous": float(sub["same_as_prev_draw"].mean()),
            "identity_overlap": float(sub["overlap_with_prev_draw"].mean())}

    series = [(c, res["by_coverage"][f"{c:.2f}"]) for c in sorted(LEVELS, reverse=True)
              if f"{c:.2f}" in res["by_coverage"]]
    vals = [e["marginal"] for _, e in series]
    viol = sum(1 for i in range(len(vals) - 1) if vals[i] < vals[i + 1] - 0.005)
    h240 = bool(len(vals) >= 3 and viol <= 1)
    fails = [c for c, e in series if e["hit_minus_random"]["ci95"][0] <= 0]
    h241 = bool(fails)
    avail = [e["avail_combos"] for _, e in series]
    h242 = bool(len(avail) >= 2 and avail[0] > avail[-1] * 1.2)
    res["decisions"] = {"H240_value_falls_with_coverage": h240,
                        "H241_coverage_threshold_exists": h241,
                        "H242_available_pool_shrinks": h242,
                        "first_failing_coverage": (min(fails) if fails else None)}
    res["decisions"]["verdict"] = (
        "coverage_is_a_real_condition" if h240 else
        "coverage_does_not_show_as_a_limit")
    res["limits"] = [
        "Masking is artificial; real missingness carries selection bias.",
        "m=5 is still small, though far steadier than R93's effective 1-2.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r94/PROTOCOL_E089.md",
                "research/2026-10-27-agent-cell-identifiability-r94/e094_coverage_redo.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E094_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.drop(columns=["top"]).to_csv(OUT / "E094_rows.csv", index=False)

    print("keys=%d combos=%d units=%d" % (len(g), len(combos_all), len(r)))
    for c, e in series:
        a = e["hit_minus_random"]
        print("  cov %.2f (act %.2f) avail=%4.0f | marginal %.4f random %.4f | diff %+.4f [%+.4f,%+.4f] | ident %.2f/%.2f" % (
            c, e["actual_coverage"], e["avail_combos"], e["marginal"], e["random"],
            a["mean_diff"], a["ci95"][0], a["ci95"][1],
            e["identity_same_as_previous"], e["identity_overlap"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
