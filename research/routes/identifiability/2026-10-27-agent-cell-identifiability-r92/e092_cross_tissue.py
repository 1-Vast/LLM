"""E092: does the final recommended algorithm (rank by drug marginals) transfer to an
UNSEEN TISSUE?

Three tissues; train the marginals on two and test on the third. Two variants: marginals from
the other tissues only (true transfer) and marginals that include the target tissue (ceiling).
Criterion is the dataset's boolean Synergy call, fixed by R91.

Pre-registered in PROTOCOL_E087.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r92"
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
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        tissue=("Tissue", "first"), syn=("syn", "mean"))
    g["syn"] = g["syn"] > 0.5
    for c in ("cell", "a", "b", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")
    A = g["a"].to_numpy()
    B = g["b"].to_numpy()
    T = g["tissue"].to_numpy()
    y = g["syn"].to_numpy(bool)
    tissues = sorted(set(T))

    rng = np.random.default_rng(SEED)
    rows = []
    for held in tissues:
        te = np.where(T == held)[0]
        tr = np.where(T != held)[0]
        if len(te) < 500 or len(tr) < 5000:
            continue
        # marginals from the other tissues only (true transfer)
        grand_t = float(y[tr].mean())
        dm_t = {}
        for i in tr:
            dm_t.setdefault(A[i], []).append(y[i])
            dm_t.setdefault(B[i], []).append(y[i])
        deff_t = {k: float(np.mean(v)) - grand_t for k, v in dm_t.items()}
        # marginals including the target tissue (ceiling)
        dm_c = {k: list(v) for k, v in dm_t.items()}
        for i in te:
            dm_c.setdefault(A[i], []).append(y[i])
            dm_c.setdefault(B[i], []).append(y[i])
        grand_c = float(y.mean())
        deff_c = {k: float(np.mean(v)) - grand_c for k, v in dm_c.items()}

        for _ in range(SUBSAMPLES):
            sub = rng.choice(te, size=min(2000, len(te)), replace=False)
            sc_t = np.array([0.5 * (deff_t.get(A[i], np.nan) + deff_t.get(B[i], np.nan)) for i in sub])
            covered = np.isfinite(sc_t)
            sc_c = np.array([0.5 * (deff_c.get(A[i], 0.0) + deff_c.get(B[i], 0.0)) for i in sub])
            if covered.sum() < 2 * K:
                continue
            idx_cov = np.where(covered)[0]
            hit_t = float(y[sub][idx_cov][np.argsort(-sc_t[idx_cov])[:K]].mean())
            hit_c = float(y[sub][np.argsort(-sc_c)[:K]].mean())
            hit_r = float(y[sub][rng.choice(len(sub), size=K, replace=False)].mean())
            rows.append({"held_tissue": held, "n_test": int(len(sub)),
                         "transfer": hit_t, "ceiling": hit_c, "random": hit_r,
                         "base": float(y[sub].mean()),
                         "coverage": float(covered.mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "cross_tissue_transfer_of_the_final_algorithm",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "subsamples": SUBSAMPLES, "n_boot": N_BOOT, "seed": SEED,
                        "criterion": "dataset boolean Synergy (fixed by R91)"},
           "audit": {"units": int(len(r)), "tissues": tissues},
           "by_tissue": {}, "files": {}}

    for held in tissues:
        sub = r[r.held_tissue == held]
        if len(sub) < 5:
            continue
        res["by_tissue"][held] = {
            "n": int(len(sub)), "base": float(sub["base"].mean()),
            "random": float(sub["random"].mean()),
            "transfer": float(sub["transfer"].mean()),
            "ceiling": float(sub["ceiling"].mean()),
            "coverage": float(sub["coverage"].mean()),
            "transfer_minus_random": paired(sub["transfer"], sub["random"], 18001 + len(held)),
            "ceiling_minus_transfer": paired(sub["ceiling"], sub["transfer"], 18101 + len(held))}

    trans_ok = []
    for held, e in res["by_tissue"].items():
        trans_ok.append(e["transfer_minus_random"]["ci95"][0] > 0)
    ceil_ok = [e["ceiling_minus_transfer"]["ci95"][0] > 0 for e in res["by_tissue"].values()]
    h234 = bool(trans_ok) and all(trans_ok)
    h235 = bool(ceil_ok) and any(ceil_ok)
    h236 = bool(trans_ok) and not all(trans_ok)
    res["decisions"] = {"H234_transfers_in_every_tissue": h234,
                        "H235_transfer_costs_something": h235,
                        "H236_fails_somewhere": h236}
    res["decisions"]["verdict"] = (
        "algorithm_transfers_across_tissues" if h234 and not h235 else
        "algorithm_transfers_but_at_a_cost" if h234 and h235 else
        "cross_tissue_is_a_failure_condition")
    res["limits"] = [
        "Only three tissues, so leave-one-tissue-out gives three folds; within-fold subsampling makes units non-independent and the CIs optimistic.",
        "Drugs absent from the training tissues fall back to no information, which is a genuine transfer difficulty and is reported as coverage.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r92/PROTOCOL_E087.md",
                "research/2026-10-27-agent-cell-identifiability-r92/e092_cross_tissue.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E092_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E092_rows.csv", index=False)

    print("units=%d tissues=%s" % (len(r), tissues))
    for held, e in res["by_tissue"].items():
        a = e["transfer_minus_random"]; b = e["ceiling_minus_transfer"]
        print("  [%-9s] base=%.4f rand=%.4f transfer=%.4f ceiling=%.4f cov=%.2f" % (
            held, e["base"], e["random"], e["transfer"], e["ceiling"], e["coverage"]))
        print("      transfer-rand %+.4f [%+.4f,%+.4f] | ceil-transfer %+.4f [%+.4f,%+.4f]" % (
            a["mean_diff"], a["ci95"][0], a["ci95"][1], b["mean_diff"], b["ci95"][0], b["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
