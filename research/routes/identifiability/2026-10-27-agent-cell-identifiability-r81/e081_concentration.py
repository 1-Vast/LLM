"""E081: when you rank by a per-combination constant (drug marginals), does the top-k
consist of k different discoveries, or of one combination repeated across cells?

Pre-registered in PROTOCOL_E078.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r81"
METRIC = "SYNERGY_DELTA_AUC"
K = 20
REPEATS = 40
HOLDOUT = 0.20
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
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        combo=("combo", "first"), synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    y = d.synergy.to_numpy(float)
    syn = d.syn.to_numpy(bool)
    A = d["a"].to_numpy()
    B = d["b"].to_numpy()
    COMBO = d["combo"].to_numpy()
    drugs = sorted(set(A) | set(B))

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        rng.shuffle(drugs)
        held = set(drugs[: max(3, int(round(HOLDOUT * len(drugs))))])
        drug_seen = np.array([(x not in held) and (z not in held) for x, z in zip(A, B)])
        tr = np.where(drug_seen)[0]
        if len(tr) < 30000:
            continue
        grand = float(y[tr].mean())
        dm = {}
        for i, yy in zip(tr, y[tr]):
            dm.setdefault(A[i], []).append(yy)
            dm.setdefault(B[i], []).append(yy)
        deff = {g: float(np.mean(v)) - grand for g, v in dm.items()}

        perm = rng.permutation(len(tr))
        half = len(tr) // 2
        for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
            p = tr[idxs]
            marg = np.array([0.5 * (deff.get(A[i], 0.0) + deff.get(B[i], 0.0)) + grand for i in p])
            order = np.argsort(-marg, kind="stable")   # stable: ties keep pool order
            top = order[:K]
            top_combos = COMBO[p[top]]
            uniq, counts = np.unique(top_combos, return_counts=True)
            # de-duplicated hit rate: average the synergy flag once per distinct combo in the top-k
            dedup = float(np.mean([syn[p[top]][top_combos == c].mean() for c in uniq]))
            rand_top = rng.choice(len(p), size=K, replace=False)
            r_combos = COMBO[p[rand_top]]
            rows.append({
                "rep": rep, "part": part,
                "raw_hit": float(syn[p[top]].mean()),
                "dedup_hit": dedup,
                "n_combos": int(len(uniq)),
                "n_drugs": int(len(set(A[p[top]]) | set(B[p[top]]))),
                "max_single_combo": int(counts.max()),
                "rand_n_combos": int(len(np.unique(r_combos))),
                "base": float(syn[p].mean()),
                "n_pool": int(len(p)),
            })

    r = pd.DataFrame(rows)
    ev = r[r.part == "eval"].set_index("rep")
    res = {"kind": "does_marginal_topk_select_distinct_discoveries",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"k": K, "repeats": REPEATS, "holdout": HOLDOUT, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "drugs": len(drugs), "n_eval": int(len(ev))},
           "summary": {}, "files": {}}

    res["summary"] = {
        "n_combos_median": float(ev["n_combos"].median()),
        "n_combos_mean": float(ev["n_combos"].mean()),
        "n_drugs_median": float(ev["n_drugs"].median()),
        "max_single_combo_median": float(ev["max_single_combo"].median()),
        "max_single_combo_mean_frac": float((ev["max_single_combo"] / K).mean()),
        "rand_n_combos_median": float(ev["rand_n_combos"].median()),
        "raw_hit": float(ev["raw_hit"].mean()),
        "dedup_hit": float(ev["dedup_hit"].mean()),
        "raw_minus_dedup": paired(ev["raw_hit"], ev["dedup_hit"], 11001),
        "base": float(ev["base"].mean()),
        "n_pool_median": float(ev["n_pool"].median()),
    }
    s = res["summary"]
    h205 = bool(s["n_combos_median"] <= 5)
    h206 = bool(s["raw_minus_dedup"]["mean_diff"] > 0.02)
    h207 = bool(s["rand_n_combos_median"] >= 15)
    res["decisions"] = {"H205_topk_is_concentrated": h205,
                        "H206_dedup_reduces_value": h206,
                        "H207_random_is_not_concentrated": h207}
    res["decisions"]["verdict"] = (
        "the_decision_value_is_a_few_combos_counted_many_times" if h205 and h206
        else "concentration_present_but_value_holds" if h205
        else "topk_is_diverse")
    res["limits"] = [
        "The pool is key-level (same combination across cells), which is exactly what produces the concentration.",
        "The de-duplicated hit rate is a combination-level quantity and is not directly comparable with the key-level rate.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r81/PROTOCOL_E078.md",
                "research/2026-10-27-agent-cell-identifiability-r81/e081_concentration.py"):
        pp = ROOT / rel
        if pp.exists():
            res["files"][rel] = sha256(pp)
    (OUT / "E081_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E081_rows.csv", index=False)

    print("keys=%d drugs=%d n_eval=%d pool~%.0f" % (len(d), len(drugs), len(ev), s["n_pool_median"]))
    print("  top-20 distinct combos: median %.1f (mean %.1f) | distinct drugs median %.1f" % (
        s["n_combos_median"], s["n_combos_mean"], s["n_drugs_median"]))
    print("  largest single combo in top-20: median %.1f (%.1f%% of k)" % (
        s["max_single_combo_median"], 100 * s["max_single_combo_mean_frac"]))
    print("  random top-20 distinct combos: median %.1f" % s["rand_n_combos_median"])
    print("  raw hit %.4f vs dedup hit %.4f | diff %+.4f [%+.4f,%+.4f]" % (
        s["raw_hit"], s["dedup_hit"], s["raw_minus_dedup"]["mean_diff"],
        s["raw_minus_dedup"]["ci95"][0], s["raw_minus_dedup"]["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
