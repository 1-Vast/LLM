"""E152: is SCALE_SHRUNK a false alarm for a model that standardises its inputs?"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r152"
SEED = 20261055
SCALES = (0.5, 0.1, 0.01, 0.001, 0.0)


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def oh(vals, levels):
    ix = {v: i for i, v in enumerate(levels)}
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        M[t, ix[v]] = 1.0
    return M


def ridge_fp(Xtr, ytr, Xte, lam=1.0):
    mu, sd = Xtr.mean(0), Xtr.std(0); sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
    return ytr.mean() + ((Xte - mu) / sd) @ w


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False,
                    usecols=["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY",
                             "LIBRARY_PATHWAY", "SYNERGY_DELTA_EMAX"])
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
    Xid = np.hstack([oh(A, drugs), oh(B, drugs)])
    Xpa = np.hstack([oh(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                     oh(g["lp"].to_numpy(), sorted(g["lp"].unique()))])
    X = np.hstack([Xid, Xpa])
    y = g["emax"].to_numpy(float)
    rng = np.random.default_rng(SEED)
    idx = rng.permutation(len(g)); cut = int(0.8 * len(g))
    tr, te = idx[:cut], idx[cut:]
    base = ridge_fp(X[tr], y[tr], X[te])
    rows = {}
    for s in SCALES:
        X2 = X.copy(); X2[:, Xid.shape[1]:] = X2[:, Xid.shape[1]:] * s
        p = ridge_fp(X2[tr], y[tr], X2[te])
        delta = float(np.max(np.abs(p - base)))
        rows["%.3f" % s] = {"max_abs_delta": delta, "identical": bool(delta < 1e-9)}
    h370 = all(v["identical"] for k, v in rows.items() if float(k) > 0)
    res = {"kind": "is_scale_shrink_a_no_op_for_a_standardising_model",
           "input_sha256": sha256(ORIG),
           "settings": {"scales": list(SCALES), "seed": SEED},
           "results": rows,
           "decisions": {"H370_scaling_is_a_no_op": bool(h370), "H371_scaling_matters": not h370},
           "decisions_verdict": ("scaling_is_exactly_a_no_op_so_the_ratio_rule_is_a_false_alarm_for_this_model_family"
                                 if h370 else "scaling_changes_predictions"),
           "limits": ["Only for models that standardise inputs; trees on raw inputs and distance methods may be scale sensitive.",
                     "Retrospective; no mechanism, clinical or drug-choice claim."]}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r152/PROTOCOL_E142.md",
                "research/2026-10-27-agent-cell-identifiability-r152/e152_scale_noop.py"):
        p = ROOT / rel
        if p.exists():
            res.setdefault("files", {})[rel] = sha256(p)
    (OUT / "E152_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    for k, v in rows.items():
        print("  scale %-7s max|delta| %.3e  identical=%s" % (k, v["max_abs_delta"], v["identical"]))
    print("H370:", h370)


if __name__ == "__main__":
    main()
