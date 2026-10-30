"""E120: the decisive decomposition - is the annotation increment pathway or tissue?

R119 showed the increment reverses under tissue holdout, and suspected that tissue, being inside
the annotation block, is what actually carries the gain. This splits the block into
pathway-only and tissue-only and measures each against identity.

Pre-registered in PROTOCOL_E113.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r120"
LAMBDA = 1.0
K = 20
REPEATS = 60
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261027
METRICS = ["Synergy", "SYNERGY_DELTA_EMAX"]
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "Synergy", "SYNERGY_DELTA_EMAX"]


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
    Mt = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        j = idx.get(v)
        if j is not None:
            Mt[t, j] = 1.0
    return Mt


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["emax"] = pd.to_numeric(d["SYNERGY_DELTA_EMAX"], errors="coerce")
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), syn=("syn", "mean"), emax=("emax", "mean"))
    g["syn"] = g["syn"] > 0.5
    for c in ("cell", "a", "b", "ap", "lp", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpath = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                       onehot(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    Xtis = onehot(g["tissue"].to_numpy(), sorted(g["tissue"].unique()))
    targets = {"Synergy": (g["syn"].to_numpy(bool), "flag"),
               "SYNERGY_DELTA_EMAX": (g["emax"].to_numpy(float), "quartile")}

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        rng.shuffle(drugs); rng.shuffle(cells)
        heldd = set(drugs[: max(3, int(round(HOLDOUT * len(drugs))))])
        heldc = set(cells[: max(3, int(round(HOLDOUT * len(cells))))])
        a_u = np.array([x in heldd for x in A]); b_u = np.array([z in heldd for z in B])
        cell_u = np.array([c in heldc for c in CELL])
        tr = np.where((~cell_u) & (~a_u) & (~b_u))[0]
        if len(tr) < 20000:
            continue
        arms = {"identity": Xid,
                "plus_pathway": np.hstack([Xid, Xpath]),
                "plus_tissue": np.hstack([Xid, Xtis]),
                "plus_both": np.hstack([Xid, Xpath, Xtis])}
        Xrand = np.hstack([Xid, rng.normal(size=(len(g), Xpath.shape[1]))])
        arms["plus_random"] = Xrand

        for crit, (yt, kind) in targets.items():
            ytr = yt[tr].astype(float)
            ok = np.isfinite(ytr)
            if ok.sum() < 20000:
                continue
            trk = tr[ok]; yv = ytr[ok]
            scorers = {}
            for nm, XX in arms.items():
                Xt = XX[trk]
                mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
                Z = (Xt - mu) / sd
                w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (yv - yv.mean()))
                scorers[nm] = (lambda XXe, mu=mu, sd=sd, w=w, b=yv.mean(): b + ((XXe - mu) / sd) @ w, XX)
            pools = {"one_unseen": np.where((a_u ^ b_u) & (~cell_u))[0],
                     "cell_unseen": np.where(cell_u & (a_u | b_u))[0],
                     "both_unseen": np.where(a_u & b_u)[0]}
            for pname, pool in pools.items():
                pool = pool[np.isfinite(yt[pool])]
                if len(pool) < 60:
                    continue
                perm = rng.permutation(len(pool)); half = len(pool) // 2
                for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                    if len(idxs) < 40:
                        continue
                    p = pool[idxs]
                    yp = yt[p].astype(float)
                    hit = (yp >= np.quantile(yp, 0.75)).astype(float) if kind == "quartile" else yp
                    row = {"rep": rep, "criterion": crit, "pool": pname, "part": part}
                    for nm, (f, XX) in scorers.items():
                        row[nm] = float(hit[np.argsort(-f(XX[p]))[:K]].mean())
                    rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "pathway_versus_tissue_decomposition_of_the_annotation_increment",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "holdout": HOLDOUT, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "rows": int(len(r)),
                     "identity_dims": int(Xid.shape[1]), "pathway_dims": int(Xpath.shape[1]),
                     "tissue_dims": int(Xtis.shape[1])},
           "by_criterion": {}, "files": {}}

    for crit in METRICS:
        res["by_criterion"][crit] = {}
        for pname in ("one_unseen", "cell_unseen", "both_unseen"):
            ev = r[(r.criterion == crit) & (r.pool == pname) & (r.part == "eval")].set_index("rep")
            if len(ev) < 5:
                continue
            res["by_criterion"][crit][pname] = {
                "n": int(len(ev)),
                **{nm: float(ev[nm].mean()) for nm in ("identity", "plus_pathway", "plus_tissue",
                                                        "plus_both", "plus_random")},
                "pathway_minus_identity": paired(ev["plus_pathway"], ev["identity"], 47001 + len(pname) + len(crit)),
                "tissue_minus_identity": paired(ev["plus_tissue"], ev["identity"], 47101 + len(pname) + len(crit)),
                "both_minus_identity": paired(ev["plus_both"], ev["identity"], 47201 + len(pname) + len(crit)),
                "random_minus_identity": paired(ev["plus_random"], ev["identity"], 47301 + len(pname) + len(crit))}

    def wins(crit, key):
        return sum(1 for e in res["by_criterion"].get(crit, {}).values() if e[key]["ci95"][0] > 0)

    w_path_s = wins("Synergy", "pathway_minus_identity")
    w_tis_s = wins("Synergy", "tissue_minus_identity")
    w_path_e = wins("SYNERGY_DELTA_EMAX", "pathway_minus_identity")
    w_tis_e = wins("SYNERGY_DELTA_EMAX", "tissue_minus_identity")
    res["decisions"] = {"pathway_wins": {"Synergy": w_path_s, "dEMAX": w_path_e},
                        "tissue_wins": {"Synergy": w_tis_s, "dEMAX": w_tis_e},
                        "H299_pathway_carries_independent_signal": (w_path_s >= 2 and w_path_e >= 2),
                        "H300_increment_is_mainly_tissue": (w_path_s < 2 and w_tis_s >= 2),
                        "H301_both_contribute": (w_path_s >= 2 and w_tis_s >= 2)}
    res["decisions"]["verdict"] = (
        "pathway_carries_independent_signal_so_C74_stands" if (w_path_s >= 2 and w_path_e >= 2) else
        "the_increment_is_mainly_tissue_so_C74_must_be_rewritten" if (w_path_s < 2 and w_tis_s >= 2) else
        "mixed_or_unresolved")
    res["limits"] = [
        "The pathway block has only 38 levels and the tissue block only 3, so both are coarse.",
        "The three pools share one training set.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r120/PROTOCOL_E113.md",
                "research/2026-10-27-agent-cell-identifiability-r120/e120_decomposition.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E120_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E120_rows.csv", index=False)

    print("rows=%d dims id=%d pathway=%d tissue=%d" % (
        len(r), Xid.shape[1], Xpath.shape[1], Xtis.shape[1]))
    for crit in METRICS:
        print(" [%s]" % crit)
        for pname, e in res["by_criterion"].get(crit, {}).items():
            a = e["pathway_minus_identity"]; b = e["tissue_minus_identity"]; c = e["random_minus_identity"]
            print("   %-12s id %.4f +path %.4f +tis %.4f +both %.4f +rand %.4f" % (
                pname, e["identity"], e["plus_pathway"], e["plus_tissue"], e["plus_both"], e["plus_random"]))
            print("       path-id %+.4f [%+.4f,%+.4f] | tis-id %+.4f [%+.4f,%+.4f] | rand-id %+.4f [%+.4f,%+.4f]" % (
                a["mean_diff"], a["ci95"][0], a["ci95"][1], b["mean_diff"], b["ci95"][0], b["ci95"][1],
                c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
