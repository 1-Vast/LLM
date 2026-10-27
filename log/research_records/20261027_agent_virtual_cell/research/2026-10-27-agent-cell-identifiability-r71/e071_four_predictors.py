"""E071: four predictors on the same table - annotation ridge, drug marginals, additive
(drug + cell marginals), and combo lookup (memory).

Pre-registered in PROTOCOL_E068.md. All four share the same training rows and the same
information; only the scoring rule differs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r71"
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
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"),
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), combo=("combo", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("cell", "a", "b", "combo", "tissue", "ap", "lp"):
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
    CELL = d["cell"].to_numpy()
    COMBO = d["combo"].to_numpy()
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

        # ridge
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        Am = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        w = np.linalg.solve(Am, Xs.T @ (ytr - ytr.mean()))

        # marginals
        grand = float(ytr.mean())
        dm, cm, combo_m = {}, {}, {}
        for i, yy in zip(tr, ytr):
            dm.setdefault(A[i], []).append(yy)
            dm.setdefault(B[i], []).append(yy)
            cm.setdefault(CELL[i], []).append(yy)
            combo_m.setdefault(COMBO[i], []).append(yy)
        drug_eff = {g: float(np.mean(v)) - grand for g, v in dm.items()}
        cell_eff = {c: float(np.mean(v)) - grand for c, v in cm.items()}
        combo_mean = {c: float(np.mean(v)) for c, v in combo_m.items()}

        def scores(idx):
            out = {}
            Xp = (X[idx] - mu) / sd
            out["ridge"] = ytr.mean() + Xp @ w
            dm_s = np.array([0.5 * (drug_eff.get(A[i], 0.0) + drug_eff.get(B[i], 0.0)) + grand for i in idx])
            add_s = np.array([drug_eff.get(A[i], 0.0) + drug_eff.get(B[i], 0.0) + cell_eff.get(CELL[i], 0.0) + grand
                              for i in idx])
            out["drug_marg"] = dm_s
            out["additive"] = add_s
            out["combo_marg"] = np.array([combo_mean.get(COMBO[i], add_s[j]) for j, i in enumerate(idx)])
            return out

        for setting, mask in (("seen", drug_seen), ("unseen", any_unseen)):
            pool = np.where(mask)[0]
            if len(pool) < 400:
                continue
            perm = rng.permutation(len(pool))
            half = len(pool) // 2
            for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                p = pool[idxs]
                sc = scores(p)
                rand_idx = rng.choice(len(p), size=K, replace=False)
                row = {"rep": rep, "setting": setting, "part": part,
                       "hit_random": float(syn[p][rand_idx].mean()),
                       "base": float(syn[p].mean()), "n_pool": int(len(p)),
                       "combo_seen_frac": float(np.mean([COMBO[i] in combo_mean for i in p]))}
                for name, scv in sc.items():
                    row[f"hit_{name}"] = float(syn[p][np.argsort(-scv)[:K]].mean())
                rows.append(row)

    r = pd.DataFrame(rows)
    preds = ["ridge", "drug_marg", "additive", "combo_marg"]
    res = {"kind": "four_predictors_same_information",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "k": K, "repeats": REPEATS, "holdout": HOLDOUT,
                        "n_boot": N_BOOT, "seed": SEED, "predictors": preds},
           "audit": {"keys": int(len(d)), "drugs": len(drugs),
                     "reps_used": int(r["rep"].nunique()) if len(r) else 0},
           "by_setting": {}, "files": {}}

    for setting in ("seen", "unseen"):
        sub = r[(r.setting == setting) & (r.part == "eval")]
        if not len(sub):
            continue
        ev = sub.set_index("rep")
        ent = {"n_eval": int(len(ev)), "base": float(ev["base"].mean()),
               "random": float(ev["hit_random"].mean()),
               "combo_seen_frac": float(ev["combo_seen_frac"].mean()),
               "n_pool_median": float(ev["n_pool"].median())}
        for p in preds:
            ent[p] = float(ev[f"hit_{p}"].mean())
        for a_, b_ in (("ridge", "drug_marg"), ("ridge", "additive"), ("ridge", "combo_marg"),
                       ("additive", "drug_marg"), ("combo_marg", "additive")):
            ent[f"{a_}_minus_{b_}"] = paired(ev[f"hit_{a_}"], ev[f"hit_{b_}"], 7001 + len(setting) + len(a_) + len(b_))
        for p in preds:
            ent[f"{p}_minus_random"] = paired(ev[f"hit_{p}"], ev["hit_random"], 7501 + len(setting) + len(p))
        res["by_setting"][setting] = ent

    seen = res["by_setting"].get("seen", {})
    unseen = res["by_setting"].get("unseen", {})
    # the pair is stored as "ridge_minus_combo_marg"; H179 asks whether the MEMORY baseline
    # fails to lose to the model, i.e. (ridge - combo_marg) < 0 or its CI contains 0
    rm = seen.get("ridge_minus_combo_marg") if seen else None
    h179 = bool(rm and (rm["mean_diff"] < 0 or (rm["ci95"][0] <= 0 <= rm["ci95"][1])))
    h180 = bool(seen and seen["additive_minus_drug_marg"]["ci95"][0] > 0)
    h181 = bool(unseen and unseen["ridge_minus_additive"]["ci95"][0] > 0)
    res["decisions"] = {"H179_memory_matches_or_beats_model": h179,
                        "H180_cell_marginals_help": h180,
                        "H181_model_wins_only_where_combo_unseen": h181}
    res["decisions"]["verdict"] = (
        "model_has_no_identified_advantage" if not h181 else
        "model_advantage_confined_to_unseen_combinations")
    res["limits"] = [
        "All four predictors see exactly the same training rows, so the comparison is about the scoring rule only.",
        "combo_marg necessarily falls back to additive on unseen drugs, so its edge is only readable on the seen setting.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r71/PROTOCOL_E068.md",
                "research/2026-10-27-agent-cell-identifiability-r71/e071_four_predictors.py"):
        pp = ROOT / rel
        if pp.exists():
            res["files"][rel] = sha256(pp)
    (OUT / "E071_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E071_rows.csv", index=False)

    print("keys=%d drugs=%d reps=%d" % (len(d), len(drugs), res["audit"]["reps_used"]))
    for setting in ("seen", "unseen"):
        e = res["by_setting"].get(setting)
        if not e:
            continue
        print("  [%s] base=%.4f random=%.4f combo_seen=%.2f pool~%.0f" % (
            setting, e["base"], e["random"], e["combo_seen_frac"], e["n_pool_median"]))
        for p in preds:
            print("      %-11s %.4f" % (p, e[p]))
        for kk in ("ridge_minus_drug_marg", "ridge_minus_additive", "ridge_minus_combo_marg",
                   "additive_minus_drug_marg", "combo_marg_minus_additive"):
            c = e[kk]
            print("      %-26s %+.4f [%+.4f,%+.4f]" % (kk, c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
