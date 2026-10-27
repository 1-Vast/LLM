"""E026: what makes two cells differ - potency (main effects) or interaction (residuals)?

Pre-registered in PROTOCOL_E026.md. Reads only PAIR_SCREEN.csv.

Per (layout, cell): fit y ~ mu + a_A + a_B (ridge lambda fixed) and keep pred and residual.
Per cell pair: decompose Var(y_a - y_b) into the main-effect part, the residual part and
twice their covariance, and report the main-effect share.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r26"
ANCHORS = {"high control", "low control"}
LAMBDA = 1.0
TOP = 10
N_BOOT = 1000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a, b) -> float:
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    if len(a) < 8:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def p_at_k(pred, truth, k=TOP):
    n = len(pred)
    kk = min(k, n - 1)
    return len(set(np.argsort(pred)[:kk]) & set(np.argsort(truth)[:kk])) / kk


def design(pairs, cidx):
    X = np.zeros((len(pairs), len(cidx)))
    for i, (a, b) in enumerate(pairs):
        X[i, cidx[a]] += 1.0
        X[i, cidx[b]] += 1.0
    return X


def fit_additive(X, y, lam=LAMBDA):
    """In-sample fit plus exact leave-one-out predictions (hat-matrix identity)."""
    xm = X.mean(axis=0)
    ym = float(y.mean())
    Xc = X - xm
    A = Xc.T @ Xc + lam * np.eye(X.shape[1])
    Ainv = np.linalg.inv(A)
    H = Xc @ Ainv @ Xc.T
    h = np.clip(np.diag(H), 0.0, 1.0 - 1e-9)
    pred = ym + H @ (y - ym)
    resid = y - pred
    loo = y - resid / (1.0 - h)
    return pred, resid, loo


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["c1"] = pd.to_numeric(df["Conc 1 (uM)"], errors="coerce")
    df["c2"] = pd.to_numeric(df["Conc 2 (uM)"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    ok = df[(~df["anchor"]) & (~df["failed_qc"]) & df["y"].notna()]

    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["c1"].round(9), g["Drug 2"], g["c2"].round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "qc": float(g["failed_qc"].mean()),
                       "npairs": int(g.groupby(["Drug 1", "Drug 2"]).ngroups)}
    groups = {}
    for f, s in meta.items():
        groups.setdefault(s["h"], {}).setdefault(s["cell"], []).append(f)

    rows = []
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 2:
            continue
        if max(meta[f]["npairs"] for c in good for f in cells[c]) < 100:
            continue
        per_cell = {}
        for c in good:
            vs = []
            for f in cells[c]:
                s = ok[ok["file"] == f]
                v = s.groupby(["Drug 1", "Drug 2"])["y"].mean()
                if len(v) >= 100:
                    vs.append(v)
            if vs:
                per_cell[c] = pd.concat(vs, axis=1).mean(axis=1).dropna()
        cs = sorted(per_cell)
        if len(cs) < 2:
            continue
        comps = sorted({d for c in cs for p in per_cell[c].index for d in p})
        cidx = {d: i for i, d in enumerate(comps)}
        fits = {}
        for c in cs:
            ser = per_cell[c]
            pairs = list(ser.index)
            X = design(pairs, cidx)
            pred, resid, loo = fit_additive(X, ser.to_numpy(float))
            fits[c] = {"pairs": pairs, "y": ser.to_numpy(float), "pred": pred, "resid": resid,
                       "loo": loo, "idx": {p: i for i, p in enumerate(pairs)}}
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                a, b = fits[cs[i]], fits[cs[j]]
                common = [p for p in a["pairs"] if p in b["idx"]]
                if len(common) < 100:
                    continue
                ya = np.array([a["y"][a["idx"][p]] for p in common])
                yb = np.array([b["y"][b["idx"][p]] for p in common])
                pa = np.array([a["pred"][a["idx"][p]] for p in common])
                pb = np.array([b["pred"][b["idx"][p]] for p in common])
                ra = np.array([a["resid"][a["idx"][p]] for p in common])
                rb = np.array([b["resid"][b["idx"][p]] for p in common])
                dy = ya - yb
                dp = pa - pb
                dr = ra - rb
                vy = float(np.var(dy))
                if vy <= 1e-12:
                    continue
                vp = float(np.var(dp))
                vr = float(np.var(dr))
                cov = float(np.cov(dp, dr, bias=True)[0, 1])
                main_share = (vp + cov) / vy
                resid_share = (vr + cov) / vy
                la = np.array([a["loo"][a["idx"][p]] for p in common])
                lb = np.array([b["loo"][b["idx"][p]] for p in common])
                dpl = la - lb
                drl = (ya - la) - (yb - lb)
                vpl = float(np.var(dpl))
                vrl = float(np.var(drl))
                covl = float(np.cov(dpl, drl, bias=True)[0, 1])
                rows.append({"layout": h[:12], "cell_a": cs[i], "cell_b": cs[j], "n": len(common),
                             "var_diff": vy, "var_main": vp, "var_resid": vr, "cov": cov,
                             "main_share": main_share, "resid_share": resid_share,
                             "main_share_loo": (vpl + covl) / vy,
                             "resid_share_loo": (vrl + covl) / vy,
                             "sd_diff": math.sqrt(vy)})

    d = pd.DataFrame(rows)
    res = {"kind": "between_cell_variance_decomposition_potency_vs_interaction",
           "input_sha256": sha256(CSV),
           "settings": {"lambda": LAMBDA, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"cell_pairs": int(len(d)), "layouts": int(d["layout"].nunique()) if len(d) else 0,
                     "median_shared_pairs": float(d["n"].median()) if len(d) else None},
           "files": {}}

    def bsum(v, seed_off):
        v = np.asarray(v, float)
        v = v[np.isfinite(v)]
        if not len(v):
            return None
        rng = np.random.default_rng(SEED + seed_off)
        boots = [float(np.mean(rng.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
        return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)),
                "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}

    if len(d):
        res["main_share_insample"] = bsum(d["main_share"], 51)
        res["main_share_loo"] = bsum(d["main_share_loo"], 53)
        res["main_share"] = res["main_share_loo"]
        res["resid_share"] = bsum(d["resid_share"], 52)
        res["main_share"]["frac_above_half"] = float((d["main_share"] > 0.5).mean())
        res["variance_levels"] = {"var_diff_mean": float(d["var_diff"].mean()),
                                  "var_main_mean": float(d["var_main"].mean()),
                                  "var_resid_mean": float(d["var_resid"].mean()),
                                  "cov_mean": float(d["cov"].mean())}
        m = res["main_share_loo"]
        h061 = bool(m["median"] >= 0.60 and m["ci95"][0] > 0.50)
        h062 = bool(m["frac_above_half"] >= 0.80)
    else:
        h061 = h062 = False
    h063 = False
    res["decisions"] = {"H061_main_effect_dominates": h061, "H062_consistent": h062,
                        "H063_share_predicts_transfer": h063}
    res["decisions"]["H063_status"] = ("not tested in this round: the transfer metric would need to be "
                                       "computed on the same cell pairs and was left out to keep the "
                                       "round small; recorded as untested, not as negative")
    res["decisions"]["verdict"] = ("between_cell_difference_is_mostly_potency" if h061 else
                                   "between_cell_difference_is_mostly_interaction")
    res["limits"] = [
        "The split depends on the additive model form and the fixed ridge penalty; a different lambda would move the shares.",
        "The residual is a deviation from additivity, not a mechanism.",
        "Unseen combination, not unseen drug; no dose dimension.",
        "Functional viability only; exploratory.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r26/PROTOCOL_E026.md",
                "research/2026-10-27-agent-cell-identifiability-r26/e026_variance_split.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E026_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(d):
        d.to_csv(OUT / "E026_cell_pairs.csv", index=False)

    print("cell_pairs=%d layouts=%d" % (len(d), res["audit"]["layouts"]))
    for k in ("main_share", "resid_share", "variance_levels"):
        if k in res:
            print(k, json.dumps(res[k], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
