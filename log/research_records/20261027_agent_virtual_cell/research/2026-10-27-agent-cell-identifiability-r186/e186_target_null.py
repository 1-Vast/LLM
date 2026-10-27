"""E186: does the TARGET annotation carry content value, or is its gain just group size?

R185 showed the pathway's gain survives a size-matched random null. R164 measured a smaller but significant
target gain (+0.066). This asks what that target gain is made of, which decides between two quite different
practical rules: "any contentful partition works, pathway is just better" versus "only pathway carries
content, target's apparent value is bin size".

Pre-registered in PROTOCOL_E174.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r186"
REPS = 20
N_BOOT = 2000
SEED = 20261078
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
FOLDS = 3
N_RAND = 5
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
    return ym + Zte @ ww


def boot_ci(v, seed):
    rng = np.random.default_rng(seed)
    bs = [float(np.mean(rng.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
    return [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))]


def size_matched_partition(level_values, rng):
    vals, counts = np.unique(level_values, return_counts=True)
    sizes = counts.copy(); rng.shuffle(sizes)
    labels = []
    for i, n in enumerate(sizes):
        labels.extend([i] * int(n))
    labels = np.array(labels[:len(level_values)])
    rng.shuffle(labels)
    return labels


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    g = d.groupby("key", as_index=False).agg(
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        at=("ANCHOR_TARGET", "first"), lt=("LIBRARY_TARGET", "first"), emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp", "at", "lt"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    ap = g["ap"].to_numpy(); lp = g["lp"].to_numpy()
    at = g["at"].to_numpy(); lt = g["lt"].to_numpy()
    drugs = sorted(set(A) | set(B)); nd = len(drugs)
    didx = {v: i for i, v in enumerate(drugs)}
    ai = np.array([didx[x] for x in A]); bi = np.array([didx[x] for x in B])
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    y = g["emax"].to_numpy(float)

    def per_drug(side_vals, other_vals, first_is_anchor=True):
        out = np.empty(nd, dtype=object)
        for k in range(nd):
            own = np.where(ai == k)[0] if first_is_anchor else np.where(bi == k)[0]
            oth = np.where(bi == k)[0] if first_is_anchor else np.where(ai == k)[0]
            src = side_vals if len(own) else other_vals
            idx = own if len(own) else oth
            out[k] = src[idx[0]]
        return out

    ap_by = per_drug(ap, lp, True); lp_by = per_drug(lp, ap, False)
    at_by = per_drug(at, lt, True); lt_by = per_drug(lt, at, False)

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
        ytr = y[tr]; yte = y[te]
        p_id = fit_arm(Xid[tr], ytr, Xid[te], LAMBDAS, SEED + rep)

        Xp = np.hstack([oh(ap, sorted(set(ap))), oh(lp, sorted(set(lp)))])
        p_pa = fit_arm(np.hstack([Xid, Xp])[tr], ytr, np.hstack([Xid, Xp])[te], LAMBDAS, SEED + rep)

        Xt = np.hstack([oh(at, sorted(set(at))), oh(lt, sorted(set(lt)))])
        p_at = fit_arm(np.hstack([Xid, Xt])[tr], ytr, np.hstack([Xid, Xt])[te], LAMBDAS, SEED + rep + 11)

        def rand_rho(base_by_a, base_by_b, tag):
            vals = []
            for k in range(N_RAND):
                r2 = np.random.default_rng(SEED + 7000 + rep * 19 + k + tag)
                ra = size_matched_partition(base_by_a, r2)
                rb = size_matched_partition(base_by_b, r2)
                Xr = np.hstack([oh(ra[ai], list(range(ra.max() + 1))),
                                oh(rb[bi], list(range(rb.max() + 1)))])
                pr = fit_arm(np.hstack([Xid, Xr])[tr], ytr, np.hstack([Xid, Xr])[te], LAMBDAS, SEED + rep + 200 * k + tag)
                s = spearmanr(pr, yte).statistic
                vals.append(0.0 if not np.isfinite(s) else float(s))
            return float(np.mean(vals))

        def safe(p):
            # the identity arm is constant on this pool, so spearmanr returns NaN; record 0 rather than
            # letting NaN propagate into every contrast that touches identity
            s = spearmanr(p, yte).statistic
            return 0.0 if not np.isfinite(s) else float(s)

        rows.append({"rep": rep,
                     "rho_identity": safe(p_id),
                     "rho_pathway": safe(p_pa),
                     "rho_target": safe(p_at),
                     "rho_path_rand": rand_rho(ap_by, lp_by, 0),
                     "rho_target_rand": rand_rho(at_by, lt_by, 500)})

    r = pd.DataFrame(rows)
    res = {"kind": "does_the_target_annotation_carry_content_or_only_group_size",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "n_rand_draws": N_RAND, "seed": SEED,
                        "lambdas": list(LAMBDAS), "folds": FOLDS, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))}, "arms": {}, "contrasts": {}, "files": {}}
    for nm in ("rho_identity", "rho_pathway", "rho_target", "rho_path_rand", "rho_target_rand"):
        res["arms"][nm.replace("rho_", "")] = float(r[nm].mean())
    for a, b, key in (("rho_pathway", "rho_identity", "pathway_minus_identity"),
                      ("rho_target", "rho_identity", "target_minus_identity"),
                      ("rho_path_rand", "rho_identity", "path_rand_minus_identity"),
                      ("rho_target_rand", "rho_identity", "target_rand_minus_identity"),
                      ("rho_pathway", "rho_path_rand", "pathway_minus_path_rand"),
                      ("rho_target", "rho_target_rand", "target_minus_target_rand"),
                      ("rho_pathway", "rho_target", "pathway_minus_target")):
        v = (r[a] - r[b]).to_numpy()
        ci = boot_ci(v, SEED + (abs(hash(key)) % 997))
        res["contrasts"][key] = {"mean": float(v.mean()), "ci95": ci,
                                  "mde_80pct": float(2.802 * v.std(ddof=1) / np.sqrt(len(v)))}
    tt = res["contrasts"]["target_minus_target_rand"]
    h436 = bool(tt["ci95"][0] > 0)
    res["decisions"] = {"target_minus_own_null": tt["mean"],
                        "H436_target_also_carries_content": h436,
                        "H437_target_is_only_group_size": not h436}
    res["decisions"]["verdict"] = (
        "target_also_beats_its_own_size_matched_null_so_both_annotations_carry_content" if h436 else
        "target_does_not_beat_its_own_size_matched_null_so_only_pathway_carries_content")
    res["limits"] = ["Matching is on drug counts per level, not on training rows.",
                     "Only ridge and one resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r186/PROTOCOL_E174.md",
                "research/2026-10-27-agent-cell-identifiability-r186/e186_target_null.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E186_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E186_rows.csv", index=False)

    for k, v in res["arms"].items():
        print("  %-14s rho %+.4f" % (k, v))
    print()
    for k, c in res["contrasts"].items():
        print("  %-26s %+.4f [%+.4f,%+.4f]  MDE %.4f" % (k, c["mean"], c["ci95"][0], c["ci95"][1], c["mde_80pct"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
