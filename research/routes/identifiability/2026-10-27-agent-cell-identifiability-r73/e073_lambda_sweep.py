"""E073: is R72's negative just bad tuning? Sweep lambda and re-test against drug marginals.

Lambda is CHOSEN on the search half and REPORTED on the eval half, so no evaluation data is
used for selection. Pre-registered in PROTOCOL_E070.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r73"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDAS = (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0)
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
    CELL = d["cell"].to_numpy()
    drugs = sorted(set(A) | set(B))
    cells = sorted(set(CELL))

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        rng.shuffle(drugs)
        rng.shuffle(cells)
        held_d = set(drugs[: max(3, int(round(HOLDOUT * len(drugs))))])
        held_c = set(cells[: max(3, int(round(HOLDOUT * len(cells))))])
        drug_seen = np.array([(x not in held_d) and (z not in held_d) for x, z in zip(A, B)])
        cell_unseen = np.array([c in held_c for c in CELL])
        tr = np.where((~cell_unseen) & drug_seen)[0]
        if len(tr) < 20000:
            continue
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd

        grand = float(ytr.mean())
        dm = {}
        for i, yy in zip(tr, ytr):
            dm.setdefault(A[i], []).append(yy)
            dm.setdefault(B[i], []).append(yy)
        drug_eff = {g: float(np.mean(v)) - grand for g, v in dm.items()}

        pool = np.where(cell_unseen & (~drug_seen))[0]   # both_unseen
        if len(pool) < 400:
            continue
        perm = rng.permutation(len(pool))
        half = len(pool) // 2
        for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
            p = pool[idxs]
            Xp = (X[p] - mu) / sd
            marg = np.array([0.5 * (drug_eff.get(A[i], 0.0) + drug_eff.get(B[i], 0.0)) + grand for i in p])
            row = {"rep": rep, "part": part,
                   "hit_marginal": float(syn[p][np.argsort(-marg)[:K]].mean()),
                   "base": float(syn[p].mean())}
            for lam in LAMBDAS:
                Am = Xs.T @ Xs + lam * np.eye(Xs.shape[1])
                w = np.linalg.solve(Am, Xs.T @ (ytr - ytr.mean()))
                pred = ytr.mean() + Xp @ w
                row[f"hit_lam{lam:g}"] = float(syn[p][np.argsort(-pred)[:K]].mean())
            rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "lambda_sweep_against_marginal_baseline",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambdas": list(LAMBDAS), "k": K, "repeats": REPEATS,
                        "holdout": HOLDOUT, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "reps_used": int(r["rep"].nunique()) if len(r) else 0},
           "by_lambda": {}, "files": {}}

    srch = r[r.part == "search"]
    ev = r[r.part == "eval"].set_index("rep")
    search_gain = {}
    for lam in LAMBDAS:
        g = float((srch[f"hit_lam{lam:g}"] - srch["hit_marginal"]).mean())
        search_gain[f"{lam:g}"] = g
        res["by_lambda"][f"{lam:g}"] = {
            "search_gain_vs_marginal": g,
            "eval_hit": float(ev[f"hit_lam{lam:g}"].mean()),
            "eval_gain_vs_marginal": float((ev[f"hit_lam{lam:g}"] - ev["hit_marginal"]).mean()),
            "paired_eval": paired(ev[f"hit_lam{lam:g}"], ev["hit_marginal"], 8001 + int(lam * 100) % 97)}
    res["by_lambda"]["marginal"] = {"eval_hit": float(ev["hit_marginal"].mean())}

    best = max(search_gain, key=search_gain.get)
    best_lam = float(best)
    res["selected_on_search"] = {"lambda": best_lam,
                                 "search_gain": search_gain[best],
                                 "eval_hit": float(ev[f"hit_lam{best_lam:g}"].mean()),
                                 "eval_gain_vs_marginal": float((ev[f"hit_lam{best_lam:g}"] - ev["hit_marginal"]).mean()),
                                 "paired_eval": paired(ev[f"hit_lam{best_lam:g}"], ev["hit_marginal"], 8999)}

    any_lambda_wins = any(v["paired_eval"] and v["paired_eval"]["ci95"][0] > 0 for v in res["by_lambda"].values() if "paired_eval" in v)
    best_pw = res["selected_on_search"]["paired_eval"]
    best_wins = bool(best_pw and best_pw["ci95"][0] > 0)
    res["decisions"] = {"H185_no_lambda_wins": (not any_lambda_wins),
                        "H186_best_lambda_does_not_win": (not best_wins),
                        "best_lambda": best_lam}
    res["decisions"]["verdict"] = ("R72_negative_is_not_a_tuning_artefact" if (not any_lambda_wins and not best_wins)
                                   else "R72_negative_was_partly_tuning")
    res["limits"] = [
        "Only six lambdas are swept; a finer grid could in principle find a winner.",
        "Lambda is selected on the search half, never on the evaluation half.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r73/PROTOCOL_E070.md",
                "research/2026-10-27-agent-cell-identifiability-r73/e073_lambda_sweep.py"):
        pp = ROOT / rel
        if pp.exists():
            res["files"][rel] = sha256(pp)
    (OUT / "E073_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E073_rows.csv", index=False)

    print("keys=%d reps=%d | marginal eval hit = %.4f" % (
        len(d), res["audit"]["reps_used"], res["by_lambda"]["marginal"]["eval_hit"]))
    for lam in LAMBDAS:
        v = res["by_lambda"][f"{lam:g}"]
        c = v["paired_eval"]
        print("  lam=%-7g search %+.4f | eval hit %.4f | eval %+.4f [%+.4f,%+.4f]" % (
            lam, v["search_gain_vs_marginal"], v["eval_hit"], v["eval_gain_vs_marginal"],
            c["ci95"][0], c["ci95"][1]))
    print("selected on search:", json.dumps(res["selected_on_search"], ensure_ascii=False)[:200])
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
