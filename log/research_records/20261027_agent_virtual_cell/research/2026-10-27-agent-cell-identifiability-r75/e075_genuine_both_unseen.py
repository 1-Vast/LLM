"""E075: verify the pool labels by data, then run the one remaining head-to-head on the
genuine both-drugs-unseen pool, where the marginal baseline is necessarily constant.

Pre-registered in PROTOCOL_E072.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r75"
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
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("cell", "a", "b", "tissue", "ap", "lp"):
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
        a_u = np.array([x in held for x in A])
        b_u = np.array([z in held for z in B])
        both_unseen = a_u & b_u
        any_unseen = a_u | b_u
        seen = ~any_unseen
        tr = np.where(seen)[0]
        if len(tr) < 30000:
            continue
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        Am = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        w = np.linalg.solve(Am, Xs.T @ (ytr - ytr.mean()))
        grand = float(ytr.mean())
        dm = {}
        for i, yy in zip(tr, ytr):
            dm.setdefault(A[i], []).append(yy)
            dm.setdefault(B[i], []).append(yy)
        drug_eff = {g: float(np.mean(v)) - grand for g, v in dm.items()}

        for label, mask in (("seen", seen), ("any_unseen", any_unseen), ("both_unseen", both_unseen)):
            pool = np.where(mask)[0]
            if len(pool) < 400:
                rows.append({"rep": rep, "pool": label, "skipped": True, "n": int(len(pool)),
                             "frac_both": float(both_unseen[pool].mean()) if len(pool) else None})
                continue
            perm = rng.permutation(len(pool))
            half = len(pool) // 2
            for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                p = pool[idxs]
                if len(p) < 2 * K:
                    continue
                Xp = (X[p] - mu) / sd
                pred = ytr.mean() + Xp @ w
                marg = np.array([0.5 * (drug_eff.get(A[i], 0.0) + drug_eff.get(B[i], 0.0)) + grand for i in p])
                rows.append({"rep": rep, "pool": label, "part": part,
                             "hit_ridge": float(syn[p][np.argsort(-pred)[:K]].mean()),
                             "hit_marginal": float(syn[p][np.argsort(-marg)[:K]].mean()),
                             "hit_random": float(syn[p][rng.choice(len(p), size=K, replace=False)].mean()),
                             "base": float(syn[p].mean()), "n_pool": int(len(p)),
                             "frac_both": float(both_unseen[p].mean())})

    r = pd.DataFrame(rows)
    ok = r[~r.get("skipped", pd.Series([False] * len(r)))].copy()
    res = {"kind": "label_verification_and_genuine_both_unseen_head_to_head",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "k": K, "repeats": REPEATS, "holdout": HOLDOUT,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "drugs": len(drugs), "reps_used": int(ok["rep"].nunique()) if len(ok) else 0},
           "by_pool": {}, "files": {}}

    for label in ("seen", "any_unseen", "both_unseen"):
        sub = ok[ok["pool"] == label]
        if not len(sub):
            continue
        ev = sub[sub.part == "eval"].set_index("rep")
        sr = sub[sub.part == "search"].set_index("rep")
        res["by_pool"][label] = {
            "n_eval": int(len(ev)), "n_pool_median": float(ev["n_pool"].median()),
            "frac_both_drugs_unseen": float(ev["frac_both"].mean()),
            "base": float(ev["base"].mean()),
            "ridge": float(ev["hit_ridge"].mean()),
            "marginal": float(ev["hit_marginal"].mean()),
            "random": float(ev["hit_random"].mean()),
            "ridge_minus_random": paired(ev["hit_ridge"], ev["hit_random"], 9001 + len(label)),
            "ridge_minus_marginal": paired(ev["hit_ridge"], ev["hit_marginal"], 9101 + len(label)),
            "marginal_minus_random": paired(ev["hit_marginal"], ev["hit_random"], 9201 + len(label)),
            "search_ridge_minus_random": float((sr["hit_ridge"] - sr["hit_random"]).mean())}

    bu = res["by_pool"].get("both_unseen", {})
    h189 = bool(bu and abs(bu["frac_both_drugs_unseen"] - 1.0) < 0.001)
    h190 = bool(bu and bu["ridge_minus_random"]["ci95"][0] > 0 and bu["ridge_minus_marginal"]["ci95"][0] > 0)
    m_ci = bu.get("marginal_minus_random") if bu else None
    h191 = bool(m_ci and m_ci["ci95"][0] <= 0 <= m_ci["ci95"][1])
    res["decisions"] = {"H189_R66_label_correct": h189,
                        "H190_model_wins_where_baseline_is_blind": h190,
                        "H191_marginal_is_constant_there": h191}
    res["decisions"]["verdict"] = (
        "annotation_model_scope_is_both_drugs_unseen" if h190 else
        "annotation_model_ties_random_even_where_the_baseline_is_blind")
    res["limits"] = [
        "The both-unseen pool is small (about 2,000 keys), so power is limited.",
        "Tissue is still mostly seen for the cells involved.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r75/PROTOCOL_E072.md",
                "research/2026-10-27-agent-cell-identifiability-r75/e075_genuine_both_unseen.py"):
        pp = ROOT / rel
        if pp.exists():
            res["files"][rel] = sha256(pp)
    (OUT / "E075_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    ok.to_csv(OUT / "E075_rows.csv", index=False)

    print("keys=%d drugs=%d reps=%d" % (len(d), len(drugs), res["audit"]["reps_used"]))
    for label in ("seen", "any_unseen", "both_unseen"):
        e = res["by_pool"].get(label)
        if not e:
            continue
        print("  [%s] frac_both=%.2f pool~%.0f base=%.4f | ridge=%.4f marginal=%.4f random=%.4f" % (
            label, e["frac_both_drugs_unseen"], e["n_pool_median"], e["base"],
            e["ridge"], e["marginal"], e["random"]))
        for kk in ("ridge_minus_random", "ridge_minus_marginal", "marginal_minus_random"):
            c = e[kk]
            print("      %-24s %+.4f [%+.4f,%+.4f]" % (kk, c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
