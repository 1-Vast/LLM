"""E174: can this model rank CELL LINES, or only drug combinations?

Every reported gain is a rank correlation over (cell x combination) keys. But a practitioner choosing
experiments needs to rank both axes. If the model assigns the same score to every cell of a given
combination, it answers only half the question. This measures a variance decomposition to say which half.

Pre-registered in PROTOCOL_E162.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r174"
REPS = 20
SEED = 20261070
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
FOLDS = 3
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY",
       "SYNERGY_DELTA_EMAX"]


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
    return ym + Zte @ ww


def decompose(pred, groups):
    df = pd.DataFrame({"p": pred, "g": groups})
    grand = df["p"].mean()
    gmeans = df.groupby("g")["p"].transform("mean")
    between = float(((gmeans - grand) ** 2).sum())
    within = float(((df["p"] - gmeans) ** 2).sum())
    total = between + within
    return {"between": between, "within": within,
            "between_frac": (between / total) if total > 0 else None,
            "within_frac": (within / total) if total > 0 else None,
            "n_groups": int(df["g"].nunique()), "n_rows": int(len(df))}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"),
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("cell", "a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    # group on the ORDERED PAIR as a tuple key, not a joined string: drug names in this resource
    # contain separators such as "|" and "+", so a string join collides different pairs into one
    # group and would make a constant prediction look variable.
    g["combo_code"] = g.groupby(["a", "b"]).ngroup().to_numpy()
    combo = g["combo_code"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xp = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                    oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xboth = np.hstack([Xid, Xp])
    y = g["emax"].to_numpy(float)
    rng = np.random.default_rng(SEED)

    rows = []
    for rep in range(REPS):
        ds = drugs[:]; rng.shuffle(ds)
        held = set(ds[: max(3, int(round(0.20 * len(ds))))])
        au = np.array([x in held for x in A]); bu = np.array([z in held for z in B])
        tr = np.where((~au) & (~bu))[0]
        te = np.where(au & bu)[0]
        if len(tr) < 15000 or len(te) < 150:
            continue
        ytr = y[tr]
        for nm, XX in (("identity", Xid), ("identity_pathway", Xboth)):
            p = fit_arm(XX[tr], ytr, XX[te], LAMBDAS, SEED + rep)
            dec = decompose(p, combo[te])
            # within-combo cells: how many combos have more than one distinct prediction?
            s = pd.DataFrame({"p": p, "g": combo[te]})
            nun = s.groupby("g")["p"].nunique()
            varying = int((nun > 1).sum())
            rows.append({"rep": rep, "arm": nm, "n_eval": int(len(te)),
                         "between_frac": dec["between_frac"], "within_frac": dec["within_frac"],
                         "n_combos": dec["n_groups"],
                         "combos_with_varying_prediction": varying,
                         "rho": float(spearmanr(p, y[te]).statistic)})

    r = pd.DataFrame(rows)
    res = {"kind": "can_the_model_rank_cells_or_only_combinations",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "seed": SEED, "lambdas": list(LAMBDAS), "folds": FOLDS},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "by_arm": {}, "files": {}}
    for nm in ("identity", "identity_pathway"):
        sub = r[r.arm == nm]
        if len(sub) < 5:
            continue
        res["by_arm"][nm] = {
            "n": int(len(sub)), "mean_eval": float(sub["n_eval"].mean()),
            "between_frac": float(sub["between_frac"].mean()),
            "within_frac": float(sub["within_frac"].mean()),
            "combos_with_varying_prediction": float(sub["combos_with_varying_prediction"].mean()),
            "mean_n_combos": float(sub["n_combos"].mean()),
            "rho": float(sub["rho"].mean())}
    wp = res["by_arm"].get("identity_pathway", {})
    h412 = bool(wp and (wp["within_frac"] is not None and wp["within_frac"] < 1e-12
                         and wp["combos_with_varying_prediction"] == 0))
    res["decisions"] = {"H412_ranks_combinations_only": h412,
                        "H413_also_ranks_cells": bool(wp and not h412)}
    res["decisions"]["verdict"] = (
        "the_model_is_constant_across_cells_within_a_combination_so_it_ranks_combinations_only" if h412 else
        "the_model_varies_across_cells_within_a_combination_so_it_ranks_cells_too")
    res["why_this_is_structural_not_empirical"] = {
        "reason": "neither arm contains any cell-level feature: identity is a drug indicator and the pathway block is a drug annotation. With no cell covariate the prediction cannot depend on the cell.",
        "so": "the result is forced by the design. It is worth stating because the limitation has never been written down, not because the experiment could have come out the other way.",
        "what_would_lift_it": "a cell-level covariate block, which the resource cannot supply in the both-unseen setting beyond tissue, and C90 showed the tissue block is itself unreliable under holdout"}
    res["limits"] = ["Only ridge and one resource; two feature sets.",
                     "The result follows from the feature design, so its interest is in the boundary it names, not in its surprise.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r174/PROTOCOL_E162.md",
                "research/2026-10-27-agent-cell-identifiability-r174/e174_cell_axis.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E174_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E174_rows.csv", index=False)

    for nm, e in res["by_arm"].items():
        print("  [%-16s] rho %+.4f | between_frac %s within_frac %s | combos with varying prediction %.1f / %.0f" % (
            nm, e["rho"],
            ("%.6f" % e["between_frac"]) if e["between_frac"] is not None else "n/a",
            ("%.6f" % e["within_frac"]) if e["within_frac"] is not None else "n/a",
            e["combos_with_varying_prediction"], e["mean_n_combos"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
