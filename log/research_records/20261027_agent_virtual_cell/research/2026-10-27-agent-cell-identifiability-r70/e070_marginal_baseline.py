"""E070: is the pathway-annotated ridge actually better than a trivial marginal-mean baseline?

Two settings (all drugs seen / some drugs unseen) x three predictors (ridge, marginal, random).
Pre-registered in PROTOCOL_E067.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r70"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
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
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("a", "b", "tissue", "ap", "lp"):
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
    drugs = sorted(set(A) | set(B))

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        rng.shuffle(drugs)
        held = set(drugs[: max(3, int(round(HOLDOUT * len(drugs))))])
        drug_seen = np.array([(x not in held) and (z not in held) for x, z in zip(A, B)])
        any_unseen = ~drug_seen

        tr = np.where(drug_seen)[0]
        if len(tr) < 30000:
            continue
        # --- ridge
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        Am = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        w = np.linalg.solve(Am, Xs.T @ (ytr - ytr.mean()))

        # --- marginal means from the SAME training rows (no extra information)
        marg = {}
        for row_i, yy in zip(tr, ytr):
            for g in (A[row_i], B[row_i]):
                marg.setdefault(g, []).append(yy)
        marg_mean = {g: float(np.mean(v)) for g, v in marg.items()}
        fill = float(np.median(ytr))

        def marginal_pred(idx):
            out = np.empty(len(idx))
            for j, i in enumerate(idx):
                m1 = marg_mean.get(A[i], fill)
                m2 = marg_mean.get(B[i], fill)
                out[j] = 0.5 * (m1 + m2)
            return out

        for setting, mask in (("seen", drug_seen), ("unseen", any_unseen)):
            pool = np.where(mask)[0]
            if len(pool) < 400:
                continue
            perm = rng.permutation(len(pool))
            half = len(pool) // 2
            for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                p = pool[idxs]
                Xp = (X[p] - mu) / sd
                pred_ridge = ytr.mean() + Xp @ w
                pred_marg = marginal_pred(p)
                r_idx = rng.choice(len(p), size=K, replace=False)
                hits = {}
                for name, sc in (("ridge", pred_ridge), ("marginal", pred_marg)):
                    hits[name] = float(syn[p][np.argsort(-sc)[:K]].mean())
                hits["random"] = float(syn[p][r_idx].mean())
                rows.append({"rep": rep, "setting": setting, "part": part, "k": K,
                             **{f"hit_{k2}": v for k2, v in hits.items()},
                             "base": float(syn[p].mean()), "n_pool": int(len(p))})

    r = pd.DataFrame(rows)
    res = {"kind": "annotation_model_versus_marginal_mean_baseline",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "k": K, "repeats": REPEATS, "holdout": HOLDOUT,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "drugs": len(drugs),
                     "reps_used": int(r["rep"].nunique()) if len(r) else 0},
           "by_setting": {}, "files": {}}

    for setting in ("seen", "unseen"):
        sub = r[r.setting == setting]
        if not len(sub):
            continue
        ev = sub[sub.part == "eval"].set_index("rep")
        res["by_setting"][setting] = {
            "n_eval": int(len(ev)),
            "base": float(ev["base"].mean()),
            "ridge": float(ev["hit_ridge"].mean()),
            "marginal": float(ev["hit_marginal"].mean()),
            "random": float(ev["hit_random"].mean()),
            "ridge_minus_marginal": paired(ev["hit_ridge"], ev["hit_marginal"], 6001 + len(setting)),
            "ridge_minus_random": paired(ev["hit_ridge"], ev["hit_random"], 6101 + len(setting)),
            "marginal_minus_random": paired(ev["hit_marginal"], ev["hit_random"], 6201 + len(setting)),
            "n_pool_median": float(ev["n_pool"].median())}

    seen = res["by_setting"].get("seen", {})
    unseen = res["by_setting"].get("unseen", {})
    h176 = bool(seen and seen["ridge_minus_marginal"]["ci95"][0] <= 0 <= seen["ridge_minus_marginal"]["ci95"][1])
    h177 = bool(unseen and unseen["ridge_minus_marginal"]["ci95"][0] > 0
                and unseen["ridge_minus_random"]["ci95"][0] > 0)
    h178 = bool(seen and unseen
                and seen["ridge_minus_random"]["ci95"][0] > 0 and seen["marginal_minus_random"]["ci95"][0] > 0
                and unseen["ridge_minus_random"]["ci95"][0] > 0)
    res["decisions"] = {"H176_marginal_matches_ridge_on_seen": h176,
                        "H177_ridge_unique_on_unseen": h177,
                        "H178_both_beat_random": h178}
    res["decisions"]["verdict"] = (
        "annotation_model_value_is_exactly_the_unseen_drug_case" if h176 and h177 else
        "annotation_model_adds_value_even_on_seen_drugs" if not h176 else
        "marginal_baseline_dominates_somewhere")
    res["limits"] = [
        "The marginal-mean baseline is the one I constructed here, not the best baseline in the literature.",
        "Unseen drugs are filled with the training median, which is equivalent to 'rank in the middle when unknown'.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r70/PROTOCOL_E067.md",
                "research/2026-10-27-agent-cell-identifiability-r70/e070_marginal_baseline.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E070_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E070_rows.csv", index=False)

    print("keys=%d drugs=%d reps=%d" % (len(d), len(drugs), res["audit"]["reps_used"]))
    for setting in ("seen", "unseen"):
        e = res["by_setting"].get(setting)
        if not e:
            continue
        print("  %-7s base=%.4f ridge=%.4f marginal=%.4f random=%.4f | pool~%.0f" % (
            setting, e["base"], e["ridge"], e["marginal"], e["random"], e["n_pool_median"]))
        for name in ("ridge_minus_marginal", "ridge_minus_random", "marginal_minus_random"):
            c = e[name]
            print("      %-22s %+.4f [%+.4f,%+.4f]" % (name, c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
