"""E090: is the main conclusion an artefact of using SYNERGY_DELTA_AUC alone?

GDSC ships four synergy definitions (dAUC, dEmax, dfAUC, dXMID). Every conclusion in this
project was built on dAUC. Here the clean unseen-combination comparison (marginals / two-way
additive / pathway ridge) is repeated on all four.

Pre-registered in PROTOCOL_E085.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r90"
METRICS = ["SYNERGY_DELTA_AUC", "SYNERGY_DELTA_EMAX", "SYNERGY_DELTA_fAUC", "SYNERGY_DELTA_XMID"]
LAMBDA = 1.0
K = 20
REPEATS = 40
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY"] + METRICS


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
    for m in METRICS:
        d[m] = pd.to_numeric(d[m], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"), tissue=("Tissue", "first"),
        **{m: (m, "mean") for m in METRICS})
    for c in ("cell", "a", "b", "tissue", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")

    ap_lv = sorted(g["ap"].unique())
    lp_lv = sorted(g["lp"].unique())
    ti_lv = sorted(g["tissue"].unique())
    X = np.hstack([onehot(g["ap"].to_numpy(), ap_lv), onehot(g["lp"].to_numpy(), lp_lv),
                   onehot(g["tissue"].to_numpy(), ti_lv)])
    A = g["a"].to_numpy()
    B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))

    res = {"kind": "metric_dependence_of_the_main_conclusion",
           "input_sha256": sha256(ORIG),
           "settings": {"metrics": METRICS, "k": K, "repeats": REPEATS, "holdout": HOLDOUT,
                        "lambda": LAMBDA, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "drugs": len(drugs)},
           "by_metric": {}, "files": {}}

    for metric in METRICS:
        ok = np.isfinite(g[metric].to_numpy(float))
        y = g[metric].to_numpy(float)
        rng = np.random.default_rng(SEED)
        rows = []
        for rep in range(REPEATS):
            rng.shuffle(drugs)
            held = set(drugs[: max(3, int(round(HOLDOUT * len(drugs))))])
            unseen_combo = np.array([(x in held) != (z in held) for x, z in zip(A, B)]) & ok
            tr = np.where((~np.array([(x in held) or (z in held) for x, z in zip(A, B)])) & ok)[0]
            te = np.where(unseen_combo)[0]
            if len(tr) < 20000 or len(te) < 400:
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
            deff = {k: float(np.mean(v)) - grand for k, v in dm.items()}

            perm = rng.permutation(len(te))
            half = len(te) // 2
            for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                p = te[idxs]
                if len(p) < 100:
                    continue
                Xp = (X[p] - mu) / sd
                pred_ridge = ytr.mean() + Xp @ w
                pred_marg = np.array([0.5 * (deff.get(A[i], 0.0) + deff.get(B[i], 0.0)) + grand for i in p])
                pred_add = (0.5 * (deff.get(A[i], 0.0) + deff.get(B[i], 0.0)) +
                            0.5 * (deff.get(A[i], 0.0) * deff.get(B[i], 0.0)) + grand for i in p) \
                    if False else (np.array([deff.get(A[i], 0.0) for i in p]) + np.array([deff.get(B[i], 0.0) for i in p]) + grand)
                yp = y[p]
                cut = np.quantile(yp, 0.75)
                hit = (yp >= cut).astype(float)
                row = {"rep": rep, "part": part, "n": len(p), "base": float(hit.mean())}
                for name, sc in (("ridge", pred_ridge), ("marginal", pred_marg), ("additive", pred_add)):
                    row[name] = float(hit[np.argsort(-sc)[:K]].mean())
                rows.append(row)
        r = pd.DataFrame(rows)
        ev = r[r.part == "eval"].set_index("rep") if len(r) else pd.DataFrame()
        if len(ev) < 5:
            res["by_metric"][metric] = {"error": "insufficient folds"}
            continue
        res["by_metric"][metric] = {
            "n": int(len(ev)), "base": float(ev["base"].mean()),
            "ridge": float(ev["ridge"].mean()), "marginal": float(ev["marginal"].mean()),
            "additive": float(ev["additive"].mean()),
            "additive_minus_ridge": paired(ev["additive"], ev["ridge"], 17001 + int(abs(hash(metric)) % 97)),
            "marginal_minus_ridge": paired(ev["marginal"], ev["ridge"], 17101 + int(abs(hash(metric)) % 97))}

    wins = 0
    signs = []
    for m in METRICS:
        e = res["by_metric"].get(m, {})
        if "additive_minus_ridge" not in e:
            continue
        c = e["additive_minus_ridge"]
        signs.append(c["mean_diff"])
        if c["ci95"][0] > 0:
            wins += 1
    res["decisions"] = {"H229_holds_on_at_least_3_of_4": wins >= 3,
                        "H230_metric_specific": wins <= 1,
                        "H231_same_sign_everywhere": bool(signs) and all(s > 0 for s in signs),
                        "n_metrics_with_significant_additive_win": int(wins)}
    res["decisions"]["verdict"] = (
        "main_conclusion_is_robust_to_metric_choice" if wins >= 3 else
        "main_conclusion_is_metric_specific" if wins <= 1 else
        "mixed")
    res["limits"] = [
        "The four metrics are highly correlated, so this is not four independent replications.",
        "Missingness differs per metric, so pool membership differs slightly.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r90/PROTOCOL_E085.md",
                "research/2026-10-27-agent-cell-identifiability-r90/e090_metrics.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E090_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E090_rows.csv", index=False)

    print("keys=%d drugs=%d" % (len(g), len(drugs)))
    for m in METRICS:
        e = res["by_metric"].get(m, {})
        if "additive_minus_ridge" not in e:
            print("  %-22s %s" % (m, e.get("error", "n/a")))
            continue
        c = e["additive_minus_ridge"]
        print("  %-22s base=%.4f ridge=%.4f marg=%.4f add=%.4f | add-ridge %+.4f [%+.4f,%+.4f]" % (
            m, e["base"], e["ridge"], e["marginal"], e["additive"],
            c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
