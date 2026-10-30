"""E098: does pathway annotation add anything beyond drug identity?

C45 pitted a two-way additive model built on DRUG IDENTITY against a ridge built on PATHWAY
annotation. That compares fine granularity with coarse granularity, which is close to
guaranteed to favour the fine one, and says nothing about whether the annotation carries
information. This matters because C45 carries the programme's headline conclusion.

Pre-registered in PROTOCOL_E093.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r98"
LAMBDA = 1.0
K = 20
REPEATS = 40
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
    M = np.zeros((len(vals), len(levels)))
    for j, v in enumerate(levels):
        M[:, j] = (vals == v).astype(float)
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
    drugs = sorted(set(A) | set(B))
    dl = {x: i for i, x in enumerate(drugs)}
    ap_lv = sorted(g["ap"].unique())
    lp_lv = sorted(g["lp"].unique())
    ti_lv = sorted(g["tissue"].unique())

    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpa = np.hstack([onehot(g["ap"].to_numpy(), ap_lv), onehot(g["lp"].to_numpy(), lp_lv),
                     onehot(g["tissue"].to_numpy(), ti_lv)])
    Xboth = np.hstack([Xid, Xpa])
    y = g["syn"].to_numpy(bool)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        rng.shuffle(drugs)
        held = set(drugs[: max(3, int(round(HOLDOUT * len(drugs))))])
        # unseen-combination pool: exactly one side unseen
        one_unseen = np.array([(x in held) != (z in held) for x, z in zip(A, B)])
        tr = np.where(np.array([(x not in held) and (z not in held) for x, z in zip(A, B)]))[0]
        te = np.where(one_unseen)[0]
        if len(tr) < 20000 or len(te) < 400:
            continue

        def rid(XX):
            Xt, yt = XX[tr], y[tr].astype(float)
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0)
            sd[sd == 0] = 1.0
            Xs = (Xt - mu) / sd
            Am = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
            w = np.linalg.solve(Am, Xs.T @ (yt - yt.mean()))
            Xe = (XX[te] - mu) / sd
            return yt.mean() + Xe @ w

        pr = {"identity": rid(Xid), "pathway": rid(Xpa), "identity+pathway": rid(Xboth)}
        # drug-effect additive (C45's original comparator), computed from training rows
        grand = float(y[tr].mean())
        dm = {}
        for i, yy in zip(tr, y[tr]):
            dm.setdefault(A[i], []).append(yy)
            dm.setdefault(B[i], []).append(yy)
        deff = {k: float(np.mean(v)) - grand for k, v in dm.items()}
        pr["additive"] = np.array([deff.get(A[i], 0.0) + deff.get(B[i], 0.0) + grand for i in te])

        perm = rng.permutation(len(te))
        half = len(te) // 2
        for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
            p = te[idxs]
            if len(p) < 100:
                continue
            hit = y[p].astype(float)
            row = {"rep": rep, "part": part, "base": float(hit.mean())}
            for name, sc in pr.items():
                row[name] = float(hit[np.argsort(-sc[idxs])[:K]].mean())
            rows.append(row)

    r = pd.DataFrame(rows)
    ev = r[r.part == "eval"].set_index("rep")
    res = {"kind": "does_annotation_add_anything_beyond_drug_identity",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "holdout": HOLDOUT, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "drugs": len(drugs),
                     "identity_dims": int(Xid.shape[1]), "pathway_dims": int(Xpa.shape[1]),
                     "n_eval": int(len(ev))},
           "summary": {}, "files": {}}
    if len(ev) >= 5:
        res["summary"] = {
            "base": float(ev["base"].mean()),
            "identity": float(ev["identity"].mean()),
            "pathway": float(ev["pathway"].mean()),
            "identity_pathway": float(ev["identity+pathway"].mean()),
            "additive": float(ev["additive"].mean()),
            "identity_minus_pathway": paired(ev["identity"], ev["pathway"], 24001),
            "combined_minus_identity": paired(ev["identity+pathway"], ev["identity"], 24101),
            "additive_minus_identity": paired(ev["additive"], ev["identity"], 24201)}

    s = res["summary"]
    h252 = bool(s and s["combined_minus_identity"]["ci95"][0] <= 0)
    h253 = bool(s and s["combined_minus_identity"]["ci95"][0] > 0)
    h254 = bool(s and h252 and s["identity_minus_pathway"]["ci95"][0] > 0)
    res["decisions"] = {"H252_annotation_adds_nothing_beyond_identity": h252,
                        "H253_annotation_does_add": h253,
                        "H254_C45_is_a_granularity_comparison": h254}
    res["decisions"]["verdict"] = (
        "C45_compares_granularities_and_annotation_adds_nothing_beyond_identity" if h254 else
        "annotation_adds_signal_beyond_identity_C45_was_misread" if h253 else
        "indeterminate")
    res["limits"] = [
        "Only 65 drugs, so the 130-dim identity block can overfit small training sets even with ridge.",
        "The pathway annotation is coarse (about 38 levels), so its information ceiling is low by construction.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r98/PROTOCOL_E093.md",
                "research/2026-10-27-agent-cell-identifiability-r98/e098_granularity.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E098_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E098_rows.csv", index=False)

    print("keys=%d drugs=%d identity_dims=%d pathway_dims=%d n_eval=%d" % (
        len(g), len(drugs), Xid.shape[1], Xpa.shape[1], len(ev)))
    if s:
        for k in ("base", "pathway", "identity", "identity_pathway", "additive"):
            print("  %-18s %.4f" % (k, s[k]))
        for k in ("identity_minus_pathway", "combined_minus_identity", "additive_minus_identity"):
            c = s[k]
            print("  %-24s %+.4f [%+.4f,%+.4f]" % (k, c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
