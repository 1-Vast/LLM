"""E103: leakage review by permuting the drug-to-pathway mapping.

If the annotation increment comes from the real correspondence between drugs and pathways,
breaking that correspondence must destroy it. If the increment survives permutation, then the
value is coming from feature count or some other structure and promotion is refused.

Pre-registered in PROTOCOL_E098.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r103"
LAMBDA = 1.0
K = 20
REPEATS = 70
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "Synergy"]


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
    idx = {v: j for j, v in enumerate(levels)}
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        j = idx.get(v)
        if j is not None:
            M[t, j] = 1.0
    return M


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), syn=("syn", "mean"))
    g["syn"] = g["syn"] > 0.5
    for c in ("cell", "a", "b", "ap", "lp", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy()
    B = g["b"].to_numpy()
    CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B))
    cells = sorted(set(CELL))
    y = g["syn"].to_numpy(bool)

    # drug -> pathway map (use the pathway seen for that drug on either side)
    drug_path = {}
    for nm, pw in zip(list(A) + list(B), list(g["ap"]) + list(g["lp"])):
        if nm not in drug_path and pw != "NA":
            drug_path[nm] = pw
    pws = sorted(set(drug_path.values()))
    ti_lv = sorted(g["tissue"].unique())

    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])

    def pathway_block(path_map):
        pa = [path_map.get(x, "NA") for x in A]
        pb = [path_map.get(z, "NA") for z in B]
        lv = pws + ["NA"]
        return np.hstack([onehot(pa, lv), onehot(pb, lv), onehot(g["tissue"].to_numpy(), ti_lv)])

    Xreal = pathway_block(drug_path)
    tis = onehot(g["tissue"].to_numpy(), ti_lv)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        order = list(drugs)
        rng.shuffle(order)
        cells_sh = list(cells)
        rng.shuffle(cells_sh)
        heldd = set(order[: max(3, int(round(HOLDOUT * len(order))))])
        heldc = set(cells_sh[: max(3, int(round(HOLDOUT * len(cells_sh))))])
        a_u = np.array([x in heldd for x in A])
        b_u = np.array([z in heldd for z in B])
        cell_u = np.array([c in heldc for c in CELL])
        tr = np.where((~cell_u) & (~a_u) & (~b_u))[0]
        if len(tr) < 20000:
            continue

        # permuted drug->pathway mapping, drawn independently each split
        labels = list(drug_path.values())
        rng.shuffle(labels)
        perm_map = dict(zip(list(drug_path.keys()), labels))
        Xperm = pathway_block(perm_map)

        ytr = y[tr].astype(float)

        def fit(XX):
            Xt = XX[tr]
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0)
            sd[sd == 0] = 1.0
            Xs = (Xt - mu) / sd
            Am = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
            w = np.linalg.solve(Am, Xs.T @ (ytr - ytr.mean()))
            return lambda XXe: ytr.mean() + ((XXe - mu) / sd) @ w

        f_id = fit(Xid)
        f_real = fit(np.hstack([Xid, Xreal]))
        f_perm = fit(np.hstack([Xid, Xperm]))

        pools = {"one_unseen": np.where((a_u ^ b_u) & (~cell_u))[0],
                 "both_unseen": np.where(a_u & b_u)[0]}
        for pname, pool in pools.items():
            if len(pool) < 60:
                continue
            s_id = f_id(Xid[pool])
            s_real = f_real(np.hstack([Xid, Xreal])[pool])
            s_perm = f_perm(np.hstack([Xid, Xperm])[pool])
            perm_idx = rng.permutation(len(pool))
            half = len(pool) // 2
            for part, idxs in (("search", perm_idx[:half]), ("eval", perm_idx[half:])):
                if len(idxs) < 40:
                    continue
                hit = y[pool][idxs].astype(float)
                rows.append({"rep": rep, "pool": pname, "part": part,
                             "identity": float(hit[np.argsort(-s_id[idxs])[:K]].mean()),
                             "real": float(hit[np.argsort(-s_real[idxs])[:K]].mean()),
                             "permuted": float(hit[np.argsort(-s_perm[idxs])[:K]].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "leakage_review_by_permuting_the_drug_to_pathway_mapping",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "holdout": HOLDOUT, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "drugs": len(drugs),
                     "pathways": len(pws), "pathway_block_dims": int(Xreal.shape[1]),
                     "rows": int(len(r))},
           "by_pool": {}, "files": {}}

    for pname in ("one_unseen", "both_unseen"):
        ev = r[(r.pool == pname) & (r.part == "eval")].set_index("rep")
        if len(ev) < 5:
            continue
        ev = ev.assign(real_gain=ev["real"] - ev["identity"],
                       perm_gain=ev["permuted"] - ev["identity"])
        res["by_pool"][pname] = {
            "n": int(len(ev)),
            "identity": float(ev["identity"].mean()),
            "real": float(ev["real"].mean()),
            "permuted": float(ev["permuted"].mean()),
            "real_minus_identity": paired(ev["real"], ev["identity"], 30001 + len(pname)),
            "permuted_minus_identity": paired(ev["permuted"], ev["identity"], 30101 + len(pname)),
            "real_gain_minus_perm_gain": paired(ev["real_gain"], ev["perm_gain"], 30201 + len(pname))}

    tests = [e for e in res["by_pool"].values()]
    h266 = bool(tests) and all(e["real_gain_minus_perm_gain"]["ci95"][0] > 0 for e in tests)
    h267 = bool(tests) and all(e["permuted_minus_identity"]["ci95"][0] <= 0 for e in tests)
    res["decisions"] = {"H266_real_gain_exceeds_permuted_gain": h266,
                        "H267_no_gain_after_permutation": h267,
                        "H268_leakage_review_passed": bool(h266 and h267)}
    res["decisions"]["verdict"] = (
        "leakage_review_passed_promotion_may_proceed_on_this_check" if h266 and h267 else
        "promotion_REFUSED_annotation_gain_does_not_depend_on_the_real_mapping" if not h266 else
        "permutation_still_gains_so_the_41_dim_structure_needs_investigation")
    res["limits"] = [
        "Permutation preserves the marginal pathway distribution but destroys the drug-pathway pairing, which is the intended cut.",
        "Only two pools were run; an opposite result would require all three.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r103/PROTOCOL_E098.md",
                "research/2026-10-27-agent-cell-identifiability-r103/e103_leakage.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E103_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E103_rows.csv", index=False)

    print("rows=%d pathways=%d dims=%d" % (len(r), len(pws), Xreal.shape[1]))
    for pname, e in res["by_pool"].items():
        a = e["real_minus_identity"]; b = e["permuted_minus_identity"]; c = e["real_gain_minus_perm_gain"]
        print("  %-12s identity %.4f real %.4f permuted %.4f" % (pname, e["identity"], e["real"], e["permuted"]))
        print("      real-id %+.4f [%+.4f,%+.4f] | perm-id %+.4f [%+.4f,%+.4f] | diff %+.4f [%+.4f,%+.4f]" % (
            a["mean_diff"], a["ci95"][0], a["ci95"][1], b["mean_diff"], b["ci95"][0], b["ci95"][1],
            c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
