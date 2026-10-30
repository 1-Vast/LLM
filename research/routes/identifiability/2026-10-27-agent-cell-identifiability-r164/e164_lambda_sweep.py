"""E164: sweep the other load-bearing magnitudes for lambda sensitivity.

R163 verified the frozen claim's headline number under a tuned penalty. Two further magnitudes still
rest on lambda equal to 1: identity's rank correlation in the one-drug-seen pools (C103, about 0.253 and
0.229), and the pathway-versus-target gap that the practitioner rule depends on (C113, about 0.0685).

Pre-registered in PROTOCOL_E152.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r164"
REPS = 40
N_BOOT = 2000
SEED = 20261066
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
FOLDS = 3
HISTORICAL = {"identity_one_unseen": 0.253, "pathway_gain_both": 0.1254,
              "target_gain_both": 0.0536, "pathway_minus_target": 0.0685}
TOL = 0.20
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "ANCHOR_TARGET", "LIBRARY_TARGET", "SYNERGY_DELTA_EMAX"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def oh(vals, levels):
    ix = {v: i for i, v in enumerate(levels)}
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        M[t, ix[v]] = 1.0
    return M


def solve_path(G, b, lams):
    out = {}
    d = np.diag(G).copy()
    for lam in lams:
        out[lam] = np.linalg.solve(G + np.diag(lam + 1e-9 * (d + 1.0)), b)
    return out


def fit_arm(Xtr, ytr, Xte, lams, seed, folds=FOLDS):
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    Zte = (Xte - mu) / sd
    rng = np.random.default_rng(seed)
    chunks = np.array_split(rng.permutation(len(Z)), folds)
    score = {lam: [] for lam in lams}
    for f in range(folds):
        va = chunks[f]
        tr = np.setdiff1d(np.arange(len(Z)), va)
        ym = ytr[tr].mean()
        w = solve_path(Z[tr].T @ Z[tr], Z[tr].T @ (ytr[tr] - ym), lams)
        yv = ytr[va]
        for lam, ww in w.items():
            p = ym + Z[va] @ ww
            s = spearmanr(p, yv).statistic if np.std(p) > 0 else -2.0
            score[lam].append(0.0 if not np.isfinite(s) else float(s))
    best = max(lams, key=lambda lam: float(np.mean(score[lam])))
    ym = ytr.mean()
    ww = solve_path(Z.T @ Z, Z.T @ (ytr - ym), [best])[best]
    return ym + Zte @ ww, best


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), at=("ANCHOR_TARGET", "first"), lt=("LIBRARY_TARGET", "first"),
        emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp", "at", "lt"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xp = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                    oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xt = np.hstack([oh(g["at"].to_numpy(), sorted(g["at"].unique())),
                    oh(g["lt"].to_numpy(), sorted(g["lt"].unique()))])
    arms = {"identity": Xid, "pathway": np.hstack([Xid, Xp]), "target": np.hstack([Xid, Xt])}
    y = g["emax"].to_numpy(float)
    rng = np.random.default_rng(SEED)

    rows = []
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(0.20 * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        tr = np.where((~au) & (~bu))[0]
        for pool_name, te in (("both_unseen", np.where(au & bu)[0]),
                              ("one_unseen", np.where(au ^ bu)[0])):
            if len(te) < 150:
                continue
            ytr = y[tr]; yte = y[te]
            row = {"rep": rep, "pool": pool_name, "n_eval": int(len(te))}
            for nm, XX in arms.items():
                p, lam = fit_arm(XX[tr], ytr, XX[te], LAMBDAS, SEED + rep)
                s = spearmanr(p, yte).statistic
                row["rho_" + nm] = 0.0 if not np.isfinite(s) else float(s)
                row["lam_" + nm] = lam
            rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "lambda_sensitivity_sweep_of_the_other_key_magnitudes",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "seed": SEED, "lambdas": list(LAMBDAS), "folds": FOLDS,
                        "tolerance": TOL, "historical": HISTORICAL, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_pool": {}, "files": {}}
    for pool in ("both_unseen", "one_unseen"):
        sub = r[r.pool == pool]
        if len(sub) < 10:
            continue
        cell = {"n": int(len(sub)), "mean_eval": float(sub["n_eval"].mean())}
        for nm in arms:
            cell["rho_" + nm] = float(sub["rho_" + nm].mean())
            cell["lam_" + nm] = float(sub["lam_" + nm].mean())
        for a, b in (("pathway", "identity"), ("target", "identity"), ("pathway", "target")):
            v = (sub["rho_" + a] - sub["rho_" + b]).to_numpy()
            rng2 = np.random.default_rng(SEED + 900 + hash(a + b) % 97)
            boots = [float(np.mean(rng2.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
            cell["%s_minus_%s" % (a, b)] = {
                "mean": float(v.mean()),
                "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}
        res["by_pool"][pool] = cell

    one = res["by_pool"].get("one_unseen", {})
    both = res["by_pool"].get("both_unseen", {})
    checks = {}
    if one:
        checks["identity_one_unseen"] = {"historical": HISTORICAL["identity_one_unseen"],
                                          "observed": one["rho_identity"]}
    if both and "pathway_minus_identity" in both:
        checks["pathway_gain_both"] = {"historical": HISTORICAL["pathway_gain_both"],
                                        "observed": both["pathway_minus_identity"]["mean"]}
        checks["target_gain_both"] = {"historical": HISTORICAL["target_gain_both"],
                                       "observed": both["target_minus_identity"]["mean"]}
        checks["pathway_minus_target"] = {"historical": HISTORICAL["pathway_minus_target"],
                                           "observed": both["pathway_minus_target"]["mean"]}
    for k, v in checks.items():
        v["relative_change"] = ((v["observed"] - v["historical"]) / abs(v["historical"])
                                if v["historical"] else None)
        v["beyond_tolerance"] = bool(v["relative_change"] is not None
                                      and abs(v["relative_change"]) > TOL)
    res["checks"] = checks
    any_beyond = any(v["beyond_tolerance"] for v in checks.values())
    res["decisions"] = {"any_beyond_tolerance": bool(any_beyond),
                        "H392_all_stable": not any_beyond, "H393_some_magnitude_changes": any_beyond}
    res["decisions"]["verdict"] = (
        "at_least_one_key_magnitude_moves_beyond_twenty_percent_under_a_tuned_penalty" if any_beyond else
        "all_key_magnitudes_are_stable_under_a_tuned_penalty")
    res["limits"] = ["Historical values came from different seeds and split implementations, so magnitudes are compared, not exact numbers.",
                     "Only ridge and one resource; three inner folds.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r164/PROTOCOL_E152.md",
                "research/2026-10-27-agent-cell-identifiability-r164/e164_lambda_sweep.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E164_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E164_rows.csv", index=False)

    for pool, c in res["by_pool"].items():
        print("  [%-11s] eval %6.0f | rho_id %+.4f (lam %.1f) rho_path %+.4f (lam %.1f) rho_tgt %+.4f (lam %.1f)" % (
            pool, c["mean_eval"], c["rho_identity"], c["lam_identity"],
            c["rho_pathway"], c["lam_pathway"], c["rho_target"], c["lam_target"]))
        for k in ("pathway_minus_identity", "target_minus_identity", "pathway_minus_target"):
            v = c[k]
            print("        %-24s %+.4f [%+.4f,%+.4f]" % (k, v["mean"], v["ci95"][0], v["ci95"][1]))
    print("  --- vs historical ---")
    for k, v in checks.items():
        print("  %-24s historical %+.4f  observed %+.4f  change %s  beyond=%s" % (
            k, v["historical"], v["observed"],
            ("%+.1f%%" % (100 * v["relative_change"])) if v["relative_change"] is not None else "n/a",
            v["beyond_tolerance"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
