"""E107: how stable is the annotation increment across independent random streams?

R101 gave +2.87 pp for pathway minus identity on cell_unseen, R106 gave +0.33 pp on the same
contrast, differing only in the random stream. This repeats the whole comparison under five
independent seeds and reports the between-stream spread, which is the quantity that decides
whether the effect should be quoted at all.

Pre-registered in PROTOCOL_E102.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r107"
LAMBDA = 1.0
K = 20
SPLITS = 40
STREAMS = 5
BLOCKS = 8
HOLDOUT = 0.20
N_BOOT = 2000
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def paired(a, b, seed):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(j) < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(seed)
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

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs0 = sorted(set(A) | set(B)); cells0 = sorted(set(CELL))
    Xid = np.hstack([onehot(A, drugs0), onehot(B, drugs0)])
    Xpa = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                     onehot(g["lp"].to_numpy(), sorted(g["lp"].unique())),
                     onehot(g["tissue"].to_numpy(), sorted(g["tissue"].unique()))])
    Xcombo = np.hstack([Xid, Xpa])
    y = g["syn"].to_numpy(bool)

    all_rows = []
    for stream in range(STREAMS):
        seed = 20261027 + stream * 1000
        rng = np.random.default_rng(seed)
        drugs = list(drugs0); cells = list(cells0)
        for rep in range(SPLITS):
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

            f_id = fit(Xid); f_cb = fit(Xcombo)
            acc = []
            for _ in range(BLOCKS):
                R = np.hstack([Xid, rng.normal(size=(len(g), Xpa.shape[1]))])
                acc.append((fit(R), R))
            pools = {"one_unseen": np.where((a_u ^ b_u) & (~cell_u))[0],
                     "cell_unseen": np.where(cell_u & (a_u | b_u))[0],
                     "both_unseen": np.where(a_u & b_u)[0]}
            for pname, pool in pools.items():
                if len(pool) < 60:
                    continue
                s_id = f_id(Xid[pool]); s_cb = f_cb(Xcombo[pool])
                s_r = np.mean([f(XX[pool]) for f, XX in acc], axis=0)
                perm = rng.permutation(len(pool)); half = len(pool) // 2
                for part, idxs in (("search", perm[:half]), ("eval", perm[half:])):
                    if len(idxs) < 40:
                        continue
                    hit = y[pool][idxs].astype(float)
                    all_rows.append({"stream": stream, "rep": rep, "pool": pname, "part": part,
                                     "identity": float(hit[np.argsort(-s_id[idxs])[:K]].mean()),
                                     "combo": float(hit[np.argsort(-s_cb[idxs])[:K]].mean()),
                                     "random": float(hit[np.argsort(-s_r[idxs])[:K]].mean())})

    r = pd.DataFrame(all_rows)
    res = {"kind": "between_stream_stability_of_the_annotation_increment",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "splits_per_stream": SPLITS, "streams": STREAMS, "blocks": BLOCKS,
                        "holdout": HOLDOUT, "lambda": LAMBDA, "n_boot": N_BOOT},
           "audit": {"keys": int(len(g)), "rows": int(len(r))},
           "per_stream": {}, "files": {}}

    for pname in ("one_unseen", "cell_unseen", "both_unseen"):
        res["per_stream"][pname] = {}
        for s in range(STREAMS):
            ev = r[(r.stream == s) & (r["pool"] == pname) & (r.part == "eval")].set_index("rep")
            if len(ev) < 5:
                continue
            res["per_stream"][pname][str(s)] = {
                "n": int(len(ev)),
                "identity": float(ev["identity"].mean()),
                "combo": float(ev["combo"].mean()),
                "random": float(ev["random"].mean()),
                "combo_minus_identity": paired(ev["combo"], ev["identity"], 33001 + s * 10 + len(pname))}

    res["between_stream"] = {}
    for pname, streams in res["per_stream"].items():
        ests = [v["combo_minus_identity"]["mean_diff"] for v in streams.values()]
        sig = sum(1 for v in streams.values() if v["combo_minus_identity"]["ci95"][0] > 0)
        res["between_stream"][pname] = {
            "n_streams": len(ests), "mean": float(np.mean(ests)), "sd": float(np.std(ests, ddof=1)),
            "min": float(np.min(ests)), "max": float(np.max(ests)),
            "n_significant": int(sig),
            "estimates": [round(e, 4) for e in ests]}

    sig_counts = [v["n_significant"] for v in res["between_stream"].values()]
    res["decisions"] = {"significant_streams_per_pool": sig_counts,
                        "H277_robust_sig_in_4_of_5": all(c >= 4 for c in sig_counts),
                        "H278_fragile_sig_in_2_or_fewer": all(c <= 2 for c in sig_counts)}
    res["decisions"]["verdict"] = (
        "increment_is_robust_across_random_streams" if all(c >= 4 for c in sig_counts) else
        "increment_is_fragile_across_random_streams" if all(c <= 2 for c in sig_counts) else
        "increment_is_pool_dependent_and_unstable")
    res["limits"] = [
        "Five streams are enough to see spread but not to estimate its distribution.",
        "The three pools share one training set within a stream.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r107/PROTOCOL_E102.md",
                "research/2026-10-27-agent-cell-identifiability-r107/e107_streams.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E107_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E107_rows.csv", index=False)

    print("rows=%d streams=%d" % (len(r), STREAMS))
    for pname, v in res["between_stream"].items():
        print("  [%-12s] mean %+.4f sd %.4f range [%+.4f,%+.4f] | significant in %d/%d streams" % (
            pname, v["mean"], v["sd"], v["min"], v["max"], v["n_significant"], v["n_streams"]))
        print("      estimates:", v["estimates"])
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
