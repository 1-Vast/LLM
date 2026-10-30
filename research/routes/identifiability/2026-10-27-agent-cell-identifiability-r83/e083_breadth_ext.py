"""E082: combination-level top-m curve - does the annotation model buy breadth that the
marginal strategy cannot?

Pre-registered in PROTOCOL_E079.md. For each predictor, rank DISTINCT combinations by their
mean score in the pool, take the top m, and measure the synergy rate over all keys of those m.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r83"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
MS = (1, 5, 10, 20, 50, 100, 200, 500)
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


def onehot(vals, levels):
    M = np.zeros((len(vals), len(levels)))
    for j, v in enumerate(levels):
        M[:, j] = (vals == v).astype(float)
    return M


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
        combo=("combo", "first"), ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("a", "b", "combo", "tissue", "ap", "lp"):
        d[c] = d[c].astype(str).fillna("NA")

    ap_lv = sorted(d["ap"].unique())
    lp_lv = sorted(d["lp"].unique())
    ti_lv = sorted(d["tissue"].unique())
    X = np.hstack([onehot(d["ap"].to_numpy(), ap_lv), onehot(d["lp"].to_numpy(), lp_lv),
                   onehot(d["tissue"].to_numpy(), ti_lv)])
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
        # ridge on the training rows
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        Am = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        w = np.linalg.solve(Am, Xs.T @ (ytr - ytr.mean()))
        # marginals
        grand = float(ytr.mean())
        dm = {}
        for i, yy in zip(tr, ytr):
            dm.setdefault(A[i], []).append(yy)
            dm.setdefault(B[i], []).append(yy)
        deff = {g: float(np.mean(v)) - grand for g, v in dm.items()}

        perm = rng.permutation(len(tr))
        half = len(tr) // 2
        for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
            p = tr[idxs]
            Xp = (X[p] - mu) / sd
            pred_ridge = ytr.mean() + Xp @ w
            pred_marg = np.array([0.5 * (deff.get(A[i], 0.0) + deff.get(B[i], 0.0)) + grand for i in p])
            combos_p = COMBO[p]
            uniq = pd.unique(combos_p)
            # mean score per combination inside this half
            df = pd.DataFrame({"combo": combos_p, "ridge": pred_ridge, "marg": pred_marg, "syn": syn[p]})
            agg = df.groupby("combo", as_index=False).agg(ridge=("ridge", "mean"), marg=("marg", "mean"),
                                                          rate=("syn", "mean"), n=("syn", "size"))
            if len(agg) < 60:
                continue
            for m in MS:
                if m > len(agg) // 2:
                    continue
                for name, col in (("marginal", "marg"), ("ridge", "ridge")):
                    top = agg.nlargest(m, col)
                    rows.append({"rep": rep, "part": part, "predictor": name, "m": m,
                                 "hit": float((top["rate"] * top["n"]).sum() / top["n"].sum()),
                                 "n_keys": int(top["n"].sum())})
                rnd = agg.sample(n=m, random_state=int(rng.integers(0, 10**6)))
                rows.append({"rep": rep, "part": part, "predictor": "random", "m": m,
                             "hit": float((rnd["rate"] * rnd["n"]).sum() / rnd["n"].sum()),
                             "n_keys": int(rnd["n"].sum())})

    r = pd.DataFrame(rows)
    ev = r[r.part == "eval"]
    res = {"kind": "combination_level_top_m_curve_extended",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"ms": list(MS), "repeats": REPEATS, "holdout": HOLDOUT, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "drugs": len(drugs), "n_eval_rows": int(len(ev))},
           "by_m": {}, "files": {}}

    for m in MS:
        sub = ev[ev.m == m]
        if not len(sub):
            continue
        piv = sub.pivot_table(index="rep", columns="predictor", values="hit")
        res["by_m"][str(m)] = {
            "n": int(len(piv)),
            "marginal": float(piv["marginal"].mean()), "ridge": float(piv["ridge"].mean()),
            "random": float(piv["random"].mean()),
            "ridge_minus_marginal": paired(piv["ridge"], piv["marginal"], 12001 + m),
            "marginal_minus_random": paired(piv["marginal"], piv["random"], 12101 + m),
            "ridge_minus_random": paired(piv["ridge"], piv["random"], 12201 + m),
            "mean_n_keys": float(sub[sub.predictor == "marginal"]["n_keys"].mean())}

    # first m at which marginal is no longer distinguishable from random
    first_fail = None
    for m in MS:
        e = res["by_m"].get(str(m))
        if not e:
            continue
        ci = e["marginal_minus_random"]["ci95"]
        if ci[0] <= 0:
            first_fail = m
            break
    h211 = first_fail is not None
    h212 = bool(first_fail is not None and first_fail <= 200)
    # at the failure point, is the marginal rate close to the base rate of the keys it covers?
    base_at_fail = None
    if first_fail is not None:
        e = res["by_m"][str(first_fail)]
        base_at_fail = e["marginal"] - e["marginal_minus_random"]["mean_diff"]
    h213 = bool(base_at_fail is not None and abs(res["by_m"][str(first_fail)]["marginal"] - base_at_fail) < 0.005)
    res["decisions"] = {"H211_failure_point_exists": h211,
                        "H212_capacity_at_most_200": h212,
                        "H213_failure_is_saturation_not_noise": h213,
                        "first_failing_m": first_fail,
                        "marginal_rate_at_failure": (res["by_m"][str(first_fail)]["marginal"] if first_fail else None),
                        "random_rate_at_failure": (res["by_m"][str(first_fail)]["random"] if first_fail else None)}
    res["decisions"]["verdict"] = ("capacity_limit_found" if h211 else
                                   "capacity_exceeds_a_quarter_of_the_space")
    res["limits"] = [
        "Combination-level aggregation deliberately removes within-combination cell differences.",
        "Only 2,025 combinations exist, so m=50 is already 2.5% of the space.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r82/PROTOCOL_E079.md",
                "research/2026-10-27-agent-cell-identifiability-r82/e082_breadth.py"):
        pp = ROOT / rel
        if pp.exists():
            res["files"][rel] = sha256(pp)
    (OUT / "E083_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E083_rows.csv", index=False)

    print("keys=%d drugs=%d" % (len(d), len(drugs)))
    for m in MS:
        e = res["by_m"].get(str(m))
        if not e:
            continue
        d1 = e["ridge_minus_marginal"]
        print("  m=%-3d keys~%.0f | marginal=%.4f ridge=%.4f random=%.4f | ridge-marg %+.4f [%+.4f,%+.4f]" % (
            m, e["mean_n_keys"], e["marginal"], e["ridge"], e["random"],
            d1["mean_diff"], d1["ci95"][0], d1["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
