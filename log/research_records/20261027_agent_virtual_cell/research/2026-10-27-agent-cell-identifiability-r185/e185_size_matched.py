"""E185: is the pathway gain content, or just group size?

C108's random control matched the NUMBER of groups, not their size distribution. Pathway levels differ
enormously in how many training rows they carry, and a bigger group has a better-estimated mean, so
"the annotation works" could be "big groups work". That is a competing explanation, not a detail.

This builds a random partition with the SAME multiset of group sizes as the real pathway partition and
asks whether the real one still wins.

Pre-registered in PROTOCOL_E173.md.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r185"
REPS = 20
N_BOOT = 2000
SEED = 20261077
LAMBDAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
FOLDS = 3
N_RAND = 5          # average over several size-matched draws to reduce draw noise
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


def boot_ci(v, seed):
    rng = np.random.default_rng(seed)
    bs = [float(np.mean(rng.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
    return [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))]


def size_matched_partition(level_values, rng):
    """Random assignment of levels whose MULTISET of sizes equals the real one."""
    vals, counts = np.unique(level_values, return_counts=True)
    sizes = counts.copy()
    rng.shuffle(sizes)
    labels = []
    for i, n in enumerate(sizes):
        labels.extend([i] * int(n))
    labels = np.array(labels[:len(level_values)])
    rng.shuffle(labels)
    return labels


def equal_count_partition(n_items, n_groups, rng):
    """C108-style control: same NUMBER of groups, sizes as equal as possible."""
    labels = np.array([i % n_groups for i in range(n_items)])
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
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), emax=("emax", "mean"))
    for c in ("a", "b", "ap", "lp"):
        g[c] = g[c].astype(str).fillna("NA")
    g = g[np.isfinite(g["emax"])].reset_index(drop=True)

    A = g["a"].to_numpy(); B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    nd = len(drugs)
    drug_index = {v: i for i, v in enumerate(drugs)}
    ai = np.array([drug_index[x] for x in A])
    bi = np.array([drug_index[x] for x in B])
    ap = g["ap"].to_numpy(); lp = g["lp"].to_numpy()
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])

    # real pathway levels, as per-drug labels
    ap_by_drug = np.array([ap[np.where(ai == k)[0][0]] if (ai == k).any() else lp[np.where(bi == k)[0][0]]
                           for k in range(nd)])
    lp_by_drug = np.array([lp[np.where(bi == k)[0][0]] if (bi == k).any() else ap[np.where(ai == k)[0][0]]
                           for k in range(nd)])
    n_ap = len(np.unique(ap_by_drug)); n_lp = len(np.unique(lp_by_drug))

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
        ytr = y[tr]; yte = y[te]

        # real pathway block
        Xp = np.hstack([oh(ap, sorted(set(ap))), oh(lp, sorted(set(lp)))])
        p_id = fit_arm(Xid[tr], ytr, Xid[te], LAMBDAS, SEED + rep)
        p_pa = fit_arm(np.hstack([Xid, Xp])[tr], ytr, np.hstack([Xid, Xp])[te], LAMBDAS, SEED + rep)

        # size-matched random block (averaged over draws)
        sm_rhos = []
        for k in range(N_RAND):
            r2 = np.random.default_rng(SEED + 5000 + rep * 17 + k)
            sm_ap = size_matched_partition(ap_by_drug, r2)
            sm_lp = size_matched_partition(lp_by_drug, r2)
            Xsm = np.hstack([oh(sm_ap[ai], list(range(sm_ap.max() + 1))),
                             oh(sm_lp[bi], list(range(sm_lp.max() + 1)))])
            ps = fit_arm(np.hstack([Xid, Xsm])[tr], ytr, np.hstack([Xid, Xsm])[te], LAMBDAS, SEED + rep + 100 * k)
            sm_rhos.append(spearmanr(ps, yte).statistic)

        # C108-style: same number of groups, near-equal sizes
        r3 = np.random.default_rng(SEED + 9000 + rep)
        eq_ap = equal_count_partition(nd, n_ap, r3)
        eq_lp = equal_count_partition(nd, n_lp, r3)
        Xeq = np.hstack([oh(eq_ap[ai], list(range(n_ap))), oh(eq_lp[bi], list(range(n_lp)))])
        p_eq = fit_arm(np.hstack([Xid, Xeq])[tr], ytr, np.hstack([Xid, Xeq])[te], LAMBDAS, SEED + rep + 777)

        ri = spearmanr(p_id, yte).statistic
        rp = spearmanr(p_pa, yte).statistic
        row = {"rep": rep,
               "rho_identity": 0.0 if not np.isfinite(ri) else float(ri),
               "rho_pathway": 0.0 if not np.isfinite(rp) else float(rp),
               "rho_size_matched": float(np.nanmean(sm_rhos)),
               "rho_equal_count": 0.0 if not np.isfinite(spearmanr(p_eq, yte).statistic)
                                   else float(spearmanr(p_eq, yte).statistic)}
        rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "is_the_pathway_gain_content_or_group_size",
           "input_sha256": sha256(ORIG),
           "settings": {"reps": REPS, "n_rand_draws": N_RAND, "seed": SEED,
                        "lambdas": list(LAMBDAS), "folds": FOLDS, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r)), "n_anchor_levels": int(n_ap),
                     "n_library_levels": int(n_lp)},
           "arms": {}, "contrasts": {}, "files": {}}
    for nm in ("rho_identity", "rho_pathway", "rho_size_matched", "rho_equal_count"):
        res["arms"][nm.replace("rho_", "")] = float(r[nm].mean())
    for a, b, key in (("rho_pathway", "rho_identity", "pathway_minus_identity"),
                      ("rho_size_matched", "rho_identity", "size_matched_minus_identity"),
                      ("rho_equal_count", "rho_identity", "equal_count_minus_identity"),
                      ("rho_pathway", "rho_size_matched", "pathway_minus_size_matched")):
        v = (r[a] - r[b]).to_numpy()
        ci = boot_ci(v, SEED + hash(key) % 997)
        sd = float(v.std(ddof=1))
        res["contrasts"][key] = {"mean": float(v.mean()), "ci95": ci,
                                  "mde_80pct": float(2.802 * sd / np.sqrt(len(v)))}
    pm = res["contrasts"]["pathway_minus_size_matched"]
    h435 = bool(pm["ci95"][0] > 0)
    res["decisions"] = {"pathway_minus_size_matched": pm["mean"],
                        "H434_content_adds_nothing": not h435,
                        "H435_content_matters": h435}
    res["decisions"]["verdict"] = (
        "content_adds_value_beyond_a_size_matched_random_partition" if h435 else
        "a_size_matched_random_partition_does_as_well_so_the_gain_may_be_group_size")
    res["limits"] = ["Matching is on drug counts per level, not on training rows per level, because row counts follow drug frequency and cannot be matched simultaneously.",
                     "Only ridge and one resource.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r185/PROTOCOL_E173.md",
                "research/2026-10-27-agent-cell-identifiability-r185/e185_size_matched.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E185_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E185_rows.csv", index=False)

    print("levels: anchor %d, library %d | rows %d" % (n_ap, n_lp, len(r)))
    for k, v in res["arms"].items():
        print("  %-14s rho %+.4f" % (k, v))
    for k, c in res["contrasts"].items():
        print("  %-30s %+.4f [%+.4f,%+.4f]  MDE %.4f" % (k, c["mean"], c["ci95"][0], c["ci95"][1], c["mde_80pct"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
