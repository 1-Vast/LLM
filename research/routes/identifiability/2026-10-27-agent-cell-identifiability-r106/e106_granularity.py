"""E106: is the annotation signal coming from coarse pathways or finer target genes?

GDSC ships ANCHOR_TARGET / LIBRARY_TARGET (about 96 levels, comma-separated gene lists) alongside
ANCHOR_PATHWAY / LIBRARY_PATHWAY (about 38). Every previous round used pathways only, so the
unresolved question in C46's limitations - whether the finding is about granularity - has never
been tested. This compares identity, +pathway, +target, +both, and a capacity control.

Pre-registered in PROTOCOL_E101.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r106"
LAMBDA = 1.0
K = 20
REPEATS = 60
HOLDOUT = 0.20
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "ANCHOR_TARGET", "LIBRARY_TARGET", "Synergy"]


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


def tok(v):
    return [x.strip() for x in str(v).replace(";", ",").split(",") if x.strip()]


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
        at=("ANCHOR_TARGET", "first"), lt=("LIBRARY_TARGET", "first"),
        tissue=("Tissue", "first"), syn=("syn", "mean"))
    g["syn"] = g["syn"] > 0.5
    for c in ("cell", "a", "b", "ap", "lp", "at", "lt", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    y = g["syn"].to_numpy(bool)

    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    ap_lv = sorted(g["ap"].unique()); lp_lv = sorted(g["lp"].unique())
    ti_lv = sorted(g["tissue"].unique())
    Xpa = np.hstack([onehot(g["ap"].to_numpy(), ap_lv), onehot(g["lp"].to_numpy(), lp_lv),
                     onehot(g["tissue"].to_numpy(), ti_lv)])

    # target tokens per side
    at_tok = [tok(v) for v in g["at"]]
    lt_tok = [tok(v) for v in g["lt"]]
    tlv = sorted({t for row in at_tok for t in row} | {t for row in lt_tok for t in row})
    tidx = {t: j for j, t in enumerate(tlv)}
    Xt = np.zeros((len(g), 2 * len(tlv)))
    for i in range(len(g)):
        for t in at_tok[i]:
            Xt[i, tidx[t]] = 1.0
        for t in lt_tok[i]:
            Xt[i, len(tlv) + tidx[t]] = 1.0
    Xt = np.hstack([Xt, onehot(g["tissue"].to_numpy(), ti_lv)])

    arms = {"identity": Xid,
            "plus_pathway": np.hstack([Xid, Xpa]),
            "plus_target": np.hstack([Xid, Xt]),
            "plus_both": np.hstack([Xid, Xpa, Xt])}

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
        ytr = y[tr].astype(float)

        def fit(XX):
            Xt_ = XX[tr]
            mu, sd = Xt_.mean(axis=0), Xt_.std(axis=0); sd[sd == 0] = 1.0
            Z = (Xt_ - mu) / sd
            w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
            return lambda XXe: ytr.mean() + ((XXe - mu) / sd) @ w

        scorers = {nm: (fit(XX), XX) for nm, XX in arms.items()}
        Rr = np.hstack([Xid, rng.normal(size=(len(g), Xt.shape[1]))])
        scorers["plus_random"] = (fit(Rr), Rr)

        pools = {"one_unseen": np.where((a_u ^ b_u) & (~cell_u))[0],
                 "cell_unseen": np.where(cell_u & (a_u | b_u))[0],
                 "both_unseen": np.where(a_u & b_u)[0]}
        for pname, pool in pools.items():
            if len(pool) < 60:
                continue
            sc = {nm: f(XX[pool]) for nm, (f, XX) in scorers.items()}
            perm = rng.permutation(len(pool)); half = len(pool) // 2
            for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                if len(idxs) < 40:
                    continue
                hit = y[pool][idxs].astype(float)
                row = {"rep": rep, "pool": pname, "part": part}
                for nm in scorers:
                    row[nm] = float(hit[np.argsort(-sc[nm][idxs])[:K]].mean())
                rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "pathway_versus_target_granularity",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "holdout": HOLDOUT, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "drugs": len(drugs),
                     "pathway_levels": len(ap_lv) + len(lp_lv), "target_levels": len(tlv),
                     "identity_dims": int(Xid.shape[1]), "pathway_block": int(Xpa.shape[1]),
                     "target_block": int(Xt.shape[1]), "rows": int(len(r))},
           "by_pool": {}, "files": {}}

    for pname in ("one_unseen", "cell_unseen", "both_unseen"):
        ev = r[(r.pool == pname) & (r.part == "eval")].set_index("rep")
        if len(ev) < 5:
            continue
        res["by_pool"][pname] = {
            "n": int(len(ev)),
            **{nm: float(ev[nm].mean()) for nm in ("identity", "plus_pathway", "plus_target",
                                                   "plus_both", "plus_random")},
            "pathway_minus_identity": paired(ev["plus_pathway"], ev["identity"], 32001 + len(pname)),
            "target_minus_identity": paired(ev["plus_target"], ev["identity"], 32101 + len(pname)),
            "target_minus_pathway": paired(ev["plus_target"], ev["plus_pathway"], 32201 + len(pname)),
            "both_minus_pathway": paired(ev["plus_both"], ev["plus_pathway"], 32301 + len(pname))}

    def wins(key):
        return sum(1 for e in res["by_pool"].values() if e[key]["ci95"][0] > 0)

    w_path = wins("pathway_minus_identity")
    w_targ = wins("target_minus_identity")
    w_t_over_p = wins("target_minus_pathway")
    res["decisions"] = {"pathway_wins": w_path, "target_wins": w_targ,
                        "target_beats_pathway_count": w_t_over_p,
                        "H275_target_more_informative_than_pathway": w_t_over_p >= 2,
                        "H276_pathway_not_subsumed_by_target": wins("both_minus_pathway") >= 2}
    res["decisions"]["verdict"] = (
        "finer_annotation_is_better" if w_t_over_p >= 2 else
        "pathway_granularity_is_sufficient")
    res["limits"] = [
        "Target strings mix genes and complexes (for example 'Proteasome'), so the target block is not a clean gene set.",
        "The three pools share one training set.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r106/PROTOCOL_E101.md",
                "research/2026-10-27-agent-cell-identifiability-r106/e106_granularity.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E106_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E106_rows.csv", index=False)

    print("rows=%d pathways=%d targets=%d dims id=%d pa=%d tg=%d" % (
        len(r), len(ap_lv) + len(lp_lv), len(tlv),
        Xid.shape[1], Xpa.shape[1], Xt.shape[1]))
    for pname, e in res["by_pool"].items():
        print("  [%-12s] id %.4f +pa %.4f +tg %.4f +both %.4f +rand %.4f" % (
            pname, e["identity"], e["plus_pathway"], e["plus_target"], e["plus_both"], e["plus_random"]))
        for k in ("pathway_minus_identity", "target_minus_identity", "target_minus_pathway", "both_minus_pathway"):
            c = e[k]
            print("      %-24s %+.4f [%+.4f,%+.4f]" % (k, c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
