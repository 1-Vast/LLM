"""E099: settle pathway-versus-capacity with a bagged random-feature control.

R98 used a single random block, which is itself noisy. Here ten random blocks are fitted and
their predicted scores averaged, so the capacity control is stable, and the number of splits
is doubled.

Pre-registered in PROTOCOL_E094.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r99"
LAMBDA = 1.0
K = 20
REPEATS = 80
BLOCKS = 10
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
        a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), syn=("syn", "mean"))
    g["syn"] = g["syn"] > 0.5
    for c in ("a", "b", "ap", "lp", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy()
    B = g["b"].to_numpy()
    drugs = sorted(set(A) | set(B))
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpa = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                     onehot(g["lp"].to_numpy(), sorted(g["lp"].unique())),
                     onehot(g["tissue"].to_numpy(), sorted(g["tissue"].unique()))])
    y = g["syn"].to_numpy(bool)
    drug_order = list(drugs)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        order = list(drug_order)
        rng.shuffle(order)
        held = set(order[: max(3, int(round(HOLDOUT * len(order))))])
        tr = np.where(np.array([(x not in held) and (z not in held) for x, z in zip(A, B)]))[0]
        te = np.where(np.array([(x in held) != (z in held) for x, z in zip(A, B)]))[0]
        if len(tr) < 20000 or len(te) < 400:
            continue
        ytr = y[tr].astype(float)

        def ridge_scores(XX):
            Xt = XX[tr]
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0)
            sd[sd == 0] = 1.0
            Xs = (Xt - mu) / sd
            Am = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
            w = np.linalg.solve(Am, Xs.T @ (ytr - ytr.mean()))
            return ytr.mean() + ((XX[te] - mu) / sd) @ w

        sc_id = ridge_scores(Xid)
        sc_combo = ridge_scores(np.hstack([Xid, Xpa]))
        # bagged random-feature control: 10 independent blocks of the same width
        acc = np.zeros(len(te))
        for _ in range(BLOCKS):
            Xr = rng.normal(size=(len(g), Xpa.shape[1]))
            acc += ridge_scores(np.hstack([Xid, Xr]))
        sc_rand = acc / BLOCKS

        perm = rng.permutation(len(te))
        half = len(te) // 2
        for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
            p = te[idxs]
            if len(p) < 100:
                continue
            hit = y[p].astype(float)
            rows.append({"rep": rep, "part": part, "base": float(hit.mean()),
                         "identity": float(hit[np.argsort(-sc_id[idxs])[:K]].mean()),
                         "identity_pathway": float(hit[np.argsort(-sc_combo[idxs])[:K]].mean()),
                         "identity_random": float(hit[np.argsort(-sc_rand[idxs])[:K]].mean())})

    r = pd.DataFrame(rows)
    ev = r[r.part == "eval"].set_index("rep")
    res = {"kind": "bagged_capacity_control_for_the_annotation_gain",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "repeats": REPEATS, "blocks": BLOCKS, "holdout": HOLDOUT,
                        "lambda": LAMBDA, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "identity_dims": int(Xid.shape[1]),
                     "pathway_dims": int(Xpa.shape[1]), "n_eval": int(len(ev))},
           "summary": {}, "files": {}}
    if len(ev) >= 5:
        res["summary"] = {
            "base": float(ev["base"].mean()),
            "identity": float(ev["identity"].mean()),
            "identity_pathway": float(ev["identity_pathway"].mean()),
            "identity_random_bagged": float(ev["identity_random"].mean()),
            "pathway_minus_identity": paired(ev["identity_pathway"], ev["identity"], 26001),
            "random_minus_identity": paired(ev["identity_random"], ev["identity"], 26101),
            "pathway_minus_random": paired(ev["identity_pathway"], ev["identity_random"], 26201)}

    s = res["summary"]
    h255 = bool(s and s["pathway_minus_random"]["ci95"][0] > 0)
    h256 = bool(s and s["pathway_minus_random"]["ci95"][0] <= 0)
    res["decisions"] = {"H255_annotation_has_a_real_increment": h255,
                        "H256_still_indeterminate": h256}
    res["decisions"]["verdict"] = (
        "annotation_model_is_REFUTED_as_useless" if h255 else
        "still_indeterminate_but_bounded")
    res["limits"] = [
        "Averaging random blocks stabilises the control but still samples only Gaussian nuisance features.",
        "80 splits is better than 40 yet may still be insufficient for an effect near 2 pp.",
        "Pathway annotation has about 41 dimensions, so its information ceiling is low by construction.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r99/PROTOCOL_E094.md",
                "research/2026-10-27-agent-cell-identifiability-r99/e099_bagged_control.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E099_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E099_rows.csv", index=False)

    print("n_eval=%d dims=%d+%d" % (len(ev), Xid.shape[1], Xpa.shape[1]))
    if s:
        for k in ("base", "identity", "identity_pathway", "identity_random_bagged"):
            print("  %-24s %.4f" % (k, s[k]))
        for k in ("pathway_minus_identity", "random_minus_identity", "pathway_minus_random"):
            c = s[k]
            print("  %-24s %+.4f [%+.4f,%+.4f]" % (k, c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
