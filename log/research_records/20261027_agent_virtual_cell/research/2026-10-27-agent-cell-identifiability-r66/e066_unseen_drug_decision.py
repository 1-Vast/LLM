"""E066: does a WEAK prediction (rho about 0.20 on unseen drugs) still have decision value?

Trains only on combinations whose two drugs are both seen, then asks whether ranking by
prediction beats random on pools that contain at least one unseen drug.
Pre-registered in PROTOCOL_E064.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r66"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
KS = (20, 50)
REPEATS = 40
SEARCH = list(range(0, 20))
EVAL = list(range(20, 40))
N_BOOT = 2000
SEED = 20261027
HOLDOUT_FRAC = 0.20
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
    a = d["ANCHOR_NAME"].astype(str)
    b = d["LIBRARY_NAME"].astype(str)
    d["combo"] = a + " + " + b
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
    meta = []
    for rep in range(REPEATS):
        rng.shuffle(drugs)
        n_hold = max(3, int(round(HOLDOUT_FRAC * len(drugs))))
        held = set(drugs[:n_hold])
        seen_combo = np.array([(x not in held) and (y2 not in held) for x, y2 in zip(A, B)])
        any_unseen = np.array([(x in held) or (y2 in held) for x, y2 in zip(A, B)])
        both_unseen = np.array([(x in held) and (y2 in held) for x, y2 in zip(A, B)])
        tr = np.where(seen_combo)[0]
        if len(tr) < 20000:
            continue
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        A_mat = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        Ainv = np.linalg.inv(A_mat)
        w = Ainv @ Xs.T @ (ytr - ytr.mean())

        for label, mask in (("any_unseen", any_unseen), ("both_unseen", both_unseen), ("seen_only", seen_combo)):
            pool = np.where(mask)[0]
            # split the pool into search/eval halves by key so both halves stay independent
            if len(pool) < 400:
                meta.append({"rep": rep, "pool": label, "n": int(len(pool)), "skipped": True})
                continue
            perm = rng.permutation(len(pool))
            half = len(pool) // 2
            for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                p = pool[idxs]
                Xp = (X[p] - mu) / sd
                pred = ytr.mean() + Xp @ w
                rp = pd.Series(pred).rank(pct=True).to_numpy()
                for k in KS:
                    if k >= len(p) // 5:
                        continue
                    e_hit = float(syn[p][np.argsort(-rp)[:k]].mean())
                    r_hit = float(syn[p][rng.choice(len(p), size=k, replace=False)].mean())
                    rows.append({"rep": rep, "pool": label, "part": part, "k": k,
                                 "exploit": e_hit, "random": r_hit,
                                 "base_rate": float(syn[p].mean()), "n_pool": int(len(p))})
            meta.append({"rep": rep, "pool": label, "n": int(len(pool)), "n_held_drugs": n_hold})

    r = pd.DataFrame(rows)
    res = {"kind": "decision_value_of_a_weak_unseen_drug_signal",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "ks": list(KS), "repeats": REPEATS,
                        "holdout_drug_fraction": HOLDOUT_FRAC, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "drugs": len(drugs),
                     "pool_sizes": {} , "reps_used": int(r["rep"].nunique()) if len(r) else 0},
           "by_pool": {}, "files": {}}

    for label in ("seen_only", "any_unseen", "both_unseen"):
        ent = {}
        for k in KS:
            sub = r[(r["pool"] == label) & (r.k == k)]
            if not len(sub):
                continue
            ev = sub[sub.part == "eval"].set_index("rep")
            sr = sub[sub.part == "search"].set_index("rep")
            ent[str(k)] = {
                "n_eval": int(len(ev)),
                "exploit": float(ev["exploit"].mean()), "random": float(ev["random"].mean()),
                "base_rate": float(ev["base_rate"].mean()),
                "gain_pp": float(ev["exploit"].mean() - ev["random"].mean()),
                "paired_all": paired(ev["exploit"], ev["random"], 3001 + k + len(label)),
                "paired_eval": paired(ev["exploit"], ev["random"], 3101 + k + len(label))}
            if len(sr):
                ent[str(k)]["search_gain_pp"] = float((sr["exploit"] - sr["random"]).mean())
            ent[str(k)]["n_pool_median"] = float(ev["n_pool"].median())
        if ent:
            res["by_pool"][label] = ent

    def gain(label, k):
        return res["by_pool"].get(label, {}).get(str(k), {}).get("gain_pp")

    au20 = gain("any_unseen", 20)
    seen20 = gain("seen_only", 20)
    bu20 = gain("both_unseen", 20)
    ci_au = res["by_pool"].get("any_unseen", {}).get("20", {}).get("paired_all")
    ci_bu = res["by_pool"].get("both_unseen", {}).get("20", {}).get("paired_all")
    h165 = bool(ci_au and ci_au["ci95"][0] > 0)
    h166 = bool(au20 is not None and seen20 is not None and au20 < seen20)
    h167 = bool(ci_bu and ci_bu["ci95"][0] > 0)
    res["decisions"] = {"H165_unseen_pool_exploit_beats_random": h165,
                        "H166_gain_smaller_than_seen": h166,
                        "H167_both_unseen_holds": h167}
    res["decisions"]["verdict"] = ("weak_signal_still_has_decision_value" if h165
                                   else "weak_signal_has_no_decision_value")
    res["limits"] = [
        "Drug-level holdout; cells still overlap between training and pool, so this is unseen-drug, not unseen-cell.",
        "Pool size falls as drugs are held out; the k values are skipped when the pool is too small.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r66/PROTOCOL_E064.md",
                "research/2026-10-27-agent-cell-identifiability-r66/e066_unseen_drug_decision.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E066_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E066_rows.csv", index=False)

    print("keys=%d drugs=%d reps=%d" % (len(d), len(drugs), res["audit"]["reps_used"]))
    for label in ("seen_only", "any_unseen", "both_unseen"):
        if label not in res["by_pool"]:
            print("  %-13s (no data)" % label)
            continue
        for k in KS:
            e = res["by_pool"][label].get(str(k))
            if not e:
                continue
            ci = e["paired_all"]
            print("  %-13s k=%-3d base=%.4f exploit=%.4f random=%.4f | gain %+.4f [%+.4f,%+.4f] n_eval=%d pool~%.0f" % (
                label, k, e["base_rate"], e["exploit"], e["random"], e["gain_pp"],
                ci["ci95"][0], ci["ci95"][1], e["n_eval"], e["n_pool_median"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
