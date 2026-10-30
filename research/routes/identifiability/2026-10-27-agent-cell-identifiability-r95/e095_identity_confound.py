"""E095: is R94's "identity instability" a confound?

R94 compared top-5 sets across draws that used DIFFERENT masks, i.e. different available drugs,
so the sets had to differ. That is not irreproducibility. Here the mask is fixed and only the
keys are resampled, so the variation measured is estimation noise alone.

Pre-registered in PROTOCOL_E090.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r95"
M = 5
BOOTS = 100
MASKS = 20
N_BOOT = 2000
SEED = 20261027
LEVELS = {1.00: 0.0, 0.36: 0.40, 0.16: 0.60}
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

    rng = np.random.default_rng(SEED)

    def top5(idx_rows, seen):
        """top-5 distinct combinations by mean marginal score over the given key rows."""
        en1 = np.array([A[i] not in seen for i in idx_rows])
        en2 = np.array([B[i] not in seen for i in idx_rows])
        dm = {}
        for j, i in enumerate(idx_rows):
            if en1[j]:
                dm.setdefault(A[i], []).append(y[i])
            if en2[j]:
                dm.setdefault(B[i], []).append(y[i])
        grand = float(y[idx_rows].mean())
        deff = {k: float(np.mean(v)) - grand for k, v in dm.items()}
        sc = np.array([0.5 * (deff.get(A[i], 0.0) + deff.get(B[i], 0.0)) for i in idx_rows])
        df = pd.DataFrame({"combo": COMBO[idx_rows], "score": sc, "syn": y[idx_rows].astype(float)})
        agg = df.groupby("combo", as_index=False).agg(score=("score", "mean"),
                                                      rate=("syn", "mean"), n=("syn", "size"))
        okc = np.array([(c.split(" + ")[0] not in seen) and (c.split(" + ")[1] not in seen)
                        for c in agg["combo"]])
        if okc.sum() < M:
            return None
        sub = agg[okc].nlargest(M, "score")
        hit = float((sub["rate"] * sub["n"]).sum() / sub["n"].sum())
        return tuple(sorted(sub["combo"].tolist())), hit

    rows = []
    for target, frac in LEVELS.items():
        for mk in range(MASKS):
            seen = set(rng.choice(drugs, size=max(1, int(round(frac * len(drugs)))), replace=False))
            base_rows = np.arange(len(g))
            newmask_tops, fixed_tops, hits_fixed = [], [], []
            # (a) R94's method: vary the mask (different available drugs)
            for _ in range(20):
                seen2 = set(rng.choice(drugs, size=max(1, int(round(frac * len(drugs)))), replace=False))
                r2 = top5(base_rows, seen2)
                if r2:
                    newmask_tops.append(r2[0])
            # (b) this round: fix the mask, resample the keys
            for _ in range(BOOTS):
                idx = rng.choice(base_rows, size=len(base_rows), replace=True)
                r = top5(np.unique(idx), seen)
                if r:
                    fixed_tops.append(r[0])
                    hits_fixed.append(r[1])

            def overlap(seq):
                if len(seq) < 2:
                    return float("nan"), float("nan")
                same = float(np.mean([seq[i] == seq[i - 1] for i in range(1, len(seq))]))
                ov = float(np.mean([len(set(seq[i]) & set(seq[i - 1])) / M for i in range(1, len(seq))]))
                return same, ov

            s_fix, o_fix = overlap(fixed_tops)
            s_new, o_new = overlap(newmask_tops)
            rows.append({"coverage": target, "mask_index": mk,
                         "same_fixed_mask": s_fix, "overlap_fixed_mask": o_fix,
                         "same_varying_mask": s_new, "overlap_varying_mask": o_new,
                         "hit_fixed_mean": float(np.mean(hits_fixed)) if hits_fixed else np.nan,
                         "hit_fixed_sd": float(np.std(hits_fixed)) if hits_fixed else np.nan})

    r = pd.DataFrame(rows)
    res = {"kind": "is_R94_identity_instability_a_confound",
           "input_sha256": sha256(ORIG),
           "settings": {"m": M, "boots": BOOTS, "masks": MASKS, "n_boot": N_BOOT, "seed": SEED,
                        "levels": {str(k): v for k, v in LEVELS.items()}},
           "audit": {"keys": int(len(g)), "units": int(len(r))},
           "by_coverage": {}, "files": {}}

    for target in LEVELS:
        sub = r[r.coverage == target]
        if len(sub) < 3:
            continue
        res["by_coverage"][f"{target:.2f}"] = {
            "n": int(len(sub)),
            "overlap_with_mask_fixed": float(sub["overlap_fixed_mask"].mean()),
            "overlap_across_masks_R94_method": float(sub["overlap_varying_mask"].mean()),
            "same_with_mask_fixed": float(sub["same_fixed_mask"].mean()),
            "hit_mean": float(sub["hit_fixed_mean"].mean()),
            "hit_sd": float(sub["hit_fixed_sd"].mean())}

    lev = res["by_coverage"]
    h243 = bool("1.00" in lev and lev["1.00"]["overlap_with_mask_fixed"] >= 0.80)
    if "1.00" in lev and "0.16" in lev:
        pm = paired(r[r.coverage == 1.00]["overlap_fixed_mask"], r[r.coverage == 0.16]["overlap_fixed_mask"], 21001)
        h244 = bool(pm and pm["ci95"][0] > 0)
    else:
        pm, h244 = None, False
    if "1.00" in lev:
        pv = paired(r[r.coverage == 1.00]["overlap_fixed_mask"],
                    r[r.coverage == 1.00]["overlap_varying_mask"], 21101)
        h245 = bool(pv and pv["ci95"][0] > 0)
    else:
        pv, h245 = None, False
    res["degradation_vs_coverage"] = pm
    res["R94_method_vs_this_method_at_full_coverage"] = pv
    res["decisions"] = {"H243_reproducible_at_full_coverage": h243,
                        "H244_low_coverage_reduces_reproducibility": h244,
                        "H245_R94_identity_statistic_was_confounded": h245}
    res["decisions"]["verdict"] = (
        "R94_identity_reading_must_be_retracted" if h245 else
        "R94_identity_reading_holds") if h243 or h244 else (
        "recommendations_not_reproducible_even_at_full_coverage")
    res["limits"] = [
        "Bootstrapping keys double-counts, so the marginal variance is understated.",
        "Only one mask per replicate drives the fixed-mask analysis.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r95/PROTOCOL_E090.md",
                "research/2026-10-27-agent-cell-identifiability-r95/e095_identity_confound.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E095_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E095_rows.csv", index=False)

    print("keys=%d units=%d" % (len(g), len(r)))
    for k, e in res["by_coverage"].items():
        print("  cov %s | overlap(fixed mask)=%.3f  overlap(varying masks, R94)=%.3f  same(fixed)=%.3f  hit=%.4f sd=%.4f" % (
            k, e["overlap_with_mask_fixed"], e["overlap_across_masks_R94_method"],
            e["same_with_mask_fixed"], e["hit_mean"], e["hit_sd"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
