"""E097: is C65's transfer cost specific to the target tissue, or just more data?

C65 compared "marginals from the other tissues" against "marginals from the other tissues PLUS
the target tissue". The ceiling arm had strictly more keys as well, so the gain may be a volume
effect. This adds a volume-matched control: the other tissues only, bootstrap-resampled to the
same key count as the ceiling.

Pre-registered in PROTOCOL_E092.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r97"
K = 20
SUBSAMPLES = 40
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "Synergy"]


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
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        tissue=("Tissue", "first"), syn=("syn", "mean"))
    g["syn"] = g["syn"] > 0.5
    g["a"] = g["a"].astype(str)
    g["b"] = g["b"].astype(str)
    g["tissue"] = g["tissue"].astype(str)
    A = g["a"].to_numpy()
    B = g["b"].to_numpy()
    T = g["tissue"].to_numpy()
    y = g["syn"].to_numpy(bool)
    tissues = sorted(set(T))

    def marginals(idx):
        grand = float(y[idx].mean())
        dm = {}
        for i in idx:
            dm.setdefault(A[i], []).append(y[i])
            dm.setdefault(B[i], []).append(y[i])
        return {k: float(np.mean(v)) - grand for k, v in dm.items()}, grand

    rng = np.random.default_rng(SEED)
    rows = []
    for held in tissues:
        te = np.where(T == held)[0]
        tr = np.where(T != held)[0]
        if len(te) < 500 or len(tr) < 5000:
            continue
        n_ceiling = len(tr) + len(te)
        for _ in range(SUBSAMPLES):
            sub = rng.choice(te, size=min(2000, len(te)), replace=False)
            # transfer
            deff_t, gr_t = marginals(tr)
            sc_t = np.array([0.5 * (deff_t.get(A[i], np.nan) + deff_t.get(B[i], np.nan)) for i in sub])
            cov = np.isfinite(sc_t)
            if cov.sum() < 2 * K:
                continue
            ic = np.where(cov)[0]
            hit_t = float(y[sub][ic][np.argsort(-sc_t[ic])[:K]].mean())
            # ceiling: other tissues + target tissue
            deff_c, gr_c = marginals(np.concatenate([tr, te]))
            sc_c = np.array([0.5 * (deff_c.get(A[i], 0.0) + deff_c.get(B[i], 0.0)) for i in sub])
            hit_c = float(y[sub][np.argsort(-sc_c)[:K]].mean())
            # volume matched: other tissues only, bootstrap-resampled to n_ceiling keys
            boot = rng.choice(tr, size=n_ceiling, replace=True)
            deff_v, gr_v = marginals(boot)
            sc_v = np.array([0.5 * (deff_v.get(A[i], 0.0) + deff_v.get(B[i], 0.0)) for i in sub])
            hit_v = float(y[sub][np.argsort(-sc_v)[:K]].mean())
            hit_r = float(y[sub][rng.choice(len(sub), size=K, replace=False)].mean())
            rows.append({"held": held, "transfer": hit_t, "ceiling": hit_c,
                         "volume_matched": hit_v, "random": hit_r})

    r = pd.DataFrame(rows)
    res = {"kind": "is_the_transfer_cost_target_tissue_specific",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "subsamples": SUBSAMPLES, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(len(r)), "tissues": tissues},
           "by_tissue": {}, "files": {}}

    for held in tissues:
        sub = r[r.held == held]
        if len(sub) < 5:
            continue
        res["by_tissue"][held] = {
            "n": int(len(sub)),
            "transfer": float(sub["transfer"].mean()),
            "ceiling": float(sub["ceiling"].mean()),
            "volume_matched": float(sub["volume_matched"].mean()),
            "random": float(sub["random"].mean()),
            "ceiling_minus_transfer": paired(sub["ceiling"], sub["transfer"], 23001 + len(held)),
            "ceiling_minus_volume_matched": paired(sub["ceiling"], sub["volume_matched"], 23101 + len(held)),
            "volume_matched_minus_transfer": paired(sub["volume_matched"], sub["transfer"], 23201 + len(held))}

    ok249 = [e["ceiling_minus_volume_matched"]["ci95"][0] > 0 for e in res["by_tissue"].values()]
    sig_cv = [e["ceiling_minus_transfer"]["ci95"][0] > 0 for e in res["by_tissue"].values()]
    h249 = bool(ok249) and all(ok249)
    h250 = bool(sig_cv) and any(sig_cv) and not any(ok249)
    h251 = all(e["volume_matched_minus_transfer"]["mean_diff"] >= -0.005 for e in res["by_tissue"].values())
    res["decisions"] = {"H249_gain_is_target_specific": h249,
                        "H250_gain_is_just_volume": h250,
                        "H251_more_data_never_hurts": bool(h251)}
    res["decisions"]["verdict"] = (
        "transfer_cost_is_target_tissue_specific" if h249 else
        "transfer_cost_is_a_volume_effect" if h250 else
        "mixed_across_tissues")
    res["limits"] = [
        "Bootstrap resampling double-counts, so the volume-matched arm is if anything optimistic, which makes H249 a conservative test.",
        "Only three tissues.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r97/PROTOCOL_E092.md",
                "research/2026-10-27-agent-cell-identifiability-r97/e097_volume_control.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E097_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E097_rows.csv", index=False)

    print("units=%d" % len(r))
    for held, e in res["by_tissue"].items():
        a = e["ceiling_minus_transfer"]; b = e["ceiling_minus_volume_matched"]
        print("  [%-9s] transfer %.4f  volume %.4f  ceiling %.4f  rand %.4f" % (
            held, e["transfer"], e["volume_matched"], e["ceiling"], e["random"]))
        print("      ceil-transfer %+.4f [%+.4f,%+.4f] | ceil-VOLUME %+.4f [%+.4f,%+.4f]" % (
            a["mean_diff"], a["ci95"][0], a["ci95"][1], b["mean_diff"], b["ci95"][0], b["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
